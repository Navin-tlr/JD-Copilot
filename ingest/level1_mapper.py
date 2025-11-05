"""
Level 1 Role Mapper Module
LLM-backed selection from predefined Level 1 candidates per specialization (loaded from YAML).
Supports union for multiple specializations with provenance.
"""

import json
import logging
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.config import get_settings
from app.openrouter_wrapper import OpenRouterWrapper

logger = logging.getLogger(__name__)

class Level1Mapper:
    def __init__(self):
        self.settings = get_settings()
        self.wrapper = None
        if self.settings.OPENROUTER_API_KEY:
            try:
                self.wrapper = OpenRouterWrapper()
                logger.info("OpenRouterWrapper initialized for Level 1 mapping")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouterWrapper: {e}")
                self.wrapper = None
        
        # Load predefined Level 1 schema from YAML
        self.level1_schema = self._load_schema()
        self.hybrids = self.level1_schema.get('hybrids', {})
        
        # Load prompt
        self.prompt_path = Path("prompts/level1_mapping_prompt.md")
        if self.prompt_path.exists():
            with open(self.prompt_path, 'r') as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = "You are an extraction assistant. Select from predefined Level 1 candidates for the given specializations and JD. Return JSON array: [{'level1': str, 'specializations': [str], 'confidence': float, 'rationale': str}]. Select 1-3 best matches. Return valid JSON only."

        # Configurable threshold
        self.confidence_threshold = getattr(self.settings, 'LEVEL1_THRESHOLD', 0.2)

    def _load_schema(self) -> Dict[str, Any]:
        """Load Level 1 mappings from config/LEVEL1_MAPS.yml."""
        schema_path = Path("config/LEVEL1_MAPS.yml")
        if not schema_path.exists():
            logger.warning("config/LEVEL1_MAPS.yml not found; using empty schema")
            return {}
        
        try:
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            logger.info(f"Loaded Level 1 schema with {len(schema)-1 if 'hybrids' in schema else len(schema)} specializations")  # -1 for hybrids
            return schema
        except Exception as e:
            logger.error(f"Failed to load Level 1 schema: {e}")
            return {}

    def map_level1_roles(self, specializations: List[str], jd_text: str) -> List[str]:
        """
        Select Level 1 roles from predefined candidates using LLM.
        
        Args:
            specializations: List of detected specializations.
            jd_text: JD text for context.
            
        Returns:
            List of selected level1 roles (simple strings for final output).
        """
        if not specializations:
            return []
        
        # Enhance specializations with hybrids (semantic check via LLM or keywords for terms)
        enhanced_specs = self._detect_hybrids(specializations, jd_text)
        
        # Get candidates from schema
        candidates = self._get_candidates(enhanced_specs)
        if not candidates:
            return []
        
        if self.wrapper:
            try:
                selected = self._llm_select(candidates, jd_text, enhanced_specs)
                # Return simple list for final output (internal keeps dicts)
                return [s['level1'] for s in selected]
            except Exception as e:
                logger.warning(f"LLM selection failed: {e}")
                # Fallback to first from each spec
                return self._fallback_select(enhanced_specs)
        
        return self._fallback_select(enhanced_specs)

    def _detect_hybrids(self, specializations: List[str], jd_text: str) -> List[str]:
        """Detect and expand hybrids semantically."""
        # Simple keyword check for hybrid terms (as per schema)
        jd_lower = jd_text.lower()
        for term, mapping in self.hybrids.items():
            if term.lower() in jd_lower:
                specs = mapping.get('specs', [])
                logger.info(f"Detected hybrid '{term}': expanding to {specs}")
                return list(set(specializations + specs))  # Union
        
        # If no explicit hybrid, return original
        return specializations

    def _get_candidates(self, specializations: List[str]) -> Dict[str, List[str]]:
        """Get Level 1 candidates from schema for specs."""
        candidates = {}
        for spec in specializations:
            spec_key = spec.replace(' ', '_').replace('/', '').lower()  # Normalize key
            if spec_key in self.level1_schema:
                candidates[spec] = self.level1_schema[spec_key]
            else:
                logger.warning(f"No schema for specialization: {spec}")
        return candidates

    def _llm_select(self, candidates: Dict[str, List[str]], jd_text: str, specializations: List[str]) -> List[Dict[str, Any]]:
        """LLM selection from candidates."""
        # Build prompt with candidates
        cand_str = "\n".join([f"{spec}: {', '.join(cands)}" for spec, cands in candidates.items()])
        user_prompt = f"Specializations: {', '.join(specializations)}\nCandidates per spec:\n{cand_str}\nJD Text: {jd_text}\n\nSelect 1-3 best Level 1 matches as JSON array."
        
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
        
        json_str = self._extract_json(response)
        if not json_str:
            return []
        
        try:
            selected = json.loads(json_str)
            filtered = [s for s in selected if s.get('confidence', 0) >= self.confidence_threshold]
            for s in filtered:
                s['source'] = 'llm'
                if 'specializations' not in s:
                    s['specializations'] = specializations
                if 'rationale' not in s:
                    s['rationale'] = 'Selected from candidates'
            return filtered
        except json.JSONDecodeError:
            return []

    def _fallback_select(self, specializations: List[str]) -> List[str]:
        """Fallback: first candidate from each spec."""
        selected = []
        for spec in specializations:
            spec_key = spec.replace(' ', '_').replace('/', '').lower()
            if spec_key in self.level1_schema:
                selected.append(self.level1_schema[spec_key][0])  # First
        return selected

    def _extract_json(self, response: str) -> Optional[str]:
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return None

# Export simple function for pipeline (returns list[str])
def map_level1_roles(specializations: List[str], jd_text: str) -> List[str]:
    mapper = Level1Mapper()
    return mapper.map_level1_roles(specializations, jd_text)