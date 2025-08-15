from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


def sha1_20(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:20]


def stable_chunk_id(source_file: str, section_id: str, chunk_idx: int, start_char: int, end_char: int) -> str:
    key = f"{source_file}|{section_id}|{chunk_idx}|{start_char}|{end_char}"
    return sha1_20(key)


def count_tokens(text: str) -> int:
    """Approximate token count; try tiktoken if available, else whitespace heuristic."""
    try:
        import tiktoken  # type: ignore

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # Rough heuristic: ~1.3 words per token for English
        words = len(text.split())
        return max(1, int(words / 1.3))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def filter_metadata(meta: Dict[str, Any], company: str | None, year: int | None) -> bool:
    if company and str(meta.get("company", "")).lower() != company.lower():
        return False
    if year and int(meta.get("year") or 0) != int(year):
        return False
    return True


def role_contains(meta: Dict[str, Any], pattern: str | None) -> bool:
    if not pattern:
        return True
    role = str(meta.get("role", ""))
    return pattern.lower() in role.lower()


def extract_skills(text: str) -> List[str]:
    """Very simple regex-based skills extractor for fallback mode."""
    # Keyword list can be extended
    skills = set()
    patterns = [
        r"python", r"java", r"c\+\+", r"nlp", r"ml|machine learning",
        r"deep learning", r"pandas", r"numpy", r"sql", r"rest|api", r"docker",
        r"kubernetes", r"aws|gcp|azure", r"spark", r"tensorflow|pytorch",
    ]
    for pat in patterns:
        if re.search(pat, text, flags=re.I):
            skills.add(re.sub(r"\\|.*", "", pat))
    # Also collect capitalized noun-like tokens
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-\+\.]{2,}", text)
    common = {"the", "and", "with", "this", "that", "you", "will", "work"}
    for tok in tokens:
        lt = tok.lower()
        if lt in common:
            continue
        if lt.isalpha() and lt in skills:
            continue
        # very light heuristic
        if tok[0].isupper() and len(tok) > 2:
            skills.add(lt)
    return sorted(skills)[:50]


def parse_salary_rows(text: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for m in re.finditer(r"([A-Za-z ]{3,15})\s*[:\-]\s*(₹?\$?\d[\d,\.]*\s*(?:-\s*₹?\$?\d[\d,\.]*)?)", text):
        rows.append({"label": m.group(1).strip(), "value": m.group(2).strip()})
    for m in re.finditer(r"(?:CTC|salary)\s*[:\-]\s*(₹?\$?\d[\d,\.]*\s*(?:LPA|PA|per annum)?)", text, flags=re.I):
        rows.append({"label": "CTC", "value": m.group(1).strip()})
    # unique by (label,value)
    uniq = {(r["label"], r["value"]): r for r in rows}
    return list(uniq.values())[:20]


def slugify_company(name: str | None) -> str | None:
    if not name:
        return None
    # normalize spaces and punctuation
    import re

    s = name.strip().lower()
    # remove company suffixes
    s = re.sub(r"\b(pvt\.?|private|ltd\.?|limited|inc\.?|llc|co\.?|corp\.?|solutions|technologies)\b", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def safe_read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def append_failure_log(path: Path, item: Dict[str, Any]) -> None:
    data = safe_read_json(path) or []
    data.append(item)
    path.write_text(json.dumps(data, indent=2))


