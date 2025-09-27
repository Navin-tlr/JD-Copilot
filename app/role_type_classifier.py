"""Role Type Classifier

Determines higher-level, specialization-aware role type classifications (e.g., B2B,
Performance Marketing, Fund Management) from a role's title + description.

Design goals:
    - Deterministic (no LLM) and auditable
    - Multi-label (a role can be both B2B and Performance Marketing)
    - Specialization-aware: same phrase may map differently based on specialization
    - Easy to extend: add patterns to RULES structure

Usage:
    from app.role_type_classifier import classify_role_types
    tags = classify_role_types(title, specialization, description)

Return format:
    List[Dict[str, Any]] sorted by confidence desc:
        [{"classification": "B2B", "confidence": 0.82, "source": "rule"}, ...]

Confidence heuristic:
    Per classification we sum weights for matched patterns / max possible weight.
    We cap at 1.0. Only return entries with confidence >= MIN_CONF.

Additions in future:
    - Embedding similarity fallback
    - Data-driven calibration (persist pattern hit statistics)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple, Iterable
import re

MIN_CONF = 0.30  # minimum confidence to emit a classification


@dataclass(frozen=True)
class Pattern:
    pattern: str            # case-insensitive substring or regex
    weight: float = 1.0     # contribution weight
    regex: bool = False     # treat pattern as regex if True


# RULES structure:
#   specialization_key (upper) OR "*" for cross-specialization ->
#       classification tag -> list[Pattern]
# Order of insertion does not matter (scoring is additive)
RULES: Dict[str, Dict[str, List[Pattern]]] = {
    # Marketing related
    "MARKETING": {
        "B2B": [
            Pattern("b2b"),
            Pattern("enterprise"),
            Pattern("corporate client"),
            Pattern("client acquisition"),
            Pattern("lead generation"),
            Pattern("partnership"),
            Pattern("account management"),
            Pattern("business development"),
            Pattern("bd team"),
            Pattern("sales development representative"),
            Pattern("sales development"),
            Pattern("sdr"),
        ],
        "PERFORMANCE MARKETING": [
            Pattern("performance marketing"),
            Pattern("paid media"),
            Pattern("google ads"),
            Pattern("meta ads"),
            Pattern("facebook ads"),
            Pattern("campaign optimization"),
            Pattern("cpc"),
            Pattern("roas"),
            Pattern("ppc"),
            Pattern("sem"),
            Pattern("ad spend"),
        ],
        "MEDIA OPERATIONS": [
            Pattern("media operations"),
            Pattern("ad operations"),
            Pattern("campaign trafficking"),
            Pattern("inventory management"),
        ],
        "BRAND MARKETING": [
            Pattern("brand strategy"),
            Pattern("brand positioning"),
            Pattern("go-to-market"),
            Pattern("brand campaign"),
        ],
        "CONTENT MARKETING": [
            Pattern("content marketing"),
            Pattern("copywriting"),
            Pattern("long-form content"),
            Pattern("blog"),
            Pattern("editorial calendar"),
            Pattern("seo"),
        ],
        "FMCG": [
            Pattern("fmcg"),
            Pattern("fast moving consumer goods"),
            Pattern("consumer product"),
            Pattern("retail distribution"),
        ],
    },
    # Finance related
    "FINANCE": {
        "FUND MANAGEMENT": [
            Pattern("fund management"),
            Pattern("portfolio management"),
            Pattern("asset management"),
            Pattern("aum"),
            Pattern("investment strategy"),
            Pattern("investment analysis"),
            Pattern("equity research"),
        ],
        "CORPORATE FINANCE": [
            Pattern("treasury"),
            Pattern("working capital"),
            Pattern("capital budgeting"),
            Pattern("financial modelling"),
            Pattern("valuation"),
            Pattern("m&a"),
        ],
        "RISK & COMPLIANCE": [
            Pattern("risk management"),
            Pattern("regulatory"),
            Pattern("compliance"),
            Pattern("audit"),
            Pattern("sox"),
            Pattern("internal control"),
        ],
    },
    # HR related
    "HR": {
        "TALENT ACQUISITION": [
            Pattern("talent acquisition"),
            Pattern("recruitment"),
            Pattern("sourcing"),
            Pattern("campus hiring"),
        ],
        "LEARNING & DEVELOPMENT": [
            Pattern("learning & development"),
            Pattern("l&d"),
            Pattern("training program"),
            Pattern("curriculum design"),
        ],
        "HR OPERATIONS": [
            Pattern("hr operations"),
            Pattern("people operations"),
            Pattern("onboarding"),
            Pattern("employee lifecycle"),
        ],
    },
    # Operations / Lean
    "LEAN OPERATION AND SYSTEMS": {
        "PROCESS EXCELLENCE": [
            Pattern("process improvement"),
            Pattern("lean"),
            Pattern("six sigma"),
            Pattern("kaizen"),
            Pattern("continuous improvement"),
        ],
        "SUPPLY CHAIN OPERATIONS": [
            Pattern("supply chain"),
            Pattern("logistics"),
            Pattern("procurement"),
            Pattern("inventory"),
            Pattern("warehouse"),
        ],
    },
    # Analytics
    "BUSINESS ANALYTICS": {
        "DATA ANALYTICS": [
            Pattern("sql"),
            Pattern("python"),
            Pattern("tableau"),
            Pattern("power bi"),
            Pattern("data visualization"),
            Pattern("data analysis"),
            Pattern("dashboard"),
        ],
        "MACHINE LEARNING": [
            Pattern("machine learning"),
            Pattern("predictive model"),
            Pattern("classification model"),
            Pattern("regression model"),
        ],
    },
    # Cross specialization (use key "*")
    "*": {
        "B2C": [Pattern("b2c"), Pattern("consumer acquisition"), Pattern("end consumer")],
    },
}


def _normalize(s: str) -> str:
    return (s or "").lower()


def classify_role_types(title: str, specialization: str, description: str = "") -> List[Dict[str, object]]:
    """Return multi-label classification results.

    Args:
        title: role title
        specialization: specialization string (case-insensitive)
        description: combined description / responsibilities / requirements
    """
    spec_key = (specialization or "").upper().strip()
    text = f"{title}\n{description}".lower()

    results: List[Dict[str, object]] = []

    # Gather applicable rule sets
    rule_sets: List[Tuple[str, Dict[str, List[Pattern]]]] = []
    if spec_key in RULES:
        rule_sets.append((spec_key, RULES[spec_key]))
    if "*" in RULES:
        rule_sets.append(("*", RULES["*"]))

    for _, spec_rules in rule_sets:
        for classification, patterns in spec_rules.items():
            total_weight = sum(p.weight for p in patterns)
            score = 0.0
            hits: List[str] = []
            for p in patterns:
                if p.regex:
                    if re.search(p.pattern, text, flags=re.IGNORECASE):
                        score += p.weight
                        hits.append(p.pattern)
                else:
                    if p.pattern in text:
                        score += p.weight
                        hits.append(p.pattern)
            if score <= 0:
                continue
            confidence = min(1.0, score / max(1e-6, total_weight))
            if confidence >= MIN_CONF:
                results.append(
                    {
                        "classification": classification,
                        "confidence": round(confidence, 4),
                        "source": "rule",
                        "hits": hits,
                    }
                )

    # Sort by confidence desc then classification
    results.sort(key=lambda r: (-r["confidence"], r["classification"]))
    return results


__all__ = ["classify_role_types"]
