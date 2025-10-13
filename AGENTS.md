# AGENTS.md
This file provides guidance to agents when working with code in this repository.

## Critical Project Patterns

### Hybrid Classification System
- Role types use both rule-based (`app/role_type_classifier.py`) and LLM-based classification (`app/llm_role_type_classifier.py`)
- Always call `classify_role_types_rule()` before LLM classification
- Classification results stored in `_role_type_debug` metadata field

### PDF Ingestion
- Requires `LLAMA_CLOUD_API_KEY` for production PDF parsing
- Multi-tier company detection: Structured → Content → Filename → Vision (logo)
- Vision-based logo detection as final fallback (requires `pdf2image` and `OPENROUTER_API_KEY`)
- Chunking uses `RecursiveCharacterTextSplitter` (700/150 size/overlap)
- Garbage company name validation prevents false positives like "pdf_123"

### Pinecone Integration
- Index validation checks dimension match (384 default)
- Metadata includes `company_norm` (normalized lowercase alphanumeric)
- Batch upsert handles 403 errors gracefully

## Key Commands
```bash
# Run single test with warnings filtered
python -m pytest tests/test_specific.py -k "test_name" -p no:warnings

# Start dev server with auto-reload
uvicorn app.main:app --reload --port 8000

# Full ingestion pipeline (with vision detection)
python -m ingest.pipeline --pdf_dir data/jds

# Install vision detection dependencies (optional)
pip install pdf2image pillow
brew install poppler  # macOS
```

## Company Detection Strategy

The ingestion pipeline uses 4 methods (in priority order):

1. **Structured Extraction** - LLM parses document text (highest priority)
2. **Content Analysis** - Regex patterns in text
3. **Filename Detection** - Extracts from filename (e.g., `Google_SDE_2024.pdf`)
4. **Vision Detection** - Claude 3.5 Sonnet analyzes logo (final fallback, PDFs only)

Vision detection only runs when all text-based methods fail. See `VISION_LOGO_DETECTION.md` for details.