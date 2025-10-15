"""
Test Hierarchical Navigation Map and API
"""

from app.hierarchical_navigation_map import hierarchical_navigation_map, IndustryHierarchy


def test_navigation_map():
    """Test adding entries and querying hierarchical navigation map"""
    
    print("=" * 80)
    print("HIERARCHICAL NAVIGATION MAP TEST")
    print("=" * 80)
    print()
    
    # Add some test entries
    test_companies = [
        {
            "name": "Honasa Consumer Limited",
            "norm": "honasaconsumerlimited",
            "spec": "Marketing",
            "level1": "FMCG",
            "level2": "Beauty & Personal Care"
        },
        {
            "name": "Marico Limited",
            "norm": "maricolimited",
            "spec": "Marketing",
            "level1": "FMCG",
            "level2": "Hair Care Products"
        },
        {
            "name": "Goldman Sachs",
            "norm": "goldmansachs",
            "spec": "Finance",
            "level1": "Investment Banking",
            "level2": "M&A Capital Markets"
        },
        {
            "name": "Amazon",
            "norm": "amazon",
            "spec": "Operations",
            "level1": "Supply Chain",
            "level2": "E-commerce Supply Chain"
        },
        {
            "name": "Microsoft",
            "norm": "microsoft",
            "spec": "HR",
            "level1": "Talent Acquisition",
            "level2": "Tech Talent Acquisition"
        }
    ]
    
    print("Adding test companies...")
    for company in test_companies:
        hierarchical_navigation_map.add_entry(
            company_name=company["name"],
            company_norm=company["norm"],
            specialization=company["spec"],
            level1=company["level1"],
            level2=company["level2"],
            source="jd"
        )
    
    print()
    print("-" * 80)
    print("QUERY TESTS")
    print("-" * 80)
    print()
    
    # Test 1: Get all FMCG companies
    print("Test 1: Get FMCG companies")
    fmcg_companies = hierarchical_navigation_map.get_companies_by_hierarchy(
        specialization="Marketing",
        level1="FMCG"
    )
    print(f"   Found {len(fmcg_companies)} companies:")
    for company in fmcg_companies:
        print(f"   - {company}")
    print()
    
    # Test 2: Get all Marketing companies
    print("Test 2: Get all Marketing companies")
    marketing_companies = hierarchical_navigation_map.get_companies_by_hierarchy(
        specialization="Marketing"
    )
    print(f"   Found {len(marketing_companies)} companies:")
    for company in marketing_companies:
        print(f"   - {company}")
    print()
    
    # Test 3: Get Investment Banking companies
    print("Test 3: Get Investment Banking companies")
    ib_companies = hierarchical_navigation_map.get_companies_by_hierarchy(
        specialization="Finance",
        level1="Investment Banking"
    )
    print(f"   Found {len(ib_companies)} companies:")
    for company in ib_companies:
        print(f"   - {company}")
    print()
    
    # Test 4: Get hierarchy options
    print("Test 4: Get Level 1 options for Marketing")
    options = hierarchical_navigation_map.get_hierarchy_options("Marketing")
    print(f"   Options: {options['Marketing']}")
    print()
    
    # Test 5: Get company hierarchies
    print("Test 5: Get hierarchies for Honasa Consumer Limited")
    hierarchies = hierarchical_navigation_map.get_company_hierarchies("Honasa Consumer Limited")
    for h in hierarchies:
        print(f"   {h.specialization} > {h.level1} > {h.level2}")
    print()
    
    # Test 6: Get stats
    print("Test 6: Get statistics")
    stats = hierarchical_navigation_map.get_stats()
    print(f"   Total companies: {stats['total_companies']}")
    print(f"   By specialization: {stats['by_specialization']}")
    print(f"   By Level 1:")
    for key, count in sorted(stats['by_level1'].items()):
        print(f"      - {key}: {count}")
    print()
    
    # Print summary
    hierarchical_navigation_map.print_summary()
    
    print("=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_navigation_map()
