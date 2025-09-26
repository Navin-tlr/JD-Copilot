User (React UI)
   │ HTTP / (future WS)
   ▼
FastAPI Backend
   │
   ├─ Query Routing & Normalization
   │     • Intent extraction (dict + OpenRouter fallback)
   │     • Classify: STRUCTURED | UNSTRUCTURED | HYBRID | MULTI_HOP
   │
   ├─ Structured Path
   │     • LlamaIndex NLSQLTableQueryEngine (OpenRouter-backed)
   │     • Deterministic SQL fallback (hand-built queries + sqlglot validation)
   │
   ├─ Retrieval Path (RAG)
   │     • Pinecone similarity search (embeddings: sentence-transformers)
   │     • Local DB fallback if Pinecone unavailable
   │
   ├─ Synthesis
   │     • System prompt (Aristotelian Strategist)
   │     • OpenRouter model only (Gemini removed)
   │
   └─ Output Formatting
         • Evidence sections vs Strategic reasoning
         • Red flags, certifications, specialization scoping
Data Layer
   • SQLite (companies, roles, offers, skills, requirements, specializations)
   • Pinecone (chunk vectors)
   • Ingested PDF-derived artifacts (LlamaParse + LangExtract company detection)User (React UI)
   │ HTTP / (future WS)
   ▼
FastAPI Backend
   │
   ├─ Query Routing & Normalization
   │     • Intent extraction (dict + OpenRouter fallback)
   │     • Classify: STRUCTURED | UNSTRUCTURED | HYBRID | MULTI_HOP
   │
   ├─ Structured Path
   │     • LlamaIndex NLSQLTableQueryEngine (OpenRouter-backed)
   │     • Deterministic SQL fallback (hand-built queries + sqlglot validation)
   │
   ├─ Retrieval Path (RAG)
   │     • Pinecone similarity search (embeddings: sentence-transformers)
   │     • Local DB fallback if Pinecone unavailable
   │
   ├─ Synthesis
   │     • System prompt (Aristotelian Strategist)
   │     • OpenRouter model only (Gemini removed)
   │
   └─ Output Formatting
         • Evidence sections vs Strategic reasoning
         • Red flags, certifications, specialization scoping
Data Layer
   • SQLite (companies, roles, offers, skills, requirements, specializations)
   • Pinecone (chunk vectors)
   • Ingested PDF-derived artifacts (LlamaParse + LangExtract company detection)# JD-Copilot System Blueprint

> Consolidated architectural blueprint (bird's‑eye + deep dive) generated on 2025-09-26.

## 1. Mission
Provide exhaustive, evidence-grounded MBA placement intelligence by combining: (a) deterministic structured SQL answers, (b) high‑recall vector retrieval of job/company docs, (c) strategic synthesis with explicit evidence vs reasoning separation.

## 2. High-Level Architecture
```
┌────────────────────────────────────────────────────────────────┐
│                           FRONTEND                             │
│  React + TS (chat UI, session mgmt, streaming-ready)            │
└───────────────▲────────────────────────────────────────────────┘
                │ HTTP (JSON) / future WS
┌───────────────┴────────────────────────────────────────────────┐
│                           FASTAPI                              │
│  chat_api / workflow_api / health (planned)                    │
│      │                                                         │
│      ├─ query_router  (mode classification)                    │
│      ├─ normalizer    (dict + OpenRouter semantic fallback)    │
│      ├─ rag           (vector retrieval + synthesis)           │
│      ├─ final_sql_tool (LlamaIndex NLSQL + deterministic)      │
│      ├─ sql_tool      (canonical + heuristic SQL)              │
│      └─ chat_service  (session orchestration)                  │
└───────────────┬────────────────────────────────────────────────┘
                │
        ┌───────┴─────────┐
        │  DATA LAYER     │
        │  SQLite         │  (companies, roles, offers, skills, requirements, specializations)
        │  Pinecone       │  (chunk embeddings)
        │  Ingest Artifacts (raw parsed text, structured extractions) 
        └─────────────────┘
```

## 3. Request Lifecycle (Single Query)
1. User submits natural language question via React UI.
2. `normalizer` enriches with normalized intents (industry / specialization / role) if detected.
3. `query_router` classifies: STRUCTURED | UNSTRUCTURED | HYBRID | MULTI_HOP.
4. Structured path → LlamaIndex SQL (OpenRouter-backed) or deterministic SQL fallback.
5. Retrieval path → Pinecone similarity search (fallback: synthetic DB snippets).
6. HYBRID merges structured facts + unstructured context.
7. MULTI_HOP decomposes then aggregates sub-answers.
8. `rag.py` synthesizes answer: system prompt (Aristotelian Strategist) + evidence + strategic reasoning.
9. OpenRouter LLM produces final output (or raw evidence if generation fails).
10. Response returned with segregated evidence & strategy sections.

## 4. Core Modules
| Module | Path | Responsibility |
|--------|------|----------------|
| Chat API | `app/chat_api.py` | HTTP endpoints, request entrypoint |
| Chat Service | `app/chat_service.py` | Session, orchestration, routing hooks |
| Query Router | `app/query_router.py` | Mode classification, multi-hop logic |
| Normalizer | `app/normalizer.py` | Dictionary + OpenRouter JSON semantic fallback |
| RAG Engine | `app/rag.py` | Retrieval + synthesis (OpenRouter-only generation) |
| Structured SQL | `app/final_sql_tool.py` | LlamaIndex NLSQL + deterministic fallback |
| Canonical SQL | `app/sql_tool.py` | Query templates + heuristics |
| DB Access | `app/database.py` | SQLite connection + accessors |
| Ingestion | `ingest/*.py` | Parsing, company extraction, chunking, indexing |

## 5. Data Model (SQLite)
```
companies(id, company_name, company_type, industry, location, batch_year, created_at)
roles(id, company_id→companies.id, title, specialization, location, role_description, created_at)
offers(id, role_id→roles.id, batch_year, salary_min_lpa, salary_max_lpa, expected_hires, created_at)
skills(id, role_id→roles.id, skill_name, skill_type, skill_priority, created_at)
requirements(id, role_id→roles.id, requirement_text, requirement_type, requirement_priority, created_at)
specializations(id, name, description, created_at)
```
Relationships: Company 1→N Roles; Role 1→N (Offers | Skills | Requirements); Specializations referenced by roles.

## 6. Retrieval (RAG)
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (384d).
- Chunking: size=700 chars, overlap=150.
- Pinecone: stores {id, vector, metadata(company, specialization, source)}.
- Fallback: Generate DB-derived context lines if Pinecone unavailable.

## 7. Structured Query Path
- Primary: LlamaIndex `NLSQLTableQueryEngine` (OpenRouter via OpenAI-compatible env: `OPENAI_API_BASE=https://openrouter.ai/api/v1`).
- Guardrails: exact table whitelist, specialization value normalization.
- Fallback: Deterministic canonical SQL builder (with `sqlglot` validation and hallucination scrubber).

## 8. Normalization Pipeline
1. Dictionary scan (phrase-first longest match).  
2. If no hits → OpenRouter semantic micro-call (low tokens, JSON allow-list).  
3. Append `[Normalized intents: key=VAL,...]` to user question for downstream models.  
4. Method tags: `dict` | `ai` | `none`.

## 9. Synthesis Prompt Strategy
- Role: "Aristotelian Placement Strategist".  
- Output segmentation: Evidence (verbatim-grounded) vs Strategic reasoning (explicit tags).  
- Red flags & risk surfacing.  
- Certification recommendations (only when not explicitly present).  
- Debiased: removed earlier B2B Sales bias.

## 10. Ingestion Flow
1. Source PDFs → LlamaParse text extraction.  
2. Company extraction: LangExtract + heuristics.  
3. Chunk & embed → Pinecone upsert.  
4. Optional structured extraction (skills/requirements) → SQLite.  
5. Reindex / maintenance scripts in `dev_tools/`.

## 11. Failure & Degradation Matrix
| Layer | Failure | Fallback |
|-------|---------|----------|
| Pinecone | API / config error | Local SQLite snippet synthesis |
| LlamaIndex | Import/model/API failure | Deterministic SQL builder |
| OpenRouter (generation) | 402 / timeout | Return raw retrieved evidence only |
| Semantic normalization | Network / quota | Skip; proceed with original question |

## 12. Security & Integrity
- Read-only SQL generation; no destructive verbs.  
- Environment isolation (`.env`, not committed).  
- Schema whitelisting & column validation.  
- Clear provenance separation reduces hallucination risk.

## 13. Dependencies (Key)
Backend: FastAPI, Uvicorn, Pydantic, SQLAlchemy, Pinecone, sentence-transformers, LlamaIndex, llama-parse, LangExtract, sqlglot, requests.
Frontend: React, TypeScript, Vite, Tailwind CSS, Framer Motion.

## 14. Observability & Logging (Current State)
- Console logs: retrieval decisions, model selection, SQL execution results.  
- Suggested next: structured JSON logs + latency metrics + vector recall counters.

## 15. Extension Roadmap
| Priority | Enhancement | Benefit |
|----------|-------------|---------|
| High | Health endpoint (index status, table counts, model id) | Ops reliability |
| High | Structured JSON output envelope | Easier UI rendering & eval |
| Medium | Retry/backoff w/ token budgeting for OpenRouter | Cost control |
| Medium | Postgres migration path | Concurrency & durability |
| Medium | Streaming token responses | Faster perceived latency |
| Low | Pluggable embedding model registry | Domain adaptation |

## 16. Current Constraints / Known Gaps
- No streaming output yet.  
- Limited test coverage for new OpenRouter semantic normalization.  
- Unused `openrouter_wrapper.py` (candidate for consolidation or removal).  
- No formal evaluation harness for retrieval quality post-debias.

## 17. Quick Start (Backend)
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Add `.env` with: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `LLAMAPARSE_API_KEY`.

## 18. Validation Hooks
- Import smoke: `python -c "import app.rag, app.final_sql_tool, app.normalizer"`.
- Deterministic SQL tests (add pytest cases for canonical queries vs expected SQL).  
- Retrieval recall sampling: compare top_k matches vs ground-truth company labels.

## 19. Design Principles
- Layered fallbacks (never fail hard if partial signal available).  
- Evidence-first reasoning (traceability).  
- Deterministic where possible (SQL, normalization annotation).  
- Minimal vendor lock-in (OpenRouter multi-model abstraction).

## 20. Summary Snapshot
JD-Copilot fuses relational factual accuracy with vector semantic richness, orchestrated through a disciplined prompt and fallback architecture, delivering placement intelligence that is explainable, debiased, and extensible.

---
_Last generated: 2025-09-26_
