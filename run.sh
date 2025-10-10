#!/usr/bin/env bash
set -euo pipefail

if command -v pnpm >/dev/null 2>&1; then
	pnpm --dir spark-home-2 install --frozen-lockfile
	pnpm --dir spark-home-2 build
else
	echo "pnpm not found on PATH; skipping spark-home-2 UI build" >&2
fi

python -m ingest.pipeline --pdf_dir data/jds
uvicorn app.main:app --reload --port 8000 --reload-exclude "venv/*"


