
import os
import httpx
import asyncio
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
    exit(1)

# Define the Gemini API endpoint and the model
# Using v1 as it's the more stable version
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# The simple user query
USER_QUERY = "how many companies came for finance?"

# The payload structure for the REST API
# This mimics what the google-generativeai library would send
payload = {
    "contents": [{
        "parts": [{"text": USER_QUERY}]
    }]
}

async def run_direct_api_test():
    """
    Makes a direct HTTP POST request to the Gemini API, bypassing the google-generativeai library.
    """
    print("🚀 Starting direct API call test...")
    print(f"   Endpoint: {API_URL.split('?')[0]}") # Don't print the key
    print(f"   Query: '{USER_QUERY}'")

    try:
        # Use httpx, which is what the Google library uses under the hood.
        # Set a reasonable timeout. If this hangs, the timeout will catch it.
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("   Sending POST request to Gemini...")
            
            response = await client.post(
                API_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Received response with status code: {response.status_code}")

            # Check if the request was successful
            if response.status_code == 200:
                print("✅ SUCCESS: Direct API call completed successfully.")
                response_data = response.json()
                # Extract and print the generated text
                try:
                    # Navigating the response structure to get the content
                    text = response_data['candidates'][0]['content']['parts'][0]['text']
                    print("\n--- Generated Content ---")
                    print(text.strip())
                    print("-------------------------\n")
                    print("CONCLUSION: The underlying Python networking and SSL are working correctly. The issue is likely within the 'google-generativeai' library.")
                except (KeyError, IndexError) as e:
                    print(f"❌ ERROR: Could not parse the response JSON. Error: {e}")
                    print("Full Response:")
                    print(json.dumps(response_data, indent=2))
            else:
                print(f"❌ FAILURE: API call failed with status {response.status_code}.")
                print("   Response body:")
                print(response.text)
                print("\nCONCLUSION: The issue is likely a deeper problem with the Python networking/SSL environment, as even a direct call is failing.")

    except httpx.TimeoutException:
        print("\n❌ CRITICAL FAILURE: The direct API call timed out.")
        print("CONCLUSION: The hang is happening at a low level in Python's networking stack. This is not an issue with the 'google-generativeai' library itself, but a fundamental environment problem.")
    except httpx.RequestError as e:
        print(f"\n❌ CRITICAL FAILURE: An HTTP request error occurred: {e}")
        print(f"   Error Type: {type(e).__name__}")
        print("CONCLUSION: A network error is preventing any connection to the Gemini API. This could be a DNS, proxy, or SSL issue not solved by previous fixes.")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_direct_api_test())
