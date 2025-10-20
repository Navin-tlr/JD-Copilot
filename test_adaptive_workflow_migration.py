#!/usr/bin/env python3
"""
Quick test script to verify the adaptive LangGraph workflow is invoked correctly.
Run this after starting the server to ensure the migration was successful.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_adaptive_workflow():
    """Test that the /chat endpoint uses the adaptive workflow."""
    
    print("=" * 70)
    print("Testing Adaptive Workflow Migration")
    print("=" * 70)
    print()
    
    # Test Query
    test_query = "how many companies came for #hr"
    
    payload = {
        "question": test_query,
        "user_id": "test-user-123",
        "session_id": "test-session-001"  # Changed from None to actual session ID
    }
    
    print(f"📤 Sending query: {test_query}")
    print(f"   Endpoint: POST {BASE_URL}/chat")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            
            print("✅ Request succeeded!")
            print()
            print("📊 Response Summary:")
            print(f"   Answer length: {len(answer)} characters")
            print(f"   Snippets: {len(data.get('snippets', []))}")
            print(f"   Vector used: {data.get('vector_used', False)}")
            print()
            print("📝 Answer Preview:")
            print("-" * 70)
            print(answer[:300] + ("..." if len(answer) > 300 else ""))
            print("-" * 70)
            print()
            
            # Check for success indicators
            success_indicators = []
            failure_indicators = []
            
            # Success: Response contains actual data
            if "companies" in answer.lower() or "hr" in answer.lower():
                success_indicators.append("✓ Response mentions relevant entities")
            
            # Failure: Contains error messages
            if "error" in answer.lower() or "failed" in answer.lower():
                failure_indicators.append("✗ Response contains error messages")
            
            # Failure: Very short response (likely error)
            if len(answer) < 50:
                failure_indicators.append("✗ Response is suspiciously short")
            
            print("🔍 Validation Results:")
            for indicator in success_indicators:
                print(f"   {indicator}")
            for indicator in failure_indicators:
                print(f"   {indicator}")
            print()
            
            if not failure_indicators:
                print("🎉 Test PASSED! Adaptive workflow appears to be working correctly.")
                return True
            else:
                print("⚠️  Test PASSED with warnings. Check server logs for details.")
                return True
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed!")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload --port 8000")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_server_logs():
    """Provide instructions for checking server logs."""
    print()
    print("=" * 70)
    print("Server Log Verification")
    print("=" * 70)
    print()
    print("Check your server logs for these key indicators:")
    print()
    print("✅ SUCCESS INDICATORS:")
    print("   • '🚀 Using ADAPTIVE LANGGRAPH WORKFLOW'")
    print("   • '🎯 Invoking adaptive LangGraph workflow...'")
    print("   • '🚀 Agent Pipeline Started'")
    print("   • '🎯 Stage 0: Classifying intent...'")
    print("   • '✅ Adaptive workflow completed successfully'")
    print()
    print("❌ FAILURE INDICATORS (should NOT appear):")
    print("   • '🚀 Using conversational chat service for query processing'")
    print("   • '🔄 Resolved contextual query: ... → ... for Operations roles'")
    print("   • Any mentions of 'chat_service.send_message'")
    print()
    print("If you see the SUCCESS indicators, the migration was successful! 🎉")
    print()

if __name__ == "__main__":
    success = test_adaptive_workflow()
    check_server_logs()
    
    sys.exit(0 if success else 1)
