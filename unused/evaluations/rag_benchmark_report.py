"""
RAG System Comprehensive Benchmark Report
Testing robustness, accuracy, and performance across multiple dimensions
"""

import requests
import json
import time
from datetime import datetime
import statistics

class RAGBenchmarkEvaluator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def send_query(self, query, session_id=None):
        """Send query to RAG system and measure response time"""
        if not session_id:
            session_id = f"benchmark_{int(time.time())}"
            
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/chat/send",
                json={
                    "content": query,
                    "session_id": session_id,
                    "user_id": "benchmark_user"
                },
                timeout=None  # No timeout constraints
            )
            end_time = time.time()
            
            if response.status_code == 200:
                # Parse streaming response
                content = ""
                response_text = response.text.strip()
                if response_text:
                    for line in response_text.split('\n'):
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if data.get('type') == 'ai_message_chunk':
                                    content += data.get('content', '')
                            except json.JSONDecodeError:
                                continue
                
                return {
                    "success": True,
                    "response": content,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "response": f"HTTP {response.status_code}",
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response": str(e),
                "response_time": end_time - start_time,
                "status_code": 0
            }
    
    def evaluate_response_quality(self, query, response, expected_keywords=None):
        """Evaluate response quality based on multiple criteria"""
        if not response or not response.get("success"):
            return {
                "relevance_score": 0,
                "completeness_score": 0,
                "accuracy_score": 0,
                "professionalism_score": 0,
                "overall_score": 0,
                "issues": ["Query failed or no response"]
            }
        
        content = response["response"].lower()
        issues = []
        
        # 1. Relevance Score (0-1)
        relevance_score = 1.0
        if "error" in content or "not available" in content:
            relevance_score = 0.0
            issues.append("Error in response")
        elif "query result: [(" in content:
            relevance_score = 0.3
            issues.append("Raw SQL result exposed")
        
        # 2. Completeness Score (0-1)
        completeness_score = 1.0
        if len(content) < 50:
            completeness_score = 0.3
            issues.append("Response too short")
        elif len(content) < 100:
            completeness_score = 0.6
            issues.append("Response somewhat brief")
        
        # 3. Accuracy Score (0-1) - Check for expected keywords
        accuracy_score = 1.0
        if expected_keywords:
            found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in content)
            accuracy_score = found_keywords / len(expected_keywords)
            if accuracy_score < 0.5:
                issues.append("Missing expected keywords")
        
        # 4. Professionalism Score (0-1)
        professionalism_score = 1.0
        if "christ university placement cell" in content:
            professionalism_score = 1.0
        elif "placement" in content or "company" in content:
            professionalism_score = 0.8
        else:
            professionalism_score = 0.5
            issues.append("Lacks professional formatting")
        
        # Overall score (weighted average)
        overall_score = (
            relevance_score * 0.3 +
            completeness_score * 0.25 +
            accuracy_score * 0.25 +
            professionalism_score * 0.2
        )
        
        return {
            "relevance_score": relevance_score,
            "completeness_score": completeness_score,
            "accuracy_score": accuracy_score,
            "professionalism_score": professionalism_score,
            "overall_score": overall_score,
            "issues": issues
        }
    
    def run_benchmark_suite(self):
        """Run comprehensive benchmark tests"""
        print("🚀 RAG System Comprehensive Benchmark Report")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Target System: {self.base_url}")
        print()
        
        # Define comprehensive test cases
        test_cases = [
            # 1. Basic Structured Queries (5 tests)
            {
                "category": "Basic Structured Queries",
                "query": "How many companies are offering finance roles?",
                "expected_keywords": ["mill story", "finance", "1 company"],
                "complexity": "Low",
                "test_type": "Count Query"
            },
            {
                "category": "Basic Structured Queries", 
                "query": "Which companies are hiring for HR roles?",
                "expected_keywords": ["accorian", "hr", "people operations"],
                "complexity": "Low",
                "test_type": "List Query"
            },
            {
                "category": "Basic Structured Queries",
                "query": "Are there any admission-related jobs?",
                "expected_keywords": ["masters union", "admission", "counselor"],
                "complexity": "Low", 
                "test_type": "Existence Query"
            },
            {
                "category": "Basic Structured Queries",
                "query": "Which jobs are specifically internships?",
                "expected_keywords": ["mill story", "internship", "finance"],
                "complexity": "Low",
                "test_type": "Filter Query"
            },
            {
                "category": "Basic Structured Queries",
                "query": "Which jobs are based in Bangalore?",
                "expected_keywords": ["bangalore", "mill story", "tap academy", "madison pr"],
                "complexity": "Low",
                "test_type": "Location Query"
            },
            
            # 2. Complex Structured Queries (5 tests)
            {
                "category": "Complex Structured Queries",
                "query": "How many companies are offering marketing roles and what are their names?",
                "expected_keywords": ["marketing", "companies", "madison pr", "tap academy", "target"],
                "complexity": "Medium",
                "test_type": "Multi-part Query"
            },
            {
                "category": "Complex Structured Queries",
                "query": "Which companies have both HR and marketing roles?",
                "expected_keywords": ["companies", "hr", "marketing"],
                "complexity": "Medium",
                "test_type": "Intersection Query"
            },
            {
                "category": "Complex Structured Queries",
                "query": "What is the total number of distinct companies recruiting?",
                "expected_keywords": ["companies", "total", "distinct"],
                "complexity": "Medium",
                "test_type": "Aggregation Query"
            },
            {
                "category": "Complex Structured Queries",
                "query": "List all companies and their respective specializations",
                "expected_keywords": ["companies", "specializations", "finance", "hr", "marketing"],
                "complexity": "Medium",
                "test_type": "Join Query"
            },
            {
                "category": "Complex Structured Queries",
                "query": "Which companies are NOT offering finance roles?",
                "expected_keywords": ["companies", "not", "finance"],
                "complexity": "Medium",
                "test_type": "Negation Query"
            },
            
            # 3. Unstructured/Descriptive Queries (5 tests)
            {
                "category": "Unstructured Queries",
                "query": "What finance-related tasks are mentioned in the job descriptions?",
                "expected_keywords": ["finance", "tasks", "accounting", "budgeting", "p&l"],
                "complexity": "Medium",
                "test_type": "Content Analysis"
            },
            {
                "category": "Unstructured Queries",
                "query": "What do HR operations jobs involve and what skills are required?",
                "expected_keywords": ["hr operations", "skills", "employee", "lifecycle", "compliance"],
                "complexity": "Medium",
                "test_type": "Role Description"
            },
            {
                "category": "Unstructured Queries",
                "query": "What opportunities does TAP Academy offer for MBA students?",
                "expected_keywords": ["tap academy", "opportunities", "mba", "lead generation", "partnership"],
                "complexity": "Medium",
                "test_type": "Company Analysis"
            },
            {
                "category": "Unstructured Queries",
                "query": "List all the tools and software mentioned in the job descriptions",
                "expected_keywords": ["tools", "software", "excel", "hrms", "office"],
                "complexity": "Medium",
                "test_type": "Tool Extraction"
            },
            {
                "category": "Unstructured Queries",
                "query": "What are the key responsibilities for marketing roles across different companies?",
                "expected_keywords": ["marketing", "responsibilities", "companies", "lead generation", "outreach"],
                "complexity": "Medium",
                "test_type": "Cross-Company Analysis"
            },
            
            # 4. Multi-hop/Complex Reasoning (5 tests)
            {
                "category": "Multi-hop Reasoning",
                "query": "Which companies offer both internships and full-time roles?",
                "expected_keywords": ["companies", "internships", "full-time", "roles"],
                "complexity": "High",
                "test_type": "Multi-hop Query"
            },
            {
                "category": "Multi-hop Reasoning",
                "query": "What are the common skills required across all HR-related positions?",
                "expected_keywords": ["skills", "hr", "common", "positions", "analytical"],
                "complexity": "High",
                "test_type": "Pattern Recognition"
            },
            {
                "category": "Multi-hop Reasoning",
                "query": "Which companies have the most diverse role offerings?",
                "expected_keywords": ["companies", "diverse", "roles", "offerings"],
                "complexity": "High",
                "test_type": "Comparative Analysis"
            },
            {
                "category": "Multi-hop Reasoning",
                "query": "What is the relationship between company industry and role specializations?",
                "expected_keywords": ["industry", "specializations", "relationship", "companies"],
                "complexity": "High",
                "test_type": "Correlation Analysis"
            },
            {
                "category": "Multi-hop Reasoning",
                "query": "Which roles would be best suited for someone interested in both finance and operations?",
                "expected_keywords": ["roles", "finance", "operations", "suited", "interested"],
                "complexity": "High",
                "test_type": "Recommendation Query"
            },
            
            # 5. Edge Cases and Error Handling (5 tests)
            {
                "category": "Edge Cases",
                "query": "What companies are offering data science roles?",
                "expected_keywords": ["companies", "data science"],
                "complexity": "Low",
                "test_type": "Non-existent Data"
            },
            {
                "category": "Edge Cases",
                "query": "Show me all the job details for every position",
                "expected_keywords": ["job", "details", "position"],
                "complexity": "Medium",
                "test_type": "Broad Query"
            },
            {
                "category": "Edge Cases",
                "query": "Which companies are offering remote work opportunities?",
                "expected_keywords": ["companies", "remote", "work"],
                "complexity": "Low",
                "test_type": "Missing Information"
            },
            {
                "category": "Edge Cases",
                "query": "What is the average salary for these positions?",
                "expected_keywords": ["salary", "average", "positions"],
                "complexity": "Low",
                "test_type": "Missing Data"
            },
            {
                "category": "Edge Cases",
                "query": "Compare the benefits offered by different companies",
                "expected_keywords": ["benefits", "companies", "compare"],
                "complexity": "Medium",
                "test_type": "Missing Information"
            },
            
            # 6. Performance and Stress Tests (5 tests)
            {
                "category": "Performance Tests",
                "query": "Give me a comprehensive analysis of all available opportunities with detailed recommendations for MBA students",
                "expected_keywords": ["analysis", "opportunities", "mba", "students", "recommendations"],
                "complexity": "High",
                "test_type": "Comprehensive Analysis"
            },
            {
                "category": "Performance Tests",
                "query": "What are the career progression paths for each specialization mentioned in the job descriptions?",
                "expected_keywords": ["career", "progression", "specialization", "paths"],
                "complexity": "High",
                "test_type": "Career Analysis"
            },
            {
                "category": "Performance Tests",
                "query": "Provide a detailed comparison of all companies including their culture, values, and growth opportunities",
                "expected_keywords": ["comparison", "companies", "culture", "values", "growth"],
                "complexity": "High",
                "test_type": "Company Comparison"
            },
            {
                "category": "Performance Tests",
                "query": "What are the industry trends and market insights based on the available job descriptions?",
                "expected_keywords": ["trends", "market", "insights", "industry"],
                "complexity": "High",
                "test_type": "Market Analysis"
            },
            {
                "category": "Performance Tests",
                "query": "Create a strategic placement guide for MBA students with specific recommendations for each specialization",
                "expected_keywords": ["strategic", "placement", "guide", "mba", "specialization"],
                "complexity": "High",
                "test_type": "Strategic Guide"
            }
        ]
        
        print(f"📊 Running {len(test_cases)} comprehensive test cases...")
        print()
        
        # Run all tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i:2d}/{len(test_cases)}: {test_case['query'][:60]}...")
            
            # Send query
            response = self.send_query(test_case['query'])
            
            # Evaluate response
            evaluation = self.evaluate_response_quality(
                test_case['query'], 
                response, 
                test_case.get('expected_keywords')
            )
            
            # Store results
            result = {
                "test_number": i,
                "category": test_case['category'],
                "query": test_case['query'],
                "complexity": test_case['complexity'],
                "test_type": test_case['test_type'],
                "expected_keywords": test_case.get('expected_keywords', []),
                "response": response,
                "evaluation": evaluation,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            
            # Print result
            status = "✅ PASS" if evaluation['overall_score'] >= 0.7 else "❌ FAIL"
            print(f"    {status} | Score: {evaluation['overall_score']:.2f} | Time: {response['response_time']:.2f}s")
            if evaluation['issues']:
                print(f"    Issues: {', '.join(evaluation['issues'])}")
            print()
        
        # Generate comprehensive report
        self.generate_benchmark_report()
    
    def generate_benchmark_report(self):
        """Generate comprehensive benchmark report"""
        print("=" * 60)
        print("📈 COMPREHENSIVE BENCHMARK REPORT")
        print("=" * 60)
        
        # Overall statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['evaluation']['overall_score'] >= 0.7)
        failed_tests = total_tests - successful_tests
        
        # Performance metrics
        response_times = [r['response']['response_time'] for r in self.results if r['response']['success']]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Quality metrics
        overall_scores = [r['evaluation']['overall_score'] for r in self.results]
        avg_overall_score = statistics.mean(overall_scores)
        
        relevance_scores = [r['evaluation']['relevance_score'] for r in self.results]
        completeness_scores = [r['evaluation']['completeness_score'] for r in self.results]
        accuracy_scores = [r['evaluation']['accuracy_score'] for r in self.results]
        professionalism_scores = [r['evaluation']['professionalism_score'] for r in self.results]
        
        print(f"🎯 OVERALL PERFORMANCE")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"   Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print()
        
        print(f"⚡ PERFORMANCE METRICS")
        print(f"   Average Response Time: {avg_response_time:.2f}s")
        print(f"   Fastest Response: {min_response_time:.2f}s")
        print(f"   Slowest Response: {max_response_time:.2f}s")
        print()
        
        print(f"📊 QUALITY METRICS")
        print(f"   Overall Score: {avg_overall_score:.3f}")
        print(f"   Relevance Score: {statistics.mean(relevance_scores):.3f}")
        print(f"   Completeness Score: {statistics.mean(completeness_scores):.3f}")
        print(f"   Accuracy Score: {statistics.mean(accuracy_scores):.3f}")
        print(f"   Professionalism Score: {statistics.mean(professionalism_scores):.3f}")
        print()
        
        # Category-wise analysis
        print(f"📋 CATEGORY-WISE ANALYSIS")
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, results in categories.items():
            cat_scores = [r['evaluation']['overall_score'] for r in results]
            cat_avg = statistics.mean(cat_scores)
            cat_success = sum(1 for r in results if r['evaluation']['overall_score'] >= 0.7)
            print(f"   {category}: {cat_avg:.3f} avg score ({cat_success}/{len(results)} passed)")
        print()
        
        # Complexity analysis
        print(f"🎚️ COMPLEXITY ANALYSIS")
        complexities = {}
        for result in self.results:
            comp = result['complexity']
            if comp not in complexities:
                complexities[comp] = []
            complexities[comp].append(result)
        
        for complexity, results in complexities.items():
            comp_scores = [r['evaluation']['overall_score'] for r in results]
            comp_avg = statistics.mean(comp_scores)
            comp_success = sum(1 for r in results if r['evaluation']['overall_score'] >= 0.7)
            print(f"   {complexity}: {comp_avg:.3f} avg score ({comp_success}/{len(results)} passed)")
        print()
        
        # Detailed failure analysis
        failures = [r for r in self.results if r['evaluation']['overall_score'] < 0.7]
        if failures:
            print(f"❌ FAILURE ANALYSIS")
            for failure in failures:
                print(f"   Test {failure['test_number']}: {failure['query'][:50]}...")
                print(f"      Issues: {', '.join(failure['evaluation']['issues'])}")
                print(f"      Score: {failure['evaluation']['overall_score']:.3f}")
            print()
        
        # Recommendations
        print(f"💡 RECOMMENDATIONS")
        if avg_overall_score >= 0.8:
            print("   ✅ System performing excellently across all test categories")
        elif avg_overall_score >= 0.7:
            print("   ✅ System performing well with minor improvements needed")
        elif avg_overall_score >= 0.5:
            print("   ⚠️ System needs significant improvements")
        else:
            print("   ❌ System requires major overhaul")
        
        if max_response_time > 10:
            print("   ⚠️ Consider optimizing response times for better user experience")
        
        if statistics.mean(accuracy_scores) < 0.7:
            print("   ⚠️ Improve accuracy by enhancing keyword matching and context understanding")
        
        if statistics.mean(professionalism_scores) < 0.8:
            print("   ⚠️ Enhance response formatting and professional presentation")
        
        print()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rag_benchmark_report_{timestamp}.json"
        
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests/total_tests*100,
                "average_response_time": avg_response_time,
                "average_overall_score": avg_overall_score,
                "average_relevance_score": statistics.mean(relevance_scores),
                "average_completeness_score": statistics.mean(completeness_scores),
                "average_accuracy_score": statistics.mean(accuracy_scores),
                "average_professionalism_score": statistics.mean(professionalism_scores)
            },
            "category_analysis": {
                cat: {
                    "average_score": statistics.mean([r['evaluation']['overall_score'] for r in results]),
                    "success_count": sum(1 for r in results if r['evaluation']['overall_score'] >= 0.7),
                    "total_count": len(results)
                }
                for cat, results in categories.items()
            },
            "complexity_analysis": {
                comp: {
                    "average_score": statistics.mean([r['evaluation']['overall_score'] for r in results]),
                    "success_count": sum(1 for r in results if r['evaluation']['overall_score'] >= 0.7),
                    "total_count": len(results)
                }
                for comp, results in complexities.items()
            },
            "detailed_results": self.results,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"💾 Detailed report saved to: {filename}")
        print("=" * 60)

if __name__ == "__main__":
    evaluator = RAGBenchmarkEvaluator()
    evaluator.run_benchmark_suite()
