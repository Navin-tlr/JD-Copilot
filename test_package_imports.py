#!/usr/bin/env python3
"""
Test script to verify package imports work correctly
"""

import sys
from pathlib import Path

def test_package_imports():
    """Test if the app package can be imported correctly"""
    try:
        print("Testing package imports...")
        
        # Add the current directory to Python path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Try to import the app package
        import app
        print("✅ App package imported successfully")
        
        # Try to import specific modules
        from app import sql_validator
        print("✅ SQL validator imported successfully")
        
        from app import agent
        print("✅ Agent module imported successfully")
        
        from app import rag
        print("✅ RAG module imported successfully")
        
        from app import config
        print("✅ Config module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import package: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_package_imports()
    if success:
        print("\n🎉 Package import test passed!")
    else:
        print("\n❌ Package import test failed!")
        sys.exit(1)
