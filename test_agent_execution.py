#!/usr/bin/env python3
"""
Test script to verify agent execution flow
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

def test_agent_execution():
    """Test if the agent can execute queries properly"""
    try:
        print("Testing agent execution...")
        
        # Import the agent
        from agent import create_production_agent
        print("✅ Agent imported successfully")
        
        # Create the agent
        agent = create_production_agent()
        print("✅ Agent created successfully")
        
        # Test a simple query
        test_query = "How many companies are there?"
        print(f"\n🧪 Testing query: {test_query}")
        
        # Execute the query
        response = agent.invoke({
            "input": test_query
        })
        
        print(f"✅ Agent response received")
        print(f"   Response type: {type(response)}")
        print(f"   Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        
        if isinstance(response, dict):
            output = response.get("output", "No output")
            print(f"   Output: {output}")
            
            # Check if it's a SQL query or actual result
            if "SELECT" in str(output).upper():
                print("   📝 Agent generated SQL query (needs tool execution)")
            else:
                print("   ✅ Agent provided direct answer")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test agent execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_execution()
    if success:
        print("\n🎉 Agent execution test completed!")
    else:
        print("\n❌ Agent execution test failed!")
        sys.exit(1)
