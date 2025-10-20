#!/usr/bin/env python3
"""
Test script to verify Operations query works with DB value "LEAN OPERATION AND SYSTEMS"
"""

import sqlite3
import sys

def test_operations_query():
    """Test that we can query operations companies using the DB value."""
    
    print("=" * 70)
    print("Testing Operations Query with DB Value")
    print("=" * 70)
    
    # Connect to database
    db_path = "data/placement_data.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"✅ Connected to database: {db_path}\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False
    
    # Test 1: Count companies with LEAN OPERATION AND SYSTEMS specialization
    print("Test 1: Count companies with specialization 'LEAN OPERATION AND SYSTEMS'")
    print("-" * 70)
    
    query_count = """
        SELECT COUNT(DISTINCT c.company_name) 
        FROM roles r 
        JOIN companies c ON r.company_id = c.id 
        WHERE LOWER(r.specialization) = 'lean operation and systems'
    """
    
    cursor.execute(query_count)
    count = cursor.fetchone()[0]
    print(f"Query: {query_count.strip()}")
    print(f"Result: {count} companies\n")
    
    # Test 2: List companies with LEAN OPERATION AND SYSTEMS specialization
    print("Test 2: List companies with specialization 'LEAN OPERATION AND SYSTEMS'")
    print("-" * 70)
    
    query_list = """
        SELECT DISTINCT c.company_name 
        FROM roles r 
        JOIN companies c ON r.company_id = c.id 
        WHERE LOWER(r.specialization) = 'lean operation and systems'
        ORDER BY c.company_name
    """
    
    cursor.execute(query_list)
    companies = cursor.fetchall()
    
    print(f"Query: {query_list.strip()}")
    print(f"\nCompanies ({len(companies)} total):")
    for i, (company,) in enumerate(companies, 1):
        print(f"  {i}. {company}")
    
    print()
    
    # Test 3: Show all distinct specialization values in DB
    print("Test 3: All distinct specialization values in database")
    print("-" * 70)
    
    query_specs = """
        SELECT DISTINCT r.specialization, COUNT(*) as role_count
        FROM roles r
        GROUP BY r.specialization
        ORDER BY role_count DESC
    """
    
    cursor.execute(query_specs)
    specs = cursor.fetchall()
    
    print(f"Query: {query_specs.strip()}\n")
    print("Specializations in database:")
    for spec, role_count in specs:
        print(f"  • {spec}: {role_count} roles")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    
    return count > 0

if __name__ == "__main__":
    success = test_operations_query()
    sys.exit(0 if success else 1)
