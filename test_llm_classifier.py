#!/usr/bin/env python3
"""Test LLM role type classifier in isolation"""

import os
import sys

# Add the current directory to path so we can import app modules
sys.path.insert(0, '.')

os.environ["ROLE_TYPES_DEBUG"] = "1"

from app.llm_role_type_classifier import classify_role_types_llm

# Test data similar to what comes from structured extraction
test_roles = [
    {
        "title": "Associate – People Operations",
        "specialization": "HR",
        "location": None,
        "responsibilities": [
            "Handle employee onboarding",
            "Manage HR processes"
        ],
        "requirements": [
            "Bachelor's degree",
            "Strong communication skills"
        ],
        "skills": ["Communication", "HR Management"]
    }
]

test_doc_text = """
About Accorian

Accorian is an established cybersecurity advisory and consulting firm headquartered in Silicon Valley.

Role: Associate – People Operations
Department: People
Experience Range: Fresher
Educational Qualification: Bachelor's Degree/MBA

We are looking for an Associate in People Operations to join our team.
"""

print("Testing LLM role type classifier...")
print(f"Test roles: {test_roles}")
print(f"Doc text preview: {test_doc_text[:200]}...")

try:
    result = classify_role_types_llm(test_roles, test_doc_text)
    print(f"✅ Success! Result: {result}")
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(f"Full traceback:\n{traceback.format_exc()}")
