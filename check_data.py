#!/usr/bin/env python3

from app.database import PlacementDatabase

def check_data():
    db = PlacementDatabase()
    
    print("=== COMPANIES ===")
    companies = db.get_companies()
    print(f"Total companies: {len(companies)}")
    for c in companies:
        print(f"- {c['company_name']}")
    
    print("\n=== ROLES BY SPECIALIZATION ===")
    roles = db.get_all_roles()
    print(f"Total roles: {len(roles)}")
    
    marketing_count = 0
    hr_count = 0
    other_count = 0
    
    for r in roles:
        spec = r['specialization']
        if spec == 'MARKETING':
            marketing_count += 1
            print(f"MARKETING: {r['title']} at {r['company_name']}")
        elif spec == 'HR':
            hr_count += 1
            print(f"HR: {r['title']} at {r['company_name']}")
        else:
            other_count += 1
            print(f"{spec}: {r['title']} at {r['company_name']}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Marketing roles: {marketing_count}")
    print(f"HR roles: {hr_count}")
    print(f"Other roles: {other_count}")
    print(f"Total roles: {len(roles)}")
    
    # Check which companies have marketing roles
    marketing_companies = set()
    for r in roles:
        if r['specialization'] == 'MARKETING':
            marketing_companies.add(r['company_name'])
    
    print(f"\n=== COMPANIES WITH MARKETING ROLES ===")
    print(f"Count: {len(marketing_companies)}")
    for company in marketing_companies:
        print(f"- {company}")

if __name__ == "__main__":
    check_data()
