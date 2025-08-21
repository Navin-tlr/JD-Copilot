#!/usr/bin/env python3
"""
Test New LLM Extraction on Real PDFs
Tests the new structured extraction using LLM on your actual PDF files
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ingest.structured_extractor_new import StructuredExtractor

def test_new_llm_extraction():
    """Test new LLM extraction on real PDFs"""
    print("🧪 Testing NEW LLM Extraction on Real PDFs")
    print("=" * 50)
    
    # Initialize the extractor
    extractor = StructuredExtractor()
    
    # Test with sample text from your PDFs
    test_cases = [
        {
            "name": "Accorian HR Role",
            "text": """
ACCORIAN

# Role
Associate – People Operations

# Department
People

# Experience Range
Fresher

# Educational Qualification
Bachelor's Degree/MBA

# About Accorian
Accorian is an established cybersecurity advisory and consulting firm headquartered in New Jersey with regional offices in India, Canada and UAE. In today's dynamic digital world, we serve a global clientele, helping businesses of all sizes strategize cybersecurity initiatives, identify risks, develop solutions, program management.
            """
        },
        {
            "name": "Target India Media Operations",
            "text": """
# TII Apprenticeship Program

# JOIN US AS APPRENTICE – Media Operations

# About Target
As a Fortune 50 company with more than 400,000 team members worldwide, Target is an iconic brand and one of America's leading retailers. At Target, we have a timeless purpose and a proven strategy and that hasn't happened by accident. Some of the best minds from diverse backgrounds come together at Target to redefine retail in an inclusive learning environment that values people and delivers world-class outcomes.
            """
        }
    ]
    
    print("🔍 Testing new LLM extraction on sample texts...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📄 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Extract structured data
            extraction = extractor.extract_structured_data(test_case['text'])
            
            if extraction:
                print("✅ LLM Extraction Successful!")
                print(f"   Company: {extraction.company_name}")
                print(f"   Roles: {len(extraction.roles)}")
                
                for role in extraction.roles:
                    print(f"   - {role.title} ({role.specialization if hasattr(role, 'specialization') else 'N/A'})")
                    if role.skills:
                        print(f"     Skills: {', '.join(role.skills[:3])}...")
                
                # Save to file
                output_file = f"data/structured_json/llm_test_{i}.json"
                extractor.save_structured_data(extraction, f"test_{i}.txt")
                print(f"   💾 Saved to: {output_file}")
                
            else:
                print("❌ LLM Extraction Failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎯 New LLM Extraction Test Complete!")
    print("\nNext steps:")
    print("1. Check the generated JSON files in data/structured_json/")
    print("2. If successful, replace the old extractor with the new one")
    print("3. Run the full ingestion pipeline")

if __name__ == "__main__":
    test_new_llm_extraction()
