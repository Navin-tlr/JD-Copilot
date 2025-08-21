#!/usr/bin/env python3
"""
Show Specialization Segregation
Displays how roles are segregated by MBA specializations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import PlacementDatabase

def show_specialization_segregation():
    """Show how roles are segregated by MBA specializations"""
    print("🎯 MBA Specialization Segregation")
    print("=" * 50)
    
    # Initialize database
    db = PlacementDatabase()
    
    try:
        # Get all roles with specializations
        roles = db.get_all_roles()
        
        # Group by specialization
        specialization_groups = {}
        for role in roles:
            spec = role.get('specialization', 'UNKNOWN')
            if spec not in specialization_groups:
                specialization_groups[spec] = []
            specialization_groups[spec].append(role)
        
        # Display by specialization
        print(f"📊 Total Roles: {len(roles)}")
        print(f"🎯 Specializations Found: {len(specialization_groups)}")
        print()
        
        for specialization, role_list in specialization_groups.items():
            print(f"🔹 {specialization} Specialization ({len(role_list)} roles):")
            for role in role_list:
                company = role.get('company_name', 'N/A')
                title = role.get('title', 'N/A')
                location = role.get('location', 'N/A')
                print(f"   • {company}: {title}")
                if location:
                    print(f"     📍 Location: {location}")
            print()
        
        # Test specialization-specific queries
        print("🔍 Testing Specialization-Specific Queries:")
        print("-" * 40)
        
        specializations = ["HR", "MARKETING", "FINANCE", "OPERATIONS", "BUSINESS ANALYTICS"]
        for spec in specializations:
            try:
                insights = db.get_specialization_insights(spec)
                if insights and insights.get('stats', {}).get('company_count', 0) > 0:
                    stats = insights['stats']
                    print(f"   ✅ {spec}: {stats['company_count']} companies, {stats['role_count']} roles")
                else:
                    print(f"   ⚠️ {spec}: No roles found")
            except Exception as e:
                print(f"   ❌ {spec}: Error - {e}")
        
        # Test company comparison by specialization
        print(f"\n🏢 Company Specialization Analysis:")
        print("-" * 40)
        
        companies = db.get_companies()
        for company in companies:
            company_name = company['company_name']
            company_roles = db.get_company_roles(company_name)
            if company_roles:
                specs = set()
                for role in company_roles:
                    # Extract specialization from role data
                    if hasattr(role, 'get'):
                        spec = role.get('specialization')
                    else:
                        # Handle tuple format
                        spec = role[4] if len(role) > 4 else 'UNKNOWN'
                    if spec:
                        specs.add(spec)
                
                print(f"   {company_name}: {', '.join(specs) if specs else 'No specialization'}")
        
    except Exception as e:
        print(f"❌ Error analyzing specializations: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 Specialization Analysis Complete!")
    print(f"\nYour MBA Specializations:")
    print("   • HR")
    print("   • MARKETING") 
    print("   • FINANCE")
    print("   • LEAN OPERATION AND SYSTEMS")
    print("   • BUSINESS ANALYTICS")

if __name__ == "__main__":
    show_specialization_segregation()
