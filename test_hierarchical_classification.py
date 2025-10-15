"""
Test Hierarchical Industry Classification System
"""

import asyncio
from app.industry_classifier import industry_classifier


async def test_classifications():
    """Test industry classification on various job descriptions"""
    
    test_cases = [
        {
            "name": "FMCG Marketing",
            "specialization": "Marketing",  # Already extracted
            "jd": """
            Honasa Consumer Limited is looking for Brand Managers.
            
            Responsibilities:
            - Manage FMCG brand portfolio
            - Develop marketing strategies for consumer goods
            - Work on product launches for beauty and personal care
            
            Requirements:
            - MBA in Marketing
            - Experience in FMCG sector
            - Strong brand management skills
            """,
            "context": {"company": "Honasa Consumer", "role_title": "Brand Manager"}
        },
        {
            "name": "Investment Banking",
            "specialization": "Finance",  # Already extracted
            "jd": """
            Goldman Sachs is hiring Investment Banking Analysts.
            
            Responsibilities:
            - M&A deal execution
            - Financial modeling and valuation
            - Client pitch preparation
            - Capital markets transactions
            
            Requirements:
            - MBA in Finance
            - Strong analytical skills
            - Knowledge of corporate finance
            """,
            "context": {"company": "Goldman Sachs", "role_title": "Investment Banking Analyst"}
        },
        {
            "name": "Supply Chain Operations",
            "specialization": "Operations",  # Already extracted
            "jd": """
            Amazon is looking for Supply Chain Managers.
            
            Responsibilities:
            - Manage logistics and warehousing
            - Optimize supply chain processes
            - Coordinate with vendors and partners
            - Implement ERP systems
            
            Requirements:
            - MBA in Operations
            - Experience in supply chain management
            - Knowledge of logistics and procurement
            """,
            "context": {"company": "Amazon", "role_title": "Supply Chain Manager"}
        },
        {
            "name": "HR Talent Acquisition",
            "specialization": "HR",  # Already extracted
            "jd": """
            Microsoft is hiring Talent Acquisition Specialists.
            
            Responsibilities:
            - End-to-end recruitment
            - Campus hiring strategy
            - Employer branding
            - Candidate experience management
            
            Requirements:
            - MBA in HR
            - Experience in talent acquisition
            - Strong people skills
            """,
            "context": {"company": "Microsoft", "role_title": "Talent Acquisition Specialist"}
        },
        {
            "name": "Business Analytics",
            "specialization": "Analytics",  # Already extracted
            "jd": """
            Accenture is looking for Business Analysts.
            
            Responsibilities:
            - Data analysis and insights
            - Build dashboards and reports
            - Predictive modeling
            - Business intelligence implementation
            
            Requirements:
            - MBA in Analytics
            - Strong SQL and Python skills
            - Data visualization expertise
            """,
            "context": {"company": "Accenture", "role_title": "Business Analyst"}
        }
    ]
    
    print("=" * 80)
    print("HIERARCHICAL INDUSTRY CLASSIFICATION TEST")
    print("(Specialization → Level 1 → Level 2)")
    print("=" * 80)
    print()
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"Company: {test['context']['company']}")
        print(f"Role: {test['context']['role_title']}")
        print(f"Specialization: {test['specialization']} (already extracted)")
        print("-" * 80)
        
        try:
            # Pass specialization to classifier
            classification = industry_classifier.classify(
                job_description=test['jd'],
                specialization=test['specialization'],
                context=test['context']
            )
            
            print(f"✅ Level 1: {classification.level1}")
            print(f"✅ Level 2: {classification.level2}")
            print(f"🎯 Confidence: {classification.confidence:.2%}")
            print(f"💡 Reasoning: {classification.reasoning}")
            
            # Verify format for metadata
            metadata = industry_classifier.format_for_metadata(classification)
            print(f"\n📊 Metadata format:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
            
        except Exception as e:
            print(f"❌ Classification failed: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        print("=" * 80)
        print()


async def test_query_inference():
    """Test inferring Level 1 from user queries"""
    
    from app.agents.orchestrator import AgentOrchestrator
    
    queries = [
        "How many companies came for FMCG?",
        "List investment banking companies",
        "Supply chain roles",
        "Talent acquisition positions",
        "Data science companies"
    ]
    
    print("=" * 80)
    print("QUERY INFERENCE TEST")
    print("(Infers Level 1 subcategory like FMCG, Investment Banking, etc.)")
    print("=" * 80)
    print()
    
    orchestrator = AgentOrchestrator()
    
    for query in queries:
        print(f"Query: {query}")
        print("-" * 80)
        
        try:
            # Use orchestrator's inference method
            level1 = orchestrator._infer_level1_category(query, query)
            
            if level1:
                print(f"✅ Inferred Level 1: {level1}")
            else:
                print(f"⚠️ No Level 1 inferred (too general)")
            
        except Exception as e:
            print(f"❌ Inference failed: {e}")
            import traceback
            traceback.print_exc()
        
        print()


async def main():
    """Run all tests"""
    print("\n🚀 Starting Hierarchical Classification Tests...\n")
    
    await test_classifications()
    await test_query_inference()
    
    print("\n✅ All tests complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
