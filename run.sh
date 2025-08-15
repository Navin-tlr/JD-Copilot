#!/usr/bin/env bash
set -euo pipefail

python -m ingest.ingest_docling --pdf_dir data/jds --persist_dir data/chroma
uvicorn app.main:app --reload --port 8000


