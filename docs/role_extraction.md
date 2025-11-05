# Dynamic Role Extraction Documentation

## Overview
This document describes the new LLM-driven approach for specialization detection and role hierarchy extraction, replacing hardcoded `LEVEL1_MAPS`. The system now uses modular components for multi-label specialization detection, Level 1 role mapping, and dynamic Level 2 sub-role extraction. This enables flexible, context-aware inference without rigid maps, supporting hybrids (e.g., Financial Analytics → Finance + Business Analytics union).

Key Benefits:
- **Multi-label Support**: Detects 1+ specializations per JD (e.g., Marketing + Analytics).
- **Provenance & Confidence**: Each output includes source (LLM/fallback), confidence (0-1), evidence/rationale.
- **Hybrid Handling**: Automatic union of Level 1 from multiple specs, marked with originating specializations.
- **Fallbacks**: Keyword classifier if LLM unavailable; generic roles as last resort.
- **Persistence**: JSONB/TEXT fields in DB for structured storage/querying (e.g., filter by level1_roles).

The flow integrates into `ingest/pipeline.py`: Core extraction → Detect specs → Map Level 1 → Extract Level 2 → Persist to DB/Pinecone metadata.

## Components

### 1. Specialization Detector (`ingest/specialization_detector.py`)
- **Function**: `detect_specializations(text: str) → List[Dict]`
- **Input**: JD text.
- **Output**: `[{"specialization": "Finance", "confidence": 0.92, "source": "llm", "evidence": "forecasting models"}]`
- **Logic**:
  - Primary: LLM call using `prompts/specialization_prompt.md` (zero/few-shot, multi-label).
  - Fallback: Keyword matching (e.g., "finance" → Finance with capped confidence ≤0.5).
  - Filtering: Threshold (default 0.15), top_k (default None).
- **Tuning**: Adjust `SPECIALIZATION_THRESHOLD`/`TOP_K` in settings or config/extraction.yml. Edit prompt for better examples.

### 2. Level 1 Mapper (`ingest/level1_mapper.py`)
- **Function**: `map_level1_roles(specializations: List[str], jd_text: str) → List[Dict]`
- **Input**: Detected specs (e.g., ['Finance', 'Business Analytics']), JD text.
- **Output**: `[{"level1": "FP&A", "specializations": ["Finance"], "confidence": 0.85, "source": "llm", "rationale": "budgeting mention"}]`
- **Logic**:
  - LLM call using `prompts/level1_mapping_prompt.md` (infers broad MBA labels like "B2B Sales", "Data Analytics").
  - Union for multiples: Attributes each level1 to originating spec(s) (e.g., hybrid gets merged provenance).
  - Fallback: Generic per spec (e.g., "General Marketing" for Marketing).
  - Filtering: Threshold (default 0.2).
- **Tuning**: Update prompt examples for preferred labels. Set `LEVEL1_THRESHOLD` in config.

### 3. Level 2 Extractor (`ingest/level2_extractor.py`)
- **Function**: `extract_level2_roles(jd_text: str, level1_candidates: List[str]) → List[Dict]`
- **Input**: JD text, Level 1 list (e.g., ['B2B Sales']).
- **Output**: `[{"level2": "SDR", "level1": "B2B Sales", "confidence": 0.9, "source": "llm", "rationale": "SDR team management"}]`
- **Logic**:
  - LLM infers 1-3 granular sub-roles per Level 1 from responsibilities/skills (e.g., B2B Sales → SDR, Account Executive).
  - Ties each Level 2 to its parent Level 1.
  - Fallback: Generic sub-roles (e.g., "SDR" for B2B Sales).
  - Filtering: Threshold (default 0.2).
- **Tuning**: Inline system prompt can be externalized. Set `LEVEL2_THRESHOLD` in config.

## Integration in Pipeline (`ingest/pipeline.py`)
- **Flow** (if `LEGACY_ROLE_MAP != true`):
  1. Core structured extraction (company, roles via LLM).
  2. `detect_specializations(text)` → multi-label specs.
  3. `map_level1_roles(spec_names, text)` → Level 1 with provenance.
  4. `extract_level2_roles(text, level1_list)` → Level 2 tied to Level 1.
  5. Merge into extraction_dict (specializations, level1_roles, level2_roles as lists of dicts).
  6. Persist to DB (`roles` table JSON/TEXT fields) and Pinecone metadata.
- **Legacy Rollback**: Set `LEGACY_ROLE_MAP=true` to use old `LEVEL1_MAPS` from `structured_extractor.py`.
- **DB Schema**: Added via `migrations/2025_add_dynamic_hierarchy_fields.sql` (TEXT for SQLite; parse with json.loads() in queries).

## Configuration (`config/extraction.yml`)
- Thresholds: `SPECIALIZATION_THRESHOLD: 0.15`, `LEVEL1_THRESHOLD: 0.2`, `LEVEL2_THRESHOLD: 0.2`.
- Models: `MODEL: "anthropic/claude-3.5-sonnet"` (or env var).
- Top K: `SPECIALIZATION_TOP_K: 3` (limit specs).
- Fallback: `USE_FALLBACK: true` (keyword/generic if LLM fails).
- Load via Pydantic or yaml.safe_load in modules.

## Logging & Telemetry (`app/logging_config.py`)
- Logs decisions: e.g., "Detected specs: Finance (0.92, evidence: FP&A)" at INFO.
- Sampling: 1% full JD+outputs to QA (via `logging` with sampler).
- Redact PII: Sanitize JD text (remove names/emails) before log.
- Enable: Set `LOG_EXTRACTION_DECISIONS=true`.

## Testing
- **Unit**: `tests/test_specialization_detector.py` (multi-label, hybrids, edges; 8 tests, all pass with mocks).
- **Integration**: `tests/test_integration_dynamic_pipeline.py` (8 JD fixtures, full flow, schema assert; mocks LLM/DB).
- **Mocks**: `tests/mocks/llm_responses.json` for deterministic CI.
- Run: `pytest tests/ -v` (focus on new files).

## Tuning & Maintenance
- **Prompts**: Edit `prompts/*.md` for better accuracy (add JD examples).
- **Thresholds**: Lower for recall, higher for precision; test with real JDs.
- **Fallback Classifier**: Expand keywords in detector for better uptime.
- **Rollback**: `export LEGACY_ROLE_MAP=true; python ingest/pipeline.py --pdf_dir data/jds`.
- **Monitoring**: Query DB for low-confidence (<0.3) entries; review sampled logs.
- **Dependencies**: Ensure OpenRouter key; fallback handles no-LLM.

For issues, check logs or run `pytest -s` for verbose output.