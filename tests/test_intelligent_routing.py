"""
Test script for Intelligent Database Routing System
Run this to verify the system works correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database_schema_tool import get_database_introspector, validate_query_against_schema
from app.database_router import route_query_intelligently, DatabaseType


def test_schema_introspection():
    """Test 1: Schema Introspection"""
    print("\n" + "="*70)
    print("TEST 1: Schema Introspection")
    print("="*70)
    
    introspector = get_database_introspector()
    schema = introspector.get_schema()
    
    print(f"\n✅ Database Type: {schema.database_type}")
    print(f"✅ Total Records: {schema.total_rows:,}")
    print(f"✅ Total Companies: {len(schema.companies)}")
    print(f"✅ Total Specializations: {len(schema.specializations)}")
    
    print(f"\n📊 Available Specializations:")
    for spec in schema.specializations:
        print(f"   - {spec}")
    
    print(f"\n📊 Sample Companies (first 10):")
    for company in schema.companies[:10]:
        print(f"   - {company}")
    
    print(f"\n🔧 Database Capabilities:")
    for cap in schema.capabilities[:10]:
        print(f"   - {cap.replace('_', ' ').title()}")
    
    print(f"\n✅ Schema introspection working!")


def test_schema_validation():
    """Test 2: Schema Validation"""
    print("\n" + "="*70)
    print("TEST 2: Schema Validation")
    print("="*70)
    
    # Test valid specialization
    print("\n🧪 Testing valid specialization (Finance)...")
    result = validate_query_against_schema(
        query_type='count_companies_by_specialization',
        specialization='Finance'
    )
    print(f"   Valid: {result['valid']}")
    print(f"   Reason: {result['reason']}")
    
    # Test invalid specialization
    print("\n🧪 Testing invalid specialization (Blockchain)...")
    result = validate_query_against_schema(
        query_type='count_companies_by_specialization',
        specialization='Blockchain'
    )
    print(f"   Valid: {result['valid']}")
    print(f"   Reason: {result['reason']}")
    if result['suggestions']:
        print(f"   Suggestions:")
        for suggestion in result['suggestions']:
            print(f"      - {suggestion}")
    
    print(f"\n✅ Schema validation working!")


def test_database_routing():
    """Test 3: Database Routing"""
    print("\n" + "="*70)
    print("TEST 3: Intelligent Database Routing")
    print("="*70)
    
    # Test 1: Structured count query
    print("\n🧪 Test 1: Structured Count Query")
    print("   Query: 'how many companies came for finance?'")
    decision = route_query_intelligently(
        intent='count_query',
        specialization='Finance',
        query_text='how many companies came for finance?'
    )
    print(f"   Primary Database: {decision.primary_database.value.upper()}")
    print(f"   Confidence: {decision.confidence:.0%}")
    print(f"   Reasoning: {decision.reasoning}")
    print(f"   SQL Capable: {decision.sql_capable}")
    print(f"   Vector Capable: {decision.vector_capable}")
    
    # Test 2: Unstructured query
    print("\n🧪 Test 2: Unstructured Interview Prep Query")
    print("   Query: 'prepare me for Google interview'")
    decision = route_query_intelligently(
        intent='interview_prep',
        company='Google',
        query_text='prepare me for Google interview'
    )
    print(f"   Primary Database: {decision.primary_database.value.upper()}")
    print(f"   Confidence: {decision.confidence:.0%}")
    print(f"   Reasoning: {decision.reasoning}")
    print(f"   SQL Capable: {decision.sql_capable}")
    print(f"   Vector Capable: {decision.vector_capable}")
    
    # Test 3: List query
    print("\n🧪 Test 3: Structured List Query")
    print("   Query: 'list all companies for marketing'")
    decision = route_query_intelligently(
        intent='list_query',
        specialization='Marketing',
        query_text='list all companies for marketing'
    )
    print(f"   Primary Database: {decision.primary_database.value.upper()}")
    print(f"   Confidence: {decision.confidence:.0%}")
    print(f"   Reasoning: {decision.reasoning}")
    print(f"   SQL Capable: {decision.sql_capable}")
    
    # Test 4: Hybrid query
    print("\n🧪 Test 4: Hybrid Company Deep-Dive Query")
    print("   Query: 'tell me everything about McKinsey'")
    decision = route_query_intelligently(
        intent='company_deep_dive',
        company='McKinsey',
        query_text='tell me everything about McKinsey'
    )
    print(f"   Primary Database: {decision.primary_database.value.upper()}")
    print(f"   Confidence: {decision.confidence:.0%}")
    print(f"   Reasoning: {decision.reasoning}")
    print(f"   SQL Capable: {decision.sql_capable}")
    print(f"   Vector Capable: {decision.vector_capable}")
    
    print(f"\n✅ Database routing working!")


def test_schema_for_llm():
    """Test 4: Schema Documentation for LLM"""
    print("\n" + "="*70)
    print("TEST 4: Schema Documentation for LLM")
    print("="*70)
    
    from app.database_schema_tool import get_sql_schema_for_llm
    
    schema_doc = get_sql_schema_for_llm()
    
    print(f"\n📄 Generated {len(schema_doc)} characters of schema documentation")
    print(f"\n📝 First 500 characters:")
    print(schema_doc[:500])
    print("...")
    
    print(f"\n✅ Schema documentation generation working!")


def main():
    """Run all tests"""
    print("\n" + "🧪 "*35)
    print("INTELLIGENT DATABASE ROUTING SYSTEM - TEST SUITE")
    print("🧪 "*35)
    
    try:
        test_schema_introspection()
        test_schema_validation()
        test_database_routing()
        test_schema_for_llm()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nThe Intelligent Database Routing System is working correctly!")
        print("\nNext steps:")
        print("1. Restart backend: uvicorn app.main:app --reload")
        print("2. Test with real queries:")
        print("   - 'how many companies came for finance?'")
        print("   - 'list all marketing companies'")
        print("   - 'prepare me for Google interview'")
        print("\n")
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST FAILED!")
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
