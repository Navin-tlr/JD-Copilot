#!/usr/bin/env python3
"""
Simple test script to verify agent creation works
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

def test_agent_creation():
    """Test if the production agent can be created"""
    try:
        print("Testing agent creation...")
        
        # Test SQL validator import
        from sql_validator import validate_sql_query, get_dynamic_schema
        print("✅ SQL validator imported successfully")
        
        # Test database import
        from database import PlacementDatabase
        print("✅ Database module imported successfully")
        
        # Test agent creation
        from agent import create_production_agent
        print("✅ Agent module imported successfully")
        
        # Try to create the agent
        print("Creating production agent...")
        agent = create_production_agent()
        print("✅ Production agent created successfully!")
        
        # Check agent properties
        print(f"   Agent type: {type(agent)}")
        print(f"   Tools available: {len(agent.tools)}")
        for tool in agent.tools:
            print(f"     - {tool.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_creation()
    if success:
        print("\n🎉 Agent creation test passed!")
    else:
        print("\n❌ Agent creation test failed!")
        sys.exit(1)
