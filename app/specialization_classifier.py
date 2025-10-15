"""
LLM-based Specialization Classifier
Analyzes JD content and maps to fixed specializations (no hardcoded rules).
"""

from typing import List
import json
import httpx
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SpecializationClassifier:
    """
    Extract specializations from JD content using LLM semantic understanding.
    Maps to fixed taxonomy: Marketing, Finance, Operations, Analytics, HR, General
    """
    
    VALID_SPECIALIZATIONS = [
        "Marketing",
        "Finance",
        "Operations",
        "Analytics",
        "HR",
        "General"
    ]
    
    CLASSIFICATION_PROMPT = """You are an expert career counselor analyzing job descriptions for an MBA placement system.

Your task: Map this job description to ONE OR MORE specializations based on semantic understanding.

SPECIALIZATIONS (with semantic definitions):

1. **Marketing**: 
   - Brand management, digital marketing, product marketing, market research
   - Customer engagement, social media, advertising, communications, PR
   - Growth strategies, positioning, competitive analysis, campaign management

2. **Finance**:
   - Accounting, financial analysis, investment management, auditing
   - Treasury, risk management, financial planning & analysis (FP&A)
   - Corporate finance, equity research, banking operations, tax, compliance

3. **HR**:
   - Talent acquisition, recruitment, employee relations
   - Learning & development, training, organizational development
   - HR operations, compensation & benefits, performance management, HRIS

4. **Analytics**:
   - Data science, business intelligence, statistical analysis
   - Market research, insights generation, reporting & visualization
   - Predictive modeling, machine learning applications, A/B testing, SQL/Python

5. **Operations**:
   - Supply chain management, logistics, inventory management
   - Process improvement, quality control, production planning
   - Project management, operations strategy, vendor management, procurement

6. **General**:
   - Management trainee programs EXPLICITLY open to ALL specializations
   - Roles stating "any background", "all streams welcome", "open to all MBA students"
   - Cross-functional rotational programs with NO specific specialization requirement

---

JOB DESCRIPTION:
Company: {company_name}
Content:
{jd_text}

---

ANALYSIS INSTRUCTIONS:

1. Read the ENTIRE job description carefully
2. Identify the PRIMARY function (what will they do day-to-day?)
3. Check required qualifications, skills, and background
4. Determine if specialized OR general

MAPPING RULES:
- Return 1-2 specializations maximum (rarely 3 if truly cross-functional)
- If JD explicitly says "open to all specializations/streams/backgrounds" → ["General"]
- If JD requires specific domain knowledge (e.g., "Finance background required") → that specialization
- If JD combines areas (e.g., "Marketing Analytics") → both ["Marketing", "Analytics"]
- If truly ambiguous or no clear fit → ["General"]
- DO NOT return invalid specializations outside the list above

OUTPUT FORMAT (JSON only, no other text):
{{
  "specializations": ["Marketing"],
  "reasoning": "Role focuses on brand strategy and digital campaigns"
}}

Examples:

Input: "Brand Manager - Digital Marketing Strategy & Social Media"
Output: {{"specializations": ["Marketing"], "reasoning": "Primary function is brand and digital marketing management"}}

Input: "Financial Analyst - SQL & Python for Financial Modeling"
Output: {{"specializations": ["Finance", "Analytics"], "reasoning": "Finance role requiring analytical/data skills"}}

Input: "Management Trainee - All Streams Welcome (Marketing/Finance/Operations)"
Output: {{"specializations": ["General"], "reasoning": "Explicitly open to all MBA specializations"}}

Input: "Supply Chain Analyst - Data-Driven Logistics"
Output: {{"specializations": ["Operations", "Analytics"], "reasoning": "Operations role with heavy analytics component"}}

Now analyze the job description above and return ONLY the JSON output:
"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            print("⚠️ OPENROUTER_API_KEY not set. Specialization extraction will fail.")
    
    async def classify(
        self, 
        jd_text: str, 
        company_name: str
    ) -> List[str]:
        """
        Classify JD into specializations using LLM.
        
        Args:
            jd_text: Full job description text
            company_name: Company name for context
        
        Returns:
            List of validated specializations (e.g., ["Marketing", "Operations"])
            Falls back to ["General"] if classification fails
        """
        
        # Build prompt
        prompt = self.CLASSIFICATION_PROMPT.format(
            jd_text=jd_text[:5000],  # First 5k characters
            company_name=company_name
        )
        
        try:
            # Call LLM
            response_text = await self._call_llm(prompt)
            
            # Parse response
            specializations = self._parse_response(response_text, company_name)
            
            return specializations
            
        except Exception as e:
            print(f"❌ LLM classification failed for {company_name}: {e}")
            print(f"   Falling back to General")
            return ["General"]
    
    def _parse_response(self, response_text: str, company_name: str) -> List[str]:
        """Parse and validate LLM response."""
        try:
            # Try to extract JSON from response
            # LLM might wrap in markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1]
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]
            
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            raw_specializations = result.get('specializations', [])
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            # Validate specializations (CASE-INSENSITIVE)
            validated = []
            for spec in raw_specializations:
                spec_normalized = spec.strip()
                
                # Case-insensitive matching against valid specializations
                matched = False
                for valid_spec in self.VALID_SPECIALIZATIONS:
                    if spec_normalized.lower() == valid_spec.lower():
                        validated.append(valid_spec)  # Use the canonical form
                        matched = True
                        break
                
                if not matched:
                    print(f"⚠️ Invalid specialization '{spec}' for {company_name}, ignoring")
            
            # Remove duplicates while preserving order
            validated = list(dict.fromkeys(validated))
            
            # Fallback to General if no valid specializations
            if not validated:
                print(f"⚠️ No valid specializations for {company_name}, defaulting to General")
                validated = ["General"]
            
            print(f"✅ {company_name} classified as: {validated}")
            print(f"   Reasoning: {reasoning}")
            
            return validated
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM JSON for {company_name}: {e}")
            print(f"   Raw response: {response_text[:200]}...")
            print(f"   Defaulting to General")
            return ["General"]
    
    async def _call_llm(self, prompt: str) -> str:
        """Call OpenRouter API with Claude 3.5 Sonnet."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "JD-Copilot Specialization Classifier"
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "max_tokens": 300
                }
            )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        if not content:
            raise Exception("Empty response from LLM")
        
        return content


# Global instance
specialization_classifier = SpecializationClassifier()
