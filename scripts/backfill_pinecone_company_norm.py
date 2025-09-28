#!/usr/bin/env python3
"""Re-ingest placement PDFs to backfill Pinecone company_norm metadata.

This script is an idempotent wrapper around the existing ingest pipeline. It
reprocesses every document in a directory, re-chunks it with the latest
normalization logic, and upserts the vectors to Pinecone so that
`company_norm` is guaranteed to be populated for every chunk.

Example usage:
```bash
python scripts/backfill_pinecone_company_norm.py --pdf-dir data/jds
```

Use `--dry-run` to preview the files that would be processed without
touching Pinecone.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ingest.pipeline import process_file
from app.rag import get_pinecone_index


def gather_files(pdf_dir: Path) -> List[Path]:
    files: List[Path] = []
    for pattern in ("*.pdf", "*.PDF", "*.txt", "*.docx", "*.DOCX"):
        files.extend(sorted(pdf_dir.glob(pattern)))
    return sorted(set(files))


def describe_index_counts() -> int | None:
    try:
        index = get_pinecone_index()
    except RuntimeError as exc:
        print(f"⚠️ Pinecone not configured: {exc}")
        return None

    try:
        stats = index.describe_index_stats()
    except Exception as exc:
        print(f"⚠️ Could not read Pinecone stats: {exc}")
        return None

    total = stats.get("total_vector_count")
    if total is None:
        namespaces = stats.get("namespaces") or {}
        total = sum(ns.get("vector_count", 0) for ns in namespaces.values())
    print(f"📊 Pinecone vector count: {total}")
    return int(total) if total is not None else None


def run_ingest(files: List[Path]) -> Tuple[int, List[str]]:
    total_chunks = 0
    companies: List[str] = []
    for path in files:
        print(f"\n🚀 Re-ingesting {path.name} ...")
        chunks, company = process_file(path)
        total_chunks += chunks
        if company:
            companies.append(company)
    return total_chunks, companies


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill Pinecone metadata by re-ingesting PDFs with the latest pipeline logic.")
    parser.add_argument("--pdf-dir", type=str, default="data/jds", help="Directory containing source PDFs or TXT files.")
    parser.add_argument("--dry-run", action="store_true", help="List the files that would be re-ingested without calling Pinecone.")
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {pdf_dir}")

    files = gather_files(pdf_dir)
    if not files:
        print(f"No PDFs or text files found in {pdf_dir}")
        return

    print(f"Found {len(files)} files to re-ingest from {pdf_dir}")
    for p in files:
        print(f"  • {p.name}")

    if args.dry_run:
        print("\nDry-run complete. Re-run without --dry-run to update Pinecone metadata.")
        return

    before = describe_index_counts()
    total_chunks, companies = run_ingest(files)
    after = describe_index_counts()

    print("\n✅ Backfill complete!")
    print(f"Re-ingested {len(files)} files, upserting {total_chunks} chunks.")
    if companies:
        unique_companies = sorted(set(companies))
        print(f"Companies updated: {', '.join(unique_companies)}")
    if before is not None and after is not None:
        delta = after - before
        print(f"Pinecone vector count delta: {delta} (before={before}, after={after})")


if __name__ == "__main__":
    main()
