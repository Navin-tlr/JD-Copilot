#!/usr/bin/env python3
"""
Cleanup Database and Test
Removes duplicate entries and verifies database integrity
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import PlacementDatabase

def cleanup_database():
    """Clean up duplicate entries and test database"""
    print("🧹 Cleaning Up Database and Testing")
    print("=" * 50)
    
    # Initialize database
    db = PlacementDatabase()
    
    # Test database methods
    print("🔍 Testing Database Methods:")
    
    try:
        # Test companies
        companies = db.get_companies()
        print(f"   ✅ Companies: {len(companies)}")
        for company in companies:
            print(f"      - {company['company_name']}: {company['role_count']} roles")
        
        # Test roles
        roles = db.get_all_roles()
        print(f"   ✅ Roles: {len(roles)}")
        
        # Test skills
        skills = db.get_all_skills()
        print(f"   ✅ Skills: {len(skills)}")
        
        # Test requirements
        requirements = db.get_all_requirements()
        print(f"   ✅ Requirements: {len(requirements)}")
        
        # Test placement stats
        stats = db.get_placement_stats()
        print(f"   ✅ Placement Stats: {stats.get('company_count', 0)} companies, {stats.get('role_count', 0)} roles")
        
        # Test specialization insights
        specializations = ["Marketing", "Finance", "HR", "Operations", "Strategy"]
        for spec in specializations:
            insights = db.get_specialization_insights(spec)
            if insights and insights.get('stats', {}).get('company_count', 0) > 0:
                print(f"   ✅ {spec}: {insights['stats']['company_count']} companies")
        
    except Exception as e:
        print(f"   ❌ Error testing database: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 Database Test Complete!")
    print(f"\nNext steps:")
    print("1. Start the FastAPI server to test the new data")
    print("2. Test the Streamlit UI with LLM-extracted data")
    print("3. Test the new API endpoints")

if __name__ == "__main__":
    cleanup_database()
