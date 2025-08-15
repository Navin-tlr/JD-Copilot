#!/usr/bin/env bash
set -euo pipefail

python -m ingest.pipeline --pdf_dir data/jds
uvicorn app.main:app --reload --port 8000


