"""
Test the agent pipeline with a sample query.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.orchestrator import agent_orchestrator


async def test_agent_pipeline():
    """Test the agent pipeline with sample queries."""
    
    print("🧪 Testing Agent Pipeline\n")
    
    # Test Case 1: Simple company query
    print("="*70)
    print("Test 1: Simple Company Query")
    print("="*70)
    
    result = await agent_orchestrator.process_query(
        query="What is the Honasa role about?",
        session_id="test-session-1",
        user_id="test-user"
    )
    
    print(f"\n📤 Response Preview:")
    print(result['response'][:300] + "...")
    print(f"\n📊 Metadata: {result['metadata']}")
    
    # Test Case 2: Interview prep query
    print("\n" + "="*70)
    print("Test 2: Interview Preparation Query")
    print("="*70)
    
    result2 = await agent_orchestrator.process_query(
        query="How to prepare for Honasa interview?",
        session_id="test-session-2",
        user_id="test-user"
    )
    
    print(f"\n📤 Response Preview:")
    print(result2['response'][:300] + "...")
    print(f"\n📊 Metadata: {result2['metadata']}")
    
    # Test Case 3: Count query
    print("\n" + "="*70)
    print("Test 3: Count Query")
    print("="*70)
    
    result3 = await agent_orchestrator.process_query(
        query="How many companies came for marketing?",
        session_id="test-session-3",
        user_id="test-user"
    )
    
    print(f"\n📤 Response Preview:")
    print(result3['response'][:300] + "...")
    print(f"\n📊 Metadata: {result3['metadata']}")
    
    print("\n" + "="*70)
    print("✅ All Tests Complete")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_agent_pipeline())
