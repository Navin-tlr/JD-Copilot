"""
Level 2 Role Extractor Module
Dynamic extraction of Level-2 sub-roles tied to Level 1 candidates using LLM.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.config import get_settings
from app.openrouter_wrapper import OpenRouterWrapper

logger = logging.getLogger(__name__)

class Level2Extractor:
    def __init__(self):
        self.settings = get_settings()
        self.wrapper = None
        if self.settings.OPENROUTER_API_KEY:
            try:
                self.wrapper = OpenRouterWrapper()
                logger.info("OpenRouterWrapper initialized for Level 2 extraction")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouterWrapper: {e}")
                self.wrapper = None
        
        # Inline system prompt (no dedicated file specified)
        self.system_prompt = """You are an extraction assistant. Given Level 1 role candidates and JD text, extract 1-3 granular Level 2 sub-roles for each Level 1.
Return JSON array: [{"level2": str, "level1": str, "confidence": float, "rationale": str}].
Prefer MBA placement sub-roles based on responsibilities/skills (e.g., for 'B2B Sales': 'SDR', 'Account Executive').
Multi-Level 1 supported; one or more Level 2 per Level 1. Return valid JSON only."""

        # Configurable threshold
        self.confidence_threshold = getattr(self.settings, 'LEVEL2_THRESHOLD', 0.2)

    def extract_level2_roles(self, jd_text: str, level1_candidates: List[str]) -> List[Dict[str, Any]]:
        """
        Extract Level 2 sub-roles for given Level 1 candidates using LLM.
        
        Args:
            jd_text: JD text for context.
            level1_candidates: List of Level 1 roles (e.g., ['B2B Sales', 'Digital Marketing']).
            
        Returns:
            List of dicts: [{"level2": str, "level1": str, "confidence": float, "source": str, "rationale": str}]
        """
        if not level1_candidates:
            logger.warning("No Level 1 candidates provided for Level 2 extraction")
            return []
        
        if self.wrapper:
            try:
                return self._llm_extract(jd_text, level1_candidates)
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}")
                return []
        
        # Fallback: generic sub-roles
        return self._fallback_extract(jd_text, level1_candidates)

    def _llm_extract(self, jd_text: str, level1_candidates: List[str]) -> List[Dict[str, Any]]:
        """LLM-based extraction."""
        level1_str = ", ".join(level1_candidates)
        user_prompt = f"Level 1 Candidates: {level1_str}\nJD Text: {jd_text}\n\nExtract Level 2 sub-roles as JSON array."
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.wrapper.chat(
            messages,
            model=self.settings.OPENROUTER_MODEL,
            temperature=0.1,
            max_tokens=400
        )
        
        # Extract JSON
        json_str = self._extract_json(response)
        if not json_str:
            logger.warning("No valid JSON from LLM for Level 2 extraction")
            return []
        
        try:
            subroles = json.loads(json_str)
            # Filter by threshold
            filtered = [r for r in subroles if r.get('confidence', 0) >= self.confidence_threshold]
            # Standardize
            for r in filtered:
                r['source'] = 'llm'
                if 'rationale' not in r:
                    r['rationale'] = 'Inferred from JD responsibilities'
            return filtered
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []

    def _fallback_extract(self, jd_text: str, level1_candidates: List[str]) -> List[Dict[str, Any]]:
        """Basic fallback with generic sub-roles."""
        generic_subroles = {
            "B2B Sales": ["SDR"],
            "Digital Marketing": ["SEO Specialist"],
            "Financial Planning and Analysis": ["Budget Analyst"],
            "Data Analytics": ["Data Scientist"],
            # Add more as needed
        }
        detected = []
        for l1 in level1_candidates:
            if l1 in generic_subroles:
                for l2 in generic_subroles[l1][:2]:  # Limit to 2
                    detected.append({
                        "level2": l2,
                        "level1": l1,
                        "confidence": 0.3,
                        "source": "fallback",
                        "rationale": "Generic fallback due to no LLM available"
                    })
        return detected

    def _extract_json(self, response: str) -> Optional[str]:
        """Extract JSON array from response."""
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return None

# Export the function
def extract_level2_roles(jd_text: str, level1_candidates: List[str]) -> List[Dict[str, Any]]:
    extractor = Level2Extractor()
    return extractor.extract_level2_roles(jd_text, level1_candidates)