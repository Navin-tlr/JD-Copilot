#!/usr/bin/env python3
"""
Test script to verify OpenRouter API connectivity with moonshotai/kimi-k2
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openrouter_api():
    """Test OpenRouter API connectivity with moonshotai/kimi-k2"""
    
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY')
    model = "moonshotai/kimi-k2"  # Use the specified model
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return False
    
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🤖 Model: {model}")
    
    # Test API endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "JD-Copilot Test"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello! Please respond with 'OpenRouter API is working!'"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        print("🚀 Testing OpenRouter API with moonshotai/kimi-k2...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ API Response: {content}")
            print(f"✅ Status Code: {response.status_code}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_agent_configuration():
    """Test the exact configuration used in the agent"""
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test with the exact model and configuration used in agent.py
    data = {
        "model": "moonshotai/kimi-k2",  # Updated to use the specified model
        "messages": [
            {"role": "user", "content": "Generate a simple SQL query to count companies"}
        ],
        "max_tokens": 100,
        "temperature": 0
    }
    
    try:
        print("\n🤖 Testing Agent Configuration (moonshotai/kimi-k2)...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Agent Model Response: {content}")
            print(f"✅ Status Code: {response.status_code}")
            return True
        else:
            print(f"❌ Agent Model Error: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Agent Model Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OpenRouter API Connectivity with moonshotai/kimi-k2")
    print("=" * 60)
    
    # Test 1: Basic API connectivity with moonshotai/kimi-k2
    success1 = test_openrouter_api()
    
    # Test 2: Agent configuration
    success2 = test_agent_configuration()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests passed! OpenRouter API is working correctly with moonshotai/kimi-k2.")
    elif success1 or success2:
        print("⚠️  Partial success. Some endpoints are working.")
    else:
        print("❌ All tests failed. OpenRouter API is not working.")
    
    print("\n📋 Summary:")
    print(f"   Basic API (moonshotai/kimi-k2): {'✅' if success1 else '❌'}")
    print(f"   Agent Model (moonshotai/kimi-k2): {'✅' if success2 else '❌'}")
    
    if success1 and success2:
        print("\n🎯 **RESULT: OpenRouter API is working perfectly with moonshotai/kimi-k2!**")
        print("   Your agent will work correctly with this model.")
    else:
        print("\n❌ **RESULT: OpenRouter API has issues with moonshotai/kimi-k2.**")
