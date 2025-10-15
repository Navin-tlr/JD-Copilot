#!/usr/bin/env python3
"""
Test script to verify Gemini 2.0 Flash prompt preservation.

This script validates that:
1. System prompts are properly converted to Gemini format
2. ALL content, formatting, tone, and personality are preserved
3. Visual separation is maintained for system instructions
"""

from app.llm_client import GeminiClient

def test_prompt_conversion():
    """Test that GeminiClient preserves all system prompt attributes."""
    
    # Create a mock system prompt with Sapient's personality
    system_prompt = """You are Sapient serving as the MBA Placement Cell Director - a professional authority figure who delivers career guidance with technical precision, institutional seriousness, and bone-dry wit.

GOAL: Provide MBA students with brutally honest, data-driven career insights. No fluff, no speculation, no false hope - just the unvarnished market realities delivered with the dry humor of someone who's reviewed thousands of resumes.

CORE SYSTEM FEATURES (NON-OVERRIDABLE):
1. SAPIENT TONE MAINTENANCE: You MUST maintain Sapient's merciless directness throughout ALL interactions.
2. SPECIALIZATION FOCUS: Restrict insights strictly to user-specified MBA specializations.
3. CONTEXT SUMMARIZATION: Summarize context at each step for multi-step reasoning.

PROHIBITED CONTENT:
• External institutional comparisons or rankings unless the exact text appears in inputs.
• Invented program names, inflated numbers, speculative salary projections.

COMPANY NAME CONSTRAINTS (HARD RULES):
• You MUST NOT introduce, invent, guess, or hallucinate any company name not in sources.
• Only reference a company if its exact name occurs in the provided data.

OUTPUT STYLE:
• Be professionally direct, authoritative, and exhaustive.
• Deploy dry humor and professional bluntness in every response without exception.
• Use **bold** for key terms, company names, critical insights.
• Use `code formatting` for technical terms, skills, tools."""

    user_query = "What roles does Honasa have for Marketing specialization?"
    
    # Create client
    client = GeminiClient()
    
    # Convert messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    gemini_messages = client._to_gemini_messages(messages)
    
    # Validation checks
    print("🧪 TESTING GEMINI PROMPT CONVERSION")
    print("=" * 80)
    
    # Check 1: Should have exactly 1 message (system + user combined)
    assert len(gemini_messages) == 1, f"Expected 1 message, got {len(gemini_messages)}"
    print("✅ Check 1: Correct number of messages")
    
    # Check 2: Should be a user role
    assert gemini_messages[0]["role"] == "user", f"Expected 'user' role, got {gemini_messages[0]['role']}"
    print("✅ Check 2: Correct role assignment")
    
    # Check 3: Should have parts array
    assert "parts" in gemini_messages[0], "Missing 'parts' field"
    assert isinstance(gemini_messages[0]["parts"], list), "'parts' should be a list"
    print("✅ Check 3: Correct 'parts' structure")
    
    # Check 4: Combined content should preserve ALL system prompt content
    combined_content = gemini_messages[0]["parts"][0]
    
    # Critical content checks
    critical_phrases = [
        "Sapient serving as the MBA Placement Cell Director",
        "bone-dry wit",
        "SAPIENT TONE MAINTENANCE",
        "SPECIALIZATION FOCUS",
        "COMPANY NAME CONSTRAINTS (HARD RULES)",
        "Deploy dry humor and professional bluntness",
        "Use **bold** for key terms",
        "Use `code formatting`"
    ]
    
    for phrase in critical_phrases:
        assert phrase in combined_content, f"Missing critical phrase: {phrase}"
    
    print("✅ Check 4: All critical personality traits preserved")
    
    # Check 5: User query should be present
    assert user_query in combined_content, "User query not found in combined content"
    print("✅ Check 5: User query preserved")
    
    # Check 6: Visual separation should be present
    assert "SYSTEM INSTRUCTIONS" in combined_content, "Missing system instructions header"
    assert "USER QUERY" in combined_content, "Missing user query header"
    assert "━" in combined_content, "Missing visual separation borders"
    print("✅ Check 6: Visual separation maintained")
    
    # Display the converted message structure
    print("\n" + "=" * 80)
    print("📋 CONVERTED MESSAGE PREVIEW:")
    print("=" * 80)
    print(f"Role: {gemini_messages[0]['role']}")
    print(f"Content length: {len(combined_content)} characters")
    print(f"\nFirst 500 characters:")
    print(combined_content[:500])
    print("\n[...]")
    print(f"\nLast 200 characters:")
    print(combined_content[-200:])
    
    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)
    print("✅ System prompt properly converted to Gemini format")
    print("✅ ALL content, formatting, tone, and personality preserved")
    print("✅ Visual separation maintained for clear instruction hierarchy")
    print("=" * 80)

def test_conversation_history():
    """Test that conversation history is properly handled."""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING CONVERSATION HISTORY HANDLING")
    print("=" * 80)
    
    client = GeminiClient()
    
    messages = [
        {"role": "system", "content": "You are Sapient, the MBA Placement Cell Director."},
        {"role": "user", "content": "Tell me about FMCG companies."},
        {"role": "assistant", "content": "We have 5 FMCG companies in our database."},
        {"role": "user", "content": "What roles do they offer?"}
    ]
    
    gemini_messages = client._to_gemini_messages(messages)
    
    # Should have 3 messages (system+user1, assistant, user2)
    assert len(gemini_messages) == 3, f"Expected 3 messages, got {len(gemini_messages)}"
    print("✅ Correct number of messages in conversation")
    
    # First message should be user with embedded system
    assert gemini_messages[0]["role"] == "user"
    assert "Sapient" in gemini_messages[0]["parts"][0]
    assert "FMCG companies" in gemini_messages[0]["parts"][0]
    print("✅ System instructions embedded in first user message")
    
    # Second message should be model (assistant)
    assert gemini_messages[1]["role"] == "model"
    assert "5 FMCG companies" in gemini_messages[1]["parts"][0]
    print("✅ Assistant response converted to 'model' role")
    
    # Third message should be user (follow-up)
    assert gemini_messages[2]["role"] == "user"
    assert "What roles" in gemini_messages[2]["parts"][0]
    # Should NOT have system instructions again
    assert "Sapient" not in gemini_messages[2]["parts"][0]
    print("✅ Follow-up user message without repeated system instructions")
    
    print("=" * 80)
    print("🎉 CONVERSATION HISTORY TESTS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_prompt_conversion()
        test_conversation_history()
        print("\n✅ ALL GEMINI PROMPT PRESERVATION TESTS PASSED! ✅")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)
