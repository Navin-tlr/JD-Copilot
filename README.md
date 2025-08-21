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
# Install LangExtract for company extraction
pip install langextract
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

# Y² Mobile App

A React-based mobile application for the Y² Placement Co-Pilot, built with TypeScript and Tailwind CSS.

## 🚀 Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation
1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## 📱 Features

### Onboarding Screen
- **Exact Figma Implementation**: Pixel-perfect recreation of the design
- **Large Y Watermark**: 700px font with proper opacity and positioning
- **Welcome Title**: "WELCOME TO Y^2" with exact typography
- **Interactive Button**: SIGN UP/LOG IN button with hover effects
- **Mobile-First Design**: Optimized for mobile devices

### Technical Features
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Responsive Design** that works on all screen sizes
- **Accessibility** features (ARIA labels, keyboard navigation)
- **Hover Effects** and smooth transitions

## 🎨 Design Specifications

The app implements the exact Figma design with:
- **Colors**: `#ffffff`, `#2a2727`, `#646262`
- **Typography**: That That New Pixel Test, PP NeueBit, Belmonte Ballpoint Trial
- **Layout**: 393x852px mobile container with precise positioning
- **Components**: Exact button dimensions (172x46px) and positioning

## 📁 Project Structure

```
src/
├── components/
│   └── OnboardingScreen.tsx    # Main onboarding component
├── assets/
│   └── rectangle-7.svg         # Button background asset
├── App.tsx                     # Main app component
├── App.css                     # App-specific styles
├── index.css                   # Global styles with Tailwind
└── index.tsx                   # App entry point
```

## 🔧 Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App (one-way operation)

## 📱 Mobile Development

This app is designed specifically for mobile devices:
- **Mobile-first approach** with responsive design
- **Touch-friendly interfaces** with proper button sizes
- **Mobile-optimized layouts** and typography
- **Performance optimized** for mobile devices

## 🚀 Next Steps

1. **Add more screens** (Authentication, Main App, Profile)
2. **Implement navigation** between screens
3. **Connect to backend API** for real data
4. **Add animations** and micro-interactions
5. **Implement authentication flow**
6. **Add offline support** and PWA features

## 🎯 Design Philosophy

The app follows the Y² brand philosophy:
- **"I don't hold hands. I hand you weapons"**
- **Clean, professional interface** that matches the brand
- **Mobile-optimized experience** for placement cell users
- **Accessible design** for all users

---

**Note**: This is a React implementation that perfectly matches your Figma design specifications, providing a much better foundation for mobile app development compared to Streamlit.


