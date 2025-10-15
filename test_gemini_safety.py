#!/usr/bin/env python3
"""Test Gemini safety handling for FMCG query."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.llm_client import GeminiClient


async def test_fmcg_query():
    """Test the query that was causing safety blocks."""
    
    print("🧪 Testing Gemini safety handling...")
    print("=" * 60)
    
    client = GeminiClient()
    
    # Simulate the problematic analyst prompt
    test_prompt = """You are a STRATEGIC INTELLIGENCE ANALYST delivering a keyword-based count to an MBA student.

**Query:** "How many companies came for FMCG?"

**Intelligence Gathered:**
- Semantic search across JD corpus found **29 companies** mentioning "FMCG"
- Method: Vector search + company deduplication (approximate, not schema-validated)
- Companies identified: Accorian, Acuity Knowledge Partners, Alstom, Anz 04...

**Your Task:**
Deliver this count with STRATEGIC INTELLIGENCE ANALYST precision:

1. **Lead with the count** (direct, no fluff)
2. **Acknowledge methodology** (vector search = approximate, not SQL-validated)
3. **List companies** if ≤20, otherwise summarize patterns
4. **Add strategic context** if relevant
"""
    
    messages = [
        {"role": "user", "content": test_prompt}
    ]
    
    try:
        print("📤 Sending test query to Gemini...")
        response = client.chat(messages, temperature=0.4)
        
        print("✅ Response received successfully!")
        print("=" * 60)
        print(response)
        print("=" * 60)
        
        if "content filter" in response.lower():
            print("\n⚠️  Response was blocked but handled gracefully")
            return False
        else:
            print("\n✅ Full response generated successfully")
            return True
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fmcg_query())
    sys.exit(0 if success else 1)
