"""
Robust NL-to-SQL query tool using LlamaIndex's NLSQLTableQueryEngine.

Goals:
- Let the LLM (Gemini) handle SQL generation and execution reliably.
- Avoid brittle, hardcoded mappings. Handle arbitrary questions gracefully.
- Provide timeouts, clear errors, and minimal dependencies on external routing.

Environment variables:
- DATABASE_PATH: path to the SQLite DB (default: data/placement_data.db)
- GEMINI_API_KEY: Google Generative AI API key
- GEMINI_MODEL: Gemini model id (default: models/gemini-2.5-flash)
"""

from __future__ import annotations

import os
import re
import json
import time
import sqlite3
import logging
import asyncio
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from sqlalchemy import create_engine

# LlamaIndex (v0.10+ split packages). Import with fallbacks for compatibility.
try:
    from llama_index.core import SQLDatabase
except Exception:  # pragma: no cover - fallback for older versions
    from llama_index import SQLDatabase  # type: ignore

try:
    from llama_index.core.query_engine import NLSQLTableQueryEngine
except Exception:  # pragma: no cover
    # Older path
    from llama_index import NLSQLTableQueryEngine  # type: ignore

# Do not import Gemini at module load to avoid import errors in environments
# where the optional package isn't installed; import lazily inside _get_llm.
Gemini = None  # type: ignore


# Module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[sql_tool] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ----------------------------- Engine Factory ------------------------------ #

_ENGINE_CACHE: Dict[str, NLSQLTableQueryEngine] = {}


def _sqlite_uri(db_path: str) -> str:
    # Ensure absolute path and proper sqlite URI
    abs_path = os.path.abspath(db_path)
    return f"sqlite:///{abs_path}"


def _get_llm() -> Any:
    """Construct a low-temperature Gemini LLM for deterministic SQL."""
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    # Lazy import to satisfy static analyzers when package isn't present
    global Gemini  # type: ignore
    if Gemini is None:
        try:
            from llama_index.llms.gemini import Gemini as _Gemini  # type: ignore
            Gemini = _Gemini  # type: ignore
        except Exception:
            raise RuntimeError(
                "Gemini LLM not available. Install 'llama-index-llms-gemini' and set GEMINI_API_KEY."
            )
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in environment.")
    # Low temperature to reduce SQL hallucinations
    return Gemini(api_key=api_key, model=model, temperature=0.0, transport="rest")


def _create_sql_query_engine(tables: Optional[list[str]] = None) -> Optional[NLSQLTableQueryEngine]:
    """Create or reuse a cached NLSQLTableQueryEngine bound to our SQLite DB.

    Args:
        tables: Optional explicit list of tables to expose. If None, expose full schema.
    """
    db_path = os.getenv("DATABASE_PATH", "data/placement_data.db")
    cache_key = json.dumps({"path": db_path, "tables": tables}, sort_keys=True)

    if cache_key in _ENGINE_CACHE:
        return _ENGINE_CACHE[cache_key]

    try:
        # Build SQLAlchemy engine and LlamaIndex SQLDatabase
        sa_engine = create_engine(_sqlite_uri(db_path))
        sql_db = SQLDatabase(sa_engine, include_tables=tables)

        llm = _get_llm()

        # Build NL-SQL engine; keep responses concise and fast
        qe = NLSQLTableQueryEngine(
            sql_database=sql_db,
            llm=llm,
        )

        _ENGINE_CACHE[cache_key] = qe
        logger.info("NLSQLTableQueryEngine initialized (tables=%s)", tables or "ALL")
        return qe
    except Exception as exc:
        logger.error("Failed to initialize NLSQL engine: %s", exc)
        return None


# ------------------------------- Public API -------------------------------- #

def run_sql_query(question: str, timeout_sec: float = 12.0) -> str:
    """Run a natural-language question against the database using NL-SQL.

    - No brittle rules or canonical mappings.
    - Enforces a timeout so the UI never appears stuck.
    - Returns a human-readable string (engine-formatted result or error text).
    """
    if not question or not isinstance(question, str):
        return "Invalid question."

    # Expose all tables to keep it flexible; NLSQL will pick what it needs.
    qe = _create_sql_query_engine(tables=None)
    if qe is None:
        return "Query engine unavailable. Check GEMINI_API_KEY and database path."

    # Synchronous engine; run in a thread pool to support timeouts nicely.
    def _do_query() -> str:
        start = time.time()
        resp = qe.query(question)
        elapsed = (time.time() - start) * 1000
        logger.info("NL-SQL answered in %.0f ms", elapsed)
        # LlamaIndex Response object pretty-prints with str()
        try:
            # Prefer the raw response text if available
            text = getattr(resp, "response", None) or str(resp)
        except Exception:
            text = str(resp)
        return text

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_do_query)
        try:
            return fut.result(timeout=timeout_sec)
        except FuturesTimeout:
            logger.warning("NL-SQL timed out after %.1fs", timeout_sec)
            return "The query took too long to answer. Please try rephrasing or narrowing the question."
        except Exception as exc:
            logger.error("NL-SQL error: %s", exc)
            return f"Unable to answer due to an internal error: {exc}"


def run_deterministic_sql_query(query: str) -> str:
    """Public wrapper maintained for compatibility. Delegates to run_sql_query.
    Accepts either NL question or raw SQL; NL will be handled by the NL-SQL engine.
    """
    return run_sql_query(query)


def execute_canonical_query(question: str) -> Optional[Dict[str, Any]]:
    """Kept for backward compatibility with callers expecting a structured dict.

    Since we removed brittle canonical rules, this returns None to indicate
    that no static canonical mapping was used; the caller should route to the
    NL-SQL path instead.
    """
    return None


# ----------------------------- Optional Helpers ---------------------------- #

def _try_extract_count(text: str) -> Optional[int]:  # pragma: no cover - utility
    """Best-effort: extract a single integer from a text answer if it looks like a count."""
    try:
        nums = [int(n) for n in re.findall(r"\b\d+\b", text)]
        if len(nums) == 1:
            return nums[0]
    except Exception:
        pass
    return None
 
