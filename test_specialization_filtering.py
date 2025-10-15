"""
Test specialization filtering behavior.

Tests:
1. Explicit specialization in query -> Should use specialization filter
2. No specialization in query -> Should NOT use specialization filter (company only)
3. Inferred specialization from context -> Should NOT use specialization filter
"""

from app.agents.intent_classifier import intent_classifier


def test_explicit_specialization():
    """Query with explicit specialization should mark it as explicit."""
    query = "Show me Google Finance roles"
    
    intent = intent_classifier.classify(query)
    
    print("\n" + "="*70)
    print("TEST 1: Explicit Specialization")
    print("="*70)
    print(f"Query: {query}")
    print(f"Specialization: {intent.specialization}")
    print(f"Specialization Explicit: {intent.specialization_explicit}")
    print(f"Expected: specialization='Finance', explicit=True")
    
    assert intent.specialization == "Finance", f"Expected 'Finance', got '{intent.specialization}'"
    assert intent.specialization_explicit == True, f"Expected explicit=True, got {intent.specialization_explicit}"
    print("✅ PASSED: Specialization marked as EXPLICIT")


def test_no_specialization():
    """Query without specialization should not extract one."""
    query = "Show me Google roles"
    
    intent = intent_classifier.classify(query)
    
    print("\n" + "="*70)
    print("TEST 2: No Specialization")
    print("="*70)
    print(f"Query: {query}")
    print(f"Specialization: {intent.specialization}")
    print(f"Specialization Explicit: {intent.specialization_explicit}")
    print(f"Expected: specialization=None, explicit=False")
    
    assert intent.specialization is None, f"Expected None, got '{intent.specialization}'"
    assert intent.specialization_explicit == False, f"Expected explicit=False, got {intent.specialization_explicit}"
    print("✅ PASSED: No specialization extracted (company-only filter will be used)")


def test_inferred_specialization():
    """Query with inferred specialization from context should mark it as NOT explicit."""
    query = "What about Google?"
    context = {"specialization": "Finance"}  # From previous conversation
    
    intent = intent_classifier.classify(query, context=context)
    
    print("\n" + "="*70)
    print("TEST 3: Inferred Specialization (from context)")
    print("="*70)
    print(f"Query: {query}")
    print(f"Context: {context}")
    print(f"Specialization: {intent.specialization}")
    print(f"Specialization Explicit: {intent.specialization_explicit}")
    print(f"Expected: specialization='Finance', explicit=False")
    
    assert intent.specialization == "Finance", f"Expected 'Finance', got '{intent.specialization}'"
    assert intent.specialization_explicit == False, f"Expected explicit=False, got {intent.specialization_explicit}"
    print("✅ PASSED: Specialization marked as INFERRED (will NOT filter)")


def test_generic_company_query():
    """Generic query like 'Google JD' should only use company filter."""
    query = "Show me the JD of Google"
    
    intent = intent_classifier.classify(query)
    
    print("\n" + "="*70)
    print("TEST 4: Generic Company Query")
    print("="*70)
    print(f"Query: {query}")
    print(f"Company: {intent.company}")
    print(f"Specialization: {intent.specialization}")
    print(f"Specialization Explicit: {intent.specialization_explicit}")
    print(f"Expected: company='Google', specialization=None, explicit=False")
    
    assert intent.company is not None, f"Expected company to be extracted"
    assert intent.specialization is None, f"Expected None, got '{intent.specialization}'"
    assert intent.specialization_explicit == False, f"Expected explicit=False, got {intent.specialization_explicit}"
    print("✅ PASSED: Company-only query (no specialization filtering)")


if __name__ == "__main__":
    print("\n" + "🧪 SPECIALIZATION FILTERING TESTS ".center(70, "="))
    
    try:
        test_explicit_specialization()
        test_no_specialization()
        test_inferred_specialization()
        test_generic_company_query()
        
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        print("\nSUMMARY:")
        print("✅ Explicit specialization -> Uses specialization filter")
        print("✅ No specialization -> Uses company filter only")
        print("✅ Inferred specialization -> Uses company filter only")
        print("✅ Generic company query -> Uses company filter only")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        raise
