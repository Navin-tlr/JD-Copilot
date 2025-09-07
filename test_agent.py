#!/usr/bin/env python3
"""
Test script to debug the agent and tool execution.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agent import create_production_agent, structured_database_query
from app.config import get_settings

def test_agent():
    """Test the agent creation and execution."""
    print("🔍 Testing agent creation...")
    
    try:
        # Test agent creation
        agent = create_production_agent()
        if agent:
            print("✅ Agent created successfully!")
            
            # Test a simple query
            print("\n🔍 Testing agent with query: 'How many companies are there?'")
            response = agent.invoke({
                "input": "How many companies are there?"
            })
            
            print(f"🔍 Agent response: {response}")
            print(f"🔍 Response type: {type(response)}")
            if hasattr(response, 'keys'):
                print(f"🔍 Response keys: {list(response.keys())}")
                
        else:
            print("❌ Agent creation failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_tool_directly():
    """Test the structured_database_query tool directly."""
    print("\n🔍 Testing tool directly...")
    
    try:
        # Test the tool with a simple SQL query
        sql = "SELECT COUNT(*) FROM companies"
        result = structured_database_query.invoke({"generated_sql": sql})
        print(f"✅ Tool result: {result}")
        
    except Exception as e:
        print(f"❌ Tool error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting agent tests...")
    test_agent()
    test_tool_directly()
    print("\n🏁 Tests completed!")
