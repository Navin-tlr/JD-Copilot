"""
Structured Extraction Module - LLM-powered fact extraction from PDFs
Extracts company, role, salary, and skill information into structured JSON format
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests
from pathlib import Path
from datetime import datetime

@dataclass
class Role:
    title: str
    specialization: str  # Required field for MBA specialization
    location: Optional[str] = None
    salary_min_lpa: Optional[float] = None
    salary_max_lpa: Optional[float] = None
    skills: List[str] = None
    requirements: List[str] = None
    responsibilities: List[str] = None

@dataclass
class CompanyExtraction:
    company_name: str
    year: Optional[int] = None
    roles: List[Role] = None
    company_type: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None

class StructuredExtractor:
    """LLM-powered structured extraction from PDF text"""
    
    def __init__(self):
        # Import here to avoid circular imports
        from app.config import get_settings
        self.settings = get_settings()
        
        self.extraction_prompt = """You are an expert MBA Placement Analyst. Extract structured information from this job description PDF.

EXTRACT ONLY the following information in valid JSON format:
{
    "company_name": "Company name (required - look for the actual company name, not the program name)",
    "year": 2024,
    "roles": [
        {
            "title": "Job title (exact as mentioned)",
            "specialization": "MBA specialization (HR, MARKETING, FINANCE, LEAN OPERATION AND SYSTEMS, BUSINESS ANALYTICS)",
            "location": "Job location if mentioned",
            "salary_min_lpa": null,
            "salary_max_lpa": null,
            "skills": ["skill1", "skill2"],
            "requirements": ["requirement1", "requirement2"],
            "responsibilities": ["responsibility1", "responsibility2"]
        }
    ],
    "company_type": "Company type if mentioned",
    "industry": "Industry if mentioned",
    "location": "Company location if mentioned"
}

CRITICAL RULES:
- Extract ONLY facts explicitly stated in the text
- Use null for missing information
- Keep skills, requirements, and responsibilities as arrays
- Ensure valid JSON format
- If multiple roles exist, list all of them
- SPECIALIZATION MUST be one of: HR, MARKETING, FINANCE, LEAN OPERATION AND SYSTEMS, BUSINESS ANALYTICS
- COMPANY NAME: Look for the actual company name (e.g., "Target", "Accorian"), not program names
- For Target TII, the company name is "Target TII" or "Target"
- For Masters' Union, the company name is "Masters' Union"
- For Tap Academy, the company name is "Tap Academy"
- For Accorian, the company name is "Accorian"
- SPECIALIZATION ANALYSIS:
  - Media Operations roles = MARKETING specialization
  - HR/People Operations roles = HR specialization
  - Business Development roles = MARKETING specialization
  - Operations roles = LEAN OPERATION AND SYSTEMS
  - Finance roles = FINANCE specialization
  - Analytics roles = BUSINESS ANALYTICS specialization
  - Admission Counselor roles = OPERATIONS specialization (student recruitment/operations)
  - Look at the actual role title and responsibilities to determine specialization

PDF TEXT:
{text}

EXTRACTED JSON:"""

    def extract_structured_data(self, text: str) -> Optional[CompanyExtraction]:
        """Extract structured data using OpenRouter LLM"""
        try:
            if not self.settings.OPENROUTER_API_KEY:
                print("❌ No OpenRouter API key available for structured extraction")
                return None

            # Optimize text length for cost efficiency
            text_preview = text[:3000]  # Reduced from 4000 to save tokens
            
            # Enhanced prompt for better JSON extraction
            enhanced_prompt = f"""
{self.extraction_prompt.replace('{text}', text_preview)}

IMPORTANT: 
- Return ONLY valid JSON, no additional text
- If salary is not mentioned, use null
- If expected_hires is not mentioned, use null
- Ensure all JSON syntax is correct
- Use proper escaping for quotes and special characters
"""
            
            payload = {
                "model": self.settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
                "messages": [
                    {"role": "system", "content": "You are a precise HR data extractor. You MUST return ONLY valid JSON with no additional text, explanations, or formatting."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 800,  # Reduced for cost efficiency
            }

            headers = {
                "Authorization": f"Bearer {self.settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }

            print("🚀 Making API call to OpenRouter...")
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            print(f"📡 Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                print(f"🔍 LLM Response: {content[:200]}...")
                
                # Clean the response and extract JSON
                json_str = self._extract_json_from_response(content)
                if json_str:
                    print(f"✅ JSON Extracted: {json_str[:200]}...")
                    data = json.loads(json_str)
                    return self._parse_extraction_data(data)
                else:
                    print(f"❌ Failed to extract JSON from response")
                    print(f"   Response length: {len(content)}")
                    print(f"   Response preview: {content}")
                    return None
            else:
                print(f"❌ OpenRouter API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Structured extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON from LLM response with enhanced parsing"""
        try:
            # Clean the response
            cleaned_response = response.strip()
            
            # Remove markdown code blocks if present
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Look for JSON blocks
            start = cleaned_response.find('{')
            end = cleaned_response.rfind('}') + 1
            
            if start != -1 and end != -1:
                json_str = cleaned_response[start:end]
                
                # Try to fix common JSON issues
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                json_str = re.sub(r'\s+', ' ', json_str)  # Normalize whitespace
                
                # Validate JSON
                json.loads(json_str)
                return json_str
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ JSON parsing failed: {e}")
            # Try to extract partial JSON
            try:
                # Look for the most complete JSON structure
                matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response)
                if matches:
                    for match in matches:
                        try:
                            json.loads(match)
                            return match
                        except:
                            continue
            except:
                pass
            
        return None

    def _parse_extraction_data(self, data: Dict[str, Any]) -> CompanyExtraction:
        """Parse extracted data into CompanyExtraction object"""
        try:
            roles = []
            if data.get("roles"):
                for role_data in data["roles"]:
                    role = Role(
                        title=role_data.get("title", ""),
                        specialization=role_data.get("specialization", "MARKETING"),  # Default to MARKETING if missing
                        location=role_data.get("location"),
                        salary_min_lpa=role_data.get("salary_min_lpa"),
                        salary_max_lpa=role_data.get("salary_max_lpa"),
                        skills=role_data.get("skills", []),
                        requirements=role_data.get("requirements", []),
                        responsibilities=role_data.get("responsibilities", [])
                    )
                    roles.append(role)

            return CompanyExtraction(
                company_name=data.get("company_name", ""),
                year=data.get("year"),
                roles=roles,
                company_type=data.get("company_type"),
                industry=data.get("industry"),
                location=data.get("location")
            )
            
        except Exception as e:
            print(f"❌ Failed to parse extraction data: {e}")
            return CompanyExtraction(company_name="", roles=[])

    def save_structured_data(self, extraction: CompanyExtraction, source_file: str) -> str:
        """Save structured data to JSON file"""
        try:
            output_dir = Path("data/structured_json")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{source_file.replace('.pdf', '').replace('.txt', '')}_structured.json"
            output_path = output_dir / filename

            # Convert to dict and save
            data = asdict(extraction)
            data["source_file"] = source_file
            data["extraction_timestamp"] = str(datetime.now())

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return str(output_path)

        except Exception as e:
            print(f"❌ Failed to save structured data: {e}")
            return ""
