# AGENTS.md
This file provides guidance to agents when working with code in this repository.

## Critical Project Patterns

### Hybrid Classification System
- Role types use both rule-based (`app/role_type_classifier.py`) and LLM-based classification (`app/llm_role_type_classifier.py`)
- Always call `classify_role_types_rule()` before LLM classification
- Classification results stored in `_role_type_debug` metadata field

### PDF Ingestion
- Requires `LLAMA_CLOUD_API_KEY` for production PDF parsing
- Fallback to filename analysis if company detection fails
- Chunking uses `RecursiveCharacterTextSplitter` (700/150 size/overlap)

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

# Full ingestion pipeline
python -m ingest.pipeline --pdf_dir data/jds