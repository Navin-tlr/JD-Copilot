import os
import sqlite3
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import create_engine, text

# --- LAYER 1: CANONICAL (PRE-DEFINED) QUERIES ---
# Note: Order matters; specialization-specific come first for higher specificity.
CANONICAL_QUERIES = {
    # Marketing
    "count_marketing_companies": {
        "keywords": [
            "companies came for marketing",
            "marketing role",
            "marketing companies",
            "companies for mkt",
            "count companies for mkt",
            "for marketing",
        ],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'marketing';"
        ),
    },
    "list_marketing_companies": {
        "keywords": ["list companies for marketing", "marketing companies list", "list companies for mkt"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'marketing' ORDER BY c.company_name;"
        ),
    },
    # HR
    "count_hr_companies": {
        "keywords": ["companies came for hr", "hr role", "count companies for hr", "for hr"],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'hr';"
        ),
    },
    "list_hr_companies": {
        "keywords": ["list companies for hr", "hr companies list"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'hr' ORDER BY c.company_name;"
        ),
    },
    # Finance
    "count_finance_companies": {
        "keywords": ["companies came for finance", "finance role", "count companies for finance", "for finance"],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'finance';"
        ),
    },
    "list_finance_companies": {
    "keywords": ["list companies for finance", "finance companies list", "list down companies for finance", "list down companies came for finance", "list down companies came for finance", "list down companies for finance"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'finance' ORDER BY c.company_name;"
        ),
    },
    # Operations
    "count_operations_companies": {
        "keywords": ["companies came for operations", "operations role", "count companies for operations", "for operations"],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'lean operation and systems';"
        ),
    },
    "list_operations_companies": {
        "keywords": ["list companies for operations", "operations companies list"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'lean operation and systems' ORDER BY c.company_name;"
        ),
    },
    # Analytics
    "count_analytics_companies": {
        "keywords": ["companies came for analytics", "analytics role", "count companies for analytics", "for analytics"],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'analytics';"
        ),
    },
    "list_analytics_companies": {
        "keywords": ["list companies for analytics", "analytics companies list"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'analytics' ORDER BY c.company_name;"
        ),
    },
    # IT
    "count_it_companies": {
        "keywords": ["companies came for it", "it role", "count companies for it", "for it", "information technology"],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'it';"
        ),
    },
    "list_it_companies": {
        "keywords": ["list companies for it", "it companies list"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'it' ORDER BY c.company_name;"
        ),
    },
    # Strategy
    "count_strategy_companies": {
        "keywords": ["companies came for strategy", "strategy role", "count companies for strategy", "for strategy"],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'strategy';"
        ),
    },
    "list_strategy_companies": {
        "keywords": ["list companies for strategy", "strategy companies list"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'strategy' ORDER BY c.company_name;"
        ),
    },
    # Generic sales / business development role queries (covers B2B, BD, inside, field)
    "count_sales_related_companies": {
        "keywords": [
            "sales companies count",
            "count sales companies",
            "how many sales companies",
            "business development companies",
            "count business development companies",
            "how many business development companies",
            "b2b sales companies",
            "b2b sales roles count",
            "inside sales companies",
            "field sales companies",
        ],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE (LOWER(r.title) LIKE '%sales%' OR LOWER(r.title) LIKE '%business development%' );"
        ),
    },
    "list_sales_related_companies": {
        "keywords": [
            "list sales companies",
            "sales companies list",
            "list companies for sales",
            "business development companies list",
            "list companies for business development",
            "b2b sales companies list",
            "inside sales companies list",
            "field sales companies list",
        ],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE (LOWER(r.title) LIKE '%sales%' OR LOWER(r.title) LIKE '%business development%') "
            "ORDER BY c.company_name;"
        ),
    },
    # Generic B2B company_type queries (independent of role titles)
    "count_b2b_companies": {
        "keywords": [
            "count b2b companies",
            "how many b2b companies",
            "b2b companies came",
            "companies came for b2b",
        ],
        "query": (
            "SELECT COUNT(DISTINCT company_name) FROM companies "
            "WHERE LOWER(company_type) = 'b2b';"
        ),
    },
    "list_b2b_companies": {
        "keywords": [
            "list b2b companies",
            "b2b companies list",
            "give me list of b2b companies",
            "list of b2b companies",
            "b2b companies came for placements",
            "b2b companies came for campus",
            "show b2b companies",
        ],
        "query": (
            "SELECT DISTINCT company_name FROM companies "
            "WHERE LOWER(company_type) = 'b2b' ORDER BY company_name;"
        ),
    },
    # PR/Communications
    "count_pr_companies": {
        "keywords": ["companies came for pr", "pr role", "count companies for pr", "for pr", "communications", "public relations"],
        "query": (
            "SELECT COUNT(DISTINCT c.company_name) FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'marketing' AND LOWER(c.industry) = 'public relations';"
        ),
    },
    "list_pr_companies": {
        "keywords": ["list companies for pr", "pr companies list", "communications companies", "public relations companies"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = 'marketing' AND LOWER(c.industry) = 'public relations' ORDER BY c.company_name;"
        ),
    },
    # Admission/Operations
    "count_admission_jobs": {
        "keywords": ["admission", "admission-related", "admission jobs", "counselor"],
        "query": (
            "SELECT COUNT(*) FROM roles r "
            "WHERE LOWER(r.title) LIKE '%admission%' OR LOWER(r.title) LIKE '%counselor%';"
        ),
    },
    "list_admission_jobs": {
        "keywords": ["admission jobs", "admission roles", "counselor jobs"],
        "query": (
            "SELECT r.title, c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.title) LIKE '%admission%' OR LOWER(r.title) LIKE '%counselor%';"
        ),
    },
    # Internships
    "count_internships": {
        "keywords": ["internships", "intern", "internship jobs", "specifically internships"],
        "query": (
            "SELECT COUNT(*) FROM roles r "
            "WHERE LOWER(r.title) LIKE '%intern%' OR LOWER(r.title) LIKE '%internship%';"
        ),
    },
    "list_internships": {
        "keywords": ["internship jobs", "intern roles", "list internships"],
        "query": (
            "SELECT r.title, c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.title) LIKE '%intern%' OR LOWER(r.title) LIKE '%internship%';"
        ),
    },
    # Location-based queries
    "count_bangalore_jobs": {
        "keywords": ["bangalore", "based in bangalore", "jobs in bangalore", "bangalore location"],
        "query": (
            "SELECT COUNT(*) FROM roles r "
            "WHERE LOWER(r.location) LIKE '%bangalore%' OR LOWER(r.location) LIKE '%bengaluru%';"
        ),
    },
    "list_bangalore_jobs": {
        "keywords": ["bangalore companies", "jobs bangalore", "companies bangalore"],
        "query": (
            "SELECT DISTINCT c.company_name FROM roles r "
            "JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.location) LIKE '%bangalore%' OR LOWER(r.location) LIKE '%bengaluru%';"
        ),
    },
    # Generic totals and lists (kept last, lowest specificity)
    "count_distinct_companies": {
        "keywords": ["how many companies", "count companies", "number of companies", "total companies"],
        "query": "SELECT COUNT(DISTINCT company_name) FROM companies;",
    },
    "list_all_companies": {
        "keywords": ["list all companies", "show me the companies", "what companies are there", "all companies"],
        "query": "SELECT DISTINCT company_name FROM companies ORDER BY company_name;",
    },
}


def get_canonical_query(question: str) -> Optional[str]:
    q = question.lower()

    # Handle multi-part questions like "how many companies... among these how many are for marketing"
    if "among these" in q or "among them" in q:
        # Extract the specialization from the second part
        if "marketing" in q:
            return CANONICAL_QUERIES["count_marketing_companies"]["query"]
        elif "finance" in q:
            return CANONICAL_QUERIES["count_finance_companies"]["query"]
        elif "hr" in q or "human resources" in q:
            return CANONICAL_QUERIES["count_hr_companies"]["query"]
        elif "operations" in q:
            return CANONICAL_QUERIES["count_operations_companies"]["query"]

    # If the user explicitly asked to list items, prefer queries that return DISTINCT rows (lists)
    list_indicators = ["list", "list down", "show", "which companies", "which companies are"]
    if any(ind in q for ind in list_indicators):
        for item in CANONICAL_QUERIES.values():
            # Prefer queries that use DISTINCT (list-type results)
            try:
                if "distinct" in item["query"].lower():
                    for kw in item["keywords"]:
                        if kw in q:
                            return item["query"]
            except Exception:
                continue
    # exact keyword containment pass (ordered by specificity via dict order)
    for item in CANONICAL_QUERIES.values():
        for kw in item["keywords"]:
            if kw in q:
                return item["query"]
    # Heuristic fallback for agent-proposed SQL or loosely phrased inputs
    try:
        if ("count" in q or "how many" in q) and "marketing" in q:
            return CANONICAL_QUERIES["count_marketing_companies"]["query"]
        if ("list" in q or "distinct" in q) and "marketing" in q:
            return CANONICAL_QUERIES["list_marketing_companies"]["query"]

        if ("count" in q or "how many" in q) and (" hr" in q or "human resources" in q or q.strip().startswith("hr")):
            return CANONICAL_QUERIES["count_hr_companies"]["query"]
        if ("list" in q or "distinct" in q) and (" hr" in q or "human resources" in q or q.strip().startswith("hr")):
            return CANONICAL_QUERIES["list_hr_companies"]["query"]

        # Finance: prefer LIST when user explicitly asks to 'list' or 'list down'
        if ("list" in q or "list down" in q or "distinct" in q) and "finance" in q:
            return CANONICAL_QUERIES["list_finance_companies"]["query"]
        if ("count" in q or "how many" in q) and "finance" in q:
            return CANONICAL_QUERIES["count_finance_companies"]["query"]

        if ("count" in q or "how many" in q) and "operations" in q:
            return CANONICAL_QUERIES["count_operations_companies"]["query"]
        if ("list" in q or "distinct" in q) and "operations" in q:
            return CANONICAL_QUERIES["list_operations_companies"]["query"]

        # Sales / business development heuristic (title pattern)
        sales_terms = ["sales", "business development", "inside sales", "field sales"]
        if any(t in q for t in sales_terms):
            if ("count" in q or "how many" in q):
                return CANONICAL_QUERIES["count_sales_related_companies"]["query"]
            if ("list" in q or "list down" in q or "distinct" in q or "give me list" in q):
                return CANONICAL_QUERIES["list_sales_related_companies"]["query"]

        # Plain B2B company_type queries when 'sales' not mentioned
        if ("count" in q or "how many" in q) and "b2b" in q and "sales" not in q:
            return CANONICAL_QUERIES["count_b2b_companies"]["query"]
        if ("list" in q or "list down" in q or "distinct" in q or "give me list" in q) and "b2b" in q and "sales" not in q:
            return CANONICAL_QUERIES["list_b2b_companies"]["query"]

        if ("list" in q and "companies" in q) or ("select" in q and " from companies" in q):
            return CANONICAL_QUERIES["list_all_companies"]["query"]
        if ("count" in q and "companies" in q) or ("count(distinct" in q and ("company" in q or "companies" in q)):
            return CANONICAL_QUERIES["count_distinct_companies"]["query"]
    except Exception:
        pass
    return None


# --- LAYER 2: LLAMAINDEX SQL ENGINE (RELIABLE FALLBACK) ---
_engine = None
_query_engine = None


def _create_sql_query_engine():
    global _engine, _query_engine
    if _query_engine is not None:
        return _query_engine

    # Lazy import to avoid hard dependency
    try:
        from llama_index.core import SQLDatabase
        from llama_index.core.indices.struct_store import NLSQLTableQueryEngine
        from .agent import GeminiLLM
    except Exception:
        return None

    db_path = os.getenv("DATABASE_PATH", "data/placement_data.db")
    _engine = create_engine(f"sqlite:///{db_path}")
    sql_db = SQLDatabase(_engine)

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return None

    # Use Gemini LLM wrapper
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    llm = GeminiLLM(api_key=gemini_key, model=model_name, temperature=0.0)
    _query_engine = NLSQLTableQueryEngine(sql_database=sql_db, tables=None, llm=llm)
    return _query_engine


# --- THE MAIN TOOL FUNCTION ---

def run_sql_query(question: str) -> str:
    """
    Deterministic structured DB query tool:
    1) Try canonical, hand-written SQL (100% deterministic)
    2) Fallback to LlamaIndex NLSQLTableQueryEngine (if available)
    """
    canonical_sql = get_canonical_query(question)
    if canonical_sql:
        try:
            db_path = os.getenv('DATABASE_PATH', 'data/placement_data.db')
            with sqlite3.connect(db_path) as conn:
                cur = conn.execute(canonical_sql)
                rows = cur.fetchall()

            # Format the response based on query type
            if "COUNT" in canonical_sql.upper():
                count = rows[0][0] if rows else 0
                # Detect specialization type from question
                question_lower = question.lower()
                if "marketing" in question_lower:
                    return f"There are {count} companies offering marketing roles."
                elif "finance" in question_lower:
                    return f"There are {count} companies offering finance roles."
                elif "hr" in question_lower or "human resources" in question_lower:
                    return f"There are {count} companies offering HR roles."
                elif "operations" in question_lower:
                    return f"There are {count} companies offering operations roles."
                elif "analytics" in question_lower:
                    return f"There are {count} companies offering analytics roles."
                elif "it" in question_lower or "information technology" in question_lower:
                    return f"There are {count} companies offering IT roles."
                elif "strategy" in question_lower:
                    return f"There are {count} companies offering strategy roles."
                else:
                    return f"There are {count} companies in total."
            else:
                # For list queries, format as a readable list
                if rows:
                    companies = [row[0] for row in rows]
                    return f"Companies: {', '.join(companies)}"
                else:
                    return "No companies found matching the criteria."

        except Exception as e:
            return f"Error executing canonical query: {e}"

    qe = _create_sql_query_engine()
    if qe is None:
        return "Structured query engine not available (fallback disabled)."
    try:
        resp = qe.query(question)
        return str(resp)
    except Exception as e:
        return f"Error using SQL engine: {e}"


def run_deterministic_sql_query(query: str) -> str:
    """
    Public wrapper expected by the final agent. Delegates to run_sql_query.
    """
    return run_sql_query(query)


def execute_canonical_query(question: str) -> Optional[Dict[str, Any]]:
    """Execute a canonical SQL query and return structured results.

    Returns None when the question does not map to a canonical query.
    """
    canonical_sql = get_canonical_query(question)
    if not canonical_sql:
        return None

    db_path = os.getenv('DATABASE_PATH', 'data/placement_data.db')

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(canonical_sql)
            rows = cursor.fetchall()
    except Exception as exc:
        return {
            'query': canonical_sql,
            'error': str(exc),
            'result': None
        }

    sql_lower = canonical_sql.lower()
    is_count_query = 'count(' in sql_lower

    if is_count_query:
        count_value: Union[int, float] = 0
        if rows:
            first_row = rows[0]
            if len(first_row.keys()) == 1:
                count_value = first_row[0] or 0
            else:
                # If additional columns exist, look for the first column containing 'count'
                for key in first_row.keys():
                    if 'count' in key.lower():
                        count_value = first_row[key] or 0
                        break
                else:
                    count_value = first_row[0] or 0

        result: Dict[str, Any] = {'count': int(count_value)}

        # Include additional columns (e.g., company lists) when present
        if rows and len(rows[0].keys()) > 1:
            supplementary: List[Dict[str, Any]] = []
            for row in rows:
                row_dict = {key: row[key] for key in row.keys() if 'count' not in key.lower()}
                if row_dict:
                    supplementary.append(row_dict)
            if supplementary:
                result['records'] = supplementary

        return {
            'query': canonical_sql,
            'result': result
        }

    # Non-count queries → return list of rows (dict when multiple columns)
    formatted_rows: List[Any] = []
    for row in rows:
        keys = row.keys()
        if len(keys) == 1:
            formatted_rows.append(row[0])
        else:
            formatted_rows.append({key: row[key] for key in keys})

    return {
        'query': canonical_sql,
        'result': formatted_rows
    }
