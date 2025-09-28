# JD-Copilot Project Documentation

## 1. Folder Structure

```
JD-Copilot/
├── .gitignore
├── AGENTS.md
├── ARCHITECTURE_VERIFICATION.md
├── audit_classifications.py
├── CHAT_INTERFACE_README.md
├── companies.json
├── COMPREHENSIVE_TECHNICAL_REPORT.md
├── DEEP_DIVE_MODE_AND_CLASSIFICATIONS.md
├── env.example
├── HALLUCINATION_PROOF_SYSTEM.md
├── package.json
├── rag_eval_requirements.txt
├── README.md
├── run.sh
├── SYSTEM_BLUEPRINT.md
├── SYSTEM_PROMPTS_DOCUMENTATION.md
├── test_llm_classifier.py
├── .roo/                  # Mode-specific AGENTS.md files
│   ├── rules-code/AGENTS.md
│   ├── rules-debug/AGENTS.md
│   ├── rules-ask/AGENTS.md
│   └── rules-architect/AGENTS.md
├── app/                    # Python backend
│   ├── chat_history_store.py
│   ├── hybrid_role_classifier.py
│   ├── llm_role_type_classifier.py
│   ├── robust_ingestion_classifier.py
│   ├── role_trigger_system.py
│   ├── sql_validator.py
│   └── database.py          # Core database schema
├── curry-forge/            # React frontend
│   ├── client/              # Client-side components
│   │   ├── components/      # UI components
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── types/
│   │   └── App.tsx
│   ├── server/              # Server-side routes
│   │   ├── routes/
│   │   └── index.ts
│   ├── shared/              # Shared code
│   │   └── api.ts
│   └── ...                # Configuration files
├── dev_tools/              # Data processing scripts
│   ├── alerts_stub.py
│   ├── bootstrap_docling_cache.sh
│   ├── check_openrouter_model.py
│   ├── cleanup_database.py
│   ├── configure_ssl.py
│   ├── debug_api.py
│   ├── deterministic_checks.py
│   ├── populate_database.py
│   ├── populate_llm_data.py
│   ├── populate_real_data.py
│   ├── prefetch_docling_models.py
│   ├── process_real_pdfs.py
│   ├── purge_pre_ingestion_data.py
│   ├── reindex.py
│   ├── setup_and_ingest.py
│   ├── show_specializations.py
│   ├── test_agent_determinism.py
│   ├── test_b2b_queries.py
│   ├── test_enhanced_intent.py
│   ├── test_intent_engine.py
│   ├── test_llm_extraction.py
│   ├── test_new_extractor.py
│   ├── test_role_classifier.py
│   └── verify_new_ingestion.py
├── ingest/                 # PDF processing
│   ├── __init__.py
│   ├── chunking.py
│   ├── company_extract.py
│   ├── company_extractor.py
│   ├── file_parser.py
│   ├── langextract_job.py
│   ├── metadata_normalize.py
│   ├── pipeline.py
│   ├── structured_extractor_old.py
│   └── structured_extractor.py
├── public/                 # Static assets
│   └── index.html
├── scripts/
│   └── backfill_pinecone_company_norm.py
├── src/                    # Additional frontend
│   ├── App.css
│   ├── App.js
│   ├── index.css
│   ├── index.js
│   └── components/
├── tests/                  # Test suite
│   ├── test_chat_history_store_flow.py
│   ├── test_company_inference.py
│   ├── test_ingest_pipeline.py
│   ├── test_ingestion.py
│   ├── test_query_api.py
│   └── test_query_augmentation.py
└── unused/                 # Legacy files
    ├── agent.py.backup
    └── ...                # Various UI alternatives
```

## 2. Database Schema

### Tables (from app/database.py)

```mermaid
erDiagram
    companies ||--o{ roles : "1..*"
    roles ||--o{ offers : "1..*"
    roles ||--o{ skills : "1..*"
    roles ||--o{ requirements : "1..*"
    
    companies {
        INTEGER id PK
        TEXT company_name UK
        TEXT company_type
        TEXT industry
        TEXT location
        TEXT batch_year DEFAULT '2024-2025'
        TIMESTAMP created_at DEFAULT CURRENT_TIMESTAMP
    }
    
    roles {
        INTEGER id PK
        INTEGER company_id FK
        TEXT title
        TEXT specialization
        TEXT location
        TEXT role_description
        TEXT role_types JSON
        TEXT source_chunk_id
        TIMESTAMP created_at DEFAULT CURRENT_TIMESTAMP
    }
    
    offers {
        INTEGER id PK
        INTEGER role_id FK
        TEXT batch_year DEFAULT '2024-2025'
        REAL salary_min_lpa
        REAL salary_max_lpa
        INTEGER expected_hires
        TIMESTAMP created_at DEFAULT CURRENT_TIMESTAMP
    }
    
    skills {
        INTEGER id PK
        INTEGER role_id FK
        TEXT skill_name
        TEXT skill_type DEFAULT 'technical'
        INTEGER skill_priority DEFAULT 1
        TIMESTAMP created_at DEFAULT CURRENT_TIMESTAMP
    }
    
    requirements {
        INTEGER id PK
        INTEGER role_id FK
        TEXT requirement_text
        TEXT requirement_type DEFAULT 'education'
        INTEGER requirement_priority DEFAULT 1
        TIMESTAMP created_at DEFAULT CURRENT_TIMESTAMP
    }
    
    specializations {
        INTEGER id PK
        TEXT name UK
        TEXT description
        TIMESTAMP created_at DEFAULT CURRENT_TIMESTAMP
    }
```

## 3. API Endpoints (from app/main.py)

```python
# Base URL: /api/v1

# Company Endpoints
GET /companies - Get all companies with basic info
GET /companies/{company_name}/roles - Get roles for specific company
GET /companies/specialization/{specialization} - Get companies by specialization
GET /companies/specialization/{specialization}/stats - Get stats by specialization

# Role Endpoints
GET /roles - Get all roles with company info
GET /roles/{role_id} - Get specific role details

# Offer Endpoints
GET /offers - Get all offers
GET /offers/{offer_id} - Get specific offer

# Skill Endpoints
GET /skills - Get all skills
GET /skills/search/{skill_query} - Search roles by skills
GET /skills/specialization/{specialization} - Get skills by specialization

# Requirement Endpoints
GET /requirements - Get all requirements
GET /requirements/role/{role_id} - Get requirements by role

# Specialization Endpoints
GET /specializations - Get all specializations
GET /specializations/{specialization}/stats - Get specialization stats
GET /specializations/{specialization}/median-salary - Get median salary
GET /specializations/{specialization}/companies - Get companies by specialization
GET /specializations/{specialization}/compare/{company_name} - Compare company specializations

# Stats Endpoints
GET /stats - Get basic stats
GET /stats/placement - Get placement stats
GET /stats/placement/{specialization} - Get specialization stats
```

## 4. Frontend Structure (curry-forge/)

### Client-Side Architecture
- **components/**: Reusable UI components with UI library components in `ui/`
- **hooks/**: Custom React hooks
  - `use-mobile.ts`: Mobile detection
  - `use-toast.ts`: Toast notifications
- **pages/**: Application pages
  - `Index.tsx`: Main chat interface
  - `NotFound.tsx`: Error page
- **lib/**: Utility functions
- **types/**: Type definitions
- **App.tsx**: Main application component

### Server-Side (curry-forge/server/)
- **routes/**: API routes
  - `demo.ts`: Demo endpoint
- **index.ts**: Server entry point
- **node-build.ts**: Build configuration

### Shared Code (curry-forge/shared/)
- **api.ts**: Shared API types and interfaces

## 5. Testing Structure

### Backend Tests (tests/)
- `test_chat_history_store_flow.py`: Chat history functionality
- `test_company_inference.py`: Company inference logic
- `test_ingest_pipeline.py`: Ingestion pipeline
- `test_ingestion.py`: General ingestion
- `test_query_api.py`: Query API endpoints
- `test_query_augmentation.py`: Query augmentation logic

### Frontend Tests (curry-forge/vitest.config.ts)
- Component tests in `__tests__` directories
- Uses Vitest with React Testing Library
- Coverage thresholds enforced

## 6. Dependencies

### Frontend (curry-forge/package.json)
- React 18
- TypeScript
- Tailwind CSS
- Vite
- Vitest (testing)
- @radix-ui/react-* (UI components)
- zod (validation)
- react-router (routing)

### Backend (requirements.txt)
- FastAPI
- Pydantic
- Uvicorn
- SQLite3
- Pinecone
- LlamaParse
- PyPDF2
- python-dotenv
- pytest
- logging
- dataclasses