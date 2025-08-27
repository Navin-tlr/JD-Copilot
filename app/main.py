from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Health, get_settings
from .rag import retrieve_snippets, synthesize_answer
from .database import PlacementDatabase
from .query_router import QueryRouter, QueryType
from .chat_memory import memory_manager, ConversationMemory
from .schemas import (
    GDSimulateRequest,
    GDSimulateResponse,
    QueryRequest,
    QueryResponse,
    ResumeMatchRequest,
    ResumeMatchResponse,
    ResumeMatchResult,
)
from .utils import extract_skills


app = FastAPI(title="jd-copilot", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health(status="ok")

@app.get("/test")
def test_endpoint():
    """Simple test endpoint to check if the server is working"""
    settings = get_settings()
    try:
        from .database import PlacementDatabase
        from .rag import EmbeddingBackend
        db = PlacementDatabase()
        companies = db.get_companies()
        
        # Test embedding backend
        embedding_backend = EmbeddingBackend("sentence-transformers/all-MiniLM-L6-v2")
        test_embedding = embedding_backend.embed(["test"])
        
        return {
            "message": "Test endpoint working",
            "openrouter_configured": bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_MODEL),
            "openrouter_model": settings.OPENROUTER_MODEL,
            "env_file_exists": Path(".env").exists(),
            "database_working": True,
            "company_count": len(companies),
            "embedding_working": True,
            "embedding_dim": test_embedding.shape[1] if hasattr(test_embedding, 'shape') else len(test_embedding[0])
        }
    except Exception as e:
        return {
            "message": "Test endpoint working",
            "openrouter_configured": bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_MODEL),
            "openrouter_model": settings.OPENROUTER_MODEL,
            "env_file_exists": Path(".env").exists(),
            "database_working": False,
            "error": str(e),
            "traceback": str(e.__class__.__name__)
        }


@app.on_event("startup")
def log_startup_settings():
    settings = get_settings()
    # Log whether OpenRouter config is set (do not print secrets)
    openrouter_set = bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_MODEL)
    print(f"Startup: OPENROUTER configured={openrouter_set}")
    print(f"Startup: OPENROUTER_API_KEY length={len(settings.OPENROUTER_API_KEY) if settings.OPENROUTER_API_KEY else 0}")
    print(f"Startup: OPENROUTER_MODEL={settings.OPENROUTER_MODEL}")
    print(f"Startup: Environment check - .env file exists={Path('.env').exists()}")


@app.get("/companies")
def get_companies():
    """Get all unique companies from the database for dropdown."""
    try:
        # Use local database instead of Pinecone
        db = PlacementDatabase()
        companies_data = db.get_companies()
        
        # Extract company names from the database
        companies = set()
        for company_info in companies_data:
            company_name = company_info.get('company_name')
            if company_name and company_name.strip():
                companies.add(company_name.strip())
        
        company_list = sorted(list(companies))
        return {"companies": company_list}
    except Exception as e:
        print(f"Error getting companies: {e}")
        return {"companies": [], "error": str(e)}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    """Enhanced query endpoint with intelligent LLM-powered routing and chat memory"""
    try:
        # Get conversation memory for this session
        conversation = memory_manager.get_session(req.session_id)
        
        # Check if this is a contextual query and resolve it
        original_question = req.question
        resolved_question = req.question
        context_info = {}
        
        if conversation.is_contextual_query(req.question):
            print(f"🧠 Contextual query detected: {req.question}")
            resolved_question, context_info = conversation.resolve_context(req.question)
            print(f"🔄 Resolved to: {resolved_question}")
        
        filters: Dict[str, Any] = {
            "company": req.filters.company,
            "year": req.filters.year,
            "role_contains": req.filters.role_contains,
        }
        
        # Use enhanced QueryRouter with LLM intelligence
        router = QueryRouter()
        query_type, params = router.classify_query(resolved_question)
        # Merge context information into parameters
        if context_info:
            for k, v in context_info.items():
                if k not in params and v:
                    params[k] = v
        
        # For structured queries, extract normalized intent via LLM JSON (guardrailed)
        if query_type == QueryType.STRUCTURED:
            intent = router.llm_extract_structured_intent(resolved_question)
            # Merge intent into params without overwriting existing explicit fields
            for k, v in intent.items():
                if k == "query":
                    continue
                if v and k not in params:
                    params[k] = v
        
        routing_strategy = router.get_routing_strategy(query_type, params)
        
        print(f"🔍 Query Type: {query_type.value}")
        print(f"📊 Parameters: {params}")
        print(f"🎯 Routing Strategy: {routing_strategy}")
        
        # Route based on intelligent classification
        if query_type == QueryType.STRUCTURED:
            print("📊 Using STRUCTURED database approach with LLM intelligence")
            try:
                db = PlacementDatabase()
                # Fallback extractors in case router params miss specialization/year
                def _fallback_specialization(q: str) -> Optional[str]:
                    ql = q.lower()
                    if "marketing" in ql and "sales" not in ql:
                        return "Marketing"
                    if "finance" in ql:
                        return "Finance"
                    if "human resources" in ql or re.search(r"\bhr\b", ql):
                        return "HR"
                    if "lean operations" in ql or "operations" in ql:
                        return "Operations"
                    if "strategy" in ql:
                        return "Strategy"
                    if "information technology" in ql or re.search(r"\bit\b", ql):
                        return "IT"
                    if "business analytics" in ql or "analytics" in ql:
                        return "Analytics"
                    return None

                def _fallback_year(q: str) -> str:
                    ql = q.lower()
                    # Only extract year if explicitly mentioned
                    if "last year" in ql or "2023" in ql:
                        return "2023-2024"
                    if "2022" in ql:
                        return "2022-2023"
                    if "this year" in ql or "current year" in ql:
                        return "2024-2025"
                    # If no year is explicitly mentioned, return None to show all data
                    return None
                
                # Handle company count queries with specialization filtering
                if "companies" in resolved_question.lower() and ("how many" in resolved_question.lower() or "count" in resolved_question.lower()):
                    # Check if this is a specialization-specific query
                    specialization = params.get("specialization") or _fallback_specialization(resolved_question)
                    year = params.get("year", None) or _fallback_year(resolved_question)
                    
                    if specialization:
                        # Get specialization-specific companies
                        spec_companies = db.get_companies_by_specialization(specialization, year)
                        if spec_companies:
                            company_names = [c['company_name'] for c in spec_companies]
                            company_count = len(company_names)
                            
                            # Check if we have salary data for these companies
                            has_salary_data = any(c.get('avg_min_salary') is not None for c in spec_companies)
                            
                            if year:
                                # Year-specific query
                                if has_salary_data:
                                    answer = f"""Based on the structured placement database for {specialization} roles in {year}:

**Total Companies:** {company_count} companies recruited for {specialization} positions
**Companies:** {', '.join(company_names)}

**Note:** This data includes salary information for {year}. If you need historical data from previous years, please contact the placement office."""
                                else:
                                    answer = f"""Based on the structured placement database for {specialization} roles in {year}:

**Total Companies:** {company_count} companies recruited for {specialization} positions
**Companies:** {', '.join(company_names)}

**Note:** These companies have {specialization} roles available for {year}, but salary/offer details may not be complete. For comprehensive historical data including salary information, please contact the placement office."""
                            else:
                                # No year specified - show all available data
                                if has_salary_data:
                                    answer = f"""Based on the structured placement database for {specialization} roles:

**Total Companies:** {company_count} companies recruited for {specialization} positions
**Companies:** {', '.join(company_names)}

**Note:** This shows all available {specialization} roles across all time periods. For year-specific data or salary information, please specify the year or contact the placement office."""
                                else:
                                    answer = f"""Based on the structured placement database for {specialization} roles:

**Total Companies:** {company_count} companies recruited for {specialization} positions
**Companies:** {', '.join(company_names)}

**Note:** This shows all available {specialization} roles across all time periods. Salary/offer details may not be complete. For comprehensive historical data including salary information, please contact the placement office."""
                            
                            # Add to conversation memory
                            conversation.add_message("user", original_question, 
                                                    query_type=query_type.value, 
                                                    specialization=specialization,
                                                    entities_mentioned=company_names)
                            conversation.add_message("assistant", answer, 
                                                    metadata={"companies": company_names, "count": company_count})
                            
                            return QueryResponse(snippets=[], answer=answer, 
                                               context_used=context_info if context_info else None)
                        else:
                            if year:
                                answer = f"""Based on the structured placement database:

**No {specialization} roles found for {year}**

**Note:** No companies recruited for {specialization} positions during {year}. This could mean:
- No {specialization} roles were available
- The data for that period is not yet loaded
- Companies focused on other specializations

Please check other specializations or contact the placement office for more details."""
                            else:
                                answer = f"""Based on the structured placement database:

**No {specialization} roles found**

**Note:** No companies recruited for {specialization} positions. This could mean:
- No {specialization} roles were available
- The data is not yet loaded
- Companies focused on other specializations

Please check other specializations or contact the placement office for more details."""
                            
                            # Add to conversation memory
                            conversation.add_message("user", original_question, 
                                                    query_type=query_type.value, 
                                                    specialization=specialization,
                                                    entities_mentioned=company_names)
                            conversation.add_message("assistant", answer, 
                                                    metadata={"companies": company_names, "count": company_count})
                            
                            return QueryResponse(snippets=[], answer=answer, 
                                               context_used=context_info if context_info else None)
                    
                    # Use basic stats method for general company queries
                    basic_stats = db.get_basic_stats()
                    company_count = basic_stats.get('company_count', 0)
                    
                    # Get company names separately
                    companies = db.get_companies()
                    company_names = [c['company_name'] for c in companies]
                    
                    answer = f"""Based on the structured placement database, here are the current statistics:

**Total Companies:** {company_count} companies are actively recruiting
**Companies Available:** {', '.join(company_names)}

**Note:** This data is from our current placement database. For historical data or specific year counts, please contact the placement office."""
                    
                    # Add to conversation memory
                    conversation.add_message("user", original_question, query_type=query_type.value)
                    conversation.add_message("assistant", answer)
                    
                    return QueryResponse(snippets=[], answer=answer, 
                                       context_used=context_info if context_info else None)
                
                # Handle salary statistics queries
                elif "salary" in req.question.lower():
                    specialization = params.get("specialization") or _fallback_specialization(req.question)
                    year = params.get("year", None) or _fallback_year(req.question)
                    
                    if specialization:
                        # Get specialization-specific salary stats
                        stats = db.get_placement_stats(specialization, year)
                        if stats and stats.get('company_count', 0) > 0:
                            answer = f"""Based on the structured placement database for {specialization} roles in {year}:

**Salary Statistics:**
- **Total Companies:** {stats.get('company_count', 0)} companies
- **Total Roles:** {stats.get('role_count', 0)} positions
- **Average Min Salary:** {stats.get('avg_min_salary', 'Not available')} LPA
- **Average Max Salary:** {stats.get('avg_max_salary', 'Not available')} LPA
- **Salary Range:** {stats.get('min_salary', 'Not available')} - {stats.get('max_salary', 'Not available')} LPA

**Note:** Salary data is only available for roles where it was explicitly mentioned."""
                        else:
                            answer = f"""Based on the structured placement database:

**No {specialization} roles found for {year}**

**Note:** No salary data available for {specialization} positions during {year}. This could mean:
- No {specialization} roles were available
- The data for that period is not yet loaded
- Companies focused on other specializations"""
                    else:
                        # Get general salary statistics
                        stats = db.get_placement_stats()
                        answer = f"""Based on the structured placement database:

**Salary Statistics:**
- **Total Companies:** {stats.get('company_count', 'Not available')} companies
- **Total Roles:** {stats.get('role_count', 'Not available')} positions
- **Average Min Salary:** {stats.get('avg_min_salary', 'Not available')} LPA
- **Average Max Salary:** {stats.get('avg_max_salary', 'Not available')} LPA
- **Salary Range:** {stats.get('min_salary', 'Not available')} - {stats.get('max_salary', 'Not available')} LPA

**Note:** Salary data is only available for roles where it was explicitly mentioned."""
                    
                    # Add to conversation memory
                    conversation.add_message("user", original_question, query_type=query_type.value)
                    conversation.add_message("assistant", answer)
                    
                    return QueryResponse(snippets=[], answer=answer, 
                                       context_used=context_info if context_info else None)
                
                # Handle other structured queries
                else:
                    # For other structured queries, try to get relevant data
                    specialization = params.get("specialization") or _fallback_specialization(req.question)
                    year = params.get("year", None) or _fallback_year(req.question)
                    
                    if specialization:
                        # Get specialization insights
                        insights = db.get_specialization_insights(specialization, year)
                        if insights and insights.get('stats', {}).get('company_count', 0) > 0:
                            stats = insights['stats']
                            answer = f"""Based on the structured placement database for {specialization} roles in {year}:

**Specialization Statistics:**
- **Total Companies:** {stats.get('company_count', 0)} companies
- **Total Roles:** {stats.get('role_count', 0)} positions
- **Average Min Salary:** {stats.get('avg_min_salary', 'Not available')} LPA
- **Average Max Salary:** {stats.get('avg_max_salary', 'Not available')} LPA

**Top Companies by Salary:**
{chr(10).join([f"- {c['company']}: ₹{c['avg_salary']:.1f} LPA ({c['role_count']} roles)" for c in insights.get('top_companies', [])])}

**Top Skills in Demand:**
{chr(10).join([f"- {s['skill']}: {s['count']} roles" for s in insights.get('top_skills', [])])}"""
                        else:
                            answer = f"""Based on the structured placement database:

**No {specialization} roles found for {year}**

**Note:** No data available for {specialization} positions during {year}. Please check other specializations or contact the placement office."""
                    else:
                        # Get general placement stats
                        stats = db.get_placement_stats()
                        answer = f"""Based on the structured placement database:

**General Placement Statistics:**
- **Total Companies:** {stats.get('company_count', 'Not available')} companies
- **Total Roles:** {stats.get('role_count', 'Not available')} positions
- **Average Min Salary:** {stats.get('avg_min_salary', 'Not available')} LPA
- **Average Max Salary:** {stats.get('avg_max_salary', 'Not available')} LPA

**Note:** This data represents the overall placement landscape. For specialization-specific insights, please specify the area of interest."""
                    
                    # Add to conversation memory
                    conversation.add_message("user", original_question, query_type=query_type.value)
                    conversation.add_message("assistant", answer)
                    
                    return QueryResponse(snippets=[], answer=answer, 
                                       context_used=context_info if context_info else None)
                    
            except Exception as e:
                print(f"❌ Structured query failed: {e}")
                # Fall back to RAG if structured query fails
        
        # For other query types, use RAG approach
        print("🔍 Using RAG approach for detailed analysis")
        # Pass specialization/year inferred params down as filters when available
        if 'specialization' not in filters or not filters['specialization']:
            try:
                # Use the router that was already created above
                if 'router' in locals():
                    _, p = router.classify_query(req.question)
                    if p.get('specialization'):
                        filters['specialization'] = p['specialization']
                    if p.get('year'):
                        filters['year'] = p['year']
            except Exception:
                pass

        # Add conversation context for RAG
        conversation_context = conversation.get_conversation_summary()
        enhanced_question = resolved_question
        if conversation_context:
            enhanced_question = f"{conversation_context}\n\nUser question: {resolved_question}"
        
        snippets = retrieve_snippets(enhanced_question, req.top_k, filters)
        answer = synthesize_answer(enhanced_question, snippets, filters) if snippets else None

        # Robust fallback: if no RAG snippets and the question asks about skills,
        # aggregate skills from the structured DB for the inferred specialization
        if not snippets and answer is None:
            ql = resolved_question.lower()
            if "skill" in ql:
                # Infer specialization from params or text
                def _infer_specialization(text: str) -> Optional[str]:
                    t = text.lower()
                    if "marketing" in t and "sales" not in t:
                        return "Marketing"
                    if "finance" in t:
                        return "Finance"
                    if "human resources" in t or re.search(r"\bhr\b", t):
                        return "HR"
                    if "operations" in t or "lean operations" in t:
                        return "Operations"
                    if "strategy" in t:
                        return "Strategy"
                    if "information technology" in t or re.search(r"\bit\b", t):
                        return "IT"
                    if "analytics" in t or "business analytics" in t:
                        return "Analytics"
                    return None

                specialization = filters.get("specialization") or params.get("specialization") or _infer_specialization(resolved_question)
                try:
                    db = PlacementDatabase()
                    if specialization:
                        insights = db.get_specialization_insights(specialization)
                        top_skills = insights.get("top_skills") or []
                        if top_skills:
                            skills_list = ", ".join([s.get("skill") for s in top_skills if s.get("skill")])
                            answer = (
                                f"Based on aggregated {specialization} roles in our database, key skills include: {skills_list}.\n\n"
                                f"Note: This answer uses structured aggregation as supporting PDFs did not yield direct snippets."
                            )
                except Exception:
                    pass
        
        # Add to conversation memory
        conversation.add_message("user", original_question, query_type=query_type.value)
        if answer:
            conversation.add_message("assistant", answer)
        
        return QueryResponse(snippets=snippets, answer=answer, 
                           context_used=context_info if context_info else None)
        
    except Exception as e:
        print(f"❌ Query endpoint error: {e}")
        import traceback
        traceback.print_exc()
        # Return a generic error response
        return QueryResponse(
            snippets=[],
            answer=f"I encountered an error while processing your question. Please try again or contact support. Error: {str(e)}"
        )

@app.get("/query/analyze")
def analyze_query(question: str):
    """Analyze query type and routing strategy"""
    router = QueryRouter()
    query_type, params = router.classify_query(question)
    routing_strategy = router.get_routing_strategy(query_type, params)
    
    return {
        "question": question,
        "query_type": query_type.value,
        "parameters": params,
        "routing_strategy": routing_strategy
    }

@app.get("/stats/placement")
def get_placement_stats(specialization: str = None, batch_year: str = "2024-2025"):
    """Get placement statistics from structured database with MBA specialization support"""
    try:
        db = PlacementDatabase()
        
        # First try to get full stats with offers
        try:
            stats = db.get_placement_stats(specialization, batch_year)
            if stats and stats.get('company_count', 0) > 0:
                return {
                    "success": True,
                    "data": stats,
                    "specialization": specialization,
                    "batch_year": batch_year
                }
        except Exception:
            pass
        
        # Fall back to basic stats if offers data is not available
        basic_stats = db.get_basic_stats()
        return {
            "success": True,
            "data": basic_stats,
            "specialization": specialization,
            "batch_year": batch_year,
            "note": "Basic stats (no offers data available)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "specialization": specialization,
            "batch_year": batch_year
        }

@app.get("/stats/companies")
def get_companies_stats():
    """Get detailed company statistics"""
    try:
        db = PlacementDatabase()
        companies = db.get_companies()
        return {
            "success": True,
            "data": companies
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/search/skills")
def search_by_skills(skill: str, company: str = None):
    """Search roles by skills with optional company filter"""
    try:
        db = PlacementDatabase()
        results = db.search_skills(skill, company)
        return {
            "success": True,
            "data": results,
            "skill": skill,
            "company_filter": company
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "skill": skill,
            "company_filter": company
        }

@app.get("/specialization/companies")
def get_companies_by_specialization(specialization: str, batch_year: str = "2024-2025"):
    """Get companies offering roles in a specific MBA specialization"""
    try:
        db = PlacementDatabase()
        results = db.get_companies_by_specialization(specialization, batch_year)
        return {
            "success": True,
            "data": results,
            "specialization": specialization,
            "batch_year": batch_year
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "specialization": specialization,
            "batch_year": batch_year
        }

@app.get("/specialization/insights")
def get_specialization_insights(specialization: str, batch_year: str = "2024-2025"):
    """Get comprehensive insights for a specific MBA specialization"""
    try:
        db = PlacementDatabase()
        results = db.get_specialization_insights(specialization, batch_year)
        return {
            "success": True,
            "data": results,
            "specialization": specialization,
            "batch_year": batch_year
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "specialization": specialization,
            "batch_year": batch_year
        }

@app.get("/company/compare")
def compare_company_specializations(company: str, batch_year: str = "2024-2025"):
    """Compare different specializations within a company"""
    try:
        db = PlacementDatabase()
        results = db.compare_company_specializations(company, batch_year)
        return {
            "success": True,
            "data": results,
            "company": company,
            "batch_year": batch_year
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "company": company,
            "batch_year": batch_year
        }

@app.get("/specialization/median-salary")
def get_median_salary_by_specialization(specialization: str, batch_year: str = "2024-2025"):
    """Get median salary for a specific MBA specialization"""
    try:
        db = PlacementDatabase()
        median = db.get_median_salary_by_specialization(specialization, batch_year)
        return {
            "success": True,
            "data": {"median_salary": median},
            "specialization": specialization,
            "batch_year": batch_year
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "specialization": specialization,
            "batch_year": batch_year
        }


@app.post("/query/resume_match", response_model=ResumeMatchResponse)
def resume_match(req: ResumeMatchRequest) -> ResumeMatchResponse:
    # Simple strategy: query for frequent skills, aggregate by JD id
    # For now, we approximate JD grouping by `source_file` in metadata
    question = "Key skills and responsibilities"
    snippets = retrieve_snippets(question, top_k=50, filters={})
    jd_groups: Dict[str, Dict[str, Any]] = {}
    for sn in snippets:
        meta = sn.get("metadata", {})
        jd_id = str(meta.get("source_file", meta.get("company", "unknown")))
        g = jd_groups.setdefault(jd_id, {"texts": [], "skills": set(), "metas": meta})
        g["texts"].append(sn["text"])
        for sk in meta.get("extracted_skills", []) or []:
            g["skills"].add(sk.lower())
    resume_skills = set(extract_skills(req.resume_text))
    results: list[ResumeMatchResult] = []
    for jid, g in jd_groups.items():
        jd_skills = set(map(str.lower, g["skills"]))
        if not jd_skills:
            continue
        overlap = len(jd_skills & resume_skills)
        union = len(jd_skills | resume_skills)
        score = float(overlap / union) if union else 0.0
        missing = sorted(list(jd_skills - resume_skills))[:15]
        plan = [
            f"Study fundamentals of {m}",
            f"Complete a mini-project using {m}",
            "Write notes and flashcards on gaps",
            "Practice interview-style questions",
        ][: max(3, min(6, len(missing) if missing else 3))]
        results.append(
            ResumeMatchResult(
                jd_id=jid,
                score=score,
                missing_skills=missing,
                upskilling_plan=plan,
                metadata=g["metas"],
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return ResumeMatchResponse(matches=results[: req.top_k])


@app.post("/gd/simulate", response_model=GDSimulateResponse)
def gd_simulate(req: GDSimulateRequest) -> GDSimulateResponse:
    text = req.transcript.strip()
    length = max(1, len(text.split()))
    scores = {
        "content": min(10.0, 5.0 + length / 200.0),
        "structure": min(10.0, 5.0 + length / 250.0),
        "clarity": min(10.0, 5.0 + length / 220.0),
        "listening": min(10.0, 5.0 + length / 260.0),
    }
    feedback = [
        "Use concrete examples and quantify achievements",
        "Keep responses structured: point → evidence → impact",
        "Pause briefly to maintain clarity and pace",
        "Paraphrase peers to show active listening",
    ]
    replay = [text[:200]] if text else []
    return GDSimulateResponse(scores=scores, feedback=feedback, replay_snippets=replay)


@app.get("/alerts")
def get_alerts() -> Any:
    path = Path("data/alerts.json")
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


@app.post("/chat/clear")
def clear_chat_memory(session_id: str = "default"):
    """Clear chat memory for a session"""
    try:
        memory_manager.clear_session(session_id)
        return {"success": True, "message": f"Chat memory cleared for session {session_id}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/chat/history")
def get_chat_history(session_id: str = "default", limit: int = 10):
    """Get chat history for a session"""
    try:
        conversation = memory_manager.get_session(session_id)
        messages = conversation.messages[-limit:] if limit > 0 else conversation.messages
        return {
            "success": True, 
            "messages": [msg.to_dict() for msg in messages],
            "session_id": session_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


