from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI

from .config import Health, get_settings
from .rag import retrieve_snippets, synthesize_answer
from .database import PlacementDatabase
from .query_router import QueryRouter, QueryType
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


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health(status="ok")


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
    """Enhanced query endpoint with intelligent routing"""
    filters: Dict[str, Any] = {
        "company": req.filters.company,
        "year": req.filters.year,
        "role_contains": req.filters.role_contains,
    }
    
    # Use QueryRouter to determine the best approach
    router = QueryRouter()
    query_type, params = router.classify_query(req.question)
    
    print(f"🔍 Query Type: {query_type.value}")
    print(f"📊 Parameters: {params}")
    
    # Route based on query type
    if query_type == QueryType.STRUCTURED:
        # Use structured database for counts, statistics, etc.
        print("📊 Using STRUCTURED database approach")
        try:
            db = PlacementDatabase()
            
            # Handle company count queries
            if "companies" in req.question.lower() and ("how many" in req.question.lower() or "count" in req.question.lower()):
                # Use basic stats method that doesn't require offers data
                basic_stats = db.get_basic_stats()
                company_count = basic_stats.get('company_count', 0)
                
                # Get company names separately
                companies = db.get_companies()
                company_names = [c['company_name'] for c in companies]
                
                answer = f"""Based on the structured placement database, here are the current statistics:

**Total Companies:** {company_count} companies are actively recruiting
**Companies Available:** {', '.join(company_names)}

**Note:** This data is from our current placement database. For historical data or specific year counts, please contact the placement office."""
                
                return QueryResponse(snippets=[], answer=answer)
            
            # Handle other structured queries
            elif "salary" in req.question.lower():
                # Get salary statistics
                stats = db.get_placement_stats()
                answer = f"""Based on the structured placement database:

**Salary Statistics:**
- Average Min Salary: {stats.get('avg_min_salary', 'Not available')} LPA
- Average Max Salary: {stats.get('avg_max_salary', 'Not available')} LPA
- Total Roles: {stats.get('role_count', 'Not available')}

**Note:** Salary data is only available for roles where it was explicitly mentioned."""
                
                return QueryResponse(snippets=[], answer=answer)
                
        except Exception as e:
            print(f"❌ Structured query failed: {e}")
            # Fall back to RAG if structured query fails
    
    # Default to RAG for other query types
    print("🔍 Using RAG approach")
    snippets = retrieve_snippets(req.question, req.top_k, filters)
    answer = synthesize_answer(req.question, snippets, filters) if snippets else None
    
    return QueryResponse(snippets=snippets, answer=answer)

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


