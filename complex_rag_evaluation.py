"""
Complex RAG System Evaluation with Answer Keys
Testing 20 complex multi-hop questions against provided answer keys
"""

import requests
import json
import time
from datetime import datetime
import statistics

class ComplexRAGEvaluator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def send_query(self, query, session_id=None):
        """Send query to RAG system and measure response time"""
        if not session_id:
            session_id = f"complex_test_{int(time.time())}"
            
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/chat/send",
                json={
                    "content": query,
                    "session_id": session_id,
                    "user_id": "complex_test_user"
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
    
    def evaluate_against_answer_key(self, query, response, answer_key, expected_keywords):
        """Evaluate response against provided answer key"""
        if not response or not response.get("success"):
            return {
                "accuracy_score": 0,
                "keyword_match": 0,
                "answer_quality": 0,
                "overall_score": 0,
                "issues": ["Query failed or no response"]
            }
        
        content = response["response"].lower()
        issues = []
        
        # 1. Keyword Match Score (0-1) - More flexible matching
        found_keywords = 0
        for keyword in expected_keywords:
            keyword_lower = keyword.lower()
            # Check for exact match or partial match
            if keyword_lower in content:
                found_keywords += 1
            else:
                # Check for semantic equivalents
                if keyword_lower == "one salary" and ("only" in content and "salary" in content):
                    found_keywords += 1
                elif keyword_lower == "diverse industries" and ("industries" in content and ("diverse" in content or "different" in content)):
                    found_keywords += 1
                elif keyword_lower == "missing data" and ("not mentioned" in content or "not specified" in content or "missing" in content):
                    found_keywords += 1
                elif keyword_lower == "entry-level" and ("entry" in content or "associate" in content or "intern" in content):
                    found_keywords += 1
                elif keyword_lower == "no remote" and ("remote" in content and ("not" in content or "no" in content)):
                    found_keywords += 1
        
        keyword_match = found_keywords / len(expected_keywords) if expected_keywords else 0
        
        if keyword_match < 0.3:  # Lowered threshold
            issues.append("Missing expected keywords")
        
        # 2. Answer Quality Score (0-1)
        answer_quality = 1.0
        
        # Check for error responses
        if "error" in content or "not available" in content:
            answer_quality = 0.0
            issues.append("Error in response")
        elif "query result: [(" in content:
            answer_quality = 0.3
            issues.append("Raw SQL result exposed")
        
        # Check response length and completeness - More lenient for complex queries
        if len(content) < 50:
            answer_quality = 0.3
            issues.append("Response too short")
        elif len(content) < 100:
            answer_quality = 0.6
            issues.append("Response somewhat brief")
        
        # 3. Accuracy Score (0-1) - Based on answer key alignment
        accuracy_score = 1.0
        
        # Check for key facts from answer key
        answer_key_lower = answer_key.lower()
        key_facts = answer_key_lower.split()
        found_facts = sum(1 for fact in key_facts if fact in content)
        accuracy_score = found_facts / len(key_facts) if key_facts else 0
        
        if accuracy_score < 0.2:  # Lowered threshold
            issues.append("Response doesn't align with answer key")
        
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
            keyword_match * 0.3 +
            answer_quality * 0.3 +
            accuracy_score * 0.3 +
            professionalism_score * 0.1
        )
        
        return {
            "keyword_match": keyword_match,
            "answer_quality": answer_quality,
            "accuracy_score": accuracy_score,
            "professionalism_score": professionalism_score,
            "overall_score": overall_score,
            "issues": issues
        }
    
    def run_complex_evaluation(self):
        """Run complex evaluation with answer keys"""
        print("🧠 COMPLEX RAG SYSTEM EVALUATION")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Target System: {self.base_url}")
        print()
        
        # Test cases with answer keys
        test_cases = [
            # 1. Multi-Hop Reasoning Questions
            {
                "query": "Which companies are offering both internships and full-time roles, and what are the common skills required across both types?",
                "answer_key": "Only Mill Story explicitly offers an internship (Finance & Accounting Intern — 2 months, paid) and mentions potential conversion to full-time. No company in the provided JDs explicitly lists both an internship and a separate full-time role. Common skills: Excel / Google Sheets, MS Office, communication skills, analytical/problem-solving skills.",
                "expected_keywords": ["Mill Story", "internship", "potential full-time", "Excel", "Google Sheets", "MS Office", "communication", "analytical"],
                "category": "Multi-Hop Reasoning",
                "complexity": "High"
            },
            {
                "query": "Among the companies hiring for marketing roles, which ones also have operations positions, and what's the relationship between their industry and role specializations?",
                "answer_key": "In the provided JDs none of the companies list both marketing and operations roles within the same company. Across companies: Madison PR and TAP Academy have marketing / business-development roles; Masters' Union and Target have operations/admissions/media-operations roles. Relationship: PR and marketing roles appear in PR/consumer/media industries; EdTech and BDA roles are marketing/business-development oriented; Education (Masters' Union) maps to admissions/operations.",
                "expected_keywords": ["Madison PR", "TAP Academy", "Masters' Union", "Target", "marketing", "operations", "PR industry", "EdTech", "education"],
                "category": "Multi-Hop Reasoning",
                "complexity": "High"
            },
            {
                "query": "What are the most in-demand skills across all companies, and which MBA specializations would benefit most from developing these skills?",
                "answer_key": "Most frequent skills: communication skills, MS Office / Excel / Google Sheets, analytical / problem-solving, CRM / LinkedIn / social outreach (TAP Academy, Masters' Union), HRMS (Accorian), PR tools (Madison PR). MBA specializations: Finance → Excel/analytical; HR → HRMS / compliance / people ops; Marketing / PR → communication, PR tools, social outreach; Operations / Analytics → analytical skills, reporting.",
                "expected_keywords": ["communication", "Excel", "MS Office", "Google Sheets", "analytical", "CRM", "HRMS", "PR tools", "Finance", "HR", "Marketing", "Operations"],
                "category": "Multi-Hop Reasoning",
                "complexity": "High"
            },
            {
                "query": "Which companies have the most diverse role offerings, and what does this tell us about their organizational structure?",
                "answer_key": "Based on the provided JDs, each company lists a single role (one JD per company). Therefore no company in this dataset shows multi-role diversity; this suggests focused / targeted campus hiring rather than broad multi-department hiring.",
                "expected_keywords": ["single roles", "focused", "specialized", "targeted hiring", "organizational structure"],
                "category": "Multi-Hop Reasoning",
                "complexity": "High"
            },
            {
                "query": "If a student is interested in both finance and operations, which specific roles would be best suited for them based on the available opportunities?",
                "answer_key": "Mill Story — Finance & Accounting Intern (hands-on finance tasks, fundraising support). Masters' Union — Admission Counselor (operations-heavy responsibilities: process management, pipeline management). Both roles include analytical/process elements.",
                "expected_keywords": ["Mill Story", "Masters' Union", "Finance", "Operations", "internship", "Admission Counselor", "analytical", "process management"],
                "category": "Multi-Hop Reasoning",
                "complexity": "High"
            },
            
            # 2. Tricky Edge-Case Questions
            {
                "query": "What's the salary range for these positions, and how does it compare across different specializations?",
                "answer_key": "Only Madison PR explicitly lists salary: Fixed CTC up to 5.5 LPA. All other JDs do not provide salary information (null / not mentioned in JD). Therefore direct comparison across specializations is not possible from the provided documents.",
                "expected_keywords": ["5.5 LPA", "Madison PR", "salary", "not mentioned", "missing data", "cannot compare"],
                "category": "Edge Cases",
                "complexity": "Medium"
            },
            {
                "query": "Which companies offer remote work opportunities, and what are the location requirements?",
                "answer_key": "No JD explicitly states remote work. Locations explicitly mentioned in JDs: Mill Story — Sarjapur Road, Bengaluru; TAP Academy — BTM Layout, Bangalore; Target (Apprentice) — Bengaluru; Madison PR — Mumbai / Gurgaon / Bangalore; Masters' Union — Gurgaon, Haryana; Accorian — HQ New Jersey with regional offices (India/Canada/UAE) (role location not explicitly specified in JD).",
                "expected_keywords": ["no remote", "Mill Story", "Sarjapur Road", "TAP Academy", "BTM Layout", "Target Bengaluru", "Madison PR", "Mumbai", "Gurgaon", "Bangalore", "Masters' Union Gurgaon", "Accorian New Jersey", "regional offices"],
                "category": "Edge Cases",
                "complexity": "Medium"
            },
            {
                "query": "What are the career progression paths for each specialization based on the job titles and requirements?",
                "answer_key": "The JDs describe entry-level roles (Intern, Associate, Apprentice, Admission Counselor, Business Development Associate, Account Executive). Explicit career progression paths are not detailed in the JDs. Therefore: roles are entry-level; any progression inference is not stated in JD.",
                "expected_keywords": ["entry-level", "Intern", "Associate", "Apprentice", "Admission Counselor", "progression not mentioned", "career path not specified"],
                "category": "Edge Cases",
                "complexity": "Medium"
            },
            {
                "query": "Compare the company cultures and values mentioned in the job descriptions, and identify which would be best for different personality types.",
                "answer_key": "Accorian: emphasizes mentorship, compliance, technical rigor → suits analytical, process-oriented candidates. Mill Story: startup, hands-on, learning from founders, 'startup hustle' → suits adaptable, learning-oriented candidates. Madison PR: creative, media-focused, storytelling emphasis → suits communicative, creative candidates. TAP Academy: ed-tech, growth & placement focus, outreach emphasis → suits proactive, sales/relationship-oriented candidates. Masters' Union: industry-immersive education, professional/target-driven admissions → suits persuasive, goal-oriented candidates. Target (Apprentice Media Ops): global/inclusive culture, hands-on media ops exposure → suits collaborative learners seeking global teams.",
                "expected_keywords": ["Accorian mentorship", "Mill Story startup", "Madison PR creative", "TAP Academy growth", "Masters' Union industry-immersive", "Target inclusive", "analytical", "creative", "adaptable"],
                "category": "Edge Cases",
                "complexity": "High"
            },
            {
                "query": "What are the industry trends based on the available job descriptions, and what does this predict about future opportunities?",
                "answer_key": "Industries present in the dataset: Cybersecurity (Accorian), Food / D2C (Mill Story), Public Relations (Madison PR), EdTech (TAP Academy), Higher Education (Masters' Union), Retail/Media Ops (Target). From these JDs we observe hiring across cybersecurity, edtech, PR/media, and D2C food — suggesting demand in these sectors within this dataset.",
                "expected_keywords": ["Cybersecurity", "Food", "PR", "EdTech", "Education", "Retail", "hiring", "sector representation", "demand"],
                "category": "Edge Cases",
                "complexity": "Medium"
            },
            
            # 3. Complex Analytical Questions
            {
                "query": "Create a skills matrix showing which companies require which tools, and identify the most versatile tools that appear across multiple companies.",
                "answer_key": "Mill Story: Excel, Google Sheets; bonus: Tally, Zoho Books (optional). Accorian: MS Office Suite, HRMS. Madison PR: MS Office Suite, PR tools (explicit), media/PR tool familiarity. Masters' Union: CRM systems (explicit), sales tools. TAP Academy: CRM tools (mentioned as 'a plus'), LinkedIn & social media outreach. Target (Apprentice Media Ops): media operations tools (not itemized by name in JD). Most versatile / common tools: MS Office / Excel appear across multiple JDs; CRM / HRMS / PR tools appear but are company-specific.",
                "expected_keywords": ["Excel", "Google Sheets", "MS Office", "HRMS", "PR tools", "CRM", "LinkedIn", "versatile", "multiple companies"],
                "category": "Analytical",
                "complexity": "High"
            },
            {
                "query": "What's the geographic distribution of opportunities, and how does location correlate with company type and role specializations?",
                "answer_key": "Geographic distribution (from JDs): Bangalore — Mill Story (Sarjapur Road), TAP Academy (BTM Layout), Target (Bengaluru); Mumbai / Gurgaon / Bangalore — Madison PR (multi-location); Gurgaon — Masters' Union; New Jersey (HQ) & regional offices — Accorian (HQ NJ, regional offices incl. India). Correlation observed in dataset: Bangalore hosts multiple tech/edtech/media roles; Mumbai/Gurgaon show PR and education roles in this set.",
                "expected_keywords": ["Bangalore", "Mumbai", "Gurgaon", "New Jersey", "Sarjapur Road", "BTM Layout", "location correlation", "tech hub", "PR/media"],
                "category": "Analytical",
                "complexity": "High"
            },
            {
                "query": "Analyze the overlap between different specializations and identify which roles combine multiple MBA specializations.",
                "answer_key": "Roles combining specializations (based on JD content): TAP Academy (Business Development Associate): Marketing (outreach) + Strategy/Partnerships. Madison PR (Account Executive): Marketing + Communications / PR. Masters' Union (Admission Counselor): Operations + Sales (inside sales for education). Mill Story (Finance Intern): Finance + some Strategy (fundraising/pitch deck exposure). Accorian (People Ops): HR + Compliance / People Analytics (HR tech emphasis).",
                "expected_keywords": ["TAP Academy", "Madison PR", "Masters' Union", "Mill Story", "Accorian", "Marketing", "Strategy", "PR", "HR", "Finance"],
                "category": "Analytical",
                "complexity": "High"
            },
            {
                "query": "What are the common requirements mentioned across job descriptions, and what skills are most valued for addressing these requirements?",
                "answer_key": "Common requirements across JDs: strong communication skills, MS Office / Excel proficiency, analytical / problem-solving skills, relevant degree (bachelor/postgrad), and experience level (freshers accepted in several roles). Most valued skills: communication (appears in nearly all JDs), analytical skills (Accorian, Mill Story), and tool literacy (MS Office / CRM / HRMS / PR tools).",
                "expected_keywords": ["communication skills", "analytical skills", "MS Office", "Excel", "relevant degree", "experience", "CRM", "HRMS"],
                "category": "Analytical",
                "complexity": "Medium"
            },
            {
                "query": "If you were to create a strategic placement guide for MBA students, what would be the top recommendations for each specialization based on these specific roles?",
                "answer_key": "Finance: Target Mill Story — gain Excel/financial statements skills, help with pitch decks/fundraising. HR / People Ops: Target Accorian — focus on HRMS, labor law, compliance, employee lifecycle. Marketing / PR: Target Madison PR or TAP Academy — build PR writing, media relations, LinkedIn outreach skills. Operations: Target Masters' Union — develop process/pipeline management and stakeholder handling. Media / Analytics: Target Apprentice Media Ops (Target) — get media operations exposure and global team experience.",
                "expected_keywords": ["Finance Mill Story", "HR Accorian", "Marketing Madison PR TAP Academy", "Operations Masters' Union", "Media Target", "skill recommendations"],
                "category": "Analytical",
                "complexity": "High"
            },
            
            # 4. Trick Questions
            {
                "query": "Which companies are NOT offering any roles in the current dataset, and what might this indicate?",
                "answer_key": "All listed companies in the uploaded documents have roles. Companies with roles in this dataset: Accorian, Mill Story, Madison PR, TAP Academy, Masters' Union, Target (Apprentice). No company in the provided files is missing a role. This indicates the dataset contains one active JD per uploaded file.",
                "expected_keywords": ["Accorian", "Mill Story", "Madison PR", "TAP Academy", "Masters' Union", "Target", "all companies covered", "no missing roles", "complete coverage"],
                "category": "Trick Questions",
                "complexity": "Low"
            },
            {
                "query": "What information is completely missing from the job descriptions that would be most valuable for MBA students to know?",
                "answer_key": "Frequently missing or not specified in the JDs: detailed salary/compensation (only Madison PR lists salary), team size, explicit career progression paths, detailed benefits, work-from-home / hybrid policies, reporting structure, and quantified growth metrics.",
                "expected_keywords": ["salary details", "team size", "career progression", "benefits", "WFH", "reporting structure", "missing data"],
                "category": "Trick Questions",
                "complexity": "Medium"
            },
            {
                "query": "If we were to rank companies by their attractiveness to MBA students based on the available data, what criteria would you use?",
                "answer_key": "Use these faithfulness-based criteria (derivable from JDs): salary transparency (Madison PR scores), industry growth potential (cybersecurity, edtech), location / hub (Bangalore/Mumbai/Gurgaon), role type (paid internship vs full-time vs apprentice), skill development opportunity (explicit training, mentorship), and company maturity (startup vs established / global HQ).",
                "expected_keywords": ["salary", "industry growth", "location", "role type", "skill development", "mentorship", "company size"],
                "category": "Trick Questions",
                "complexity": "High"
            },
            {
                "query": "What are the most surprising or unexpected findings from analyzing these specific job descriptions?",
                "answer_key": "Faithful observations from JDs: only one JD lists a numeric salary (Madison PR), diverse industries (food/D2C, PR, cybersecurity, edtech, education, retail/media ops), most roles are entry-level, strong emphasis on communication skills across JD set, and no explicit remote work or team size info.",
                "expected_keywords": ["one salary", "diverse industries", "entry-level roles", "communication emphasis", "no remote", "missing team info"],
                "category": "Trick Questions",
                "complexity": "Medium"
            },
            {
                "query": "Which questions would be most difficult for this system to answer based on the available data, and why?",
                "answer_key": "Most difficult (and why — JD-grounded): salary comparisons (most JDs lack salary data), detailed career progression (not specified), company culture depth & team dynamics (only hinted at), work-life balance / benefits (not mentioned), precise headcount or reporting lines (not mentioned). Lack of explicit fields in the JDs makes these answers impossible to produce faithfully.",
                "expected_keywords": ["salary comparisons", "career progression", "company culture", "team dynamics", "benefits", "missing data", "not mentioned"],
                "category": "Trick Questions",
                "complexity": "High"
            }
        ]
        
        print(f"📊 Running {len(test_cases)} complex test cases with answer keys...")
        print()
        
        # Run all tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i:2d}: {test_case['query'][:60]}...")
            print(f"         Category: {test_case['category']} | Complexity: {test_case['complexity']}")
            
            # Send query
            response = self.send_query(test_case['query'])
            
            # Evaluate against answer key
            evaluation = self.evaluate_against_answer_key(
                test_case['query'], 
                response, 
                test_case['answer_key'],
                test_case['expected_keywords']
            )
            
            # Store results
            result = {
                "test_number": i,
                "query": test_case['query'],
                "category": test_case['category'],
                "complexity": test_case['complexity'],
                "answer_key": test_case['answer_key'],
                "expected_keywords": test_case['expected_keywords'],
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
            print(f"         Keyword Match: {evaluation['keyword_match']:.2f} | Accuracy: {evaluation['accuracy_score']:.2f}")
            if evaluation['issues']:
                print(f"         Issues: {', '.join(evaluation['issues'])}")
            print()
        
        # Generate comprehensive report
        self.generate_complex_report()
    
    def generate_complex_report(self):
        """Generate comprehensive complex evaluation report"""
        print("=" * 60)
        print("📈 COMPLEX EVALUATION REPORT")
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
        keyword_scores = [r['evaluation']['keyword_match'] for r in self.results]
        accuracy_scores = [r['evaluation']['accuracy_score'] for r in self.results]
        
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
        print(f"   Overall Score: {statistics.mean(overall_scores):.3f}")
        print(f"   Keyword Match: {statistics.mean(keyword_scores):.3f}")
        print(f"   Accuracy Score: {statistics.mean(accuracy_scores):.3f}")
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
            cat_keywords = [r['evaluation']['keyword_match'] for r in results]
            cat_accuracy = [r['evaluation']['accuracy_score'] for r in results]
            cat_avg = statistics.mean(cat_scores)
            cat_keyword_avg = statistics.mean(cat_keywords)
            cat_accuracy_avg = statistics.mean(cat_accuracy)
            cat_success = sum(1 for r in results if r['evaluation']['overall_score'] >= 0.7)
            print(f"   {category}:")
            print(f"      Overall: {cat_avg:.3f} | Keywords: {cat_keyword_avg:.3f} | Accuracy: {cat_accuracy_avg:.3f} | Success: {cat_success}/{len(results)}")
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
        
        # Detailed results
        print(f"📋 DETAILED RESULTS")
        for result in self.results:
            status = "✅ PASS" if result['evaluation']['overall_score'] >= 0.7 else "❌ FAIL"
            print(f"   Test {result['test_number']}: {status}")
            print(f"      Query: {result['query']}")
            print(f"      Category: {result['category']} | Complexity: {result['complexity']}")
            print(f"      Overall Score: {result['evaluation']['overall_score']:.3f}")
            print(f"      Keyword Match: {result['evaluation']['keyword_match']:.3f}")
            print(f"      Accuracy: {result['evaluation']['accuracy_score']:.3f}")
            print(f"      Time: {result['response']['response_time']:.1f}s")
            if result['evaluation']['issues']:
                print(f"      Issues: {', '.join(result['evaluation']['issues'])}")
            print()
        
        # Recommendations
        print(f"💡 RECOMMENDATIONS")
        if statistics.mean(overall_scores) >= 0.8:
            print("   ✅ System performing excellently on complex queries")
        elif statistics.mean(overall_scores) >= 0.7:
            print("   ✅ System performing well on complex queries with minor improvements needed")
        elif statistics.mean(overall_scores) >= 0.5:
            print("   ⚠️ System needs significant improvements for complex queries")
        else:
            print("   ❌ System requires major overhaul for complex queries")
        
        if statistics.mean(keyword_scores) < 0.7:
            print("   ⚠️ Improve keyword matching and context understanding")
        
        if statistics.mean(accuracy_scores) < 0.7:
            print("   ⚠️ Enhance accuracy by better alignment with answer keys")
        
        print()
        print("=" * 60)

if __name__ == "__main__":
    evaluator = ComplexRAGEvaluator()
    evaluator.run_complex_evaluation()
