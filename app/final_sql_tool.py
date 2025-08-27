import os
from typing import Optional


_query_engine = None


def _build_llamaindex_engine():
    """
    Create and cache a LlamaIndex NLSQLTableQueryEngine if dependencies and keys are available.
    Returns None if unavailable so callers can gracefully fall back.
    """
    global _query_engine
    if _query_engine is not None:
        return _query_engine

    try:
        from sqlalchemy import create_engine
        from llama_index.core import SQLDatabase
        from llama_index.core.indices.struct_store import NLSQLTableQueryEngine
        from llama_index.llms.openai import OpenAI
    except Exception:
        return None

    # Prefer OpenRouter; set OpenAI-compatible env vars so the client routes to OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        return None
    os.environ.setdefault("OPENAI_API_KEY", openrouter_key)
    os.environ.setdefault("OPENAI_API_BASE", "https://openrouter.ai/api/v1")

    db_path = os.getenv("DATABASE_PATH", "data/placement_data.db")
    try:
        engine = create_engine(f"sqlite:///{db_path}")
        # Do not restrict to a specific table name to avoid schema mismatch across environments
        sql_db = SQLDatabase(engine)
        # LlamaIndex OpenAI wrapper respects OPENAI_API_BASE for routing to OpenRouter
        llm = OpenAI(api_key=openrouter_key, model="moonshotai/kimi-k2")
        _query_engine = NLSQLTableQueryEngine(sql_database=sql_db, tables=None, llm=llm)
        return _query_engine
    except Exception:
        return None


def run_llama_index_sql_query(query: str) -> str:
    """
    Self-contained structured query tool.
    Attempts to answer with LlamaIndex NLSQLTableQueryEngine.
    Falls back to the deterministic SQL tool if LlamaIndex is not available.
    """
    print(f"📦 final_sql_tool.run_llama_index_sql_query: '{query}'")

    # Try LlamaIndex first
    qe = _build_llamaindex_engine()
    if qe is not None:
        try:
            resp = qe.query(query)
            try:
                # LlamaIndex Response objects often expose .response
                return getattr(resp, "response", str(resp))
            except Exception:
                return str(resp)
        except Exception as e:
            print(f"🔥 LlamaIndex SQL engine error: {e}")

    # Fallback to our deterministic SQL tool
    try:
        from .sql_tool import run_sql_query as _fallback
    except Exception:
        _fallback = None
    if _fallback:
        try:
            return _fallback(query)
        except Exception as e:
            return f"Structured query failed: {e}"
    return "Structured query engine not available."


