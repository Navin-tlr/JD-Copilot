#!/usr/bin/env python3
"""
Populate Database with Real PDF Data
Uses the manually created structured data from real PDFs
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import PlacementDatabase

def populate_real_data():
    """Populate database with real PDF data"""
    print("🎯 JD-Copilot - Populating Database with Real PDF Data")
    print("=" * 60)
    
    # Load the real data
    data_file = Path("data/structured_json/real_data_manual.json")
    if not data_file.exists():
        print("❌ Real data file not found!")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        real_data = json.load(f)
    
    print(f"📁 Loaded {len(real_data)} companies from real PDFs")
    
    # Initialize database
    db = PlacementDatabase()
    
    # Insert each company
    success_count = 0
    total_roles = 0
    
    for company_data in real_data:
        try:
            print(f"\n🏢 Processing: {company_data['company_name']}")
            print(f"   Industry: {company_data.get('industry', 'N/A')}")
            print(f"   Location: {company_data.get('location', 'N/A')}")
            
            success = db.insert_company_extraction(company_data)
            if success:
                success_count += 1
                role_count = len(company_data.get('roles', []))
                total_roles += role_count
                print(f"   ✅ Inserted {role_count} roles")
            else:
                print(f"   ❌ Failed to insert")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Database Population Complete!")
    print(f"✅ Successfully inserted: {success_count}/{len(real_data)} companies")
    print(f"📋 Total roles inserted: {total_roles}")
    
    # Verify the data
    print("\n🔍 Verifying database contents...")
    try:
        companies = db.get_companies()
        print(f"📋 Total companies in database: {len(companies)}")
        
        stats = db.get_placement_stats()
        if stats:
            print(f"📊 Placement statistics:")
            print(f"   - Companies: {stats.get('company_count', 0)}")
            print(f"   - Roles: {stats.get('role_count', 0)}")
            print(f"   - Avg Salary Range: ₹{stats.get('avg_min_salary', 0):.1f} - ₹{stats.get('avg_max_salary', 0):.1f} LPA")
        
        # Show specialization breakdown
        if stats.get('specialization_breakdown'):
            print(f"\n🎯 Specialization Breakdown:")
            for spec in stats['specialization_breakdown']:
                print(f"   - {spec['specialization']}: {spec['role_count']} roles, ₹{spec['avg_min']:.1f}-{spec['avg_max']:.1f} LPA")
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
    
    print("\n🎉 Real data population complete!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("2. Start the enhanced Streamlit UI: streamlit run ui/streamlit_app_enhanced.py")
    print("3. Test the new endpoints and features!")
    print("\n📋 Your Real Companies:")
    for company in real_data:
        print(f"   - {company['company_name']}: {company.get('industry', 'N/A')}")

if __name__ == "__main__":
    populate_real_data()
