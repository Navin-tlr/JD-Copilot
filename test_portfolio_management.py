#!/usr/bin/env python3
"""Test portfolio management query that was causing blocks."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.llm_client import GeminiClient


def test_portfolio_management():
    """Test the query that was causing safety blocks."""
    
    print("🧪 Testing portfolio management query...")
    print("=" * 60)
    
    client = GeminiClient()
    
    # Simulate the problematic analyst prompt
    test_prompt = """You are a STRATEGIC INTELLIGENCE ANALYST delivering a keyword-based count to an MBA student.

**Query:** "How many companies came for portfolio management?"

**Intelligence Gathered:**
- Semantic search across JD corpus found **29 companies** mentioning "portfolio management"
- Method: Vector search + company deduplication (approximate, not schema-validated)
- Companies identified: Accorian, Acuity Knowledge Partners, Alstom, Anz 04, Associate Project Manager, Aurm, Cimpress India, Consilio, Customer Success Associate, Ediglobe...

**Your Task:**
Deliver this count with STRATEGIC INTELLIGENCE ANALYST precision:

1. **Lead with the count** (direct, no fluff)
2. **Acknowledge methodology** (vector search = approximate, not SQL-validated)
3. **List companies** if ≤20, otherwise summarize patterns
4. **Add strategic context** if relevant (e.g., "Most are in fintech/edtech" or "Scattered across industries")
5. **Use your voice**: Aristotle's clarity + Robert Greene's strategic realism + Linus's directness

**FORMATTING (MANDATORY):**
- Use `## Heading 2` for main section
- Use `### Heading 3` for subsections
- **Bold** company names and key numbers
- Use bullet points (`-`) for lists
- Add `---` separator before data provenance footer
- Keep paragraphs ≤3 lines

**CRITICAL:** This is a ~29-company answer. Don't write a 20-paragraph essay. Be concise, strategic, actionable.
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
    success = test_portfolio_management()
    sys.exit(0 if success else 1)
