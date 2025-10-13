# JD-Copilot Master Guide

## System Overview
- **Purpose**: JD-Copilot ingests job-description documents, normalizes them into structured placement intelligence, and exposes conversational and analytical tooling for placement teams.
- **Core Pillars**: (1) A FastAPI backend that orchestrates ingestion, retrieval-augmented generation (RAG), structured insights, and chat session management. (2) A Vite/React frontend (Spark Home UI) that delivers analyst-grade UX for querying placements, monitoring conversations, and managing history.
- **Data Flow**: PDF/TXT → Ingestion pipeline → Local SQLite + Pinecone (optional) → FastAPI endpoints → React client (RAGMode, Benchmark, History).

```text
+----------------+       +---------------------+       +-------------------+
|   Documents    |  -->  |  ingest.pipeline    |  -->  |  Storage Layer    |
|  (PDF / TXT)   |       |  (parsing, RAG prep)|       |  • SQLite (facts) |
+----------------+       +---------------------+       |  • Pinecone (vec) |
                                                       +---------+---------+
                                                                 |
                                   +-----------------------------+-----------------------------+
                                   |                                                           |
                          +--------v--------+                                           +------v------+
                          |  FastAPI API    |                                           | Spark UI    |
                          |  app/main.py    |<--JSON/REST/WebSocket-->                  | React + Vite|
                          +-----------------+                                           +-------------+
```

## Backend Architecture

### Technology Stack
- Python 3 / FastAPI (`app/main.py`) for HTTP APIs.
- Async orchestration with native asyncio tasks inside `app/chat_service.py`.
- SQLite via `app/database.py` for structured placement data; optional Pinecone vector index managed in `app/rag.py`.
- RAG assembly with local SentenceTransformers embeddings (deterministic fallback when offline).
- Specialized classification modules (`app/hybrid_role_classifier.py`, `app/role_type_classifier.py`, `app/llm_role_type_classifier.py`).
- Durable workflow and enhanced memory helpers in `app/durable_workflow.py` and `app/enhanced_chat_memory.py`.

### API Surface (`app/main.py`)
- Initializes FastAPI app, CORS, static bundle serving (`spark-home-2/dist/spa`), and router registration (`chat_api`, `workflow_api`).
- **Primary endpoints**:
  - `POST /chat` and `POST /query`: conversational RAG with deep-dive escalation. Uses `chat_service.send_message` asynchronously and decorates UI hints (`deep_dive_*` flags).
  - `POST /chat/vector`: forces unstructured retrieval for human-approved dives, synthesizes answers via `synthesize_answer`.
  - `POST /chat/enhanced`: variant wired to durable workflow state, using `enhanced_memory_manager` for detailed telemetry.
  - `GET/POST/DELETE /chat/sessions/*`: session lifecycle operations exposed via `app/chat_api.py`.
  - Legacy structured routes (e.g., `/query/resume_match`) are implemented inside `app/agent.py`, `app/rag.py`, and `app/final_sql_tool.py`.
- Shared chat history persistence uses `chat_history_store.sync_session` to mirror the in-memory transcript for UI replay.

### Chat Service (`app/chat_service.py`)
- `ChatService` holds active `ChatSession` metadata and `EnhancedConversationMemory` buffers per session.
- Memory limits configurable via `CHAT_SESSION_MEMORY_LIMIT` and `CHAT_SESSION_MESSAGE_LIMIT` environment variables; implements least-recently-used eviction.
- On `send_message`:
  1. Ensures session, auto-generates human-friendly names from first utterance.
  2. Resolves contextual follow-ups (pronoun/coreference) via `EnhancedConversationMemory.resolve_context`.
  3. Logs metadata (query type, detected specialization, entities) for downstream analytics.
  4. Builds enhanced prompt context combining full history, summary, deduced entities, and reasoning chain.
  5. Calls `_generate_rag_response` which decides between structured SQL answers, vector search, multi-hop decomposition, or placement-cell persona responses. Falls back gracefully and filters hallucinations.
  6. Persists assistant reply and yields `ChatMessage` for API streaming.
- Additional utilities: session listing (`get_user_sessions`), transcript retrieval (`get_session_messages`), deletion (`delete_session`), multi-hop handlers, JD fetch (`_fetch_full_jd_if_requested`).

### Retrieval & Synthesis (`app/rag.py`, `app/agent.py`)
- `retrieve_snippets` first attempts Pinecone search (embedding dimension validated against index), falling back to SQLite heuristics when cloud keys are absent. Includes comprehensive-mode retrieval for “all companies” queries, context-aware company detection, and snippet cleansing.
- `synthesize_answer` (inside `app/rag.py`) composes prompts via `app/prompts.py`, enforcing white-bold Markdown styling guardrails and banned-phrase filters.
- `agent.route_query` provides top-level intent routing, combining rule-based triggers, SQL pathways (`app/sql_tool.py` / `app/final_sql_tool.py`), and semantic fallback. Guardrails detect no-data results to flag deep-dive escalation.
- Hybrid classification system enforces rule-first classification (`classify_role_types_rule`) before optional LLM augmentation (`classify_role_types_llm`), storing traceability inside `role['_role_type_debug']`.

### Ingestion Pipeline (`ingest/pipeline.py`)
- CLI entrypoint `python -m ingest.pipeline --pdf_dir data/jds`.
- Steps per document:
  1. Load `.env`, parse PDFs via LlamaParse (requires `LLAMA_CLOUD_API_KEY`), fallback heuristics for filenames.
  2. Structured extraction with `ingest/structured_extractor.py`, persisted to JSON, inserted into SQLite through `PlacementDatabase.insert_company_extraction`.
  3. Role type tagging uses LLM batch classification, then deterministic rules as fallback.
  4. Text chunking (`RecursiveCharacterTextSplitter`) with 700/150 size/overlap, deterministic `stable_chunk_id`.
  5. Optional Pinecone upsert with dynamic index provisioning, 403 handling, metadata sanitization (`company_norm`, `page_number`).
- Support modules handle canonicalization, metadata normalization, and company extraction.

### Data & Configuration Layer
- `app/config.py` exposes `get_settings()` merging environment variables, `.env`, and defaults (embedding model names, Pinecone keys, directories).
- Local database schema handled by `app/database.py`; stores companies, roles, alerts, chat artifacts. `PlacementDatabase` encapsulates connection pooling and SQL builders.
- `app/utils.py` houses math helpers (cosine similarity), slugification, metadata filters.
- `app/workflow_api.py` exposes durable workflow orchestration (task queues, resumable jobs) via Prefect-style triggers.

### Observability & Testing
- Verbose logging for ingestion previews, query routing, and context resolution prints to stdout (suitable for container logs).
- `pytest` suite under `tests/` validates ingestion, RAG responses, and classifiers without external APIs.
- Key commands (`AGENTS.md`) outline uvicorn startup, ingestion, and pipeline execution.

## Frontend Architecture (Spark Home UI)

### Technology Stack
- React 18 + TypeScript with Vite bundler (`spark-home-2/vite.config.ts`).
- State/query management via `@tanstack/react-query` and native React hooks.
- Tailwind CSS for utility-first styling, with custom dark theme tokens in `client/global.css`.
- Component library wrappers (Toast, Tooltip) leveraging shadcn/ui patterns under `client/components/ui/`.

### Application Shell (`spark-home-2/client/App.tsx`)
- Establishes global providers (`QueryClientProvider`, `TooltipProvider`), toasters, and router.
- Routes:
  - `/` (`pages/Index.tsx`): landing / function launcher.
  - `/rag` (`pages/RAGMode.tsx`): primary analyst console for JD querying.
  - `/benchmark`, `/history`, and catch-all 404 stub.

### RAG Mode Experience (`pages/RAGMode.tsx`)
- Maintains local `messages`, `sessionId`, loading state, and deep-dive consent prompts.
- Submits user queries to backend via `fetch(buildApiUrl('/chat'))`, reusing existing session IDs or requesting new ones from `ChatHistory` sidebar.
- Parses backend flags (`deep_dive_consent_needed`, `needs_vector_approval`) to display `DeepDiveConsentCard`. On activation, calls `/chat/vector`.
- Renders assistant replies with `ReactMarkdown` + `remark-gfm`, styled under `.rag-response` classes that enforce white-bold headings and neutral body text.
- Integrates `ChatInput` for prompt entry, `SapientLogo` for branding, and `ModalPortal` for overlay rendering.

### Chat History Sidebar (`components/ChatHistory.tsx`)
- Slide-in panel matching dark theme. Uses REST endpoints (`GET /sessions/{userId}`, `GET /sessions/{sessionId}/messages`, `DELETE /sessions/{sessionId}`) for lifecycle.
- Displays session metadata (name, last activity, message counts); auto-generates new chats and triggers `RAGMode` session resets.
- Employs optimistic UI updates, request state indicators, and hover affordances consistent with UI spec.

### Shared Components & Hooks
- `components/ChatInput.tsx`: handles textarea autosize, disabled/loading states, CTA button styling.
- `components/DeepDiveConsentCard.tsx`: confirmation modal explaining deep-dive scope and bridging to backend vector search.
- `components/ModalPortal.tsx`: renders children into `document.body` for overlay experiences.
- `hooks/` directory provides reusable state (e.g., `useBoolean`, `useSessionHistory`), decoupled from page components.
- `lib/api.ts`: centralizes backend URL construction (`VITE_BACKEND_URL` override) and error messaging.

### Styling System
- Tailwind theme tokens defined in `client/global.css` + `tailwind.config.ts` (HSL variables). Dark mode defaults align with placement brand.
- `.rag-response` cascade enforces white headings, gray body text, custom bullet markers, and inline code styling to match “white-bold” directive.
- Utility classes (`glass-card`, `soft-glow`, `.animate-fade-in`) standardize visual treatments across modals and cards.

### Build & Deployment
- Development: `pnpm dev` proxies API requests to FastAPI (respecting `VITE_BACKEND_URL`).
- Production build: `pnpm build` outputs `dist/spa`, automatically served by FastAPI static mount when present.
- Netlify configuration (`netlify.toml`, `netlify/` directory) supports optional static hosting with edge functions.

## End-to-End Data Journey
1. **Ingestion**: Placement team drops PDFs/TXT into `data/jds/`. `python -m ingest.pipeline --pdf_dir data/jds` parses documents, extracts structured data, classifies roles, and indexes both structured records (SQLite) and semantic vectors (Pinecone).
2. **Query Routing**: User enters question in Spark UI. Frontend calls `POST /chat` with session metadata.
3. **Memory & Context Prep**: `ChatService` enriches the prompt using conversation history, query type detection, and enhanced context summarization.
4. **Inference Path Selection**: `agent.route_query` chooses between SQL-backed structured response, hybrid analytics, or vector retrieval based on intent, guardrails, and availability of data.
5. **Answer Synthesis**: `synthesize_answer` produces Markdown-formatted responses, citing context and adhering to styling guardrails. If structured route returns limited signal, backend flags deep-dive readiness.
6. **Frontend Presentation**: React renders messages with markdown theming. If deep-dive is suggested, the consent modal triggers `/chat/vector`, which reuses snippets for richer answers.
7. **History Persistence**: `chat_history_store` writes transcripts to disk for rehydration. `ChatHistory` sidebar fetches and displays them, enabling multi-session workflows akin to ChatGPT.

## Getting Started
- **Backend Setup**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  cp env.example .env  # add Pinecone, LLM, and database settings as needed
  uvicorn app.main:app --reload --port 8000
  ```
- **Frontend Setup**:
  ```bash
  cd spark-home-2
  pnpm install
  pnpm dev  # Vite dev server with proxy to FastAPI
  ```
- **Ingestion Run**:
  ```bash
  python -m ingest.pipeline --pdf_dir data/jds
  ```
- **Testing**: `pytest -q`

## Operational Considerations
- Ensure `LLAMA_CLOUD_API_KEY` or `LLAMAPARSE_API_KEY` is set before ingestion; fallback filename heuristics run when structured extraction fails.
- Pinecone credentials (`PINECONE_API_KEY`, `PINECONE_INDEX_NAME`) optional; without them the system relies solely on SQLite-backed snippets.
- Chat memory is in-memory; plan for persistence or cache invalidation in multi-instance deployments (see `chat_history_store` backing store and potential Redis extensions).
- Markdown formatting guardrails intentionally disable orange highlights—UI expects white-bold headings and muted body text.
- Deep-dive vector searches can return up to 75 snippets; monitor Pinecone quotas and adjust `top_k` / `candidate_count` to balance latency and coverage.

## Reference Directory Map
- Backend core: `app/`
  - Conversation orchestration: `chat_service.py`, `chat_memory.py`, `enhanced_chat_memory.py`
  - API surface: `main.py`, `chat_api.py`, `workflow_api.py`
  - Retrieval stack: `rag.py`, `agent.py`, `final_sql_tool.py`, `sql_tool.py`
  - Classification utilities: `hybrid_role_classifier.py`, `role_type_classifier.py`, `llm_role_type_classifier.py`, `safe_subcategory_classifier.py`
  - Infrastructure: `config.py`, `database.py`, `utils.py`
- Ingestion: `ingest/` (pipeline, company extraction, metadata normalization)
- Frontend: `spark-home-2/`
  - Client app: `client/` (pages, components, hooks, global styles)
  - Shared assets: `shared/`, `public/`
  - Deployment configs: `netlify/`, `netlify.toml`
- Data outputs: `data/` (SQLite DB, embeddings, structured JSON caches)
- Documentation & audits: root-level `*.md` plus `spark-home-2/AGENTS.md`

This document should serve as the authoritative map for both backend and frontend contributors when navigating JD-Copilot.
