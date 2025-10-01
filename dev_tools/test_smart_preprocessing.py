#!/usr/bin/env python3
"""
Test script for smart preprocessing integration.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.smart_preprocessing import SmartPreprocessor

def test_smart_preprocessing():
    """Test smart preprocessing with sample JD."""

    # Read sample JD
    sample_path = Path("dev_tools/sample_jd_texts/sample_jd_1.txt")
    text = sample_path.read_text()

    print(f"Testing smart preprocessing with {sample_path}")
    print(f"Text length: {len(text)} characters")
    print("Text preview:")
    print(text[:200] + "...")
    print("-" * 50)

    # Initialize preprocessor
    preprocessor = SmartPreprocessor()

    # Process text
    summary = preprocessor.process_text(text, str(sample_path))

    if summary:
        print("✅ Summary generated successfully!")
        print(f"Key skills: {summary.key_skills}")
        print(f"Specializations: {summary.specializations}")
        print(f"Companies: {summary.companies}")
        print(f"Salary info: {summary.salary_info}")
        print(f"Quality score: {summary.quality_score}")
    else:
        print("❌ Failed to generate summary")

    # Test duplicate detection
    print("\nTesting duplicate detection...")
    summary2 = preprocessor.process_text(text, str(sample_path))
    if summary2 is None:
        print("✅ Duplicate detection working - second call returned None")
    else:
        print("⚠️ Duplicate detection may not be working")

if __name__ == "__main__":
    test_smart_preprocessing()