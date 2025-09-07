"""
Real RAG System Evaluation
Uses the actual RAG system and compares answers with expected results
"""

from app.agent import route_query
import json
from datetime import datetime

def evaluate_real_rag_system():
    """Evaluate the real RAG system with actual queries and expected answers"""
    
    print("🧪 Real RAG System Evaluation")
    print("=" * 50)
    
    # Test cases with expected answers
    test_cases = [
        {
            "query": "How many companies are offering finance roles?",
            "expected_answer": "1 company (Mill Story) is offering finance roles",
            "description": "Should find 1 company with finance roles"
        },
        {
            "query": "Which companies are hiring for HR roles?",
            "expected_answer": "Accorian is hiring for HR roles",
            "description": "Should find Accorian with HR/People Operations role"
        },
        {
            "query": "Which companies are hiring for PR or communications roles?",
            "expected_answer": "Madison PR is hiring for PR/communications roles",
            "description": "Should find Madison PR with PR/communications role"
        },
        {
            "query": "Are there any admission-related jobs?",
            "expected_answer": "Yes, Masters' Union has admission-related jobs",
            "description": "Should find Masters' Union with Admission Counselor role"
        },
        {
            "query": "What finance-related tasks are mentioned?",
            "expected_answer": "Finance tasks include accounting, P&L, budgeting, expense tracking",
            "description": "Should list finance tasks from job descriptions"
        },
        {
            "query": "What do HR operations jobs involve?",
            "expected_answer": "HR operations involve employee lifecycle management, compliance, engagement",
            "description": "Should describe HR operations responsibilities"
        },
        {
            "query": "What opportunities does TAP Academy offer?",
            "expected_answer": "TAP Academy offers lead generation, partnership development, LinkedIn outreach",
            "description": "Should list TAP Academy opportunities"
        },
        {
            "query": "List all the tools/software mentioned in the JDs",
            "expected_answer": "Tools mentioned include Excel, Google Sheets, HRMS, CRM, LinkedIn",
            "description": "Should list tools mentioned in job descriptions"
        },
        {
            "query": "Which jobs are specifically internships?",
            "expected_answer": "Mill Story offers a Finance Internship",
            "description": "Should find Mill Story Finance Internship"
        },
        {
            "query": "Which jobs are based in Bangalore?",
            "expected_answer": "Jobs in Bangalore include Mill Story, TAP Academy, Madison PR",
            "description": "Should find companies with Bangalore locations"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📊 Test {i+1}: {test_case['query']}")
        print(f"Expected: {test_case['expected_answer']}")
        
        try:
            # Get actual response from the real RAG system
            actual_response = route_query(test_case['query'])
            print(f"Actual: {actual_response}")
            
            # Simple evaluation: check if expected answer is contained in actual response
            expected_lower = test_case['expected_answer'].lower()
            actual_lower = actual_response.lower()
            
            # Check for key terms from expected answer
            expected_terms = expected_lower.split()
            found_terms = sum(1 for term in expected_terms if term in actual_lower)
            match_score = found_terms / len(expected_terms) if expected_terms else 0
            
            # Check if the answer makes sense (not an error message)
            is_error = any(error in actual_lower for error in ['error', 'failed', 'not available', 'query result: [('])
            
            # Determine if test passed
            passed = match_score > 0.3 and not is_error
            
            print(f"Match Score: {match_score:.2f}")
            print(f"Is Error: {is_error}")
            print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
            
            results.append({
                "test_number": i + 1,
                "query": test_case['query'],
                "expected_answer": test_case['expected_answer'],
                "actual_response": actual_response,
                "match_score": match_score,
                "is_error": is_error,
                "passed": passed,
                "description": test_case['description']
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "test_number": i + 1,
                "query": test_case['query'],
                "expected_answer": test_case['expected_answer'],
                "actual_response": f"Error: {str(e)}",
                "match_score": 0.0,
                "is_error": True,
                "passed": False,
                "description": test_case['description']
            })
    
    # Calculate overall results
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    avg_match_score = sum(r['match_score'] for r in results) / total_tests
    error_tests = sum(1 for r in results if r['is_error'])
    
    print(f"\n" + "=" * 50)
    print(f"📊 OVERALL RESULTS")
    print(f"=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed Tests: {passed_tests}")
    print(f"Failed Tests: {total_tests - passed_tests}")
    print(f"Error Tests: {error_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Average Match Score: {avg_match_score:.2f}")
    
    # Show detailed results
    print(f"\n📋 DETAILED RESULTS")
    print(f"=" * 50)
    
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"\nTest {result['test_number']}: {status}")
        print(f"Query: {result['query']}")
        print(f"Expected: {result['expected_answer']}")
        print(f"Actual: {result['actual_response']}")
        print(f"Match Score: {result['match_score']:.2f}")
        print(f"Is Error: {result['is_error']}")
    
    # Save results to file
    results_file = f"real_rag_evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "error_tests": error_tests,
                "success_rate": (passed_tests/total_tests)*100,
                "average_match_score": avg_match_score
            },
            "detailed_results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    evaluate_real_rag_system()
