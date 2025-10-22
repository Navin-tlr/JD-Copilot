"""
Basic test of Gemini SDK with the fixed configuration.
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

print("🚀 Testing Gemini SDK with fixed configuration...")
print(f"   API Key present: Yes ({len(API_KEY)} chars)")

# CRITICAL FIX: Force REST API instead of gRPC
# Configure the SDK to use REST transport (gRPC is being blocked)
genai.configure(api_key=API_KEY, transport="rest")

# Use the model name from your config
model_name = "gemini-2.5-flash"
print(f"   Model: {model_name}")

try:
    # Create model instance
    model = genai.GenerativeModel(model_name)
    print(f"✅ Model instance created successfully")
    
    # Simple hello world test
    test_query = "Say 'Hello World' and nothing else."
    print(f"\n📤 Sending test query: '{test_query}'")
    
    start = time.time()
    response = model.generate_content(
        test_query,
        request_options={"timeout": 15.0}
    )
    elapsed = time.time() - start
    
    print(f"✅ Response received in {elapsed:.2f}s")
    print(f"📥 Response: {response.text}")
    print(f"\n🎉 SUCCESS! Gemini is working correctly.")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
