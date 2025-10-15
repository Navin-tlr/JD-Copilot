#!/usr/bin/env python3
"""
Test script to validate the industry validation and filtering system
with the original FMCG query: "how many companies came for fmcg and who are they?"

This script tests:
1. Industry validation for FMCG queries
2. Filtering out non-FMCG companies like "Eze Cloud Consulting"
3. Retention of actual FMCG companies
4. Validation logs and confidence scores
"""

import sys
import os
from typing import List, Dict, Any

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.rag import retrieve_snippets
from app.industry_validator import IndustryValidator


def test_fmcg_query():
    """Test the FMCG query through the industry validation system"""

    query = "how many companies came for fmcg and who are they?"

    print("🧪 Testing FMCG Industry Validation System")
    print("=" * 50)
    print(f"Query: {query}")
    print()

    # Step 1: Retrieve snippets using the RAG system
    print("🔍 Step 1: Retrieving snippets from RAG system...")
    try:
        snippets = retrieve_snippets(query, top_k=50, filters={})
        print(f"✅ Retrieved {len(snippets)} snippets")
    except Exception as e:
        print(f"❌ Failed to retrieve snippets: {e}")
        return

    # Step 2: Analyze industry validation in retrieved results
    print("\n🔍 Step 2: Analyzing industry validation...")

    try:
        industry_validator = IndustryValidator()
    except Exception as e:
        print(f"⚠️ Industry validator initialization failed: {e}")
        industry_validator = None

    # Collect unique companies and their industries
    companies_analyzed = {}
    validation_results = []

    for snippet in snippets:
        metadata = snippet.get('metadata', {})
        company = metadata.get('company', '').strip()

        if not company:
            continue

        if company in companies_analyzed:
            continue

        companies_analyzed[company] = metadata

        # Get industry from metadata
        industry = metadata.get('industry', '')

        if industry and industry_validator:
            # Validate the industry
            context = snippet.get('text', '')[:300]
            validation_result = industry_validator.validate_industry(
                industry,
                context=context,
                use_llm=True
            )

            validation_results.append({
                'company': company,
                'original_industry': industry,
                'validated_industry': validation_result.normalized_industry,
                'confidence': validation_result.confidence,
                'source': validation_result.source,
                'alternatives': validation_result.alternatives,
                'is_fmcg': 'fmcg' in validation_result.normalized_industry.lower() or
                          'consumer goods' in validation_result.normalized_industry.lower() or
                          'fast moving consumer goods' in validation_result.normalized_industry.lower()
            })
        elif industry:
            # Fallback if validator fails - basic check
            validation_results.append({
                'company': company,
                'original_industry': industry,
                'validated_industry': industry,
                'confidence': 0.5,
                'source': 'fallback',
                'alternatives': [],
                'is_fmcg': 'fmcg' in industry.lower() or
                          'consumer goods' in industry.lower() or
                          'fast moving consumer goods' in industry.lower()
            })

    # Step 3: Categorize results
    print("\n📊 Step 3: Categorizing results...")

    fmcg_companies = []
    non_fmcg_companies = []
    low_confidence_companies = []

    for result in validation_results:
        if result['is_fmcg']:
            fmcg_companies.append(result)
        else:
            non_fmcg_companies.append(result)

        if result['confidence'] < 0.6:
            low_confidence_companies.append(result)

    # Step 4: Display results
    print("\n📈 RESULTS SUMMARY")
    print("=" * 50)

    print(f"Total companies analyzed: {len(validation_results)}")
    print(f"FMCG companies: {len(fmcg_companies)}")
    print(f"Non-FMCG companies: {len(non_fmcg_companies)}")
    print(f"Low confidence validations: {len(low_confidence_companies)}")
    print()

    # Check for Eze Cloud Consulting specifically
    eze_found = any(r['company'].lower() == 'eze cloud consulting' for r in validation_results)
    if eze_found:
        eze_result = next(r for r in validation_results if r['company'].lower() == 'eze cloud consulting')
        print("🚨 EZE CLOUD CONSULTING DETECTED:")
        print(f"   Company: {eze_result['company']}")
        print(f"   Industry: {eze_result['original_industry']}")
        print(f"   Validated: {eze_result['validated_industry']}")
        print(f"   Confidence: {eze_result['confidence']:.2f}")
        print(f"   Is FMCG: {eze_result['is_fmcg']}")
        print()
    else:
        print("✅ Eze Cloud Consulting was NOT found in results (correctly filtered out)")
        print()

    # Display FMCG companies
    if fmcg_companies:
        print("✅ FMCG COMPANIES RETAINED:")
        for company in sorted(fmcg_companies, key=lambda x: x['confidence'], reverse=True):
            print(f"   • {company['company']} (confidence: {company['confidence']:.2f}, source: {company['source']})")
        print()

    # Display non-FMCG companies that should be filtered
    if non_fmcg_companies:
        print("⚠️  NON-FMCG COMPANIES DETECTED:")
        for company in sorted(non_fmcg_companies, key=lambda x: x['confidence'], reverse=True):
            print(f"   • {company['company']} - {company['validated_industry']} (confidence: {company['confidence']:.2f})")
        print()

    # Display low confidence validations
    if low_confidence_companies:
        print("⚠️  LOW CONFIDENCE VALIDATIONS:")
        for company in sorted(low_confidence_companies, key=lambda x: x['confidence']):
            print(f"   • {company['company']} - {company['validated_industry']} (confidence: {company['confidence']:.2f})")
        print()

    # Step 5: Validation assessment
    print("🎯 VALIDATION ASSESSMENT")
    print("=" * 50)

    success_criteria = {
        'eze_filtered': not eze_found,
        'fmcg_retained': len(fmcg_companies) > 0,
        'non_fmcg_filtered': len(non_fmcg_companies) == 0,
        'high_confidence': all(r['confidence'] >= 0.6 for r in validation_results)
    }

    all_passed = all(success_criteria.values())

    print("Success Criteria:")
    print(f"   ✅ Eze Cloud Consulting filtered out: {'PASS' if success_criteria['eze_filtered'] else 'FAIL'}")
    print(f"   ✅ FMCG companies retained: {'PASS' if success_criteria['fmcg_retained'] else 'FAIL'}")
    print(f"   ✅ Non-FMCG companies filtered: {'PASS' if success_criteria['non_fmcg_filtered'] else 'FAIL'}")
    print(f"   ✅ High confidence validations: {'PASS' if success_criteria['high_confidence'] else 'FAIL'}")
    print()

    if all_passed:
        print("🎉 ALL TESTS PASSED - Industry validation system is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Industry validation system needs improvement")

    return all_passed


if __name__ == "__main__":
    success = test_fmcg_query()
    sys.exit(0 if success else 1)