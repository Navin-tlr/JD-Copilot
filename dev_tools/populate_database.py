#!/usr/bin/env python3
"""
Database Population Script
Populates the SQLite database with structured data from existing JSON files
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import PlacementDatabase
from ingest.structured_extractor import CompanyExtraction

def load_existing_json_files() -> List[Dict[str, Any]]:
    """Load existing structured JSON files if they exist"""
    json_dir = Path("data/structured_json")
    if not json_dir.exists():
        print("No existing structured JSON files found.")
        return []
    
    data = []
    for json_file in json_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                file_data["source_file"] = json_file.name
                data.append(file_data)
            print(f"✅ Loaded: {json_file.name}")
        except Exception as e:
            print(f"❌ Failed to load {json_file.name}: {e}")
    
    return data

def create_sample_data() -> List[Dict[str, Any]]:
    """Create sample structured data for testing with MBA specializations"""
    sample_data = [
        {
            "company_name": "Oracle",
            "year": 2024,
            "company_type": "Technology",
            "industry": "Software",
            "location": "Bangalore",
            "batch_year": "2024-2025",
            "roles": [
                {
                    "title": "Marketing Analyst",
                    "specialization": "Marketing",
                    "location": "Bangalore",
                    "salary_min_lpa": 8.0,
                    "salary_max_lpa": 10.0,
                    "expected_hires": 5,
                    "skills": ["branding", "market research", "digital marketing", "analytics", "campaign management"],
                    "requirements": ["MBA in Marketing", "Strong analytical skills", "Digital marketing experience"],
                    "responsibilities": ["Market analysis", "Brand strategy", "Digital campaigns", "Performance tracking"]
                },
                {
                    "title": "Financial Associate",
                    "specialization": "Finance",
                    "location": "Bangalore",
                    "salary_min_lpa": 9.0,
                    "salary_max_lpa": 12.0,
                    "expected_hires": 3,
                    "skills": ["financial modeling", "excel", "accounting", "budgeting", "compliance"],
                    "requirements": ["MBA in Finance", "CFA preferred", "Financial analysis experience"],
                    "responsibilities": ["Financial planning", "Budget management", "Compliance reporting", "Risk analysis"]
                }
            ]
        },
        {
            "company_name": "Target India (TII)",
            "year": 2024,
            "company_type": "Retail",
            "industry": "E-commerce",
            "location": "Bangalore",
            "batch_year": "2024-2025",
            "roles": [
                {
                    "title": "Apprentice – Media Operations",
                    "specialization": "Marketing",
                    "location": "Bangalore",
                    "salary_min_lpa": 4.5,
                    "salary_max_lpa": 6.0,
                    "expected_hires": 10,
                    "skills": ["marketing", "media operations", "digital marketing", "analytics"],
                    "requirements": ["Master's in management with Marketing specialization", "CGPA requirements", "No backlogs"],
                    "responsibilities": ["Media operations", "Digital marketing", "Analytics", "Team collaboration"]
                }
            ]
        },
        {
            "company_name": "Microsoft",
            "year": 2024,
            "company_type": "Technology",
            "industry": "Software",
            "location": "Hyderabad",
            "batch_year": "2024-2025",
            "roles": [
                {
                    "title": "Product Manager",
                    "specialization": "Strategy",
                    "location": "Hyderabad",
                    "salary_min_lpa": 15.0,
                    "salary_max_lpa": 22.0,
                    "expected_hires": 8,
                    "skills": ["product strategy", "market analysis", "user research", "data analysis", "stakeholder management"],
                    "requirements": ["MBA from top-tier institute", "Product management experience", "Technical background preferred"],
                    "responsibilities": ["Product strategy", "User research", "Feature development", "Cross-functional collaboration"]
                },
                {
                    "title": "HR Business Partner",
                    "specialization": "HR",
                    "location": "Hyderabad",
                    "salary_min_lpa": 12.0,
                    "salary_max_lpa": 18.0,
                    "expected_hires": 4,
                    "skills": ["employee relations", "talent acquisition", "performance management", "organizational development"],
                    "requirements": ["MBA in HR", "HR experience", "Strong communication skills"],
                    "responsibilities": ["Employee relations", "Talent development", "Performance management", "Culture building"]
                }
            ]
        },
        {
            "company_name": "Unacademy",
            "year": 2024,
            "company_type": "Education",
            "industry": "EdTech",
            "location": "Mumbai",
            "batch_year": "2024-2025",
            "roles": [
                {
                    "title": "Content Creator",
                    "specialization": "Marketing",
                    "location": "Mumbai",
                    "salary_min_lpa": 6.0,
                    "salary_max_lpa": 10.0,
                    "expected_hires": 15,
                    "skills": ["content creation", "education", "communication", "subject expertise", "digital marketing"],
                    "requirements": ["Subject matter expertise", "Communication skills", "Teaching experience"],
                    "responsibilities": ["Content creation", "Course development", "Student engagement", "Marketing collaboration"]
                }
            ]
        },
        {
            "company_name": "Razorpay",
            "year": 2024,
            "company_type": "FinTech",
            "industry": "Financial Services",
            "location": "Bangalore",
            "batch_year": "2024-2025",
            "roles": [
                {
                    "title": "Product Manager",
                    "specialization": "Strategy",
                    "location": "Bangalore",
                    "salary_min_lpa": 15.0,
                    "salary_max_lpa": 25.0,
                    "expected_hires": 6,
                    "skills": ["product management", "fintech", "user experience", "data analysis", "strategy"],
                    "requirements": ["MBA or relevant degree", "Product management experience", "Fintech knowledge"],
                    "responsibilities": ["Product strategy", "User research", "Feature development", "Stakeholder management"]
                },
                {
                    "title": "Operations Manager",
                    "specialization": "Operations",
                    "location": "Bangalore",
                    "salary_min_lpa": 12.0,
                    "salary_max_lpa": 18.0,
                    "expected_hires": 4,
                    "skills": ["process optimization", "supply chain", "operations management", "data analysis", "team leadership"],
                    "requirements": ["MBA in Operations", "Operations experience", "Process improvement skills"],
                    "responsibilities": ["Process optimization", "Team management", "Performance monitoring", "Continuous improvement"]
                }
            ]
        },
        {
            "company_name": "BCG",
            "year": 2024,
            "company_type": "Consulting",
            "industry": "Management Consulting",
            "location": "Mumbai",
            "batch_year": "2024-2025",
            "roles": [
                {
                    "title": "Consultant",
                    "specialization": "Strategy",
                    "location": "Mumbai",
                    "salary_min_lpa": 18.0,
                    "salary_max_lpa": 30.0,
                    "expected_hires": 12,
                    "skills": ["consulting", "strategy", "analytics", "problem-solving", "client management"],
                    "requirements": ["Top-tier MBA", "Analytical skills", "Communication skills", "Consulting experience preferred"],
                    "responsibilities": ["Client engagement", "Strategy development", "Data analysis", "Presentation", "Team leadership"]
                }
            ]
        }
    ]
    
    return sample_data

def populate_database(data: List[Dict[str, Any]]) -> None:
    """Populate the database with structured data"""
    db = PlacementDatabase()
    
    success_count = 0
    total_count = len(data)
    
    print(f"\n🚀 Populating database with {total_count} companies...")
    
    for company_data in data:
        try:
            success = db.insert_company_extraction(company_data)
            if success:
                success_count += 1
                print(f"✅ Inserted: {company_data['company_name']}")
            else:
                print(f"❌ Failed to insert: {company_data['company_name']}")
        except Exception as e:
            print(f"❌ Error inserting {company_data['company_name']}: {e}")
    
    print(f"\n📊 Database Population Complete!")
    print(f"✅ Successfully inserted: {success_count}/{total_count} companies")
    
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
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")

def main():
    """Main function"""
    print("🎯 JD-Copilot Database Population Tool")
    print("=" * 50)
    
    # Try to load existing data first
    existing_data = load_existing_json_files()
    
    if existing_data:
        print(f"\n📁 Found {len(existing_data)} existing structured files")
        use_existing = input("Use existing data? (y/n): ").lower().strip() == 'y'
        
        if use_existing:
            data_to_use = existing_data
        else:
            data_to_use = create_sample_data()
            print("\n📝 Using sample data instead")
    else:
        print("\n📝 No existing data found, using sample data")
        data_to_use = create_sample_data()
    
    # Populate database
    populate_database(data_to_use)
    
    print("\n🎉 Database population complete!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("2. Start the enhanced Streamlit UI: streamlit run ui/streamlit_app_enhanced.py")
    print("3. Test the new endpoints and features!")

if __name__ == "__main__":
    main()
