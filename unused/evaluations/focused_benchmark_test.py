"""
Focused RAG System Benchmark Test
Testing 10 key queries to identify system performance
"""

import requests
import json
import time
from datetime import datetime
import statistics

class FocusedRAGTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def send_query(self, query, session_id=None):
        """Send query to RAG system and measure response time"""
        if not session_id:
            session_id = f"focused_test_{int(time.time())}"
            
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/chat/send",
                json={
                    "content": query,
                    "session_id": session_id,
                    "user_id": "focused_test_user"
                },
                timeout=None
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
    
    def evaluate_response(self, query, response):
        """Evaluate response quality"""
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
        expected_keywords = []
        if "finance" in query.lower():
            expected_keywords = ["finance", "mill story"]
        elif "hr" in query.lower():
            expected_keywords = ["hr", "accorian", "people operations"]
        elif "tools" in query.lower():
            expected_keywords = ["tools", "excel", "hrms", "office"]
        elif "admission" in query.lower():
            expected_keywords = ["admission", "masters union", "counselor"]
        elif "internship" in query.lower():
            expected_keywords = ["internship", "mill story"]
        elif "bangalore" in query.lower():
            expected_keywords = ["bangalore", "companies"]
        
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
    
    def run_focused_test(self):
        """Run focused benchmark test with 10 key queries"""
        print("🎯 FOCUSED RAG SYSTEM BENCHMARK TEST")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Target System: {self.base_url}")
        print()
        
        # 10 focused test cases covering different scenarios
        test_cases = [
            {
                "query": "How many companies are offering finance roles?",
                "type": "Structured Count Query",
                "expected_time": "< 3s"
            },
            {
                "query": "Which companies are hiring for HR roles?",
                "type": "Structured List Query", 
                "expected_time": "< 3s"
            },
            {
                "query": "What finance-related tasks are mentioned?",
                "type": "Unstructured Analysis Query",
                "expected_time": "< 25s"
            },
            {
                "query": "What do HR operations jobs involve?",
                "type": "Unstructured Description Query",
                "expected_time": "< 25s"
            },
            {
                "query": "List all the tools mentioned in the JDs",
                "type": "Unstructured Extraction Query",
                "expected_time": "< 25s"
            },
            {
                "query": "Are there any admission-related jobs?",
                "type": "Structured Existence Query",
                "expected_time": "< 3s"
            },
            {
                "query": "Which jobs are specifically internships?",
                "type": "Structured Filter Query",
                "expected_time": "< 3s"
            },
            {
                "query": "Which jobs are based in Bangalore?",
                "type": "Structured Location Query",
                "expected_time": "< 3s"
            },
            {
                "query": "What opportunities does TAP Academy offer?",
                "type": "Unstructured Company Analysis",
                "expected_time": "< 25s"
            },
            {
                "query": "Which companies have both HR and marketing roles?",
                "type": "Complex Multi-condition Query",
                "expected_time": "< 10s"
            }
        ]
        
        print(f"📊 Running {len(test_cases)} focused test cases...")
        print()
        
        # Run all tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i:2d}: {test_case['query'][:50]}...")
            print(f"         Type: {test_case['type']} | Expected: {test_case['expected_time']}")
            
            # Send query
            response = self.send_query(test_case['query'])
            
            # Evaluate response
            evaluation = self.evaluate_response(test_case['query'], response)
            
            # Store results
            result = {
                "test_number": i,
                "query": test_case['query'],
                "type": test_case['type'],
                "expected_time": test_case['expected_time'],
                "response": response,
                "evaluation": evaluation,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            
            # Print result
            status = "✅ PASS" if evaluation['overall_score'] >= 0.7 else "❌ FAIL"
            actual_time = f"{response['response_time']:.1f}s"
            time_status = "⏱️" if response['response_time'] > 25 else "⚡" if response['response_time'] < 3 else "🕐"
            
            print(f"         {status} | Score: {evaluation['overall_score']:.2f} | Time: {time_status} {actual_time}")
            if evaluation['issues']:
                print(f"         Issues: {', '.join(evaluation['issues'])}")
            print()
        
        # Generate focused report
        self.generate_focused_report()
    
    def generate_focused_report(self):
        """Generate focused benchmark report"""
        print("=" * 50)
        print("📈 FOCUSED BENCHMARK REPORT")
        print("=" * 50)
        
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
        print()
        
        # Type-wise analysis
        print(f"📋 QUERY TYPE ANALYSIS")
        types = {}
        for result in self.results:
            query_type = result['type']
            if query_type not in types:
                types[query_type] = []
            types[query_type].append(result)
        
        for query_type, results in types.items():
            type_scores = [r['evaluation']['overall_score'] for r in results]
            type_times = [r['response']['response_time'] for r in results if r['response']['success']]
            type_avg_score = statistics.mean(type_scores)
            type_avg_time = statistics.mean(type_times) if type_times else 0
            type_success = sum(1 for r in results if r['evaluation']['overall_score'] >= 0.7)
            print(f"   {query_type}:")
            print(f"      Score: {type_avg_score:.3f} | Time: {type_avg_time:.1f}s | Success: {type_success}/{len(results)}")
        print()
        
        # Performance analysis
        print(f"🚀 PERFORMANCE ANALYSIS")
        fast_queries = [r for r in self.results if r['response']['response_time'] < 3]
        medium_queries = [r for r in self.results if 3 <= r['response']['response_time'] < 10]
        slow_queries = [r for r in self.results if r['response']['response_time'] >= 10]
        
        print(f"   Fast Queries (< 3s): {len(fast_queries)}")
        print(f"   Medium Queries (3-10s): {len(medium_queries)}")
        print(f"   Slow Queries (> 10s): {len(slow_queries)}")
        print()
        
        # Detailed results
        print(f"📋 DETAILED RESULTS")
        for result in self.results:
            status = "✅ PASS" if result['evaluation']['overall_score'] >= 0.7 else "❌ FAIL"
            print(f"   Test {result['test_number']}: {status}")
            print(f"      Query: {result['query']}")
            print(f"      Type: {result['type']}")
            print(f"      Score: {result['evaluation']['overall_score']:.3f}")
            print(f"      Time: {result['response']['response_time']:.1f}s")
            if result['evaluation']['issues']:
                print(f"      Issues: {', '.join(result['evaluation']['issues'])}")
            print()
        
        # Recommendations
        print(f"💡 RECOMMENDATIONS")
        if avg_overall_score >= 0.8:
            print("   ✅ System performing excellently")
        elif avg_overall_score >= 0.7:
            print("   ✅ System performing well with minor improvements needed")
        elif avg_overall_score >= 0.5:
            print("   ⚠️ System needs significant improvements")
        else:
            print("   ❌ System requires major overhaul")
        
        if max_response_time > 25:
            print("   ⚠️ Consider optimizing LLM calls for better response times")
        
        if len(slow_queries) > len(fast_queries):
            print("   ⚠️ More queries are slow than fast - investigate LLM bottlenecks")
        
        print()
        print("=" * 50)

if __name__ == "__main__":
    tester = FocusedRAGTest()
    tester.run_focused_test()
