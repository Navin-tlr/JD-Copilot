"""Hybrid normalization layer for user intent terms (industries, roles, specializations).

Strategy:
1. Fast dictionary expansion of known synonyms/abbreviations to canonical tokens.
2. (Optional) Semantic/LLM fallback if dictionary yields nothing (stub – safely returns none if LLM unavailable).

Outputs a NormalizationResult containing:
- enhanced_question: original question optionally augmented with an inline normalized intent hint
- expansions: dict of categories -> set of canonical tokens
- method: 'dict', 'ai', or 'none'

Low‑risk: If nothing matches, we return the original question unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import json
import time
import re
import os
import requests

try:  # Avoid hard dependency if not configured
    from .config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # type: ignore


# Canonical dictionary – deliberately small & easy to extend.
# Each key is a lowercase synonym; values are structured category->canonical token.
DICTIONARY: Dict[str, Dict[str, str]] = {
    # Industries / broad sectors
    "fmcg": {"industry": "FMCG"},
    "fast moving consumer goods": {"industry": "FMCG"},
    "fast-moving consumer goods": {"industry": "FMCG"},
    "consumer goods": {"industry": "FMCG"},
    "bfs": {"industry": "BFSI"},
    "bfsi": {"industry": "BFSI"},
    "banking": {"industry": "BFSI"},
    "financial services": {"industry": "BFSI"},
    # Company / business model types
    "b2b": {"company_type": "B2B"},
    "b2c": {"company_type": "B2C"},
    # Roles / functions / specializations
    # Sales / revenue roles (treat Business Development as a sales variant, not only B2B)
    "b2b sales": {"role": "Sales", "sales_mode": "B2B"},
    "sales": {"role": "Sales"},
    "inside sales": {"role": "Sales", "sales_channel": "Inside"},
    "field sales": {"role": "Sales", "sales_channel": "Field"},
    "business development": {"role": "Sales", "alias": "Business Development"},
    "bd": {"role": "Sales", "alias": "Business Development"},
    "business development executive": {"role": "Sales", "alias": "Business Development"},
    "business development manager": {"role": "Sales", "alias": "Business Development"},
    "bd executive": {"role": "Sales", "alias": "Business Development"},
    "bdm": {"role": "Sales", "alias": "Business Development"},
    "bd manager": {"role": "Sales", "alias": "Business Development"},
    "marketing": {"specialization": "Marketing"},
    "brand management": {"specialization": "Marketing"},
    "digital marketing": {"specialization": "Marketing"},
    "finance": {"specialization": "Finance"},
    "hr": {"specialization": "HR"},
    "human resources": {"specialization": "HR"},
    "operations": {"specialization": "Operations"},
    "ops": {"specialization": "Operations"},
    "supply chain": {"specialization": "Operations"},
    "analytics": {"specialization": "Analytics"},
    "business analytics": {"specialization": "Analytics"},
    "data science": {"specialization": "Analytics"},
    "it": {"specialization": "IT"},
    "technology": {"specialization": "IT"},
}


@dataclass
class NormalizationResult:
    original_question: str
    enhanced_question: str
    expansions: Dict[str, Set[str]]
    method: str  # 'dict' | 'ai' | 'none'

    def has_expansions(self) -> bool:
        return any(v for v in self.expansions.values())


class HybridNormalizer:
    def __init__(self):
        self.dictionary = self._load_dictionary()
        # Initialize settings lazily if accessor available
        try:
            self.settings = get_settings() if get_settings else None  # type: ignore
        except Exception:
            self.settings = None
        # Removed AI cache as per user request: "REMOVE CACHE FOR EVERYTHING"

    def _load_dictionary(self) -> Dict[str, Dict[str, str]]:
        """Return the in-memory DICTIONARY (hook kept for future extensibility)."""
        return DICTIONARY

    def normalize(self, question: str) -> NormalizationResult:
        q_lower = question.lower()
        expansions: Dict[str, Set[str]] = {
            "industry": set(),
            "company_type": set(),
            "specialization": set(),
            "role": set(),
        }

        method = "none"

        # --- 1. Dictionary pass (token & phrase scanning) ---
        # Check multi-word phrases first (longest keys first)
        for phrase, mapping in sorted(DICTIONARY.items(), key=lambda kv: -len(kv[0])):
            if phrase in q_lower:
                for k, v in mapping.items():
                    expansions.setdefault(k, set()).add(v)
                method = "dict"

        # --- 2. Semantic fallback via OpenRouter (only if no dict hits) ---
        if method == "none":
            ai_added = self._semantic_expand_openrouter(q_lower)
            if ai_added:
                for k, v in ai_added.items():
                    expansions.setdefault(k, set()).add(v)
                method = "ai"

        # --- 3. Build enhanced question (non-invasive) ---
        enhanced_question = question
        if any(expansions.values()):
            # Compact annotation appended so downstream LLMs can leverage canonical context
            parts = []
            for cat, vals in expansions.items():
                if vals:
                    parts.append(f"{cat}={','.join(sorted(vals))}")
            hint = "; ".join(parts)
            enhanced_question = f"{question}\n\n[Normalized intents: {hint}]"

        return NormalizationResult(
            original_question=question,
            enhanced_question=enhanced_question,
            expansions=expansions,
            method=method,
        )

    # ---------------- Internal Helpers -----------------
    def _semantic_expand_openrouter(self, question: str) -> Optional[Dict[str, List[str]]]:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None
        allowed = {
            "industry": ["FMCG", "BFSI"],
            "company_type": ["B2B", "B2C"],
            "specialization": ["Marketing", "Finance", "HR", "Operations", "Analytics", "IT", "Strategy"],
            "role": ["Sales", "Inside Sales", "Field Sales", "Business Development"],
        }
        model = os.getenv("OPENROUTER_NORMALIZER_MODEL") or os.getenv("OPENROUTER_MODEL") or "mistralai/mistral-medium-3.1"
        prompt = (
            "Extract canonical placement intent categories. Return STRICT minified JSON only.\n"
            f"Allowed values: {allowed}.\n"
            "Include a key only if explicitly present or an unambiguous synonym.\n"
            f"User Query: {question}\nJSON:"  # question already lowercase
        )
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You output ONLY strict JSON without commentary."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 128,
                },
                timeout=20,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                return None
            content = (choices[0].get("message", {}) or {}).get("content") or choices[0].get("text")
            if not content:
                return None
            raw = content.strip()
            start, end = raw.find("{"), raw.rfind("}")
            if start == -1 or end == -1:
                return None
            blob = raw[start : end + 1]
            parsed = json.loads(blob)
            cleaned: Dict[str, List[str]] = {}
            for k, v in parsed.items():
                if k in allowed and isinstance(v, str) and v in allowed[k]:
                    cleaned[k] = [v]
            return cleaned or None
        except Exception:
            return None


# Singleton instance
hybrid_normalizer = HybridNormalizer()

__all__ = [
    "hybrid_normalizer",
    "HybridNormalizer",
    "NormalizationResult",
]
