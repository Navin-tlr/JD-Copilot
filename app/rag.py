from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import numpy as np
from pinecone import Pinecone
import sqlite3
import json

from .config import get_settings
from .utils import cosine_similarity, filter_metadata, role_contains, slugify_company
from .database import PlacementDatabase
# Removed circular import - QueryRouter is not needed in this file
import os
import certifi
import requests

# Add OpenRouter import
try:
    import requests
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False


class EmbeddingBackend:
    """Provides embeddings with local model and robust fallback for offline tests."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.dim = 384
        self._model = None
        self._tokenizer = None
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            # Infer output dimension with a quick pass
            test_vec = self._model.encode(["test"], normalize_embeddings=True)
            self.dim = int(test_vec.shape[1]) if hasattr(test_vec, "shape") else len(test_vec[0])
        except Exception:
            self._model = None

    def embed(self, texts: List[str]) -> np.ndarray:
        if self._model is not None:
            try:
                vecs = self._model.encode(texts, normalize_embeddings=True)
                return np.array(vecs, dtype=np.float32)
            except Exception:
                pass
        # Deterministic hashing fallback for offline reliability
        return self._hashing_vectors(texts)

    def _hashing_vectors(self, texts: List[str]) -> np.ndarray:
        rng = np.random.default_rng(42)
        # Fixed random projection matrix seeded for determinism
        projection = rng.standard_normal((1024, self.dim)).astype(np.float32)
        arrs: List[np.ndarray] = []
        for t in texts:
            h = np.frombuffer(t.encode("utf-8", errors="ignore"), dtype=np.uint8)
            if h.size == 0:
                h = np.array([0], dtype=np.uint8)
            # Repeat to length 1024 deterministically
            repeated = np.resize(h, 1024).astype(np.float32)
            vec = repeated @ projection
            # normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            arrs.append(vec.astype(np.float32))
        return np.vstack(arrs)


def get_pinecone_index():
    settings = get_settings()
    if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
        raise RuntimeError("Pinecone not configured. Set PINECONE_API_KEY and PINECONE_INDEX_NAME.")
    
    # Harden SSL for Pinecone HTTP client
    try:
        ca = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", ca)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca)
    except Exception:
        pass
    
    try:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        # Check if index exists before trying to access it
        index_list = pc.list_indexes()
        index_names = [idx.name for idx in index_list] if hasattr(index_list, '__iter__') else []
        
        if settings.PINECONE_INDEX_NAME not in index_names:
            raise RuntimeError(f"Pinecone index '{settings.PINECONE_INDEX_NAME}' does not exist. Available indexes: {index_names}")
        
        return pc.Index(settings.PINECONE_INDEX_NAME)
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Pinecone: {e}")


MAX_SNIPPET_CHARS = 400
MAX_FULL_JD_CHARS = 10000  # Much larger limit for full JD requests


def retrieve_snippets(question: str, top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    settings = get_settings()
    
    # Try Pinecone first, fall back to local database if not configured
    try:
        index = get_pinecone_index()
        embedder = EmbeddingBackend(settings.EMBED_MODEL)
        q_emb = embedder.embed([question])[0]
    except RuntimeError as e:
        print(f"⚠️ Pinecone not configured, using local database: {e}")
        # Fall back to local database - return sample snippets for now
        from .database import PlacementDatabase
        db = PlacementDatabase()
        companies = db.get_companies()
        
        # Create simple snippets from available data
        snippets = []
        for i, company in enumerate(companies[:top_k]):
            snippet = {
                "text": f"Company: {company.get('company_name', 'Unknown')} - Industry: {company.get('industry', 'Not specified')} - Location: {company.get('location', 'Not specified')}",
                "metadata": {
                    "company": company.get('company_name', ''),
                    "industry": company.get('industry', ''),
                    "location": company.get('location', ''),
                    "source": "database"
                }
            }
            snippets.append(snippet)
        
        print(f"📊 Returning {len(snippets)} snippets from local database")
        return snippets

    # Check if this is a "full jd" request
    is_full_jd_request = any(phrase in question.lower() for phrase in [
        "full jd", "complete jd", "entire jd", "full job description", 
        "complete job description", "entire job description", "show me jd", "give jd"
    ])
    
    # Use larger snippet size for full JD requests
    snippet_limit = MAX_FULL_JD_CHARS if is_full_jd_request else MAX_SNIPPET_CHARS
    
    # Auto-detect company from question text if not provided in filters
    company_text = filters.get("company")
    if not company_text:
        # --- REVISED, SAFER COMPANY DETECTION LOGIC ---
        question_lower = question.lower()
        # Only trigger detection on explicit keywords that imply a company name will follow.
        # Use more specific patterns to avoid false positives
        trigger_patterns = [
            ("full jd of ", "of "),
            ("jd of ", "of "),
            ("job description of ", "of "),
            ("full jd for ", "for "),
            ("jd for ", "for "),
            ("job description for ", "for "),
            ("details about ", "about "),
            ("information about ", "about "),
            ("jd from ", "from "),
            ("job description from ", "from "),
            ("full jd from ", "from "),
            ("complete jd from ", "from "),
            ("complete jd of ", "of "),
            ("entire jd of ", "of "),
            ("entire jd for ", "for "),
            ("entire jd from ", "from ")
        ]
        
        company_text = None
        for pattern, phrase in trigger_patterns:
            if pattern in question_lower:
                # Extract the text *after* the trigger pattern
                potential_company = question_lower.split(pattern, 1)[1]
                # Clean up and limit to reasonable company name length
                words = potential_company.strip().split()
                
                # Stop at common non-company words
                stop_words = ['company', 'corporation', 'limited', 'inc', 'ltd', 'roles', 'positions', 'specializations', 'skills', 'requirements', 'jd', 'description', 'job', 'details', 'information']
                filtered_words = []
                for word in words:
                    if word in stop_words:
                        break
                    filtered_words.append(word)
                
                company_text = " ".join(filtered_words[:4])  # Limit to 4 words
                
                # Additional validation: ensure we have a reasonable company name
                if company_text and len(company_text.split()) >= 1:
                    print(f"🔍 Auto-detected potential company: '{company_text}'")
                    break
        # --- END OF REVISED LOGIC ---
    
    # If company filter provided (either from filters or auto-detected), bias the query
    if company_text:
        # Use company + context for better embedding match
        search_query = f"{company_text} job description"
        q_emb = embedder.embed([search_query])[0]

    # Query more results to ensure we get comprehensive coverage
    # For full JD requests, get more chunks to reconstruct the complete document
    query_top_k = max(50, top_k * 8) if is_full_jd_request else max(20, top_k * 4)
    res = index.query(vector=q_emb.tolist(), top_k=query_top_k, include_metadata=True, include_values=False)
    matches = res.get("matches", []) if isinstance(res, dict) else getattr(res, "matches", [])
    # We don't store the original document text in Pinecone; return metadata with preview fields
    # To provide text for snippets, include a small slice from metadata if present
    scored = []
    for m in matches:
        meta = m.get("metadata", {}) if isinstance(m, dict) else getattr(m, "metadata", {})
        
        # Company filtering - STRICT matching to prevent JD mixing
        if company_text:
            meta_company = meta.get("company", "")
            if not meta_company:  # Skip chunks without company metadata
                continue
                
            # Robust company matching with normalization
            def normalize_name(name: str) -> str:
                if not name: return ""
                # Keep letters/numbers only, case-insensitive
                return "".join(c for c in name.lower() if c.isalnum())

            norm_query = normalize_name(company_text)
            # Prefer normalized metadata field if available, fallback to normalizing the original
            norm_meta = meta.get("company_norm") or normalize_name(meta_company)
            
            should_include = norm_query in norm_meta or norm_meta in norm_query
            
            # --- DEBUGGING ---
            if "tap" in norm_query or "tap" in norm_meta:
                 print(f"DEBUG: Query='{norm_query}', Meta='{norm_meta}', Match={should_include}")
            # --- END DEBUGGING ---

            if not should_include:
                continue
        
        if not role_contains(meta, filters.get("role_contains")):
            continue
            
        full_text = meta.get("chunk_text") or meta.get("preview") or ""
        text = full_text[:snippet_limit]
        scored.append({
            "id": m.get("id") if isinstance(m, dict) else getattr(m, "id", None),
            "text": text,
            "metadata": meta,
            "score": float(m.get("score", 0.0) if isinstance(m, dict) else getattr(m, "score", 0.0)),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    # Debug logging for company filtering
    if company_text:
        company_chunks = [s for s in scored if s.get("metadata", {}).get("company", "").lower() == company_text.lower()]
        print(f"🔍 Company filter '{company_text}': Found {len(company_chunks)} chunks out of {len(scored)} total")
    
    # For full JD requests, return more chunks to reconstruct the complete document
    if is_full_jd_request:
        print(f"📄 Full JD request detected - returning up to {len(scored)} chunks for complete document reconstruction")
        
        # For full JD requests, prioritize company-specific chunks and return comprehensive coverage
        if company_text:
            # Get ALL chunks for the specific company to ensure 100% JD coverage
            company_specific_chunks = [s for s in scored if s.get("metadata", {}).get("company", "").lower() == company_text.lower()]
            print(f"🎯 Company-specific chunks for '{company_text}': {len(company_specific_chunks)} chunks")
            
            # Return all company-specific chunks for complete JD reconstruction
            return company_specific_chunks
        else:
            # If no company specified, return more chunks but still limit to prevent mixing
            return scored[:min(len(scored), 100)]  # Return up to 100 chunks for full JD
    
    return scored[:top_k]


def synthesize_answer(question: str, snippets: List[Dict[str, Any]], filters: Dict[str, Any] = None) -> str | None:
    settings = get_settings()
    # Aristotelian strategist system prompt (replaces earlier role-specific only prompt)
    system_prompt = """You are JD-Copilot — The Aristotelian Placement Strategist.
Role: act as a ruthless, wise mentor and strategic advisor for MBA students and placement officers. Interpret intent first, answer whatever the user asks, and always distinguish hard evidence (retrieved from the system) from strategic reasoning (external knowledge, frameworks, or creative strategy).

PRINCIPLES (non-negotiable)
1. Evidence first — Any factual claim about a JD, company, requirement, or compensation must be supported by retrieved data (SQL rows or vector snippets). If the retrieval contains no supporting text, reply exactly:
"I could not find this information in the available documents."
2. No hallucinations about source data — Never invent or alter JD contents. If you infer, label it (INFERENCE) and show the data used to infer.
3. Strategic roaming allowed — You MAY draw on external domain knowledge (HBR, academic papers, best‑practice frameworks, market intelligence) for strategy, certifications, frameworks, or comparative context. Clearly label these as STRATEGIC; cite source when possible or note established practice.
4. Distinguish evidence types — Use explicit tags:
   (EVID:SQL:table:row) or (EVID:VEC:docID[:loc]) for retrieved facts.
   (STRAT:EXT:Source:year:label) for external knowledge.
5. Aristotelian tone — Wise, merciless, precise. Imperatives for actions. Explain reasoning concisely.
6. MBA lens mandatory — Map implications to Finance, Marketing, Operations, HR, Business Analytics. Clarify long‑term career impact + immediate tactics.

OPERATION PROCESS
1. Parse intent — State detected intent (e.g., role analysis, skill demand, comparative query, strategic prep, resume shaping, compensation benchmarking, multi-company contrast).
2. Retrieve & anchor — Quote only what retrieval provides. If a requested fact is missing output the exact missing phrase.
3. Analyze strategically — Build recommendations, roadmaps, certifications, competitive positioning. Tag non‑evidence parts STRATEGIC.
4. Mark inferences — Any deduction beyond literal text is (INFERENCE) with minimal reasoning chain.
5. Provide certifications only if tied to evidence or widely accepted (CFA, SHRM‑CP, PMP, CEH, Google Analytics, Six Sigma). Otherwise mark (SUGGESTION).
6. Evidence block mandatory — List all used snippet IDs / row tags with ≤25 word quotes supporting claims.

STYLE
- Flexible structure: choose bullets, sections, or narrative fit for intent.
- No fluff. Each sentence must carry data, inference, or directive value.
- For numeric derivations show arithmetic.
- End every response with: Data-grounded. No assumptions left unstated.

TAGS EXAMPLES
(EVID:SQL:roles:row_12)
(EVID:VEC:JD_doc45:p2)
(STRAT:EXT:HBR:2019:Leadership-Transition)
(INFERENCE)
(SUGGESTION)

ETHICS
- If asked to fabricate: "I cannot fabricate information. Provide data or permit a data lookup."
- Never misrepresent authority beyond being JD-Copilot.

FINISH
Always end with: Data-grounded. No assumptions left unstated.

Role-Focused Output Formats (reference – adapt structure as needed)
For role/position queries:
    - Position Title: [Exact role from JD]
    - Department/Function: [Specific area]
    - Role-Critical Skills: [Skills for THIS job]
    - MBA Specialization Fit: [Which specializations match THIS role]
    - Role-Specific Strategic Advice: [How to win THIS position]
    - Position-Relevant Certifications: [Certs that help]
For company queries about specific roles:
    - Company: [Name]
    - Recruiting For: [Specific position/department]
    - Role Requirements: [Position-specific needs]
    - Position Compensation: [If available]
    - Role Relevance for MBA Students: [Why THIS job matters]

Special Instructions (condensed)
    - ALWAYS identify exact job title first.
    - Tie every requirement to business impact for THAT role.
    - Map to MBA specializations via concrete responsibilities, not industry stereotypes.
    - If role missing: output missing data phrase.
    - Never drift into generic industry commentary.
"""

    # --- Build the final prompt for the API call ---
    context = "\n\n".join(
        f"[{s.get('metadata', {}).get('company','?')} | {s.get('metadata', {}).get('role','?')} | {s.get('metadata', {}).get('year','?')}] {s['text']}"
        for s in snippets
    )
    
    # Detect if user explicitly asks for strategic advice for a single company (avoid generic multi-specialization spill)
    question_lower = question.lower()
    single_company_mode = False
    if len({s.get('metadata', {}).get('company') for s in snippets if s.get('metadata', {}).get('company')}) == 1:
        # Heuristic: if query contains words like 'strategy', 'strategic advice', 'advise', limit advice to directly inferable specialization(s)
        if any(tok in question_lower for tok in ["strategic", "strategy", "advise", "advice"]):
            single_company_mode = True

    # Dynamic instruction based on company filter
    company_text = filters.get("company") if filters else None
    if company_text:
        mode_instruction = f"""
IMPORTANT: You are in COMPANY-SPECIFIC MODE. Focus EXCLUSIVELY on {company_text}.
Analyze ONLY the chunks from this company and provide comprehensive, detailed insights.
Act as the company's placement coordinator who knows every detail about their requirements.

🚨 CRITICAL FILTERING INSTRUCTIONS:
- You MUST ONLY use information from {company_text}
- If you see chunks from other companies (like Accorian, Mill Story, etc.), IGNORE them completely
- Only process and respond with information from {company_text}
- If no information is found for {company_text}, clearly state: "No information found for {company_text}"

📋 SPECIAL INSTRUCTION FOR FULL JD REQUESTS:
When the user asks for "full jd", "complete jd", "entire jd", or similar phrases:
- Provide the COMPLETE job description from all available snippets for {company_text}
- Reconstruct the full document by combining all relevant chunks from {company_text} ONLY
- Include ALL details: responsibilities, requirements, qualifications, benefits, etc.
- Do NOT truncate or summarize - give the user the complete information
- If chunks are incomplete, clearly indicate what parts are missing
- Structure the response as a complete, readable job description for {company_text}
"""
    else:
        mode_instruction = f"""
IMPORTANT: You are in STRATEGIC CONSULTANT MODE. Analyze ALL available data across companies.
Provide comprehensive market insights, trends, and cross-company recommendations.
Act as a placement consultant who understands the entire landscape.
"""

    if single_company_mode and not company_text:
        # Override to a focused specialization mode using actual snippet roles/specializations only
        specializations_present = sorted({(s.get('metadata', {}) or {}).get('specialization') for s in snippets if (s.get('metadata', {}) or {}).get('specialization')})
        spec_list = ", ".join(sp for sp in specializations_present if sp) or "(none detected)"
        mode_instruction += f"\nFOCUS OVERRIDE: Provide strategic advice ONLY for the specializations explicitly present in the retrieved snippets: {spec_list}. Do NOT fabricate advice for absent specializations. If only one specialization exists, restrict advice strictly to that specialization.\n"

    final_prompt = (
        f"{mode_instruction}\n\n"
        "CONTEXT:\n"
        "---------------------\n"
        f"{context}\n"
        "---------------------\n\n"
        f"QUESTION: {question}"
    )

    # OpenRouter only (Gemini removed per user request)
    if settings.OPENROUTER_API_KEY and OPENROUTER_AVAILABLE:
        print(f"🟡 Attempting synthesis with OpenRouter model: moonshotai/kimi-k2 (fallback)")
        try:
            openrouter_model = settings.OPENROUTER_MODEL or "moonshotai/kimi-k2"
            payload = {
                "model": openrouter_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": final_prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 2048,
            }
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            for attempt in range(1, 3):
                try:
                    resp = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        j = resp.json()
                        choice = None
                        if isinstance(j.get("choices"), list) and j["choices"]:
                            choice = j["choices"][0]
                        if choice:
                            text = choice.get("message", {}).get("content") or choice.get("text")
                            if text:
                                print("✅ Successfully received answer from OpenRouter.")
                                return text.strip()
                        return "The model generated an empty response. Please try rephrasing your question."
                    else:
                        print(f"❌ OpenRouter API error (status {resp.status_code}): {resp.text}")
                except requests.exceptions.Timeout:
                    print(f"⏰ OpenRouter request timed out on attempt {attempt}")
                except Exception as e:
                    print(f"❌ OpenRouter request failed: {e}")
            return "OpenRouter generation failed after retries."
        except Exception as e:
            print(f"❌ Error while calling OpenRouter: {e}")
            import traceback
            traceback.print_exc()
            return f"Error calling OpenRouter: {e}"

    print("🔴 No LLM API keys configured or all LLM generation failed. Skipping synthesis.")
    return None


# ----------------------------- TEXT-TO-SQL (GUARDED) -----------------------------

TEXT2SQL_PROMPT = """You are an expert SQLite developer. Given a user's question, create a syntactically correct SQLite SELECT query.

CRUCIAL INSTRUCTIONS:
1) You MUST only use tables and columns from the schema provided below.
2) NEVER invent table or column names. If the user asks for 'skills', use the 'skills' table and the 'skill_name' column.
3) If the answer cannot be obtained from the given schema, output exactly: I cannot answer this question with the available data.
4) Use appropriate JOINs across tables by their foreign keys when needed. Prefer readable column aliases.
5) LIMIT results to 100 rows unless the user explicitly asks for all rows.

You have access to these tables. Here is the schema:
{schema}

Helpful mapping hints:
- companies.company_name is the company name.
- roles.title is the role title, roles.specialization is the MBA specialization.
- offers has salary_min_lpa, salary_max_lpa, batch_year.
- skills.skill_name contains the skill text linked to roles.
- requirements.requirement_text contains requirement text linked to roles.

Question: {question}
SQLQuery:"""


def _introspect_sqlite_schema(db_path: str) -> str:
    tables = ["companies", "roles", "offers", "skills", "requirements"]
    schema_lines: List[str] = []
    try:
        with sqlite3.connect(db_path) as conn:
            for t in tables:
                cur = conn.execute(f"PRAGMA table_info({t})")
                cols = cur.fetchall()
                if not cols:
                    continue
                col_defs = ", ".join([f"{c[1]} {c[2]}" for c in cols])
                schema_lines.append(f"CREATE TABLE {t} ({col_defs});")
    except Exception:
        # Fallback to known schema (from database.py)
        schema_lines = [
            "CREATE TABLE companies (id INTEGER PRIMARY KEY, company_name TEXT, company_type TEXT, industry TEXT, location TEXT, batch_year TEXT);",
            "CREATE TABLE roles (id INTEGER PRIMARY KEY, company_id INTEGER, title TEXT, specialization TEXT, location TEXT, role_description TEXT);",
            "CREATE TABLE offers (id INTEGER PRIMARY KEY, role_id INTEGER, batch_year TEXT, salary_min_lpa REAL, salary_max_lpa REAL, expected_hires INTEGER);",
            "CREATE TABLE skills (id INTEGER PRIMARY KEY, role_id INTEGER, skill_name TEXT, skill_type TEXT, skill_priority INTEGER);",
            "CREATE TABLE requirements (id INTEGER PRIMARY KEY, role_id INTEGER, requirement_text TEXT, requirement_type TEXT, requirement_priority INTEGER);",
        ]
    return "\n".join(schema_lines)


def _llm_generate_sql(question: str, schema: str) -> str | None:
    settings = get_settings()
    prompt = TEXT2SQL_PROMPT.format(schema=schema, question=question)
    # Prefer OpenRouter
    if settings.OPENROUTER_API_KEY and OPENROUTER_AVAILABLE:
        try:
            payload = {
                "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2",
                "messages": [
                    {"role": "system", "content": "You output only the SQL query or the fixed error sentence. No explanations."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 300,
            }
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                return content
        except Exception:
            pass
    # No key or failure
    return None


def _is_safe_select(sql: str) -> bool:
    s = sql.strip().rstrip(";")
    if not s.lower().startswith("select"):
        return False
    forbidden = [";", "--", "drop ", "delete ", "insert ", "update ", "pragma ", "attach ", "alter "]
    return not any(tok in s.lower() for tok in forbidden)


def _execute_sql(db_path: str, sql: str) -> Tuple[List[str], List[tuple]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
    return cols, rows


def _format_sql_result(question: str, columns: List[str], rows: List[tuple]) -> str:
    # If no LLM key, do a simple textual rendering
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY or not OPENROUTER_AVAILABLE:
        if not rows:
            return "I could not find any matching results in the database."
        preview = []
        limit = min(len(rows), 10)
        for r in rows[:limit]:
            preview.append(", ".join(f"{c}: {v}" for c, v in zip(columns, r)))
        return "\n".join(preview)

    # Ask LLM to format nicely
    try:
        data = {"columns": columns, "rows": rows[:50]}
        payload = {
            "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
            "messages": [
                {"role": "system", "content": """You are a helpful database assistant. Take the SQL results and convert them into a clear, user-friendly answer.

**User Question:** {question}
**SQL Results:** {results}

**Your Job:**
1. Process the SQL results into natural language
2. Provide context and insights
3. Make it helpful for students and recruiters
4. DON'T HALLUCINATE - if the data doesn't show something, don't make it up
5. If no results, say "No data found for this query."

**For Skills Questions Specifically:**
- Analyze which companies are asking for which skills
- Provide strategic insights for MBA students
- Explain what this means for career planning
- Give actionable advice based on the data
- Connect skills to specific company needs and roles

**Example:**
SQL Results: "Result: 3"
Answer: "There are 3 companies that came for this role."

SQL Results: "Results: 1. Marketing | 2. Finance | 3. HR"
Answer: "The available specializations are: Marketing, Finance, and HR."

**Skills Analysis Example:**
SQL Results: "Results: 1. Reporting | 2. Marketing | 3. Leadership"
Answer: "**Skills Analysis by Company Demand:**

**Top Skills Requested:**
1. **Reporting** - Companies need data-driven decision makers
2. **Marketing** - Digital and traditional marketing expertise
3. **Leadership** - Team management and strategic thinking

**Strategic Implications for MBA Students:**
- **Focus Areas**: Develop strong analytical and leadership skills
- **Career Paths**: Consider roles in consulting, product management, or business development
- **Competitive Advantage**: Combine technical skills with strategic thinking

**Company Insights**: [Based on actual data from the database]"""},
                {"role": "user", "content": (
                    f"**User Question:** {question}\n"
                    f"**SQL Results:** {json.dumps(data)}\n\n"
                    "Convert these SQL results into a clear, user-friendly answer following the guidelines above."
                )},
            ],
            "temperature": 0.0,
            "max_tokens": 400,
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return "I could not find any matching results in the database."


def answer_from_text2sql(question: str) -> str | None:
    """Top-level helper for structured, free-form DB questions using guarded Text-to-SQL."""
    db = PlacementDatabase()
    schema = _introspect_sqlite_schema(db.db_path)
    sql = _llm_generate_sql(question, schema)
    if not sql:
        return None
    if sql.strip().startswith("I cannot answer this question with the available data."):
        return sql.strip()
    # Ensure safety
    if not _is_safe_select(sql):
        return "I cannot answer this question with the available data."
    try:
        columns, rows = _execute_sql(db.db_path, sql)
    except Exception as e:
        return f"I cannot answer this question with the available data. (SQL error: {e})"
    return _format_sql_result(question, columns, rows)


def _build_prompt(question: str, snippets: List[Dict[str, Any]]) -> str:
    ctx_lines = []
    for s in snippets:
        meta = s.get("metadata", {})
        cite = f"[{meta.get('company','?')} | {meta.get('role','?')} | {meta.get('year','?')}]"
        ctx_lines.append(f"{cite} {s['text']}")
    context = "\n\n".join(ctx_lines)
    return (
        "Context snippets:\n" + context + "\n\n"
        + "Question: " + question + "\n"
        + "Instructions: Answer only the question, briefly (<=120 words). Use only provided context. Include inline citations in the form [Company | Role | Year]."
    )


def _handle_structured_query(question: str, params: Dict[str, Any], db: PlacementDatabase, snippets: List[Dict[str, Any]]) -> str:
    """Handle structured queries using SQL database"""
    try:
        if params.get("entity") == "companies":
            if params.get("year"):
                stats = db.get_placement_stats(params["year"])
            else:
                stats = db.get_placement_stats()
            
            if stats:
                return f"""
**Placement Statistics:**
- **Total Companies:** {stats.get('company_count', 0)}
- **Total Roles:** {stats.get('role_count', 0)}
- **Salary Range:** ₹{stats.get('min_salary', 0):.1f} - ₹{stats.get('max_salary', 0):.1f} LPA
- **Average Salary:** ₹{stats.get('avg_min_salary', 0):.1f} - ₹{stats.get('avg_max_salary', 0):.1f} LPA

**Top Skills in Demand:**
{chr(10).join([f"- {skill['skill']}: {skill['count']} roles" for skill in stats.get('top_skills', [])])}

*Data extracted from structured placement database*
"""
        
        return "I'll analyze the structured data for you. Please try rephrasing your question."
        
    except Exception as e:
        print(f"Structured query failed: {e}")
        return "I encountered an error while processing the structured data. Please try again."

def _handle_hybrid_query(question: str, params: Dict[str, Any], db: PlacementDatabase, snippets: List[Dict[str, Any]]) -> str:
    """Handle hybrid queries combining SQL and RAG"""
    try:
        # Get structured data
        structured_answer = _handle_structured_query(question, params, db, snippets)
        
        # Get RAG insights
        rag_answer = _handle_rag_query(question, snippets, {})
        
        return f"""
**Structured Data Analysis:**
{structured_answer}

**Detailed Insights from Job Descriptions:**
{rag_answer}
"""
        
    except Exception as e:
        print(f"Hybrid query failed: {e}")
        return "I encountered an error while processing the hybrid query. Please try again."

def _handle_multi_hop_query(question: str, params: Dict[str, Any], db: PlacementDatabase, snippets: List[Dict[str, Any]]) -> str:
    """Handle multi-hop queries with filtering then analysis"""
    try:
        # Step 1: Apply filters (e.g., salary threshold)
        if params.get("salary_threshold"):
            threshold = params["salary_threshold"]
            operator = params.get("salary_operator", ">")
            
            # Get companies meeting salary criteria
            filtered_companies = db.search_skills("", None)  # Get all for now
            high_paying = [c for c in filtered_companies if c.get("salary_max_lpa", 0) > threshold]
            
            if high_paying:
                company_list = ", ".join([c["company_name"] for c in high_paying[:5]])
                
                return f"""
**Multi-Step Analysis Results:**

**Step 1: Companies with Salary {operator} ₹{threshold} LPA:**
{company_list}

**Step 2: Skills Analysis for High-Paying Roles:**
Based on the filtered companies, here are the key skills in demand:

{_handle_rag_query(question, snippets, {})}
"""
        
        return "I'll perform the multi-step analysis. Please try rephrasing your question."
        
    except Exception as e:
        print(f"Multi-hop query failed: {e}")
        return "I encountered an error while processing the multi-step query. Please try again."

def _handle_rag_query(question: str, snippets: List[Dict[str, Any]], filters: Dict[str, Any]) -> str:
    """Handle traditional RAG queries"""
    # This is the existing synthesis logic
    return synthesize_answer(question, snippets)


