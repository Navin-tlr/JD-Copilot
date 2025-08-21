from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class QueryFilters(BaseModel):
    company: Optional[str] = None
    # Accept either int or string (UI may send empty string); backend will coerce to int when needed
    year: Optional[Union[int, str]] = None
    role_contains: Optional[str] = None


class QueryRequest(BaseModel):
    question: str
    filters: QueryFilters = Field(default_factory=QueryFilters)
    top_k: int = 5


class Snippet(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    snippets: List[Snippet]
    answer: Optional[str] = None


class ResumeMatchRequest(BaseModel):
    resume_text: str
    top_k: int = 3


class ResumeMatchResult(BaseModel):
    jd_id: str
    score: float
    missing_skills: List[str]
    upskilling_plan: List[str]
    metadata: Dict[str, Any]


class ResumeMatchResponse(BaseModel):
    matches: List[ResumeMatchResult]


class GDSimulateRequest(BaseModel):
    transcript: str


class GDSimulateResponse(BaseModel):
    scores: Dict[str, float]
    feedback: List[str]
    replay_snippets: List[str]


