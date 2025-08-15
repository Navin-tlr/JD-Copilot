from __future__ import annotations

import os
import re
from typing import Optional, List

from langextract import extract as lx_extract, data as lx_data


SYSTEM_PROMPT = (
    "You are extracting the employer company name from a job description.\n"
    "Output strict JSON: {\"company\": \"<exact company name as appears in the text>\"}.\n"
    "Rules:\n"
    "- Use the exact name that appears in the document.\n"
    "- Prefer the employer organization, not the school/program/role.\n"
    "- Strong cues: lines starting with 'Company:', 'Employer:', 'Organization:', headings like 'About <Name>', logo/header text, or the first large ALL CAPS brand header.\n"
    "- If both a local legal entity and a parent brand appear (e.g., 'TII Apprenticeship Program' and 'About Target'), treat the employer as the brand/parent unless the legal entity name explicitly indicates hiring (e.g., 'Target in India (TII)').\n"
    "- If no clear employer found, return null."
)

SIMPLE_PROMPT = "Return only: {\"company\": \"...\"} — no prose, no markdown."


def _few_shot_examples() -> List[lx_data.ExampleData]:
    exs: List[lx_data.ExampleData] = []
    # Example 1: Accorian
    exs.append(
        lx_data.ExampleData(
            text="ACCORIAN\n...\n# About Accorian ...",
            extractions=[lx_data.Extraction("company", "Accorian")],
        )
    )
    # Example 2: Masters’ Union
    exs.append(
        lx_data.ExampleData(
            text="# Admission Counselor ...\nCompany: Masters’ Union",
            extractions=[lx_data.Extraction("company", "Masters’ Union")],
        )
    )
    # Example 3: TAP Academy
    exs.append(
        lx_data.ExampleData(
            text="TAP Academy is an Ed-Tech company that helps individuals ...",
            extractions=[lx_data.Extraction("company", "TAP Academy")],
        )
    )
    # Example 4: TII / Target (brand preference)
    exs.append(
        lx_data.ExampleData(
            text="# TII Apprenticeship Program ...\n# About Target ...",
            extractions=[lx_data.Extraction("company", "Target")],
        )
    )
    return exs


def extract_company_raw(text: str) -> Optional[str]:
    """Run LangExtract to obtain the employer company name from full JD text.

    - Uses Gemini via GEMINI_API_KEY (falls back to LANGEXTRACT_API_KEY if present)
    - Retries up to 3 times, simplifying prompt if needed
    - Returns the raw string as found in text, or None
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LANGEXTRACT_API_KEY")
    if not api_key:
        return None

    # LangExtract expects IDs like 'gemini-2.5-pro' (no 'models/' prefix)
    configured = (os.getenv("GEMINI_MODEL") or "gemini-2.5-pro").replace("models/", "")
    candidates = [configured, "gemini-2.5-flash"]
    examples = _few_shot_examples()

    prompts = [SYSTEM_PROMPT, SIMPLE_PROMPT]
    for attempt in range(1, 4):
        prompt = prompts[0] if attempt == 1 else prompts[1]
        for model_id in candidates:
            try:
                doc = lx_extract(
                    text_or_documents=text,
                    prompt_description=prompt,
                    examples=examples,
                    api_key=api_key,
                    model_id=model_id,
                    format_type=lx_data.FormatType.JSON,
                    temperature=0.0,
                    debug=True,
                    resolver_params={"fence_output": False},
                    extraction_passes=1 if attempt == 1 else 2,
                )
                for ex in getattr(doc, "extractions", []) or []:
                    if getattr(ex, "extraction_class", "") == "company":
                        raw = (getattr(ex, "extraction_text", None) or "").strip()
                        if raw:
                            return raw
            except Exception:
                continue
    return None


def normalize_company(raw: str) -> str:
    """Normalize and canonicalize company names for dropdowns."""
    # Standardize quotes/apostrophes
    s = raw.replace("’", "’").replace("'", "’").strip()
    # Collapse whitespace and strip common punctuations
    s = re.sub(r"\s+", " ", s).strip(" \t\n\r-–—|,:;()[]{}\"’")
    # Light title/brand normalization: keep known casing when applicable
    preferred_case = {
        "tap academy": "TAP Academy",
        "masters’ union": "Masters’ Union",
        "masters' union": "Masters’ Union",
        "accorian": "Accorian",
        "target": "Target",
    }
    key = s.lower()
    if key in preferred_case:
        s = preferred_case[key]

    canonical_map = {
        "Target": "Target India (TII)",
        "Target Corporation": "Target India (TII)",
        "TII": "Target India (TII)",
        "TAP Academy": "TAP Academy",
        "Masters' Union": "Masters’ Union",
        "Masters’ Union": "Masters’ Union",
        "Accorian": "Accorian",
    }
    return canonical_map.get(s, s)


def _heuristic_company(text: str) -> Optional[str]:
    head = text[:3000]
    lines = [ln.strip() for ln in head.splitlines() if ln.strip()]
    # Basic heuristics similar to previous approach
    for ln in lines[:80]:
        m = re.match(r"(?i)^(?:company|employer|organization)\s*[:\-]\s*(.+)$", ln)
        if m:
            val = m.group(1).strip(" \t\n\r-–—|,:;()[]{}\"’")
            if val:
                return val
        m2 = re.search(r"(?i)^about\s+(?!us\b)([A-Za-z0-9&.,'\- ]{2,})\s*:?$", ln)
        if m2:
            val = m2.group(1).strip(" \t\n\r-–—|,:;()[]{}\"’")
            if val:
                return val
    return None


def extract_company(text: str) -> Optional[str]:
    """Public helper: try LangExtract, then heuristic; return normalized or None."""
    raw = extract_company_raw(text)
    if not raw:
        raw = _heuristic_company(text)
    return normalize_company(raw) if raw else None


