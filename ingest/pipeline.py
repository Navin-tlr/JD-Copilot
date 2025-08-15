from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import certifi
import ssl
import urllib3
from llama_parse import LlamaParse
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

from app.config import get_settings
from app.rag import EmbeddingBackend
from app.utils import stable_chunk_id
from ingest.company_extractor import extract_company
from langchain_text_splitters import RecursiveCharacterTextSplitter


def _read_text_from_path(path: Path) -> str:
    """Return raw text for a file. For PDFs, use LlamaParse (LLAMA_CLOUD_API_KEY)."""
    if path.suffix.lower() == ".txt":
        txt = path.read_text(errors="ignore")
        if not txt.strip():
            raise RuntimeError(f"Empty text in {path}")
        return txt

    # Prefer LLAMA_CLOUD_API_KEY; fallback to LLAMAPARSE_API_KEY if present
    api_key = os.getenv("LLAMA_CLOUD_API_KEY") or os.getenv("LLAMAPARSE_API_KEY") or get_settings().LLAMAPARSE_API_KEY
    if not api_key:
        raise RuntimeError("LLAMA_CLOUD_API_KEY is required for PDF ingestion with LlamaParse")

    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        use_vendor_multimodal_model=True,
        num_workers=4,
        verbose=True,
        check_local_models=False,
    )
    # Harden SSL with certifi
    try:
        urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
        ssl.create_default_context(cafile=certifi.where())
        urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())
    except Exception:
        pass

    docs = parser.load_data(str(path))
    if not docs:
        raise RuntimeError(f"LlamaParse produced no documents for {path}")
    parts: List[str] = []
    for d in docs:
        t = (getattr(d, "text", None) or "").strip()
        if t:
            parts.append(t)
    text = "\n\n".join(parts).strip()
    if not text:
        raise RuntimeError(f"LlamaParse returned empty text for {path}")
    return text


def upsert_chunks_pinecone(chunks: List[Dict[str, Any]], source_file: str) -> int:
    settings = get_settings()
    if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
        # No Pinecone creds; skip upsert
        return len(chunks)

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    embedder = EmbeddingBackend(settings.EMBED_MODEL)
    dim = embedder.dim

    existing = {i.name for i in pc.list_indexes()}
    if settings.PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
        )
    else:
        info = pc.describe_index(settings.PINECONE_INDEX_NAME)
        if info.dimension != dim:
            raise RuntimeError(f"Pinecone index dim={info.dimension} != embedding dim={dim}. Recreate index with {dim}.")

    index = pc.Index(settings.PINECONE_INDEX_NAME)

    documents = [c["chunk_text"] for c in chunks]
    embeddings = embedder.embed(documents)
    ids = [c["_id"] for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {k: v for k, v in c.items() if k not in {"_id"}}
        meta["chunk_id"] = c.get("_id")
        meta["page_number"] = c.get("page_number", None)
        # sanitize: remove None values and coerce simple types only
        clean_meta: Dict[str, Any] = {}
        for k, v in meta.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif isinstance(v, list):
                clean_meta[k] = [x for x in v if isinstance(x, (str, int, float, bool))]
        metadatas.append(clean_meta)

    vectors = [
        {"id": id_, "values": vec.tolist(), "metadata": meta}
        for id_, vec, meta in zip(ids, embeddings, metadatas)
    ]
    index.upsert(vectors=vectors)
    return len(ids)


def extract_company_name(text: str) -> Optional[str]:
    """Heuristic company extractor without external LLMs.

    Strategy:
    1) Look for explicit labels like "Company:", "Employer:", "Organization:" early in the text
    2) Look for a heading like "About <Company>" (but not "About Us")
    3) Fallback: first all-uppercase heading line near the top (1–2 words)
    Returns canonicalized name or None.
    """
    import re

    head = text[:3000]  # focus on the start of the document
    lines = [ln.strip() for ln in head.splitlines() if ln.strip()]

    # 1) Labeled patterns
    labeled_patterns = [
        r"(?i)^(?:company|company name|employer|organization)\s*[:\-]\s*(.+)$",
        r"(?i)^\*?\s*(?:company|employer)\s*[:\-]\s*(.+)$",
    ]
    for pat in labeled_patterns:
        for ln in lines[:50]:  # scan first 50 non-empty lines
            m = re.match(pat, ln)
            if m:
                raw = m.group(1).strip(" \t\n\r-–—|,:;()[]{}\"'")
                if raw and len(raw) >= 2:
                    return canonicalize_company(raw)

    # 2) "About <Company>" heading (avoid "About Us")
    about_patterns = [
        r"(?i)^about\s+(?!us\b)([A-Za-z0-9&.,'\- ]{2,})\s*:?$",
        r"(?i)\babout\s+(?!us\b)([A-Za-z0-9&.,'\- ]{2,})\b",
    ]
    for pat in about_patterns:
        for ln in lines[:80]:
            m = re.search(pat, ln)
            if m:
                raw = m.group(1).strip(" \t\n\r-–—|,:;()[]{}\"'")
                # Avoid capturing generic words
                if raw.lower() not in {"company", "organization", "employer", "academy"}:
                    return canonicalize_company(raw)

    # 3) First all-uppercase heading (1-2 words)
    def is_all_caps_heading(s: str) -> bool:
        # consider only A–Z and common punctuation
        if len(s) < 3 or len(s) > 50:
            return False
        words = [w for w in re.split(r"\s+", s) if w]
        if not (1 <= len(words) <= 3):
            return False
        if any(w.lower() in {"about", "job", "description", "role", "department", "experience", "education", "join", "apprentice", "program"} for w in words):
            return False
        # 80% or more uppercase or punctuation
        letters = [ch for ch in s if ch.isalpha()]
        if not letters:
            return False
        upper = sum(1 for ch in letters if ch.isupper())
        return upper / max(1, len(letters)) >= 0.8

    for ln in lines[:40]:
        if is_all_caps_heading(ln):
            return canonicalize_company(ln)

    return None


def _split_into_chunks(text: str, chunk_size: int, chunk_overlap: int) -> List[Tuple[int, str]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max(100, chunk_size),
        chunk_overlap=max(0, min(chunk_overlap, chunk_size // 2)),
        separators=["\n\n", "\n", ". ", "? ", "! ", "; ", ": ", ", ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return list(enumerate(chunks))


def process_file(path: Path) -> Tuple[int, Optional[str]]:
    """Parse → extract company → chunk → embed → upsert. Returns (num_chunks, company)."""
    settings = get_settings()
    text = _read_text_from_path(path)
    preview = text[:500]
    print(f"Preview for {path.name}:\n{preview}\n{'-'*80}")

    # Extract company once per document using LangExtract (with robust prompt)
    company_name: Optional[str] = extract_company(text)
    if company_name:
        print(f"✅ company={company_name} file={path.name}")
    else:
        print(f"❌ no company extracted file={path.name}")

    # Chunk using RecursiveCharacterTextSplitter
    chunk_size = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
    enumerated = _split_into_chunks(text, chunk_size, chunk_overlap)

    # Build chunk dicts expected by upsert_chunks_pinecone
    chunks: List[Dict[str, Any]] = []
    for idx, chunk_text in enumerated:
        chunk_id = stable_chunk_id(
            source_file=path.name,
            section_id="0",
            chunk_idx=idx,
            start_char=0,
            end_char=0,
        )
        meta: Dict[str, Any] = {
            "chunk_text": chunk_text,
            "text": chunk_text,
            "source": path.name,
            "chunk_index": idx,
        }
        if company_name:
            meta["company"] = company_name
        chunks.append({"_id": chunk_id, **meta})

    n = upsert_chunks_pinecone(chunks, str(path))
    return n, company_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_dir", type=str, required=True, help="Directory of PDFs or .txt files")
    args = parser.parse_args()

    files: List[Path] = []
    for ext in ("*.pdf", "*.PDF", "*.txt"):
        files.extend(sorted(Path(args.pdf_dir).glob(ext)))
    if not files:
        print("No files found to ingest.")
        return

    total_chunks = 0
    companies: Set[str] = set()
    for f in tqdm(files, desc="Ingesting"):
        n, comp = process_file(f)
        total_chunks += n
        if comp:
            companies.add(comp)

    # Write companies.json at project root
    try:
        companies_path = Path("companies.json")
        companies_path.write_text(json.dumps(sorted(companies), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved {len(companies)} companies to {companies_path.resolve()}")
    except Exception as e:
        print(f"Could not write companies.json: {e}")

    print(f"Upserted {total_chunks} chunks to Pinecone.")


if __name__ == "__main__":
    main()


