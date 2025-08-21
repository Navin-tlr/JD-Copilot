#!/usr/bin/env python3
"""
Populate Database with LLM-Extracted Data
Loads all LLM-extracted structured JSON files into the SQLite database
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import PlacementDatabase

def populate_database_with_llm_data():
    """Populate database with LLM-extracted structured data"""
    print("🚀 Populating Database with LLM-Extracted Data")
    print("=" * 60)
    
    # Initialize database
    db = PlacementDatabase()
    
    # Get all LLM-extracted JSON files
    json_dir = Path("data/structured_json")
    llm_files = list(json_dir.glob("*_structured.json"))
    
    if not llm_files:
        print("❌ No LLM-extracted JSON files found!")
        return
    
    print(f"📁 Found {len(llm_files)} LLM-extracted files to process")
    
    # Process each file
    successful_inserts = []
    failed_inserts = []
    
    for json_file in llm_files:
        print(f"\n📄 Processing: {json_file.name}")
        print("-" * 40)
        
        try:
            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"   🏢 Company: {data.get('company_name', 'N/A')}")
            print(f"   📅 Year: {data.get('year', 'N/A')}")
            print(f"   🎯 Roles: {len(data.get('roles', []))}")
            
            # Insert into database
            company_id = db.insert_company_extraction(data)
            
            if company_id:
                print(f"   ✅ Successfully inserted with ID: {company_id}")
                successful_inserts.append({
                    "file": json_file.name,
                    "company": data.get('company_name'),
                    "company_id": company_id,
                    "roles": len(data.get('roles', []))
                })
            else:
                print(f"   ❌ Failed to insert into database")
                failed_inserts.append(json_file.name)
                
        except Exception as e:
            print(f"   ❌ Error processing {json_file.name}: {e}")
            failed_inserts.append(json_file.name)
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n🎯 Database Population Complete!")
    print(f"✅ Successfully inserted: {len(successful_inserts)}/{len(llm_files)} files")
    
    if successful_inserts:
        print(f"\n📊 Inserted Companies:")
        for item in successful_inserts:
            print(f"   - {item['company']}: {item['roles']} roles (ID: {item['company_id']})")
    
    if failed_inserts:
        print(f"\n❌ Failed Files:")
        for file in failed_inserts:
            print(f"   - {file}")
    
    # Verify database contents
    print(f"\n🔍 Verifying Database Contents:")
    try:
        companies = db.get_companies()
        print(f"   Total companies: {len(companies)}")
        
        roles = db.get_all_roles()
        print(f"   Total roles: {len(roles)}")
        
        skills = db.get_all_skills()
        print(f"   Total skills: {len(skills)}")
        
        requirements = db.get_all_requirements()
        print(f"   Total requirements: {len(requirements)}")
        
    except Exception as e:
        print(f"   ❌ Error verifying database: {e}")
    
    print(f"\nNext steps:")
    print("1. Start the FastAPI server to test the new data")
    print("2. Test the Streamlit UI with LLM-extracted data")
    print("3. Compare query performance with new structured data")

def compare_llm_vs_manual():
    """Compare LLM extraction vs manual extraction quality"""
    print(f"\n🔍 Comparing LLM vs Manual Extraction")
    print("=" * 40)
    
    # Load manual data
    manual_file = Path("data/structured_json/real_data_manual.json")
    if manual_file.exists():
        with open(manual_file, 'r', encoding='utf-8') as f:
            manual_data = json.load(f)
        
        print(f"📊 Manual Data Summary:")
        print(f"   Companies: {len(manual_data)}")
        total_manual_roles = sum(len(company.get('roles', [])) for company in manual_data)
        print(f"   Total Roles: {total_manual_roles}")
    
    # Load LLM data
    json_dir = Path("data/structured_json")
    llm_files = list(json_dir.glob("*_structured.json"))
    
    print(f"\n📊 LLM Data Summary:")
    print(f"   Files: {len(llm_files)}")
    
    total_llm_roles = 0
    for json_file in llm_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_llm_roles += len(data.get('roles', []))
        except:
            pass
    
    print(f"   Total Roles: {total_llm_roles}")
    
    print(f"\n📈 Comparison:")
    print(f"   Manual Roles: {total_manual_roles}")
    print(f"   LLM Roles: {total_llm_roles}")
    print(f"   Difference: {total_llm_roles - total_manual_roles}")

if __name__ == "__main__":
    # First compare the data
    compare_llm_vs_manual()
    
    # Then populate the database
    print(f"\n" + "="*60)
    populate_database_with_llm_data()
