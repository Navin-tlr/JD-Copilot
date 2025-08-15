from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from app.config import get_settings
from app.utils import extract_skills, parse_salary_rows
from .metadata_normalize import canonicalize_company, canonicalize_role, parse_year


def try_llm_extract(text: str) -> Dict[str, Any] | None:
	"""Try to extract metadata using LLM (Gemini) if available.

	This version disables safety blocks for trusted, professional documents and
	adds robust response checks before JSON parsing.
	"""
	settings = get_settings()
	
	if not settings.GEMINI_API_KEY:
		return None
		
	try:
		import google.generativeai as genai
		from google.generativeai.types import HarmCategory, HarmBlockThreshold

		genai.configure(api_key=settings.GEMINI_API_KEY)
		
		prompt = f"""You are an expert at extracting company information from job descriptions. 

Analyze this job description and extract metadata. Return ONLY a valid JSON object with these exact fields:

{{
    "company": "exact company name (required - look for company names in About Us, headers, or context)",
    "role": "job title/position (required)", 
    "year": year as integer or null,
    "skills": ["skill1", "skill2", ...],
    "location": "city, state/country or null",
    "employment_type": "Full-time/Part-time/Contract/Internship or null",
    "responsibilities": ["responsibility1", "responsibility2", ...],
    "selection_process": ["Interview", "Test", "GD", ...]
}}

IMPORTANT: 
- For company: Look carefully for company names in "About Us" sections, headers, or anywhere in the text
- Extract the exact company name as written (e.g., "TAP Academy", "Microsoft", "Google")
- If you see text like "TAP Academy is an Ed-Tech company", the company is "TAP Academy"
- Do not include company suffixes like "is a company" or descriptions

Job Description:
{text[:2500]}

JSON:"""

		model = genai.GenerativeModel(settings.GEMINI_MODEL)
		
		response = model.generate_content(
			prompt,
			generation_config=genai.types.GenerationConfig(
				temperature=0.1,
				max_output_tokens=800,
			),
			# Disable safety blocks for trusted enterprise documents
			safety_settings={
				HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
				HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
				HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
				HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
			},
		)
		
		# Robust check before parsing
		if not hasattr(response, 'text') or not (response.text or '').strip():
			print("⚠️ LLM returned an empty or invalid response for a document. Skipping LLM extraction for this file.")
			# Optionally inspect response object for diagnostics
			return None

		response_text = response.text.strip()
		
		# Try to extract JSON from response (handle cases where LLM adds extra text)
		json_start = response_text.find('{')
		json_end = response_text.rfind('}')
		
		if json_start != -1 and json_end != -1:
			json_text = response_text[json_start:json_end + 1]
			result = json.loads(json_text)
		else:
			# Fallback: try parsing the whole response
			result = json.loads(response_text)
		
		# Add missing fields and normalize
		result["salary_table_rows"] = []
		result["eligibility_rules"] = {}
		result["raw_span_map"] = {}
		result["approximate"] = False
		
		if result.get("company"):
			result["company"] = canonicalize_company(result["company"])
		if result.get("role"):
			result["role"] = canonicalize_role(result["role"])
			
		return result
		
	except Exception as e:
		print(f"LLM extraction failed: {e}")
		return None


def try_langextract(text: str) -> Dict[str, Any] | None:
    """Try to run LangExtract schema extraction if available; otherwise return None."""
    try:
        from langextract import ExtractionTask  # type: ignore

        schema = {
            "company": str,
            "role": str,
            "year": int,
            "location": str,
            "employment_type": str,
            "skills": [str],
            "responsibilities": [str],
            "selection_process": [str],
            "salary_table_rows": [{"label": str, "value": str}],
            "eligibility_rules": dict,
            "raw_span_map": dict,
        }
        task = ExtractionTask(schema=schema)
        result = task.extract(text)  # type: ignore[attr-defined]
        if result:
            result["approximate"] = False
        return result
    except Exception:
        return None


def heuristic_extract(filename: str, text: str) -> Dict[str, Any]:
    """Enhanced heuristics-based extraction."""
    top = text[:2000]  # Look at more text
    
    # Enhanced company extraction
    company = None
    role = None
    
    # Look for "About Us:" followed by company name  
    about_match = re.search(r"(?:About Us|About|Company):\s*\n?\s*([A-Za-z0-9\s.&,-]+?)(?:\s+(?:is|are|provides|offers|helps))", text[:1500], re.IGNORECASE | re.MULTILINE)
    if about_match:
        company = about_match.group(1).strip()
    else:
        # Try other patterns
        company_patterns = [
            r"(?im)^(?:company|org|organization)\s*[:\-]\s*(.+)$",
            r"Company(?:\s+Name)?:\s*([A-Za-z0-9\s.&,-]+)",
            r"Employer:\s*([A-Za-z0-9\s.&,-]+)"
        ]
        for pattern in company_patterns:
            m = re.search(pattern, top)
            if m:
                company = m.group(1).strip()
                break
    
    # Enhanced role extraction
    role_patterns = [
        r"(?im)^(?:role|position|title|job title)\s*[:\-]\s*(.+)$",
        r"# Job Title:\s*([^\n]+)",
        r"Job Title:\s*([^\n]+)",
        r"Position:\s*([^\n]+)",
        r"Role:\s*([^\n]+)"
    ]
    for pattern in role_patterns:
        m = re.search(pattern, top)
        if m:
            role = m.group(1).strip()
            break
    
    # Fallback to filename parsing
    if not company:
        # Better filename parsing - avoid "Copy" prefix
        stem = Path(filename).stem
        if stem.startswith("Copy of "):
            stem = stem[8:]  # Remove "Copy of " prefix
        parts = stem.split("_")
        company = parts[0] if parts else "Unknown Company"
    
    if not role:
        stem = Path(filename).stem
        if stem.startswith("Copy of "):
            stem = stem[8:]
        parts = stem.split("_")
        role = parts[1] if len(parts) > 1 else "Software Engineer"

    year = parse_year(text) or parse_year(filename) or None
    skills = extract_skills(text)
    selection_process = []
    if re.search(r"\b(gd|group discussion)\b", text, re.I):
        selection_process.append("GD")
    if re.search(r"\binterview\b", text, re.I):
        selection_process.append("Interview")
    if re.search(r"\btest|assessment\b", text, re.I):
        selection_process.append("Test")
    salary_rows = parse_salary_rows(text)
    data = {
        "company": canonicalize_company(company),
        "role": canonicalize_role(role),
        "year": year,
        "location": None,
        "employment_type": None,
        "skills": skills,
        "responsibilities": [],
        "selection_process": selection_process,
        "salary_table_rows": salary_rows,
        "eligibility_rules": {},
        "raw_span_map": {},
        "approximate": True,
    }
    return data


def run_extraction(basename: str, text: str) -> Dict[str, Any]:
    settings = get_settings()
    out_json = Path(settings.LANGEXT_JSON_DIR) / f"{basename}.json"
    out_html = Path(settings.LANGEXT_HTML_DIR) / f"{basename}.html"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_html.parent.mkdir(parents=True, exist_ok=True)

    # Try LLM extraction first, then LangExtract, then heuristics
    result = try_llm_extract(text)
    if not result:
        result = try_langextract(text)
    if not result:
        result = heuristic_extract(basename, text)

    # Save JSON
    out_json.write_text(json.dumps(result, indent=2))
    # Very light HTML visualizer
    html = ["<html><body><h2>LangExtract Results</h2><pre>", json.dumps(result, indent=2), "</pre></body></html>"]
    out_html.write_text("".join(html))
    return result


