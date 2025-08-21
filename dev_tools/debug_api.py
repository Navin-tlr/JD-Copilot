#!/usr/bin/env python3
"""
Debug OpenRouter API
Simple test to see what's happening with the API call
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openrouter_api():
    """Test OpenRouter API directly"""
    print("🔍 Testing OpenRouter API Directly")
    print("=" * 40)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ No OPENROUTER_API_KEY found in .env")
        return
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Simple test prompt
    test_prompt = """
Extract company information from this text:

ACCORIAN
Role: Associate – People Operations
Department: People
Experience: Fresher
Education: Bachelor's Degree/MBA

Return ONLY valid JSON:
{
    "company_name": "Company name",
    "roles": [
        {
            "title": "Job title",
            "specialization": "HR"
        }
    ]
}
"""
    
    payload = {
        "model": "moonshotai/kimi-k2:free",
        "messages": [
            {"role": "system", "content": "You are a precise data extractor. Return ONLY valid JSON."},
            {"role": "user", "content": test_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 500,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    print("🚀 Making API call...")
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            print(f"✅ API Call Successful!")
            print(f"📄 Response Content:")
            print(f"   Length: {len(content)}")
            print(f"   Content: {content}")
            
            # Try to parse as JSON
            try:
                json_data = json.loads(content)
                print(f"🎯 JSON Parsing Successful!")
                print(f"   Company: {json_data.get('company_name', 'N/A')}")
                print(f"   Roles: {len(json_data.get('roles', []))}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parsing Failed: {e}")
                print(f"   Raw content: {repr(content)}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request Failed: {e}")

if __name__ == "__main__":
    test_openrouter_api()
