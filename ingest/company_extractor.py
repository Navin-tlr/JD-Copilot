"""
Robust company name extraction using LangExtract's current API.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from langextract import extract as lx_extract, data as lx_data


def extract_company_with_langextract(text: str) -> Optional[str]:
    """Extract company name using LangExtract with current API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    # Use the working model IDs (remove models/ prefix if present)
    model_id = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").replace("models/", "")
    
    # Create few-shot examples using the correct LangExtract data structures
    examples = [
        lx_data.ExampleData(
            text="ACCORIAN\n\n# About Accorian\nAccorian is an established cybersecurity advisory...",
            extractions=[lx_data.Extraction("company", "Accorian")]
        ),
        lx_data.ExampleData(
            text="Company: Masters' Union\n\n# About Masters' Union\nMasters' Union is a business school...",
            extractions=[lx_data.Extraction("company", "Masters' Union")]
        ),
        lx_data.ExampleData(
            text="TAP Academy is an Ed-Tech company that helps individuals...",
            extractions=[lx_data.Extraction("company", "TAP Academy")]
        ),
        lx_data.ExampleData(
            text="# TII Apprenticeship Program\n\n# About Target\nAs a Fortune 50 company...",
            extractions=[lx_data.Extraction("company", "Target")]
        ),
    ]

    prompt = (
        "Extract the employer company name from this job description. "
        "Look for company names in headers, 'Company:' labels, 'About <Company>' sections, "
        "or prominent all-caps headings. Return the exact company name as it appears in the text."
    )

    try:
        # Use LangExtract's extract function with current API
        result = lx_extract(
            text_or_documents=text,
            prompt_description=prompt,
            examples=examples,
            api_key=api_key,
            model_id=model_id,
            format_type=lx_data.FormatType.JSON,
            temperature=0.1,
            debug=False,
            max_char_buffer=2000,  # Focus on first 2K chars where company names usually appear
        )
        
        # Extract company from results
        if hasattr(result, 'extractions'):
            for extraction in result.extractions:
                if hasattr(extraction, 'extraction_class') and extraction.extraction_class == "company":
                    if hasattr(extraction, 'extraction_text') and extraction.extraction_text:
                        return extraction.extraction_text.strip()
        
        return None
        
    except Exception as e:
        print(f"LangExtract failed: {e}")
        return None


def extract_company_heuristic(text: str) -> Optional[str]:
    """Fallback heuristic extraction when LangExtract fails."""
    head = text[:3000]
    lines = [ln.strip() for ln in head.splitlines() if ln.strip()]
    
    # Pattern 1: Explicit company labels
    for line in lines[:50]:
        m = re.match(r"(?i)^(?:company|employer|organization)\s*[:\-]\s*(.+)$", line)
        if m:
            company = m.group(1).strip(" \t\n\r-–—|,:;()[]{}\"'")
            if company and len(company) >= 2:
                return company
    
    # Pattern 2: "About <Company>" (not "About Us")
    for line in lines[:80]:
        m = re.search(r"(?i)^#?\s*about\s+(?!us\b)([A-Za-z0-9&.,'\- ]{2,50})\s*:?\s*$", line)
        if m:
            company = m.group(1).strip(" \t\n\r-–—|,:;()[]{}\"'")
            exclude = {"company", "organization", "employer", "academy", "program", "apprenticeship"}
            if company.lower() not in exclude:
                return company
    
    # Pattern 3: All-caps brand heading (first 1-3 words, early in document)
    for line in lines[:30]:
        # Must be mostly uppercase, 1-3 words, not generic terms
        words = line.split()
        if (1 <= len(words) <= 3 and 
            len(line) >= 3 and 
            sum(1 for c in line if c.isupper()) / max(1, len([c for c in line if c.isalpha()])) >= 0.8):
            
            exclude_words = {"ABOUT", "JOB", "DESCRIPTION", "ROLE", "DEPARTMENT", "EXPERIENCE", 
                           "EDUCATION", "JOIN", "APPRENTICE", "PROGRAM", "APPLICATION"}
            if not any(word.upper() in exclude_words for word in words):
                return line.strip()
    
    return None


def normalize_company_name(raw: str) -> str:
    """Normalize and canonicalize company names."""
    if not raw:
        return raw
        
    # Basic cleanup
    s = re.sub(r"\s+", " ", raw).strip(" \t\n\r-–—|,:;()[]{}\"'")
    
    # Known canonical mappings
    canonical_map = {
        "Target": "Target India (TII)",
        "Target Corporation": "Target India (TII)", 
        "TII": "Target India (TII)",
        "TAP Academy": "TAP Academy",
        "Masters' Union": "Masters' Union",
        "Masters' Union": "Masters' Union",  # Handle both quote types
        "Accorian": "Accorian",
    }
    
    return canonical_map.get(s, s)


def extract_company(text: str) -> Optional[str]:
    """
    Main company extraction function.
    Tries LangExtract first, falls back to heuristics, then normalizes.
    """
    # Try LangExtract first
    company = extract_company_with_langextract(text)
    
    # Fall back to heuristics if LangExtract fails
    if not company:
        company = extract_company_heuristic(text)
    
    # Normalize the result
    if company:
        return normalize_company_name(company)
    
    return None
