#!/usr/bin/env python3
"""
Test script to verify the structured_database_query tool works directly
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

def test_tool_directly():
    """Test the structured_database_query tool directly"""
    try:
        print("Testing structured_database_query tool directly...")
        
        # Import the tool
        from agent import structured_database_query
        print("✅ Tool imported successfully")
        
        # Test a simple query
        test_sql = "SELECT COUNT(DISTINCT company_name) FROM companies"
        print(f"\n🧪 Testing SQL: {test_sql}")
        
        # Execute the tool
        result = structured_database_query(test_sql)
        print(f"✅ Tool result: {result}")
        
        # Test the finance query
        finance_sql = "SELECT COUNT(DISTINCT c.company_name) FROM companies c JOIN roles r ON c.id = r.company_id WHERE UPPER(r.specialization) LIKE '%FINANCE%'"
        print(f"\n🧪 Testing Finance SQL: {finance_sql}")
        
        finance_result = structured_database_query(finance_sql)
        print(f"✅ Finance result: {finance_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test tool: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tool_directly()
    if success:
        print("\n🎉 Tool test completed!")
    else:
        print("\n❌ Tool test failed!")
        sys.exit(1)
