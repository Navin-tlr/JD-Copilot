from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI

from .config import Health, get_settings
from .rag import retrieve_snippets, synthesize_answer
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
    from .rag import get_pinecone_index
    import json
    
    try:
        index = get_pinecone_index()
        # Query with a dummy vector to get some results and extract companies
        dummy_vector = [0.1] * 384  # Assuming 384-dim embeddings
        res = index.query(vector=dummy_vector, top_k=100, include_metadata=True)
        
        companies = set()
        for match in res.get("matches", []):
            meta = match.get("metadata", {})
            company = meta.get("company")
            if company and company.strip():
                companies.add(company.strip())
        
        company_list = sorted(list(companies))
        return {"companies": company_list}
    except Exception as e:
        return {"companies": [], "error": str(e)}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    filters: Dict[str, Any] = {
        "company": req.filters.company,
        "year": req.filters.year,
        "role_contains": req.filters.role_contains,
    }
    snippets = retrieve_snippets(req.question, req.top_k, filters)
    answer = synthesize_answer(req.question, snippets) if snippets else None
    return QueryResponse(snippets=snippets, answer=answer)


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


