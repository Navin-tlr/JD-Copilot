## jd-copilot

Robust local-first RAG pipeline for Job Descriptions (JDs). Ingest JD PDFs or plain-text, extract structured fields, chunk intelligently, embed locally, index into ChromaDB, and expose a FastAPI API for JD Q&A, resume↔JD match, GD simulate, and alerts.

### Quickstart

1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Configure environment

```bash
cp env.example .env
# optionally edit .env for CHROMA_DIR, EMBED_MODEL, and LLM keys
```

4) Put JD PDFs or .txt files in `data/jds/`

5) Ingest and run API server

```bash
# Option A: one-liner helper
bash run.sh

# Option B: manual (Pinecone cloud-first)
python -m ingest.pipeline --pdf_dir data/jds
uvicorn app.main:app --reload --port 8000
```

### Example API calls

```bash
# JD Q&A
curl -s -X POST "http://localhost:8000/query" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the CTC?", "filters": {"company": null, "year": null}, "top_k": 5}' | jq

# Resume ↔ JD match
curl -s -X POST "http://localhost:8000/query/resume_match" \
  -H 'Content-Type: application/json' \
  -d '{"resume_text":"Experienced Python and ML engineer with NLP projects.", "top_k": 3}' | jq

# Alerts (dev stub)
curl -s http://localhost:8000/alerts | jq
```

### Architecture

```
          +-----------------+
          |  PDFs / .txt    |
          +--------+--------+
                   |
                   v
   Docling (primary) / pdfplumber/fitz (fallback)
                   |
                   v
     LangExtract (primary) / Regex-Heuristics (fallback)
                   |
                   v
  Hybrid Chunking (Docling sections → splitter for long)
                   |
                   v
   Embeddings: SentenceTransformers (local) / OpenAI optional
                   |
                   v
           ChromaDB (persistent)
                   |
                   v
           FastAPI RAG endpoints
```

### Optional LLMs (for synthesis)

- OpenAI: set `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env`.
- Gemini: set `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env`.

If keys are not present, jd-copilot still runs fully locally and returns retrieved snippets. With keys, the API also returns a concise, cited answer synthesized from retrieved snippets (low temperature, sources cited inline as `[Company | Role | Year]`).

### Cloud-first & Fallbacks

- LlamaParse is the primary parser for PDFs (tables/images preserved). If parsing fails or returns empty text, ingestion fails fast with a clear error.
- LangExtract is the primary schema extractor. If unavailable, a deterministic regex/heuristic extractor runs and marks results as `approximate: true`.
- Chunking uses Docling sections; long sections are split into ~500–800 token chunks with 100–200 overlap. Tables/salary rows remain atomic and get flattened summaries for numeric queries.
- Embeddings use a local SentenceTransformers model.
- Vectors are stored in Pinecone (cloud-first), configured via `.env` (`PINECONE_API_KEY`, `PINECONE_INDEX_NAME`).

### Project Layout

```
app/
  __init__.py
  config.py
  main.py
  schemas.py
  rag.py
  utils.py
ingest/
  __init__.py
  pipeline.py
  langextract_job.py
  chunking.py
  metadata_normalize.py
ui/
  streamlit_app.py
dev_tools/
  sample_jd_texts/
    sample_jd_1.txt
    sample_jd_2.txt
  reindex.py
  alerts_stub.py
tests/
  test_ingest_pipeline.py
  test_query_api.py
data/
  jds/
  chroma/
  docling_json/
  langext_html/
  langext_json/
  gd_notes/
  ingest_failures.json
  alerts.json
```

### Enabling Docling and LangExtract

- Docling docs: see `docling` on PyPI and its documentation for system dependencies.
- LangExtract docs: see `langextract` on PyPI; configure provider credentials as required.

Both are optional for local testing. The pipeline falls back gracefully when unavailable.

### Exact run commands

```bash
# create venv & install deps
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# ingest PDFs (or .txt) to Pinecone
python -m ingest.pipeline --pdf_dir data/jds

# start the API server
uvicorn app.main:app --reload --port 8000
```

### Testing

```bash
pytest -q
```

Tests use `dev_tools/sample_jd_texts/` to validate ingestion and API endpoints without requiring Docling or LangExtract. No network LLM calls are made during tests.


