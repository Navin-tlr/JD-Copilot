#!/usr/bin/env python3
"""
Test script for Smart Preprocessing functionality
Tests summary generation, duplicate detection, and database operations
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.smart_preprocessing import SmartPreprocessor, DocumentSummary

def test_smart_preprocessing():
    """Test smart preprocessing functionality"""
    print("🧪 Testing Smart Preprocessing System")
    print("=" * 50)

    # Initialize preprocessor
    preprocessor = SmartPreprocessor()

    # Sample JD text for testing
    sample_jd = """
    Marketing Manager Position at TechCorp

    About TechCorp:
    TechCorp is a leading technology company specializing in digital marketing solutions.

    Job Description:
    We are looking for a skilled Marketing Manager to lead our digital marketing initiatives.

    Key Responsibilities:
    - Develop and execute marketing strategies
    - Manage social media campaigns
    - Analyze campaign performance using analytics tools
    - Create compelling content for various platforms

    Requirements:
    - Bachelor's degree in Marketing or related field
    - 3+ years of digital marketing experience
    - Proficiency in Google Analytics, Facebook Ads, and content creation tools
    - Strong communication and analytical skills

    What We Offer:
    - Competitive salary: ₹8-12 LPA
    - Health insurance and other benefits
    - Opportunity to work with cutting-edge technology
    """

    print("📄 Testing with sample JD text...")
    print(f"Text length: {len(sample_jd)} characters")

    # Test summary generation
    print("\n🔍 Testing summary generation...")
    summary = preprocessor.process_text(sample_jd, "test_jd.pdf")

    if summary:
        print("✅ Summary generated successfully!")
        print(f"Company: {summary.company_name}")
        print(f"Key Skills: {', '.join(summary.key_skills)}")
        print(f"Specializations: {', '.join(summary.specializations)}")
        print(f"Quality Score: {summary.quality_score}")
        print(f"Summary: {summary.summary[:100]}...")
    else:
        print("❌ Summary generation failed")

    # Test duplicate detection
    print("\n🔄 Testing duplicate detection...")
    summary2 = preprocessor.process_text(sample_jd, "test_jd_duplicate.pdf")

    if summary2 is None:
        print("✅ Duplicate detection working - second processing was skipped")
    else:
        print("⚠️ Duplicate detection may not be working properly")

    # Test database retrieval
    print("\n💾 Testing database operations...")
    if summary:
        retrieved = preprocessor.get_summary_by_hash(summary.file_hash)
        if retrieved:
            print("✅ Database retrieval working")
            print(f"Retrieved company: {retrieved.company_name}")
        else:
            print("❌ Database retrieval failed")

    # Test batch processing
    print("\n📦 Testing batch processing...")
    batch_summaries = [
        DocumentSummary(
            source_file="batch_test_1.pdf",
            file_hash="hash1",
            company_name="Company A",
            summary="Summary A",
            key_skills=["skill1", "skill2"],
            specializations=["marketing"],
            salary_info={},
            role_count=1,
            batch_year="2024",
            content_type="job_description",
            quality_score=0.8
        ),
        DocumentSummary(
            source_file="batch_test_2.pdf",
            file_hash="hash2",
            company_name="Company B",
            summary="Summary B",
            key_skills=["skill3", "skill4"],
            specializations=["sales"],
            salary_info={},
            role_count=1,
            batch_year="2024",
            content_type="job_description",
            quality_score=0.9
        )
    ]

    result = preprocessor.batch_process_summaries(batch_summaries)
    print(f"✅ Batch processing completed: {result.processed_files} processed, {result.skipped_duplicates} skipped")

    print("\n🎉 Smart Preprocessing Tests Completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_smart_preprocessing()