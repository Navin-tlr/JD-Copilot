from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

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


# ---------------------
# Company name utilities
# ---------------------

COMPANY_NAME_REGEX = re.compile(r"\b([A-Z][A-Za-z0-9'&.-]{1,}(?:\s+[A-Z][A-Za-z0-9'&.-]{1,})*)\b")

IGNORE_TOKENS = {
    "mba",
    "sql",
    "hr",
    "finance",
    "associate",
    "manager",
    "team",
    "program",
    "development",
    "analytics",
    "research",
}

IGNORE_SUFFIXES = {"team", "department", "program", "division", "group"}


def _normalize_company_token(token: str) -> str:
    token = token.strip("\"'`()[]{}<>.,;:!?\n\r\t ")
    if not token:
        return ""
    token = re.sub(r"\s+", " ", token)
    return token.lower()


def _expand_variants(normalized: str) -> Set[str]:
    if not normalized:
        return set()
    words = [w for w in normalized.split(" ") if w]
    variants: Set[str] = {normalized}
    for w in words:
        variants.add(w)
    for i in range(len(words) - 1):
        pair = f"{words[i]} {words[i+1]}"
        variants.add(pair)
    return {v for v in variants if v}


@lru_cache(maxsize=1)
def _canonical_company_tokens(db_path: str = "data/placement_data.db") -> Tuple[str, ...]:
    tokens: Set[str] = set()
    try:
        if not Path(db_path).exists():
            return tuple()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT company_name FROM companies WHERE company_name IS NOT NULL")
            rows = cursor.fetchall()
        for (name,) in rows:
            normalized = _normalize_company_token(str(name))
            tokens.update(_expand_variants(normalized))
    except Exception:
        return tuple(tokens)
    return tuple(tokens)


def _collect_known_tokens_from_text(text: str, known: Set[str]) -> None:
    if not text:
        return
    for match in COMPANY_NAME_REGEX.finditer(text):
        raw = match.group(1)
        normalized = _normalize_company_token(raw)
        if not normalized:
            continue
        known.update(_expand_variants(normalized))


def _collect_known_tokens_from_names(names: Iterable[str], known: Set[str]) -> None:
    for name in names:
        if not name:
            continue
        normalized = _normalize_company_token(str(name))
        if not normalized:
            continue
        known.update(_expand_variants(normalized))


def _token_is_known(normalized: str, known: Set[str]) -> bool:
    if normalized in known:
        return True
    if not normalized:
        return True
    words = [w for w in normalized.split(" ") if w]
    if not words:
        return True
    # All individual words known
    if all(w in known for w in words):
        return True
    # Any adjacent pair known
    for i in range(len(words) - 1):
        pair = f"{words[i]} {words[i+1]}"
        if pair in known:
            return True
    return False


def detect_suspicious_companies(
    answer: str,
    structured_text: str = "",
    unstructured_text: str = "",
    extra_company_names: Optional[Iterable[str]] = None,
    extra_texts: Optional[Iterable[str]] = None,
    db_path: str = "data/placement_data.db",
) -> List[str]:
    """Return list of suspicious company names that are not in known datasets.

    The answer text itself is not modified; callers can prepend warnings while retaining full content.
    """
    known: Set[str] = set(_canonical_company_tokens(db_path))
    _collect_known_tokens_from_text(structured_text or "", known)
    _collect_known_tokens_from_text(unstructured_text or "", known)
    if extra_texts:
        for text in extra_texts:
            _collect_known_tokens_from_text(text or "", known)
    if extra_company_names:
        _collect_known_tokens_from_names(extra_company_names, known)

    suspicious: List[str] = []
    seen: Set[str] = set()
    for match in COMPANY_NAME_REGEX.finditer(answer or ""):
        raw = match.group(1)
        normalized = _normalize_company_token(raw)
        if not normalized:
            continue
        # Minimum effective length (ignoring spaces)
        if len(normalized.replace(" ", "")) <= 2:
            continue
        last_word = normalized.split(" ")[-1]
        if normalized in IGNORE_TOKENS or last_word in IGNORE_SUFFIXES:
            continue
        if _token_is_known(normalized, known):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        suspicious.append(raw.strip())
    return suspicious


def prepend_company_warning(answer: str, suspicious: Iterable[str]) -> str:
    suspects = [s for s in suspicious if s]
    if not suspects:
        return answer
    unique_ordered: List[str] = []
    seen: Set[str] = set()
    for name in suspects:
        key = _normalize_company_token(name)
        if key and key not in seen:
            unique_ordered.append(name.strip())
            seen.add(key)
    if not unique_ordered:
        return answer
    warning = f"DATA_MISSING: company name(s) not in dataset: {', '.join(unique_ordered)}"
    return f"{warning}\n\n{answer}" if answer else warning


