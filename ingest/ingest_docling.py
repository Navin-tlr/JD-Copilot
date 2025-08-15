from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List

from tqdm import tqdm

from app.config import get_settings
from app.utils import append_failure_log, stable_chunk_id
from app.rag import EmbeddingBackend
from .chunking import hybrid_chunk_sections
from .langextract_job import run_extraction
from pinecone import Pinecone, ServerlessSpec


def parse_pdf_or_text(path: Path) -> Dict[str, Any]:
    """Parse document with Docling only. Fail fast on error or empty text."""
    text = ""
    basename = path.stem
    settings = get_settings()
    out_json = Path(settings.DOCLING_JSON_DIR) / f"{basename}.json"
    out_md = Path(settings.DOCLING_JSON_DIR) / f"{basename}.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".txt":
        # For tests, allow .txt as source but still require non-empty content
        text = path.read_text(errors="ignore")
        if not text.strip():
            raise RuntimeError(f"Empty text in {path}")
        sections = [{
            "id": "0",
            "type": "text",
            "text": text,
            "headings": [],
            "char_start": 0,
            "char_end": len(text),
        }]
        out_json.write_text(json.dumps({"sections": sections}, indent=2))
        out_md.write_text(text)
        return {"sections": sections}

    # Docling only
    from docling.document_converter import DocumentConverter  # type: ignore

    # Fail-fast: ensure model assets are present in the configured models dir
    models_base = Path(settings.DOCLING_MODELS_DIR) / "docling-models"
    required = models_base / "model_artifacts" / "layout" / "beehive_v0.0.5"
    if not (required.exists() and any(required.glob("**/model.*"))):
        raise RuntimeError(
            f"Missing required Docling model assets under {required}. Run dev_tools/bootstrap_docling_cache.sh first."
        )

    # Configure Docling to use local model artifacts
    conv = DocumentConverter(artifacts_path=str(models_base))
    doc = conv.convert(str(path))
    md = doc.render_as_markdown()
    out_md.write_text(md)
    sections: List[Dict[str, Any]] = []
    cursor = 0
    sid = 0
    for block in md.split("\n\n"):
        block_text = block.strip()
        if not block_text:
            continue
        sec_type = "table" if "|" in block_text and "---" in block_text else "text"
        start = cursor
        end = cursor + len(block_text)
        sections.append({
            "id": str(sid),
            "type": sec_type,
            "text": block_text,
            "headings": [],
            "char_start": start,
            "char_end": end,
        })
        sid += 1
        cursor = end + 2
    if not sections:
        raise RuntimeError(f"Docling produced no sections for {path}")
    out_json.write_text(json.dumps({"sections": sections}, indent=2))
    return {"sections": sections}


def upsert_chunks_pinecone(chunks: List[Dict[str, Any]], source_file: str) -> int:
    settings = get_settings()
    if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
        raise RuntimeError("Pinecone env not configured. Set PINECONE_API_KEY and PINECONE_INDEX_NAME in .env")
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    # Create index if not exists with sentence-transformers dim (defaults to 384; auto-detect via embedder)
    embedder = EmbeddingBackend(settings.EMBED_MODEL)
    dim = embedder.dim
    indexes = {i.name for i in pc.list_indexes()}
    if settings.PINECONE_INDEX_NAME not in indexes:
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
        )
    else:
        # Check existing index dimension
        index_info = pc.describe_index(settings.PINECONE_INDEX_NAME)
        existing_dim = index_info.dimension
        if existing_dim != dim:
            print(f"⚠ Warning: Index dimension ({existing_dim}) doesn't match embedding dimension ({dim})")
            print(f"  Either delete the index or use an embedding model with {existing_dim} dimensions")
    index = pc.Index(settings.PINECONE_INDEX_NAME)

    documents = [c["chunk_text"] for c in chunks]
    embeddings = embedder.embed(documents)
    ids = [c["_id"] for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {k: v for k, v in c.items() if k not in {"_id"}}
        meta["chunk_id"] = c.get("_id")
        meta["page_number"] = c.get("page_number", None)
        metadatas.append(meta)

    vectors = [
        {"id": id_, "values": vec.tolist(), "metadata": meta}
        for id_, vec, meta in zip(ids, embeddings, metadatas)
    ]
    # Upsert to Pinecone
    index.upsert(vectors=vectors)
    return len(ids)


def process_file(path: Path) -> int:
    settings = get_settings()
    parsed = parse_pdf_or_text(path)
    basename = path.stem
    text_all = "\n\n".join(sec.get("text", "") for sec in parsed.get("sections", []))
    # Debug preview
    preview = (text_all or "")[:500]
    print(f"Preview for {path.name}:\n{preview}\n{'-'*80}")
    langext = run_extraction(basename, text_all)
    sections = parsed.get("sections", [])
    for s in sections:
        s["extracted_skills"] = langext.get("skills", [])
        s["company"] = langext.get("company")
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


