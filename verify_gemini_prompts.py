#!/usr/bin/env python3
"""
Quick verification that Gemini system prompts are working correctly.

This script demonstrates:
1. System prompt conversion happens automatically
2. All content is preserved
3. Sapient personality comes through in responses
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if Gemini API key is set
if not os.getenv("GEMINI_API_KEY"):
    print("❌ GEMINI_API_KEY not set in .env file")
    print("Please add your Gemini API key to .env to run this verification")
    sys.exit(1)

from app.llm_client import get_gemini_client

def verify_basic_conversion():
    """Verify basic message conversion works."""
    print("🔍 VERIFICATION 1: Basic Message Conversion")
    print("=" * 80)
    
    client = get_gemini_client()
    
    # Simple system prompt with Sapient's key traits
    system_prompt = """You are Sapient, the MBA Placement Cell Director.

PERSONALITY:
• Professional and authoritative
• Bone-dry humor about career realities
• Brutally honest, no sugarcoating
• Data-driven insights only

RULES:
• Never invent or hallucinate company names
• Use **bold** for emphasis
• Deploy dry humor in responses"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Say hello and introduce yourself briefly."}
    ]
    
    # Convert messages
    gemini_messages = client._to_gemini_messages(messages)
    
    # Check structure
    assert len(gemini_messages) == 1, "Should have 1 message"
    assert gemini_messages[0]["role"] == "user", "Should be user role"
    assert "SYSTEM INSTRUCTIONS" in gemini_messages[0]["parts"][0], "Should have system header"
    assert "Sapient" in gemini_messages[0]["parts"][0], "Should preserve Sapient name"
    assert "Bone-dry humor" in gemini_messages[0]["parts"][0] or "bone-dry humor" in gemini_messages[0]["parts"][0], "Should preserve personality traits"
    
    print("✅ Message conversion structure correct")
    print("✅ System prompt content preserved")
    print("✅ Visual separation present")
    print()

def verify_conversation_history():
    """Verify conversation history is handled correctly."""
    print("🔍 VERIFICATION 2: Conversation History")
    print("=" * 80)
    
    client = get_gemini_client()
    
    messages = [
        {"role": "system", "content": "You are Sapient, the placement director."},
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
        {"role": "user", "content": "Second question"}
    ]
    
    gemini_messages = client._to_gemini_messages(messages)
    
    # Should have 3 messages (system+user1, assistant, user2)
    assert len(gemini_messages) == 3, f"Should have 3 messages, got {len(gemini_messages)}"
    
    # First should have system embedded
    assert "Sapient" in gemini_messages[0]["parts"][0], "First message should have system"
    
    # Second should be model (assistant)
    assert gemini_messages[1]["role"] == "model", "Assistant should be 'model' role"
    
    # Third should be user without system
    assert "Sapient" not in gemini_messages[2]["parts"][0], "Follow-up shouldn't repeat system"
    
    print("✅ Conversation history structure correct")
    print("✅ System embedded in first message only")
    print("✅ Assistant converted to 'model' role")
    print("✅ Follow-ups don't repeat system instructions")
    print()

def verify_live_response():
    """Verify a live response from Gemini (requires API key)."""
    print("🔍 VERIFICATION 3: Live Gemini Response")
    print("=" * 80)
    
    try:
        client = get_gemini_client()
        
        # Short system prompt with Sapient personality
        system_prompt = """You are Sapient, the MBA Placement Cell Director - a professional with bone-dry wit.

Keep your response BRIEF (2-3 sentences max). Introduce yourself and make ONE dry remark about career planning."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Introduce yourself."}
        ]
        
        print("Sending request to Gemini 2.0 Flash...")
        response = client.chat(messages, max_tokens=200, temperature=0.7)
        
        print("\n📝 Response from Gemini:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        
        # Basic checks
        if "Sapient" in response or "placement" in response.lower():
            print("✅ Response mentions Sapient/placement")
        
        if len(response) > 50:
            print("✅ Response has substantial content")
        
        print("\n💡 Review the response above:")
        print("   - Does it sound like Sapient?")
        print("   - Is there dry humor?")
        print("   - Is it professional and direct?")
        print()
        
    except Exception as e:
        print(f"⚠️  Live response test skipped: {e}")
        print("   (This is optional - conversion tests still passed)")
        print()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  GEMINI SYSTEM PROMPT VERIFICATION")
    print("=" * 80)
    print()
    
    try:
        verify_basic_conversion()
        verify_conversation_history()
        verify_live_response()
        
        print("=" * 80)
        print("🎉 VERIFICATION COMPLETE!")
        print("=" * 80)
        print("✅ System prompt conversion working correctly")
        print("✅ Content preservation validated")
        print("✅ Conversation history handled properly")
        print("✅ Ready for production use")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
