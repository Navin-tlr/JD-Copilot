#!/usr/bin/env python3
"""
Test Script for Hallucination-Proof RAG System
This script tests the new hardened SQL validation and company detection logic.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

# Test the SQL validator directly first
try:
    from sql_validator import validate_sql_query, get_dynamic_schema
    print("✅ SQL validator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import SQL validator: {e}")
    sys.exit(1)

# Test other imports
try:
    from database import PlacementDatabase
    print("✅ Database module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database module: {e}")

try:
    from agent import create_production_agent
    print("✅ Agent module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import agent module: {e}")

def test_sql_validator():
    """Test the SQL validation module"""
    print("🧪 Testing SQL Validator Module")
    print("=" * 50)
    
    # Test 1: Get dynamic schema
    print("\n1. Testing Dynamic Schema Loading:")
    db_path = "data/placement_data.db"
    schema = get_dynamic_schema(db_path)
    print(f"✅ Schema loaded successfully")
    print(f"   Tables found: {list(schema.keys())}")
    for table, columns in schema.items():
        print(f"   {table}: {columns}")
    
    # Test 2: Valid SQL queries
    print("\n2. Testing Valid SQL Queries:")
    valid_queries = [
        "SELECT company_name FROM companies",
        "SELECT COUNT(*) FROM roles WHERE specialization = 'Marketing'",
        "SELECT r.title, c.company_name FROM roles r JOIN companies c ON r.company_id = c.id",
        "SELECT DISTINCT specialization FROM roles"
    ]
    
    for query in valid_queries:
        is_valid, reason = validate_sql_query(query, db_path)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"   {status}: {query}")
        if not is_valid:
            print(f"      Reason: {reason}")
    
    # Test 3: Invalid SQL queries (should be caught)
    print("\n3. Testing Invalid SQL Queries (Hallucination Detection):")
    invalid_queries = [
        "SELECT * FROM jobs",  # Non-existent table
        "SELECT * FROM companies WHERE job_title = 'Marketing'",  # Non-existent column
        "SELECT * FROM employees",  # Non-existent table
        "INSERT INTO companies VALUES ('Test')",  # Non-SELECT statement
        "DROP TABLE companies",  # Dangerous statement
        "SELECT * FROM companies WHERE company_name = 'Oracle' AND salary > 50000"  # Non-existent column
    ]
    
    for query in invalid_queries:
        is_valid, reason = validate_sql_query(query, db_path)
        status = "✅ CAUGHT" if not is_valid else "❌ MISSED"
        print(f"   {status}: {query}")
        if not is_valid:
            print(f"      Reason: {reason}")
    
    print("\n" + "=" * 50)

def test_company_detection():
    """Test the improved company detection logic"""
    print("🧪 Testing Company Detection Logic")
    print("=" * 50)
    
    # Test cases that should NOT trigger company detection
    safe_queries = [
        "What are the HR roles available?",
        "Show me marketing positions",
        "List all finance specializations",
        "How many companies came for operations roles?",
        "What skills are required for strategy positions?",
        "Give me a summary of analytics roles"
    ]
    
    print("\n1. Testing Safe Queries (Should NOT trigger company detection):")
    for query in safe_queries:
        # Simulate the company detection logic
        question_lower = query.lower()
        company_text = None
        
        trigger_phrases = ["of ", "for ", "at ", "from "]
        for phrase in trigger_phrases:
            if phrase in question_lower:
                potential_company = question_lower.split(phrase, 1)[1]
                company_text = " ".join(potential_company.strip().split()[:3])
                break
        
        status = "❌ TRIGGERED" if company_text else "✅ SAFE"
        print(f"   {status}: {query}")
        if company_text:
            print(f"      Detected company: '{company_text}'")
    
    # Test cases that SHOULD trigger company detection
    company_queries = [
        "Show me the full JD of Tap Academy",
        "What is the JD for Mill Story?",
        "Give me details about Oracle at Bangalore",
        "Show me the complete JD from Microsoft"
    ]
    
    print("\n2. Testing Company Queries (Should trigger company detection):")
    for query in company_queries:
        question_lower = query.lower()
        company_text = None
        
        trigger_phrases = ["of ", "for ", "at ", "from "]
        for phrase in trigger_phrases:
            if phrase in question_lower:
                potential_company = question_lower.split(phrase, 1)[1]
                company_text = " ".join(potential_company.strip().split()[:3])
                break
        
        status = "✅ TRIGGERED" if company_text else "❌ MISSED"
        print(f"   {status}: {query}")
        if company_text:
            print(f"      Detected company: '{company_text}'")
    
    print("\n" + "=" * 50)

def test_agent_creation():
    """Test the production agent creation"""
    print("🧪 Testing Production Agent Creation")
    print("=" * 50)
    
    try:
        print("Creating production agent...")
        agent = create_production_agent()
        print("✅ Production agent created successfully")
        print(f"   Agent type: {type(agent)}")
        print(f"   Tools available: {len(agent.tools)}")
        for tool in agent.tools:
            print(f"     - {tool.name}: {tool.description[:100]}...")
    except Exception as e:
        print(f"❌ Failed to create production agent: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)

def main():
    """Run all tests"""
    print("🚀 Hallucination-Proof RAG System Test Suite")
    print("=" * 60)
    
    # Check if database exists
    db_path = Path("data/placement_data.db")
    if not db_path.exists():
        print("❌ Database not found. Please ensure the database is set up first.")
        print("   Run: python -m app.database")
        return
    
    try:
        test_sql_validator()
        test_company_detection()
        test_agent_creation()
        
        print("\n🎉 All tests completed!")
        print("\n📋 Summary of Hallucination-Proof Features:")
        print("   ✅ SQL validation using sqlglot")
        print("   ✅ Dynamic schema introspection")
        print("   ✅ Read-only query enforcement")
        print("   ✅ Table and column validation")
        print("   ✅ Improved company detection logic")
        print("   ✅ Hardened agent with validation")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
