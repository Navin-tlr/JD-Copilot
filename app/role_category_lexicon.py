"""Role Category Lexicon

Defines a broad but finite set of canonical role categories and their trigger phrases.
Used to derive per-document candidate categories (grounding) so LLM cannot hallucinate.

Only categories whose synonym triggers appear in text (title / description / responsibilities / requirements)
will be offered to the LLM. Post-LLM, results are filtered again against the candidate list.

Extend safely by adding new keys with a list of lowercase trigger substrings.
"""

from __future__ import annotations

from typing import Dict, List, Set


CATEGORY_SYNONYMS: Dict[str, List[str]] = {
    # Sales / Marketing
    "B2B SALES": [
        "b2b",
        "enterprise sales",
        "corporate sales",
        "account acquisition",
        "lead generation",
        "business development",
        "partner acquisition",
        "sales development representative",
        "sales development",
        "sdr",
    ],
    "B2C SALES": ["b2c", "consumer sales", "retail sales", "inside sales", "direct to consumer"],
    "INSIDE SALES": ["inside sales", "cold calling", "tele sales"],
    "ACCOUNT MANAGEMENT": ["account management", "key account", "client success", "client relationship"],
    "PARTNERSHIPS & ALLIANCES": ["partnership", "alliance", "channel partner", "strategic partner"],
    "PERFORMANCE MARKETING": ["performance marketing", "cpc", "ppc", "roas", "paid media", "google ads", "meta ads", "ad spend", "sem", "campaign optimization"],
    "GROWTH MARKETING": ["growth marketing", "growth experiments", "growth funnel", "activation rate"],
    "DIGITAL MARKETING": ["digital marketing", "online marketing", "digital channels"],
    "BRAND MARKETING": ["brand strategy", "brand positioning", "brand campaign"],
    "CONTENT MARKETING": ["content marketing", "copywriting", "blog", "editorial calendar", "long-form content"],
    "MEDIA OPERATIONS": ["media operations", "ad operations", "campaign trafficking", "inventory management"],
    "PRODUCT MARKETING": ["product marketing", "market positioning", "competitive intel"],
    "CATEGORY MANAGEMENT": ["category management", "category strategy"],
    "FMCG": ["fmcg", "fast moving consumer goods", "consumer product", "retail distribution"],
    # Finance
    "FUND MANAGEMENT": ["fund management", "portfolio management", "investment strategy", "asset management", "aum"],
    "EQUITY RESEARCH": ["equity research", "stock analysis", "valuation model"],
    "CORPORATE FINANCE": ["corporate finance", "treasury", "capital budgeting", "financial modelling", "valuation", "m&a"],
    "INVESTMENT BANKING": ["investment banking", "pitchbook", "deal execution"],
    "RISK & COMPLIANCE": ["risk management", "regulatory", "compliance", "audit", "sox", "internal control"],
    "FINANCIAL ANALYSIS": ["financial analysis", "variance analysis", "fp&a", "budget vs"],
    # HR
    "TALENT ACQUISITION": ["talent acquisition", "recruitment", "sourcing", "campus hiring"],
    "HR OPERATIONS": ["hr operations", "people operations", "employee lifecycle", "hris"],
    "LEARNING & DEVELOPMENT": ["learning & development", "l&d", "training program", "curriculum design"],
    "TOTAL REWARDS": ["total rewards", "compensation", "benefits design"],
    "EMPLOYEE ENGAGEMENT": ["employee engagement", "engagement survey", "culture initiative"],
    # Operations / Strategy
    "PROCESS EXCELLENCE": ["process improvement", "lean", "six sigma", "kaizen", "continuous improvement"],
    "SUPPLY CHAIN": ["supply chain", "logistics", "inventory", "warehouse", "distribution center"],
    "PROCUREMENT": ["procurement", "sourcing strategy", "vendor negotiation"],
    "OPERATIONS MANAGEMENT": ["operations management", "operational efficiency", "ops excellence"],
    "PROJECT MANAGEMENT": ["project management", "project plan", "gantt", "pm execution"],
    "PROGRAM MANAGEMENT": ["program management", "program governance", "program roadmap"],
    "STRATEGY & PLANNING": ["strategy", "strategic planning", "corporate strategy", "annual operating plan"],
    "CONSULTING": ["consulting", "client engagement", "advisory project"],
    # Analytics / Tech / Product
    "DATA ANALYTICS": ["data analysis", "data analytics", "sql", "tableau", "power bi", "dashboard", "data visualization"],
    "BUSINESS INTELLIGENCE": ["business intelligence", "bi solution", "etl"],
    "MACHINE LEARNING": ["machine learning", "predictive model", "classification model", "regression model"],
    "DATA ENGINEERING": ["data pipeline", "data ingestion", "data engineer", "etl pipeline"],
    "PRODUCT MANAGEMENT": ["product management", "product requirement", "prd", "feature roadmap"],
    "CUSTOMER SUCCESS": ["customer success", "csat", "renewal rate", "adoption"],
    "PRE-SALES": ["pre-sales", "presales", "solution demo", "rfi", "rfp"],
}


def extract_candidate_categories(text: str) -> Set[str]:
    """Return set of canonical categories whose synonyms appear in text (case-insensitive)."""
    t = (text or "").lower()
    found: Set[str] = set()
    for category, syns in CATEGORY_SYNONYMS.items():
        for s in syns:
            if s in t:
                found.add(category)
                break
    return found


__all__ = ["CATEGORY_SYNONYMS", "extract_candidate_categories"]
