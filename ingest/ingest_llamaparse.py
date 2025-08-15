from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Dict, List

from llama_parse import LlamaParse
from tqdm import tqdm

from app.config import get_settings
from app.rag import EmbeddingBackend
from app.utils import stable_chunk_id, slugify_company
from ingest.chunking import hybrid_chunk_sections
from ingest.langextract_job import run_extraction
from pinecone import Pinecone, ServerlessSpec
import certifi, ssl
import urllib3


def parse_pdf_or_text_llama(path: Path) -> Dict[str, Any]:
    """Parse PDF via LlamaParse (fail-fast). For .txt, load as one section."""
    settings = get_settings()

    if path.suffix.lower() == ".txt":
        text = path.read_text(errors="ignore")
        if not text.strip():
            raise RuntimeError(f"Empty text in {path}")
        return {"sections": [{
            "id": "0",
            "type": "text",
            "text": text,
            "headings": [],
            "char_start": 0,
            "char_end": len(text),
            "page_number": None,
        }]}

    api_key = settings.LLAMAPARSE_API_KEY or os.getenv("LLAMAPARSE_API_KEY")
    if not api_key:
        raise RuntimeError("LLAMAPARSE_API_KEY is required for PDF ingestion with LlamaParse")

    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        use_vendor_multimodal_model=True,
        num_workers=4,
        verbose=True,
        # Workaround for SSL issues
        check_local_models=False,
        # DANGEROUS: For local dev only
        ssl_verify=False,
    )
    # Force certifi CA on urllib3 globally
    try:
        urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    except Exception:
        pass
    docs = parser.load_data(str(path))
    if not docs:
        raise RuntimeError(f"LlamaParse produced no documents for {path}")

    sections: List[Dict[str, Any]] = []
    cursor = 0
    for idx, doc in enumerate(docs):
        md = (doc.text or "").strip()
        if not md:
            continue
        sec_type = "table" if ("|" in md and "---" in md) else "text"
        start = cursor
        end = cursor + len(md)
        sections.append({
            "id": str(idx),
            "type": sec_type,
            "text": md,
            "headings": [],
            "char_start": start,
            "char_end": end,
            "page_number": getattr(doc, "metadata", {}).get("page", idx + 1) if hasattr(doc, "metadata") else idx + 1,
        })
        cursor = end + 2

    if not sections:
        raise RuntimeError(f"LlamaParse returned empty text for {path}")

    return {"sections": sections}


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

    vectors = [{"id": id_, "values": vec.tolist(), "metadata": meta}
               for id_, vec, meta in zip(ids, embeddings, metadatas)]
    index.upsert(vectors=vectors)
    return len(ids)


def process_file(path: Path) -> int:
    parsed = parse_pdf_or_text_llama(path)
    text_all = "\n\n".join(sec.get("text", "") for sec in parsed.get("sections", []))
    preview = (text_all or "")[:500]
    print(f"Preview for {path.name}:\n{preview}\n{'-'*80}")

    # Heuristic extraction to enrich metadata (company, role, year, skills)
    basename = path.stem
    langext = run_extraction(basename, text_all)
    sections = parsed.get("sections", [])
    canonical_company = langext.get("company")
    company_slug = slugify_company(canonical_company)
    for s in sections:
        s["extracted_skills"] = langext.get("skills", [])
        s["company"] = canonical_company
        s["company_slug"] = company_slug
        s["role"] = langext.get("role")
        s["year"] = langext.get("year")
        s["langext_approximate"] = bool(langext.get("approximate", False))
    chunks = hybrid_chunk_sections(sections)

    for c in chunks:
        c["source_file"] = str(path.name)
        c["_id"] = stable_chunk_id(
            source_file=c["source_file"],
            section_id=str(c.get("id", "0")),
            chunk_idx=int(c.get("chunk_idx", 0)),
            start_char=int(c.get("char_start", 0)),
            end_char=int(c.get("char_end", 0)),
        )
        c["chunk_text"] = c.get("chunk_text") or c.get("text") or ""

    n = upsert_chunks_pinecone(chunks, str(path))
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_dir", type=str, required=True, help="Directory of PDFs or .txt files")
    args = parser.parse_args()

    files = []
    for ext in ("*.pdf", "*.PDF", "*.txt"):
        files.extend(sorted(Path(args.pdf_dir).glob(ext)))
    if not files:
        print("No files found to ingest.")
        return
    total = 0
    for f in tqdm(files, desc="Ingesting"):
        total += process_file(f)
    print(f"Upserted {total} chunks to Pinecone.")


if __name__ == "__main__":
    main()


