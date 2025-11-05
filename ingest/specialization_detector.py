"""
Specialization Detector Module
Pure semantic LLM inference for multi-label specialization detection.
Post-process for known hybrid terms to ensure multi-spec assignment.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.config import get_settings
from app.openrouter_wrapper import OpenRouterWrapper

logger = logging.getLogger(__name__)

class SpecializationDetector:
    def __init__(self):
        self.settings = get_settings()
        self.wrapper = None
        if self.settings.OPENROUTER_API_KEY:
            try:
                self.wrapper = OpenRouterWrapper()
                logger.info("OpenRouterWrapper initialized for specialization detection")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouterWrapper: {e}")
                self.wrapper = None
        
        # Load prompt (enhanced for semantic hybrid detection)
        self.prompt_path = Path("prompts/specialization_prompt.md")
        if self.prompt_path.exists():
            with open(self.prompt_path, 'r') as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = """You are an extraction assistant. Detect MBA specializations from JD text using semantic inference (no keywords). Return JSON array: [{'specialization': str, 'confidence': float, 'evidence': str}]. Multi-label allowed. For hybrids like 'financial analytics', 'marketing analytics', or 'operations analytics', include both relevant specializations (e.g., Finance + Business Analytics). Rely on JD semantics for inference. Return valid JSON only."""

        # Known hybrid terms for post-processing (light check to ensure LLM assigns multiple)
        self.hybrid_terms = {
            "financial analytics": ["Finance", "Business Analytics"],
            "marketing analytics": ["Marketing", "Business Analytics"],
            "operations analytics": ["Lean Operations & Systems", "Business Analytics"]
        }

        # Configurable threshold and top_k
        self.confidence_threshold = getattr(self.settings, 'SPECIALIZATION_THRESHOLD', 0.15)
        self.top_k = getattr(self.settings, 'SPECIALIZATION_TOP_K', None)

    def detect_specializations(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect specializations using pure LLM semantic inference, with hybrid post-processing.
        
        Args:
            text: JD text to analyze.
            
        Returns:
            List of dicts: [{"specialization": str, "confidence": float, "source": str, "evidence": str}]
        """
        if self.wrapper:
            try:
                specs = self._llm_detect(text)
                # Post-process for known hybrids
                specs = self._ensure_hybrid_assignment(specs, text)
                return specs
            except Exception as e:
                logger.warning(f"LLM detection failed: {e}")
                return []
        
        logger.warning("No LLM available; returning empty specializations")
        return []

    def _llm_detect(self, text: str) -> List[Dict[str, Any]]:
        """LLM-based semantic detection using prompt template."""
        user_prompt = f"JD Text: {text}\n\nExtract specializations as JSON array using semantic understanding."
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.wrapper.chat(
            messages,
            model=self.settings.OPENROUTER_MODEL,
            temperature=0.1,
            max_tokens=300
        )
        
        # Extract JSON from response
        json_str = self._extract_json(response)
        if not json_str:
            logger.warning("No valid JSON from LLM response")
            return []
        
        try:
            specs = json.loads(json_str)
            # Filter by threshold and top_k
            filtered = [s for s in specs if s.get('confidence', 0) >= self.confidence_threshold]
            if self.top_k:
                filtered = filtered[:self.top_k]
            # Standardize
            for s in filtered:
                s['source'] = 'llm'
                if 'evidence' not in s:
                    s['evidence'] = 'Inferred from JD semantics'
            return filtered
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []

    def _ensure_hybrid_assignment(self, specs: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Post-process to ensure known hybrid terms trigger multiple specs."""
        text_lower = text.lower()
        for term, multi_specs in self.hybrid_terms.items():
            if term in text_lower:
                # Check if LLM already included both; if not, add the missing one with medium confidence
                included = set(s['specialization'] for s in specs)
                missing = [spec for spec in multi_specs if spec not in included]
                for missing_spec in missing:
                    # Add with adjusted confidence based on existing
                    base_conf = 0.7  # Medium for post-process
                    evidence = f"Hybrid term '{term}' detected"
                    specs.append({
                        'specialization': missing_spec,
                        'confidence': base_conf,
                        'source': 'llm_hybrid',
                        'evidence': f"Triggered by hybrid term '{term}'"
                    })
                logger.info(f"Ensured hybrid assignment for '{term}': added {missing}")
        return specs

    def _extract_json(self, response: str) -> Optional[str]:
        """Extract JSON from LLM response."""
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return None

# For convenience, export the function
def detect_specializations(text: str) -> List[Dict[str, Any]]:
    detector = SpecializationDetector()
    return detector.detect_specializations(text)