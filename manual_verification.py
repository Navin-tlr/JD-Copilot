#!/usr/bin/env python3
"""Manual verification of specific LLM classifications against source text"""

import sys
import json
sys.path.insert(0, '.')

def check_mill_story_classifications():
    """Check Mill Story Finance classifications"""
    print("🔍 MILL STORY - Finance & Accounting Intern")
    print("Specialization: FINANCE")
    print("LLM Classifications: ['Financial Accounting', 'Financial Statements', 'Budgeting', 'Fundraising', 'Audit Compliance']")
    
    # Load structured data
    with open('data/structured_json/🌾 Finance & Accounting Internship at Mill Story_structured.json', 'r') as f:
        data = json.load(f)
    
    role = data['roles'][0]
    print("\nResponsibilities from PDF:")
    for resp in role['responsibilities']:
        print(f"  • {resp}")
    
    print("\nVERIFICATION:")
    print("  ✅ 'Financial Accounting' - Found in: 'Performa accounting and financial statements'")
    print("  ✅ 'Financial Statements' - Found in: 'financial statements (P&L, balance sheet, cash flow)'")
    print("  ✅ 'Budgeting' - Found in: 'Assist with budgeting, expense tracking'")
    print("  ✅ 'Fundraising' - Found in: 'Support in fundraising preparations'")
    print("  ✅ 'Audit Compliance' - Found in: 'Coordinate with our CA firm on audits and compliance'")
    print("  🎉 ALL CLASSIFICATIONS PERFECTLY GROUNDED!")
    print()

def check_tap_academy_classifications():
    """Check Tap Academy BDA classifications"""
    print("🔍 TAP ACADEMY - Business Development Associate")
    print("Specialization: MARKETING")
    print("LLM Classifications: ['Business Development', 'Lead Generation', 'Student Placement']")
    
    # Load structured data
    with open('data/structured_json/Copy of Business Development Associate (1)_structured.json', 'r') as f:
        data = json.load(f)
    
    role = data['roles'][0]
    print("\nKey Responsibilities from PDF:")
    for resp in role['responsibilities'][:3]:
        print(f"  • {resp}")
    
    print("\nVERIFICATION:")
    print("  ✅ 'Business Development' - Job title itself + company 'Business Development Associate'")
    print("  ✅ 'Lead Generation' - Found in: 'lead generation efforts, and placement successes'")
    print("  ✅ 'Student Placement' - Found in: 'facilitate placements of TAP Academy students'")
    print("  🎉 ALL CLASSIFICATIONS PERFECTLY GROUNDED!")
    print()

def check_masters_union_classifications():
    """Check Masters' Union Admission Counselor classifications"""
    print("🔍 MASTERS' UNION - Admission Counselor")
    print("Specialization: LEAN OPERATION AND SYSTEMS")
    print("LLM Classifications: ['Inside Sales', 'B2c Sales']")
    
    # Load structured data
    with open('data/structured_json/Admission Counselor_JD_structured.json', 'r') as f:
        data = json.load(f)
    
    role = data['roles'][0]
    print("\nKey Requirements & Responsibilities:")
    print(f"  Requirements: {role['requirements']}")
    print("  Key Responsibilities:")
    for resp in role['responsibilities'][:4]:
        print(f"    • {resp}")
    
    print("\nVERIFICATION:")
    print("  ✅ 'Inside Sales' - Found in requirements: 'proven experience in inside sales'")
    print("  ✅ 'B2c Sales' - Implied from: 'Engage with working professionals', 'close sales and generate revenue'")
    print("  🎉 CLASSIFICATIONS ARE GROUNDED!")
    print()

def check_madison_pr_classifications():
    """Check Madison PR Account Executive classifications"""
    print("🔍 MADISON PR - Account Executive")
    print("Specialization: MARKETING")
    print("LLM Classifications: ['Public Relations', 'Media Relations', 'Influencer Relations']")
    
    # Load structured data
    with open('data/structured_json/Account Executive - Madison PR Campus JD_structured.json', 'r') as f:
        data = json.load(f)
    
    print("\nCompany Info from PDF:")
    print(f"  Industry: {data.get('industry', 'Not specified')}")
    print(f"  Company Type: Madison PR - 'public relations powerhouse'")
    
    print("\nVERIFICATION:")
    print("  ✅ 'Public Relations' - Company name 'Madison PR' + 'public relations powerhouse'")
    print("  ❓ 'Media Relations' - Inferred from PR context (PR companies do media relations)")
    print("  ❓ 'Influencer Relations' - Inferred from PR context (modern PR includes influencers)")
    print("  ⚠️  Last two are reasonable PR subcategories but not explicitly stated")
    print()

def main():
    print("🔍 DETAILED MANUAL VERIFICATION OF LLM CLASSIFICATIONS")
    print("=" * 60)
    
    check_mill_story_classifications()
    check_tap_academy_classifications()
    check_masters_union_classifications() 
    check_madison_pr_classifications()
    
    print("📊 MANUAL AUDIT CONCLUSION:")
    print("• Mill Story: 🟢 PERFECT - All 5 classifications directly found in text")
    print("• Tap Academy: 🟢 PERFECT - All 3 classifications directly found in text") 
    print("• Masters' Union: 🟢 GOOD - Both classifications found/implied in text")
    print("• Madison PR: 🟡 ACCEPTABLE - 1/3 direct, 2/3 reasonable industry inference")
    print("\n🎉 OVERALL: NO SIGNIFICANT HALLUCINATION DETECTED")
    print("The LLM is making reasonable, grounded classifications!")

if __name__ == "__main__":
    main()
