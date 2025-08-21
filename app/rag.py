from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import numpy as np
from pinecone import Pinecone

from .config import get_settings
from .utils import cosine_similarity, filter_metadata, role_contains, slugify_company
from .database import PlacementDatabase
from .query_router import QueryRouter, QueryType
import os
import certifi
import requests

# Add Gemini import
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

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
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    return pc.Index(settings.PINECONE_INDEX_NAME)


MAX_SNIPPET_CHARS = 400
MAX_FULL_JD_CHARS = 10000  # Much larger limit for full JD requests


def retrieve_snippets(question: str, top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    settings = get_settings()
    index = get_pinecone_index()
    embedder = EmbeddingBackend(settings.EMBED_MODEL)
    q_emb = embedder.embed([question])[0]

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
        # Try to extract company name from question
        question_lower = question.lower()
        if "of " in question_lower or "for " in question_lower:
            # Look for patterns like "full jd of Tap academy" or "jd for Mill Story"
            for phrase in ["of ", "for "]:
                if phrase in question_lower:
                    parts = question_lower.split(phrase)
                    if len(parts) > 1:
                        potential_company = parts[1].strip().split()[0:3]  # Take up to 3 words
                        company_text = " ".join(potential_company)
                        print(f"🔍 Auto-detected company from question: '{company_text}'")
                        break
    
    # If company filter provided (either from filters or auto-detected), bias the query
    if company_text:
        question = f"[company={company_text}] {question}"
        q_emb = embedder.embed([question])[0]

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
        
        # Company filtering - comprehensive matching
        if company_text:
            meta_company = meta.get("company", "")
            if not meta_company:  # Skip chunks without company metadata
                continue
                
            # Multiple matching strategies for comprehensive coverage
            company_lower = company_text.lower().strip()
            meta_lower = meta_company.lower().strip()
            
            # Strategy 1: Exact match
            if company_lower == meta_lower:
                should_include = True
            # Strategy 2: Contains match (either direction)
            elif company_lower in meta_lower or meta_lower in company_lower:
                should_include = True
            # Strategy 3: Word-based matching for compound names
            company_words = set(company_lower.split())
            meta_words = set(meta_lower.split())
            if company_words & meta_words:  # Set intersection
                should_include = True
            # Strategy 4: Common abbreviations/variations
            elif any(word in meta_lower for word in company_lower.split()):
                should_include = True
            # Strategy 5: Handle acronyms and variations (e.g., "Tap academy" vs "TAP Academy")
            elif company_lower.replace(" ", "") == meta_lower.replace(" ", ""):
                should_include = True
            # Strategy 6: Handle case variations and partial matches
            elif any(word.upper() in meta_lower.upper() for word in company_lower.split()):
                should_include = True
            else:
                should_include = False
                
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
        return scored[:min(len(scored), 50)]  # Return up to 50 chunks for full JD
    
    return scored[:top_k]


def synthesize_answer(question: str, snippets: List[Dict[str, Any]], filters: Dict[str, Any] = None) -> str | None:
    settings = get_settings()

    # --- ENHANCED SYSTEM PROMPT - MBA Placement Specialist ---
    system_prompt = """You are JD-Copilot, a Placement Cell Assistant for MBA students. 
Your role is to act as a responsible member of the placement cell. 
You must answer questions ONLY based on the retrieved snippets from the placement database (PDFs that were ingested). 
You are accountable for the accuracy of your answers — if something is not present in the data, clearly state: 
"I could not find this information in the available documents."

🎯 Answering Guidelines:
1. Always ground your answer in the retrieved snippets. Never invent, assume, or guess. 
2. Present answers in a professional, clear format, as if addressing MBA students. 
3. When information is found:
   - Extract the exact details from snippets. 
   - Summarize them concisely in natural language. 
   - If multiple snippets overlap, merge the information coherently. 
4. When information is missing:
   - Do NOT fabricate. 
   - Say explicitly: "Not mentioned in the available documents."
5. Maintain a tone of responsibility, as if you are part of the Placement Cell, giving official information. 
   - Example: "According to the placement document, TAP Academy is offering the role of Business Development Associate at BTM Layout, Bangalore."
6. Provide structured formatting for clarity:
   - **Job Title:** …
   - **Location:** …
   - **Salary Range:** …
   - **Skills Required:** …
   - **Other Notes:** …
7. If the query is general (not company-specific), search across all documents and provide an aggregated answer.
8. Never answer in a role-play style (e.g., "As TAP Academy's placement coordinator..."). 
   Instead, speak as a placement cell officer reporting from official documents.

📋 SPECIAL INSTRUCTION FOR FULL JD REQUESTS:
When the user asks for "full jd", "complete jd", "entire jd", or similar phrases:
- Provide the COMPLETE job description from all available snippets
- Reconstruct the full document by combining all relevant chunks
- Include ALL details: responsibilities, requirements, qualifications, benefits, etc.
- Do NOT truncate or summarize - give the user the complete information
- If chunks are incomplete, clearly indicate what parts are missing
- Structure the response as a complete, readable job description

🚨 CRITICAL: COMPANY-SPECIFIC QUERIES
When a company name is mentioned in the question (e.g., "full jd of Tap academy"):
- Focus EXCLUSIVELY on that company
- Do NOT include information from other companies
- If the company is not found in the database, clearly state: "I could not find any information about [Company Name] in the available documents."
- If the company is found but has limited information, provide what's available and clearly state what's missing

✅ Example Output for Full JD Request:
**Complete Job Description for [Company Name]**

**Job Title:** [Role]
**Location:** [Location]
**Duration:** [Duration if mentioned]
**Start Date:** [Start date if mentioned]
**Compensation:** [Salary/benefits if mentioned]

**About the Company:**
[Complete company description from snippets]

**Job Description:**
[Complete responsibilities and role details from all snippets]

**What We're Looking For:**
[Complete requirements and qualifications from all snippets]

**What You'll Work On:**
[Complete list of responsibilities from all snippets]

**Additional Information:**
[Any other details found in the snippets]

*This is the complete job description based on all available document chunks.*
"""

    # --- Build the final prompt for the API call ---
    context = "\n\n".join(
        f"[{s.get('metadata', {}).get('company','?')} | {s.get('metadata', {}).get('role','?')} | {s.get('metadata', {}).get('year','?')}] {s['text']}"
        for s in snippets
    )
    
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

    final_prompt = (
        f"{mode_instruction}\n\n"
        "CONTEXT:\n"
        "---------------------\n"
        f"{context}\n"
        "---------------------\n\n"
        f"QUESTION: {question}"
    )

    # Use OpenRouter as the primary LLM source
    if settings.OPENROUTER_API_KEY and OPENROUTER_AVAILABLE:
        print(f"🟢 Attempting synthesis with OpenRouter model: {settings.OPENROUTER_MODEL or 'moonshotai/kimi-k2:free'}")
        try:
            openrouter_model = settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free"
            
            payload = {
                "model": openrouter_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": final_prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 2048,  # Increased from 1024 for full JD requests
            }

            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }

            # Simple retry
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

    # If OpenRouter failed, try Gemini as fallback
    if settings.GEMINI_API_KEY and GEMINI_AVAILABLE:
        print(f"🟡 Attempting synthesis with Gemini model: {settings.GEMINI_MODEL or 'gemini-2.0-flash-exp'}")
        try:
            # Configure Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Use the specified model or default to a reliable one
            gemini_model = settings.GEMINI_MODEL or "gemini-2.0-flash-exp"
            
            # Create the model instance
            model = genai.GenerativeModel(gemini_model)
            
            # Combine system prompt and user prompt for Gemini
            combined_prompt = f"{system_prompt}\n\n{final_prompt}"
            
            # Generate content with safety settings disabled for professional documents
            response = model.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=2048,  # Increased from 1024 for full JD requests
                ),
                safety_settings=[
                    {
                        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                ]
            )
            
            if response and response.text:
                print("✅ Successfully received answer from Gemini.")
                return response.text.strip()
            else:
                return "The model generated an empty response. Please try rephrasing your question."
                
        except Exception as e:
            print(f"❌ Error while calling Gemini: {e}")
            import traceback
            traceback.print_exc()
            return f"Error calling Gemini: {e}"

    # If we reach here, both OpenRouter and Gemini failed or were not configured.
    # Skip synthesis and return None so the API returns retrieved snippets only.
    print("🔴 No LLM API keys configured or all LLM generation failed. Skipping synthesis.")
    return None


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


