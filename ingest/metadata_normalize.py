from __future__ import annotations

import re
from typing import Any, Dict


def canonicalize_company(name: str | None) -> str | None:
    if not name:
        return None
    name = name.strip()
    name = re.sub(r"\s+Inc\.?$|\s+Ltd\.?$|\s+LLC$", "", name, flags=re.I)
    return name.title()


def canonicalize_role(role: str | None) -> str | None:
    if not role:
        return None
    role = role.strip()
    role = re.sub(r"intern(ship)?", "Intern", role, flags=re.I)
    role = re.sub(r"software engineer", "Software Engineer", role, flags=re.I)
    return role.title()


def parse_year(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"(20\d{2})", text)
    if m:
        return int(m.group(1))
    return None


