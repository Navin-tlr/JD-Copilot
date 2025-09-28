#!/usr/bin/env python3
"""Audit LLM role type classifications against source content to detect hallucination"""

import sys
import sqlite3
import json
import os
from pathlib import Path
import re
sys.path.insert(0, '.')

def read_pdf_preview(pdf_path):
    """Get preview text from PDF file for manual verification"""
    try:
        # Use the same approach as pipeline for consistency
        from ingest.pipeline import _read_text_from_path
        text = _read_text_from_path(Path(pdf_path))
        return text[:2000]  # First 2000 chars for verification
    except Exception as e:
        return f"Error reading PDF: {e}"

def load_structured_data(json_path):
    """Load structured extraction data"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def get_db_classifications():
    """Get all role classifications from database"""
    from app.database import PlacementDatabase
    db = PlacementDatabase()
    
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        roles = cursor.execute("""
            SELECT r.id, r.title, r.specialization, r.role_types, c.company_name
            FROM roles r
            JOIN companies c ON r.company_id = c.id
            WHERE r.role_types IS NOT NULL
            ORDER BY r.id DESC
        """).fetchall()
    
    return roles

def verify_classification_grounding(role_title, specialization, role_types, source_text, structured_data):
    """Verify that each role type classification is grounded in source material"""
    if not role_types:
        return True, []
    
    try:
        types_list = json.loads(role_types) if isinstance(role_types, str) else role_types
    except:
        return False, ["Invalid JSON format for role_types"]
    
    issues = []
    source_lower = source_text.lower()
    
    # Get role-specific content from structured data
    role_content = ""
    if structured_data and 'roles' in structured_data:
        for role in structured_data['roles']:
            if role.get('title') == role_title:
                # Collect all text content for this role
                content_parts = []
                for field in ['responsibilities', 'requirements', 'skills']:
                    if field in role and role[field]:
                        if isinstance(role[field], list):
                            content_parts.extend(role[field])
                        else:
                            content_parts.append(str(role[field]))
                role_content = ' '.join(content_parts).lower()
                break
    
    combined_text = (source_lower + " " + role_content).strip()
    
    for role_type in types_list:
        if not isinstance(role_type, str):
            continue
            
        role_type_lower = role_type.lower()
        words = [w for w in re.split(r'\W+', role_type_lower) if w and len(w) > 2]
        
        # Check if the role type phrase exists directly
        phrase_found = role_type_lower in combined_text
        
        # Check if all significant words from the role type exist
        word_coverage = sum(1 for word in words if word in combined_text) / max(1, len(words)) if words else 0
        
        # Grounding verification
        if not phrase_found and word_coverage < 0.7:  # At least 70% word coverage required
            issues.append(f"'{role_type}' not grounded (phrase found: {phrase_found}, word coverage: {word_coverage:.1%})")
    
    return len(issues) == 0, issues

def main():
    print("🔍 AUDITING LLM ROLE TYPE CLASSIFICATIONS FOR HALLUCINATION")
    print("=" * 60)
    
    # Get all classified roles from database
    roles = get_db_classifications()
    
    if not roles:
        print("❌ No classified roles found in database")
        return
    
    print(f"Found {len(roles)} classified roles to audit\n")
    
    # Map company names to source files
    pdf_dir = Path("data/jds")
    json_dir = Path("data/structured_json")
    
    company_file_map = {}
    for pdf_file in pdf_dir.glob("*.pdf"):
        # Try to match company names
        if "accorian" in pdf_file.name.lower():
            company_file_map["Accorian"] = pdf_file
        elif "madison" in pdf_file.name.lower():
            company_file_map["Madison PR"] = pdf_file
        elif "masters" in pdf_file.name.lower():
            company_file_map["Masters' Union"] = pdf_file
        elif "target" in pdf_file.name.lower() or "apprentice" in pdf_file.name.lower():
            company_file_map["Target"] = pdf_file
        elif "tap" in pdf_file.name.lower() or "business development" in pdf_file.name.lower():
            company_file_map["Tap Academy"] = pdf_file
        elif "mill" in pdf_file.name.lower() or "finance" in pdf_file.name.lower():
            company_file_map["Mill Story"] = pdf_file
    
    # Also check docx files
    for docx_file in pdf_dir.glob("*.docx"):
        if "alstom" in docx_file.name.lower():
            company_file_map["Alstom"] = docx_file  # This might not be classified due to null company_name
    
    total_issues = 0
    total_classifications = 0
    
    for role_id, title, specialization, role_types, company_name in roles:
        print(f"🔎 ROLE ID {role_id}: {title}")
        print(f"   Company: {company_name}")
        print(f"   Specialization: {specialization}")
        
        try:
            types_list = json.loads(role_types) if isinstance(role_types, str) else role_types
            print(f"   Classifications: {types_list}")
        except:
            print(f"   Classifications: [INVALID JSON] {role_types}")
            total_issues += 1
            continue
        
        # Find source file
        source_file = company_file_map.get(company_name)
        if not source_file:
            print(f"   ⚠️  Source file not found for {company_name}")
            total_issues += 1
            continue
        
        # Read source content
        source_text = read_pdf_preview(source_file)
        if "Error reading" in source_text:
            print(f"   ❌ Could not read source file: {source_text}")
            total_issues += 1
            continue
        
        # Load structured data
        json_file = json_dir / f"{source_file.stem}_structured.json"
        structured_data = load_structured_data(json_file)
        
        # Verify grounding
        is_grounded, issues = verify_classification_grounding(
            title, specialization, role_types, source_text, structured_data
        )
        
        total_classifications += len(types_list) if isinstance(types_list, list) else 1
        
        if is_grounded:
            print(f"   ✅ All classifications grounded in source material")
        else:
            print(f"   ❌ POTENTIAL HALLUCINATION DETECTED:")
            for issue in issues:
                print(f"      - {issue}")
            total_issues += len(issues)
        
        # Show brief source preview for manual verification
        print(f"   📄 Source preview: {source_text[:200]}...")
        print("-" * 60)
    
    print(f"\n📊 AUDIT SUMMARY")
    print(f"Total roles audited: {len(roles)}")
    print(f"Total classifications: {total_classifications}")
    print(f"Potential issues found: {total_issues}")
    
    if total_issues == 0:
        print("🎉 NO HALLUCINATION DETECTED - All classifications are grounded!")
    else:
        print(f"⚠️  {total_issues} potential hallucinations detected - manual review recommended")

if __name__ == "__main__":
    main()
