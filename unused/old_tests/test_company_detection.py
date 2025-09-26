#!/usr/bin/env python3
"""
Simple test script for company detection logic
"""

def test_company_detection():
    """Test the improved company detection logic"""
    
    # Simulate the company detection logic from rag.py
    def detect_company(question):
        question_lower = question.lower()
        
        # Use more specific patterns to avoid false positives
        trigger_patterns = [
            ("full jd of ", "of "),
            ("jd of ", "of "),
            ("job description of ", "of "),
            ("full jd for ", "for "),
            ("jd for ", "for "),
            ("job description for ", "for "),
            ("details about ", "about "),
            ("information about ", "about "),
            ("jd from ", "from "),
            ("job description from ", "from "),
            ("full jd from ", "from "),
            ("complete jd from ", "from "),
            ("complete jd of ", "of "),
            ("entire jd of ", "of "),
            ("entire jd for ", "for "),
            ("entire jd from ", "from ")
        ]
        
        company_text = None
        for pattern, phrase in trigger_patterns:
            if pattern in question_lower:
                # Extract the text *after* the trigger pattern
                potential_company = question_lower.split(pattern, 1)[1]
                # Clean up and limit to reasonable company name length
                company_text = " ".join(potential_company.strip().split()[:3])
                # Additional validation: company name should not end with common query words
                if company_text and not any(company_text.endswith(word) for word in ['roles', 'positions', 'specializations', 'skills', 'requirements']):
                    print(f"🔍 Auto-detected potential company: '{company_text}'")
                    break
        
        return company_text
    
    # Test cases that should NOT trigger company detection
    safe_queries = [
        "What are the HR roles available?",
        "Show me marketing positions",
        "List all finance specializations",
        "How many companies came for operations roles?",
        "What skills are required for strategy positions?",
        "Give me a summary of analytics roles",
        "Show me all companies",
        "What are the available specializations?",
        "List the skills required",
        "How many roles are there?"
    ]
    
    print("🧪 Testing Safe Queries (Should NOT trigger company detection):")
    print("=" * 60)
    
    for query in safe_queries:
        company_text = detect_company(query)
        status = "❌ TRIGGERED" if company_text else "✅ SAFE"
        print(f"   {status}: {query}")
        if company_text:
            print(f"      Detected company: '{company_text}'")
    
    print("\n" + "=" * 60)
    
    # Test cases that SHOULD trigger company detection
    company_queries = [
        "Show me the full JD of Tap Academy",
        "What is the JD for Mill Story?",
        "Give me details about Oracle at Bangalore",
        "Show me the complete JD from Microsoft",
        "Full JD of Google",
        "Job description for Apple",
        "Complete JD from Amazon",
        "Entire JD of Netflix",
        "Information about Tesla",
        "Details about Meta"
    ]
    
    print("🧪 Testing Company Queries (Should trigger company detection):")
    print("=" * 60)
    
    for query in company_queries:
        company_text = detect_company(query)
        status = "✅ TRIGGERED" if company_text else "❌ MISSED"
        print(f"   {status}: {query}")
        if company_text:
            print(f"      Detected company: '{company_text}'")
    
    print("\n" + "=" * 60)
    print("🎉 Company detection test completed!")

if __name__ == "__main__":
    test_company_detection()
