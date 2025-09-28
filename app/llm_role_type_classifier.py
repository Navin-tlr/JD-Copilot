"""LLM-based Role Type Classification

Invoked during ingestion AFTER structured extraction provided specialization.
Classifies each role into zero or more higher-level role type tags (e.g., B2B, PERFORMANCE MARKETING, FUND MANAGEMENT).

Strategy:
  * Batch classify all roles of a document in a single LLM call for efficiency.
  * Prompt constrains output to a controlled taxonomy (closed-world) to reduce hallucinations.
  * Returns JSON mapping role titles to list of tags and optional confidences.
  * On any failure, caller can fallback to deterministic rule-based classifier.

Environment:
  Uses OPENROUTER_API_KEY and OPENROUTER_MODEL from settings (same as StructuredExtractor).

Public function:
  classify_role_types_llm(roles: List[dict], doc_text: str) -> Dict[str, List[str]]
"""

from __future__ import annotations

from typing import List, Dict, Any
import json
import os
import requests

from app.config import get_settings

# Controlled taxonomy (upper-case canonical tags)
# Dynamic category discovery: no fixed taxonomy. Categories must be short noun phrases
ROLE_TYPE_TAXONOMY: list[str] = []  # kept for backward compatibility (unused)

SYSTEM_INSTRUCTIONS = """You are an expert MBA placement data normalizer. You classify roles into ONLY allowed tags.
Rules:
1. Output ONLY valid JSON.
2. NEVER invent tags outside the allowed list.
3. Multi-label is allowed if clearly justified.
4. Prefer B2B if role focuses on enterprise / partnerships / business development in Marketing.
5. If ambiguous, return an empty list for that role.
6. Do NOT infer salary.
7. Stay deterministic; do not add commentary.
"""

USER_TEMPLATE = """You will derive up to 5 concise CATEGORY tags per role.

Rules:
1. Categories must be 1-3 word noun phrases (e.g., "B2B Sales", "Performance Marketing", "Fund Management", "Process Excellence").
2. Only output categories that are explicitly supported by the role's title OR responsibilities/requirements/skills text. Use phrases that actually appear or a direct, standard professional generalization (e.g., "Business Development" -> "B2B Sales" if enterprise / client acquisition wording present).
3. If uncertain, output an empty list for that role.
4. NEVER fabricate novel buzzwords not grounded in text.
5. Avoid duplicating near-synonyms—pick the clearest professional label.
6. Output JSON ONLY with schema: {{"roles": [{{"title": "<exact title>", "categories": ["Cat1", "Cat2"]}}]}}.
7. Preserve original title exactly.

ROLES INPUT:
{roles_block}

DOCUMENT TEXT PREVIEW (truncated):
{doc_preview}

Return ONLY JSON. No prose.
"""


def _build_roles_block(roles: List[dict]) -> str:
    lines = []
    for r in roles:
        lines.append(
            json.dumps(
                {
                    "title": r.get("title"),
                    "specialization": r.get("specialization"),
                    "location": r.get("location"),
                    "responsibilities": r.get("responsibilities", []),
                    "requirements": r.get("requirements", []),
                    "skills": r.get("skills", []),
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines)


def classify_role_types_llm(roles: List[dict], doc_text: str, max_doc_chars: int = 3500) -> Dict[str, List[str]]:
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY or not settings.OPENROUTER_MODEL:
        # Cannot use LLM, return empty so caller can fallback
        return {}

    if not roles:
        return {}

    doc_preview = (doc_text or "")[:max_doc_chars]
    roles_block = _build_roles_block(roles)

    user_prompt = USER_TEMPLATE.format(
        roles_block=roles_block,
        doc_preview=doc_preview,
    )

    payload = {
    "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 800,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=180,
        )
        if resp.status_code != 200:
            print(f"⚠️ Role type LLM classification failed status={resp.status_code}")
            return {}
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        if os.getenv("ROLE_TYPES_DEBUG"):
            try:
                import time
                debug_dir = os.path.join("data", "debug_role_types")
                os.makedirs(debug_dir, exist_ok=True)
                ts = int(time.time())
                with open(os.path.join(debug_dir, f"raw_{ts}.json"), "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as _e:
                print(f"[role-types-debug] Failed to write raw content: {_e}")
        # Strip code fences if any
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        # Attempt JSON parse
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Attempt to isolate largest JSON object/array
            start_obj = content.find('{')
            end_obj = content.rfind('}') + 1
            start_arr = content.find('[')
            end_arr = content.rfind(']') + 1
            candidates = []
            if start_obj >= 0 and end_obj > start_obj:
                candidates.append(content[start_obj:end_obj])
            if start_arr >= 0 and end_arr > start_arr:
                candidates.append(content[start_arr:end_arr])
            parsed = None
            for snippet in candidates:
                try:
                    parsed = json.loads(snippet)
                    break
                except Exception:
                    continue
            if parsed is None:
                if os.getenv("ROLE_TYPES_DEBUG"):
                    print("[role-types-debug] Could not parse LLM content:", content[:400])
                return {}

        out: Dict[str, List[str]] = {}
        # Build evidence corpus for grounding verification
        evidence_map: Dict[str, str] = {}
        for r in roles:
            parts = []
            for k in ("title", "specialization", "role_description"):
                v = r.get(k)
                if isinstance(v, str):
                    parts.append(v.lower())
            for k in ("responsibilities", "requirements", "skills"):
                v = r.get(k)
                if isinstance(v, list):
                    parts.extend([x.lower() for x in v if isinstance(x, str)])
            evidence_map[r.get("title", "")] = "\n".join(parts)

        # Normalize different possible JSON shapes:
        # 1) {"roles": [...]} (preferred)
        # 2) [{...}, {...}]
        # 3) {"data": {"roles": [...]}}
        if isinstance(parsed, dict):
            role_entries = (
                parsed.get("roles")
                or (parsed.get("data", {}) if isinstance(parsed.get("data"), dict) else {}).get("roles")
                or []
            )
        elif isinstance(parsed, list):
            role_entries = parsed
        else:
            role_entries = []

        if not isinstance(role_entries, list):
            role_entries = []

        for entry in role_entries:
            if not isinstance(entry, dict):
                continue
            title = entry.get("title")
            if not title or not isinstance(title, str) or title not in evidence_map:
                continue
            cats = entry.get("categories") or entry.get("role_types") or []
            cleaned: List[str] = []
            ev = evidence_map[title]
            for cat in cats:
                if not isinstance(cat, str):
                    continue
                c = cat.strip()
                if not c:
                    continue
                # Basic sanitation: length & charset
                if len(c) > 40:
                    continue
                # Evidence grounding: phrase appears OR all words appear individually
                words = [w for w in c.lower().split() if w.isalpha()]
                if c.lower() in ev or all(w in ev for w in words):
                    # Normalize capitalization (Title Case)
                    norm = " ".join(w.capitalize() for w in c.split())
                    if norm not in cleaned:
                        cleaned.append(norm)
            if cleaned:
                out[title] = cleaned
        if os.getenv("ROLE_TYPES_DEBUG"):
            print(f"[role-types-debug] Parsed categories: {out}")
        return out
    except Exception as e:
        import traceback
        if os.getenv("ROLE_TYPES_DEBUG"):
            print(f"[role-types-debug] Full traceback: {traceback.format_exc()}")
        print(f"⚠️ Role type LLM classification exception: {e}")
        return {}


__all__ = ["classify_role_types_llm", "ROLE_TYPE_TAXONOMY"]
