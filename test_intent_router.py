"""
Test script for Intent Router
"""

from app.agents.intent_router import get_intent_router


def test_router():
    """Test the Intent Router with sample queries."""
    
    router = get_intent_router()
    
    test_queries = [
        "How many companies came for consulting?",
        "Give me details of UNIQLO",
        "Help me prepare for PwC interview",
        "What were GD topics last year?",
        "Compare Finance and Marketing placements",
        "How about Marketing?",  # Ambiguous - should trigger memory
        "Show marketing roles in FMCG sector",
    ]
    
    print("=" * 80)
    print("INTENT ROUTER TEST")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Testing: {query}")
        print(f"{'='*80}")
        
        try:
            decision = router.classify_and_route(query)
            
            print("\n✅ Decision:")
            print(f"   Intent: {decision.intent}")
            print(f"   Route: {decision.route.value}")
            print(f"   Confidence: {decision.confidence}")
            print(f"   Use Memory: {decision.use_memory}")
            print(f"   Entities:")
            print(f"      - Specialization: {decision.entities.specialization}")
            print(f"      - Role: {decision.entities.role}")
            print(f"      - Company: {decision.entities.company}")
            print(f"      - Year: {decision.entities.year}")
            print(f"   Reasoning: {decision.reasoning}")
            
            if decision.clarification_question:
                print(f"   ❓ Clarification: {decision.clarification_question}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_router()
