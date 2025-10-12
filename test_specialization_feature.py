#!/usr/bin/env python3
"""
Test script for the Specialization Trigger Feature
Verifies that the SQL queries work correctly for all specializations
"""

import sqlite3
import os

DB_PATH = 'data/placement_data.db'

def test_specialization_query(specialization: str):
    """Test count and list queries for a given specialization"""
    with sqlite3.connect(DB_PATH) as conn:
        # Count query
        count_query = f"""
            SELECT COUNT(DISTINCT c.company_name) 
            FROM roles r 
            JOIN companies c ON r.company_id = c.id 
            WHERE LOWER(r.specialization) = '{specialization.lower()}';
        """
        cur = conn.execute(count_query)
        count = cur.fetchone()[0]
        
        # List query
        list_query = f"""
            SELECT DISTINCT c.company_name 
            FROM roles r 
            JOIN companies c ON r.company_id = c.id 
            WHERE LOWER(r.specialization) = '{specialization.lower()}' 
            ORDER BY c.company_name;
        """
        cur = conn.execute(list_query)
        companies = [row[0] for row in cur.fetchall()]
        
        return count, companies

def main():
    print("=" * 80)
    print("SPECIALIZATION TRIGGER FEATURE - TEST RESULTS")
    print("=" * 80)
    print()
    
    specializations = [
        'Marketing',
        'Finance',
        'HR',
        'Operations',
        'Analytics',
        'IT',
        'Strategy',
    ]
    
    for spec in specializations:
        count, companies = test_specialization_query(spec)
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} {spec}:")
        print(f"   Count: {count} companies")
        if companies:
            print(f"   Companies: {', '.join(companies)}")
        else:
            print(f"   Companies: None")
        print()
    
    # Show actual specializations in DB
    print("=" * 80)
    print("ACTUAL SPECIALIZATIONS IN DATABASE")
    print("=" * 80)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            SELECT DISTINCT specialization, COUNT(*) as role_count, COUNT(DISTINCT company_id) as company_count
            FROM roles 
            GROUP BY specialization 
            ORDER BY role_count DESC
        """)
        for row in cur.fetchall():
            print(f"  • {row[0]}: {row[1]} roles across {row[2]} companies")
    print()
    
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("Some specializations like 'LEAN OPERATION AND SYSTEMS' don't match")
    print("the dropdown options exactly. Consider:")
    print("  1. Normalizing specializations during ingestion")
    print("  2. Using fuzzy matching in SQL queries")
    print("  3. Updating the dropdown to show actual database values")
    print()

if __name__ == '__main__':
    main()
