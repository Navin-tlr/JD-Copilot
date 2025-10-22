"""
Test script for the new orchestrator system.

Run with: python test_orchestrator.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.orchestrator import get_orchestrator


async def test_orchestrator():
    """Test the complete orchestrator flow."""
    print("\n" + "="*80)
    print("🧪 ORCHESTRATOR TEST SUITE")
    print("="*80 + "\n")
    
    orchestrator = get_orchestrator()
    
    # Test cases
    test_queries = [
        {
            "query": "How many companies came for marketing?",
            "session_id": "test_session_1",
            "description": "Simple SQL query - count marketing companies"
        },
        {
            "query": "Tell me about Honasa Consumer's management trainee program",
            "session_id": "test_session_2",
            "description": "Vector search - company-specific JD analysis"
        },
        {
            "query": "What skills are required for finance roles?",
            "session_id": "test_session_3",
            "description": "Hybrid query - skills from both SQL and vector"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"{'='*80}\n")
        
        try:
            response = await orchestrator.process_query(
                user_query=test["query"],
                session_id=test["session_id"],
                user_context=None
            )
            
            print(f"\n✅ TEST {i} PASSED")
            print(f"   Intent: {response.intent}")
            print(f"   Route: {response.route}")
            print(f"   Confidence: {response.confidence}")
            print(f"   Memory Used: {response.used_memory}")
            print(f"   Entities: {response.entities}")
            print(f"\n   Answer Preview:")
            print(f"   {response.answer[:200]}...")
            print(f"\n   Sources: {len(response.sources)} items")
            
        except Exception as e:
            print(f"\n❌ TEST {i} FAILED")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("🏁 TEST SUITE COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
