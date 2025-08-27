#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import sys

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent import query_job_database

DB_PATH = ROOT / "data" / "placement_data.db"


def run_sql(conn: sqlite3.Connection, sql: str, params: tuple | None = None):
    cur = conn.execute(sql, params or ())
    rows = cur.fetchall()
    return rows


def db_marketing_company_count(conn):
    row = run_sql(
        conn,
        """
        SELECT COUNT(DISTINCT c.company_name)
        FROM roles r
        JOIN companies c ON r.company_id = c.id
        WHERE LOWER(r.specialization) = 'marketing'
        """,
    )
    return row[0][0] if row else 0


def db_all_companies(conn):
    rows = run_sql(conn, "SELECT company_name FROM companies ORDER BY company_name")
    return [r[0] for r in rows]


def tool(query: str) -> str:
    # The tool is a LangChain Tool; use invoke to execute underlying function deterministically
    return query_job_database.invoke({"query": query})


def main():
    assert DB_PATH.exists(), f"DB not found at {DB_PATH}"
    conn = sqlite3.connect(str(DB_PATH))
    try:
        print(f"Using DB: {DB_PATH}")

        # Expanded student-style queries
        queries = [
            # counts
            "how many companies came for marketing role",
            "how many companies came for hr",
            "how many companies came for finance",
            "how many companies came for operations",
            # lists
            "List all companies",
            "list companies for marketing",
            "list companies for hr",
            "list companies for finance",
            "list companies for operations",
            # variants
            "How many companies came for MARKETING role?",
            "count companies for mkt",
        ]

        # Repeat 3 times to prove determinism
        for i in range(3):
            print(f"\nRun {i+1}:")
            for q in queries:
                out = tool(q)
                print(f"Q: {q}\nA: {out}\n")

        # Validate correctness for key queries
        expected_marketing = db_marketing_company_count(conn)
        all_companies = db_all_companies(conn)

        # Parse marketing answer from tool
        ans = tool("how many companies came for marketing role").lower()
        import re
        m = re.search(r"(\d+)", ans)
        count_from_tool = int(m.group(1)) if m else None
        assert count_from_tool == expected_marketing, (
            f"Mismatch: tool={count_from_tool}, db={expected_marketing}"
        )

        list_ans = tool("list all companies")
        for name in all_companies:
            assert name in list_ans, f"Missing company in tool answer: {name}"
        print("\nDeterministic agent tool checks passed.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
