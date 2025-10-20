"""
Hierarchical Industry Classification System
- Specialization: Already extracted during ingestion (Marketing, Finance, Operations, HR, Analytics)
- Level 1: Industry subcategory under specialization (FMCG, Investment Banking, Supply Chain, etc.)
- Level 2: LLM-inferred specific details
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class IndustryClassification:
    """Result of hierarchical industry classification"""
    specialization: str  # Already known from ingestion: Marketing, Finance, Operations, HR, Analytics
    level1: str  # Industry subcategory (FMCG, Investment Banking, Supply Chain, etc.)
    level2: str  # Specific details (LLM-inferred)
    confidence: float
    reasoning: str


class IndustryClassifier:
    """
    Hierarchical industry classification using LLM.
    Takes existing specialization from metadata, infers Level 1 and Level 2.
    """
    
    # Level 1 options per specialization
    LEVEL1_OPTIONS = {
        "Marketing": [
            "FMCG",
            "B2B Sales",
            "Market Research",
            "Digital Marketing",
            "Content Creation",
            "Retail & E-Commerce"
        ],
        "Finance": [
            "Asset Management",
            "Portfolio Management",
            "Retail Banking",
            "Investment Banking",
            "Corporate Finance",
            "Wealth Management"
        ],
        "LEAN OPERATION AND SYSTEMS": [
            "IT & Technology",
            "Supply Chain",
            "Logistics",
            "Process Management",
            "Project Management",
            "ERP",
            "Manufacturing"
        ],
        "HR": [
            "Talent Acquisition",
            "People Operations",
            "Organizational Development",
            "Employee Relations",
            "Compensation & Benefits",
            "Learning & Development"
        ],
        "Analytics": [
            "Business Analytics",
            "Data Science",
            "Business Intelligence",
            "Predictive Analytics",
            "Data Engineering",
            "Reporting & Insights"
        ]
    }
    
    def __init__(self):
        from app.llm_client import GeminiClient
        self.llm = GeminiClient()
    
    def classify(
        self,
        job_description: str,
        specialization: str,
        context: Optional[Dict] = None
    ) -> IndustryClassification:
        """
        Classify job description into Level 1 and Level 2 given the specialization.
        
        Args:
            job_description: Full job description text
            specialization: Already extracted (Marketing, Finance, Operations, HR, Analytics)
            context: Optional context (role title, company, etc.)
        
        Returns:
            IndustryClassification with Level 1 and Level 2
        """
        
        # Get Level 1 options for this specialization
        level1_options = self.LEVEL1_OPTIONS.get(specialization, [])
        if not level1_options:
            # Fallback for unknown specialization
            return IndustryClassification(
                specialization=specialization,
                level1="General",
                level2="General",
                confidence=0.3,
                reasoning="Unknown specialization, using fallback"
            )
        
        # Build context string
        context_str = ""
        if context:
            if context.get("role_title"):
                context_str += f"\nRole Title: {context['role_title']}"
            if context.get("company"):
                context_str += f"\nCompany: {context['company']}"
            if context.get("industry"):
                context_str += f"\nCompany Industry: {context['industry']}"
        
        prompt = f"""Classify this job description into a hierarchical industry taxonomy.

SPECIALIZATION (Already Known): {specialization}

LEVEL 1 OPTIONS (choose exactly ONE that best fits):
{json.dumps(level1_options, indent=2)}

LEVEL 2 SUBCATEGORY:
- Infer the SPECIFIC subcategory from the job description
- Be precise and descriptive (e.g., "Consumer Electronics FMCG", "Equity Research", "Cloud Infrastructure")
- Base it on the actual role responsibilities and requirements
- Use 2-4 words maximum

{context_str}

JOB DESCRIPTION:
{job_description[:2000]}

Respond in EXACTLY this JSON format:
{{
    "level1": "One of the Level 1 options above",
    "level2": "Specific subcategory inferred from JD",
    "confidence": 0.0-1.0,
    "reasoning": "1-2 sentence explanation"
}}

CRITICAL: Return ONLY valid JSON, no other text."""
        
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            
            # Parse JSON response
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            data = json.loads(response_clean)
            
            # Validate Level 1
            level1 = data.get("level1", "")
            if level1 not in level1_options:
                # Try partial match
                level1_lower = level1.lower()
                for valid_opt in level1_options:
                    if valid_opt.lower() in level1_lower or level1_lower in valid_opt.lower():
                        level1 = valid_opt
                        break
                else:
                    # Default to first option
                    level1 = level1_options[0] if level1_options else "General"
                    print(f"⚠️ Invalid Level 1 '{data.get('level1')}', defaulting to {level1}")
            
            level2 = data.get("level2", "General").strip()
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "")
            
            return IndustryClassification(
                specialization=specialization,
                level1=level1,
                level2=level2,
                confidence=max(0.0, min(1.0, confidence)),
                reasoning=reasoning
            )
            
        except Exception as e:
            print(f"⚠️ Classification failed: {e}")
            # Fallback classification
            return IndustryClassification(
                specialization=specialization,
                level1=level1_options[0] if level1_options else "General",
                level2="General",
                confidence=0.3,
                reasoning=f"Classification failed: {str(e)}"
            )
    
    def get_level1_options(self, specialization: str) -> List[str]:
        """Get Level 1 options for a specialization"""
        return self.LEVEL1_OPTIONS.get(specialization, [])
    
    def format_for_metadata(self, classification: IndustryClassification) -> Dict[str, str]:
        """
        Format classification for Pinecone metadata storage.
        
        Returns:
            {
                "specialization": "Marketing",
                "industry_level1": "FMCG",
                "industry_level2": "Consumer Electronics FMCG",
                "industry_full": "Marketing > FMCG > Consumer Electronics FMCG"
            }
        """
        return {
            "specialization": classification.specialization,
            "industry_level1": classification.level1,
            "industry_level2": classification.level2,
            "industry_full": f"{classification.specialization} > {classification.level1} > {classification.level2}"
        }


# Global instance
industry_classifier = IndustryClassifier()
