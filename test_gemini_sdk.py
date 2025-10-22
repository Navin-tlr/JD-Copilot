"""
Direct test of google-generativeai SDK to isolate the hang issue.
This bypasses all application code and tests the library in isolation.
"""
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found")
    exit(1)

print("🚀 Testing google-generativeai SDK directly...")
print(f"   API Key present: {bool(API_KEY)}")
print(f"   API Key length: {len(API_KEY)}")

# Configure the SDK
genai.configure(api_key=API_KEY)

# Try different model names to see which one works
models_to_test = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]

for model_name in models_to_test:
    print(f"\n{'='*80}")
    print(f"Testing model: {model_name}")
    print(f"{'='*80}")
    
    try:
        # Create model instance
        model = genai.GenerativeModel(model_name)
        print(f"✅ Model instance created")
        
        # Simple test query
        test_query = "What is 2+2?"
        print(f"📤 Sending test query: '{test_query}'")
        
        start = time.time()
        response = model.generate_content(
            test_query,
            request_options={"timeout": 10.0}
        )
        elapsed = time.time() - start
        
        print(f"✅ Response received in {elapsed:.2f}s")
        print(f"📥 Response: {response.text[:200]}")
        print(f"\n🎉 SUCCESS: Model '{model_name}' works!")
        break
        
    except Exception as e:
        print(f"❌ FAILED with model '{model_name}': {e}")
        print(f"   Error type: {type(e).__name__}")
        continue

print(f"\n{'='*80}")
print("Test complete")
print(f"{'='*80}")
