"""
Structured Extraction Module - LLM-powered fact extraction from PDFs
Extracts company, role, salary, and skill information into structured JSON format
Augmented with role hierarchy extraction (Level 1/2 roles) using sequential LLM calls
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
    level1_roles: Optional[List[str]] = None
    level2_roles: Optional[List[str]] = None
    hierarchy_confidence: Optional[float] = None
    is_hybrid: Optional[bool] = False

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
        # Debug: Print the loaded model at init
        print(f"[DEBUG] StructuredExtractor loaded OPENROUTER_MODEL: {self.settings.OPENROUTER_MODEL}")
        
        # Initialize OpenRouter wrapper for hierarchy extraction
        self.wrapper = None
        if self.settings.OPENROUTER_API_KEY:
            try:
                from app.openrouter_wrapper import OpenRouterWrapper
                self.wrapper = OpenRouterWrapper()
                print(f"[DEBUG] OpenRouterWrapper initialized for hierarchy extraction")
            except Exception as e:
                print(f"[WARNING] Failed to initialize OpenRouterWrapper: {e}")
                self.wrapper = None
        
        # Hardcoded Level 1 role maps per specialization (based on MBA hierarchies)
        self.LEVEL1_MAPS = {
            "marketing": [
                "B2B Sales",
                "FMCG Sales",
                "Digital Marketing",
                "Brand Management",
                "Market Research",
                "Product Management",
                "Advertising",
                "Public Relations"
            ],
            "finance": [
                "Investment Banking",
                "Corporate Finance",
                "Financial Planning and Analysis",
                "Risk Management",
                "Treasury Management",
                "Internal Audit",
                "Taxation"
            ],
            "hr": [
                "Talent Acquisition",
                "Learning and Development",
                "Employee Relations",
                "Compensation and Benefits",
                "HR Business Partner",
                "Organizational Development",
                "Diversity and Inclusion"
            ],
            "lean operation and systems": [
                "Supply Chain Management",
                "Operations Management",
                "Lean Manufacturing",
                "Quality Management",
                "Project Management",
                "Logistics and Distribution",
                "Process Engineering"
            ],
            "business analytics": [
                "Data Analysis",
                "Business Intelligence",
                "Predictive Analytics",
                "Data Visualization",
                "Machine Learning for Business",
                "Operations Research",
                "Analytics Consulting"
            ]
        }
        
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
        """Extract structured data using OpenRouter LLM, augmented with hierarchy"""
        try:
            if not self.settings.OPENROUTER_API_KEY:
                print("❌ No OpenRouter API key available for structured extraction")
                return None
            if not self.settings.OPENROUTER_MODEL:
                raise RuntimeError("OPENROUTER_MODEL must be set in the environment. No fallback allowed.")

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

            model_used = self.settings.OPENROUTER_MODEL
            print(f"🔎 [DEBUG] Model used for OpenRouter API call: {model_used}")
            payload = {
                "model": model_used,
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
                    
                    # NEW: Augment core extraction with hierarchy for each role
                    if "roles" in data:
                        for role_data in data["roles"]:
                            self._derive_hierarchy(role_data, text)
                    
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

    def _derive_hierarchy(self, role_data: Dict[str, Any], text: str) -> None:
        """Derive Level 1/2 roles sequentially using LLM calls. Modifies role_data in place."""
        if not self.wrapper:
            print("[WARNING] No LLM wrapper available for hierarchy extraction")
            role_data["level1_roles"] = []
            role_data["level2_roles"] = []
            role_data["hierarchy_confidence"] = 0.0
            role_data["is_hybrid"] = False
            return

        spec = role_data.get("specialization", "").lower().strip()
        text_lower = text.lower()

        # Hybrid detection (example: financial analytics)
        is_hybrid = False
        specs_for_hierarchy = [spec]
        if "analytics" in spec and "financial" in text_lower:
            is_hybrid = True
            specs_for_hierarchy = ["finance", "business analytics"]

        # Get candidate Level 1 roles
        level1_candidates = []
        for s in specs_for_hierarchy:
            if s in self.LEVEL1_MAPS:
                level1_candidates.extend(self.LEVEL1_MAPS[s])
        level1_candidates = list(set(level1_candidates))  # Unique

        if not level1_candidates:
            role_data["level1_roles"] = ["General"]
            role_data["level2_roles"] = []
            role_data["hierarchy_confidence"] = 0.5
            role_data["is_hybrid"] = is_hybrid
            return

        # Step 2: LLM call to select matching Level 1 roles
        level1_list_md = "\n".join([f"- {role}" for role in level1_candidates])
        spec_desc = " and ".join(specs_for_hierarchy) if is_hybrid else spec.upper()
        level1_prompt = f"""You are an MBA role hierarchy expert.

Specialization: {spec_desc}
This is a {'hybrid ' if is_hybrid else ''}role.

Available Level 1 roles (use exact names):
{level1_list_md}

JD Context (select 1-3 most matching based on title, responsibilities, skills):
{text[:2000]}

Output ONLY valid JSON:
{{"selected_level1": ["Exact Role Name1", "Exact Role Name2"], "confidence": 0.85}}
If no close matches, use [] and confidence < 0.5."""

        messages = [
            {"role": "system", "content": "You are a precise JSON extractor. Return ONLY valid JSON, no additional text."},
            {"role": "user", "content": level1_prompt}
        ]

        response = self.wrapper.chat(
            messages,
            model=self.settings.OPENROUTER_MODEL,
            temperature=0.0,
            max_tokens=200
        )

        level1_json = self._extract_json_from_response(response)
        selected_level1 = []
        level1_conf = 0.5
        if level1_json:
            try:
                level1_data = json.loads(level1_json)
                selected_level1 = level1_data.get("selected_level1", [])
                level1_conf = float(level1_data.get("confidence", 0.5))
            except (json.JSONDecodeError, ValueError):
                pass

        if not selected_level1 and level1_candidates:
            selected_level1 = [level1_candidates[0]]  # Fallback to first
            level1_conf = 0.3

        if not selected_level1:
            selected_level1 = ["General"]
            level1_conf = 0.2

        role_data["level1_roles"] = selected_level1

        # Step 3: LLM call to derive Level 2 sub-roles
        level2_candidates = []
        level2_conf = 0.0
        if selected_level1:
            selected_str = ", ".join(selected_level1)
            level2_prompt = f"""You are an MBA role expert.

For each Level 1 role: {selected_str}

Dynamically extract 1-3 specific Level 2 sub-roles from the JD text (based on responsibilities, requirements, skills). Use descriptive names implied by context.

JD Text:
{text}

Output ONLY valid JSON:
{{"level2_dict": {{"Level1A": ["Sub-role1", "Sub-role2"], "Level1B": ["Sub-role3"]}}, "confidence": 0.75}}
If no sub-roles found for a Level 1, use empty list []. Overall confidence for all extractions."""

            messages2 = [
                {"role": "system", "content": "You are a precise JSON extractor. Return ONLY valid JSON."},
                {"role": "user", "content": level2_prompt}
            ]

            resp2 = self.wrapper.chat(
                messages2,
                model=self.settings.OPENROUTER_MODEL,
                temperature=0.0,
                max_tokens=300
            )

            level2_json = self._extract_json_from_response(resp2)
            if level2_json:
                try:
                    level2_data = json.loads(level2_json)
                    level2_dict = level2_data.get("level2_dict", {})
                    level2_candidates = [sub for subs in level2_dict.values() for sub in subs]
                    level2_conf = float(level2_data.get("confidence", 0.5))
                except (json.JSONDecodeError, ValueError):
                    pass

        role_data["level2_roles"] = list(set(level2_candidates))  # Unique, all combined
        role_data["hierarchy_confidence"] = round((level1_conf + level2_conf) / 2, 2)
        role_data["is_hybrid"] = is_hybrid

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
        """Parse extracted data into CompanyExtraction object, including hierarchy fields"""
        try:
            roles = []
            if data.get("roles"):
                for role_data in data["roles"]:
                    spec = role_data.get("specialization", "MARKETING")
                    # Normalize specialization: lowercase, replace '&' with 'and', remove symbols
                    spec_normalized = spec.lower().replace('&', 'and').replace('#', '').strip()
                    role = Role(
                        title=role_data.get("title", ""),
                        specialization=spec_normalized,  # Normalized lowercase
                        location=role_data.get("location"),
                        salary_min_lpa=role_data.get("salary_min_lpa"),
                        salary_max_lpa=role_data.get("salary_max_lpa"),
                        skills=role_data.get("skills", []),
                        requirements=role_data.get("requirements", []),
                        responsibilities=role_data.get("responsibilities", []),
                        level1_roles=role_data.get("level1_roles", []),
                        level2_roles=role_data.get("level2_roles", []),
                        hierarchy_confidence=role_data.get("hierarchy_confidence"),
                        is_hybrid=role_data.get("is_hybrid", False)
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
