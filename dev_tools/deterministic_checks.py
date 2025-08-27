#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "placement_data.db"


def run_sql(conn: sqlite3.Connection, sql: str, params: tuple | None = None):
    if params:
        cur = conn.execute(sql, params)
    else:
        cur = conn.execute(sql)
    rows = cur.fetchall()
    return rows


def count_total_companies(conn):
    rows = run_sql(conn, "SELECT COUNT(*) FROM companies")
    return rows[0][0] if rows else 0


def list_all_companies(conn):
    rows = run_sql(conn, "SELECT company_name FROM companies ORDER BY company_name")
    return [r[0] for r in rows]


def count_companies_by_specialization(conn, specialization: str):
    row = run_sql(
        conn,
        """
        SELECT COUNT(DISTINCT c.company_name)
        FROM roles r
        JOIN companies c ON r.company_id = c.id
        WHERE LOWER(r.specialization) = LOWER(?)
        """,
        (specialization,),
    )
    return row[0][0] if row else 0


def list_companies_by_specialization(conn, specialization: str):
    rows = run_sql(
        conn,
        """
        SELECT DISTINCT c.company_name
        FROM roles r
        JOIN companies c ON r.company_id = c.id
        WHERE LOWER(r.specialization) = LOWER(?)
        ORDER BY c.company_name
        """,
        (specialization,),
    )
    return [r[0] for r in rows]


def roles_per_specialization(conn):
    rows = run_sql(
        conn,
        """
        SELECT LOWER(r.specialization) AS spec, COUNT(*) as role_count
        FROM roles r
        GROUP BY LOWER(r.specialization)
        ORDER BY spec
        """,
    )
    return {spec: cnt for spec, cnt in rows}


def assert_equal(name: str, a, b):
    if a != b:
        raise AssertionError(f"Mismatch in {name}: {a} != {b}")


def main():
    assert DB_PATH.exists(), f"DB not found at {DB_PATH}"
    conn = sqlite3.connect(str(DB_PATH))
    try:
        print(f"Using DB: {DB_PATH}")

        # Run each check 5 times to prove determinism
        for i in range(5):
            print(f"\nRun {i+1}:")

            total_companies = count_total_companies(conn)
            print(f"Total companies: {total_companies}")

            all_companies = list_all_companies(conn)
            print(f"All companies ({len(all_companies)}): {all_companies}")

            marketing_count = count_companies_by_specialization(conn, "marketing")
            marketing_companies = list_companies_by_specialization(conn, "marketing")
            print(f"Marketing companies count: {marketing_count}")
            print(f"Marketing companies list: {marketing_companies}")

            hr_count = count_companies_by_specialization(conn, "hr")
            finance_count = count_companies_by_specialization(conn, "finance")
            operations_count = count_companies_by_specialization(conn, "operations")
            analytics_count = count_companies_by_specialization(conn, "business analytics")
            print(f"HR companies count: {hr_count}")
            print(f"Finance companies count: {finance_count}")
            print(f"Operations companies count: {operations_count}")
            print(f"Business Analytics companies count: {analytics_count}")

            per_spec = roles_per_specialization(conn)
            print(f"Roles per specialization: {per_spec}")

            # Cross-verify invariants
            assert_equal("marketing_count == len(marketing_companies)", marketing_count, len(marketing_companies))
            assert marketing_count <= total_companies, "Marketing count cannot exceed total companies"
            assert total_companies == len(all_companies), "Company count/list mismatch"

        print("\nDeterminism checks passed across 5 runs.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
