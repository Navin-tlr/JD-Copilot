#!/usr/bin/env bash
set -euo pipefail

# Configure SSL via certifi
CERT_PATH=$(python - <<'PY'
import certifi; print(certifi.where())
PY
)
export SSL_CERT_FILE="$CERT_PATH"
export REQUESTS_CA_BUNDLE="$CERT_PATH"
export HF_HUB_ENABLE_HF_TRANSFER=0

MODELS_DIR="${DOCLING_MODELS_DIR:-data/docling_models}"
mkdir -p "$MODELS_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "git not found" >&2
  exit 1
fi
if ! command -v git-lfs >/dev/null 2>&1; then
  echo "git-lfs not found. Install git-lfs first." >&2
  exit 1
fi

git lfs install
rm -rf "$MODELS_DIR/docling-models"
git clone https://huggingface.co/ds4sd/docling-models "$MODELS_DIR/docling-models"

LAYOUT_DIR="$MODELS_DIR/docling-models/model_artifacts/layout"
if ! ls "$LAYOUT_DIR"/**/model.* >/dev/null 2>&1; then
  echo "Docling layout model not found under $LAYOUT_DIR" >&2
  exit 2
fi

echo "Docling models cloned to $MODELS_DIR/docling-models"


