"""
Advanced RAG System Evaluation with Reference Answers and Advanced Metrics
Includes BLEU, ROUGE, BERTScore, and other state-of-the-art evaluation metrics
"""

import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from pathlib import Path
import logging
import re
from collections import Counter

# Advanced evaluation metrics
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Try to import BERTScore (optional)
try:
    from bert_score import score as bert_score
    BERTSCORE_AVAILABLE = True
except ImportError:
    BERTSCORE_AVAILABLE = False
    print("⚠️ BERTScore not available. Install with: pip install bert-score")

# RAG components
from app.rag import retrieve_snippets, synthesize_answer
from app.agent import route_query
from app.database import PlacementDatabase

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
except:
    pass

class AdvancedRAGEvaluator:
    """Advanced RAG evaluator with reference answers and comprehensive metrics"""
    
    def __init__(self):
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        self.smoothing = SmoothingFunction().method4
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Initialize database for context
        self.db = PlacementDatabase()
        
    def create_reference_dataset(self) -> List[Dict[str, Any]]:
        """Create test dataset with reference answers for comprehensive evaluation"""
        
        reference_dataset = [
            {
                "query": "What are the top companies hiring for software engineering roles?",
                "reference_answer": "The top companies hiring for software engineering roles include Google, Microsoft, Amazon, Apple, Meta (Facebook), Netflix, Uber, Airbnb, and many other tech giants. These companies typically offer competitive salaries ranging from $120,000 to $300,000+ for senior positions, along with comprehensive benefits packages including health insurance, stock options, flexible work arrangements, and professional development opportunities. They look for candidates with strong programming skills in languages like Python, Java, JavaScript, C++, and experience with modern frameworks and cloud technologies.",
                "expected_topics": ["companies", "software engineering", "hiring", "technology", "salaries", "benefits"],
                "expected_entities": ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix"],
                "expected_response_type": "list_companies",
                "difficulty": "easy",
                "category": "company_search",
                "expected_keywords": ["software", "engineering", "programming", "tech", "companies", "hiring"]
            },
            {
                "query": "What skills are required for data science positions?",
                "reference_answer": "Data science positions require a combination of technical and analytical skills. Key technical skills include proficiency in programming languages like Python and R, knowledge of SQL for database management, experience with machine learning frameworks like TensorFlow and PyTorch, and expertise in statistical analysis and data visualization tools like Tableau or Power BI. Additionally, strong mathematical and statistical knowledge, problem-solving abilities, and domain expertise in the specific industry are crucial. Soft skills like communication, critical thinking, and the ability to translate complex data insights into business recommendations are also highly valued.",
                "expected_topics": ["data science", "skills", "requirements", "technical", "programming", "statistics"],
                "expected_entities": ["Python", "R", "SQL", "TensorFlow", "PyTorch", "Tableau"],
                "expected_response_type": "skill_list",
                "difficulty": "medium",
                "category": "skill_analysis",
                "expected_keywords": ["python", "r", "sql", "machine learning", "statistics", "data analysis"]
            },
            {
                "query": "What is the average salary for product manager roles?",
                "reference_answer": "The average salary for product manager roles varies significantly based on location, company size, and experience level. In the United States, entry-level product managers typically earn between $70,000 to $100,000 annually, while mid-level product managers earn $100,000 to $150,000. Senior product managers can expect salaries ranging from $150,000 to $250,000, and principal or director-level product managers often earn $200,000 to $350,000 or more. In major tech hubs like San Francisco and New York, salaries are typically 20-30% higher. Additionally, many product manager positions include equity, bonuses, and comprehensive benefits packages that can add significant value to the total compensation.",
                "expected_topics": ["salary", "product manager", "compensation", "average", "experience", "location"],
                "expected_entities": ["$70,000", "$100,000", "$150,000", "$250,000", "San Francisco", "New York"],
                "expected_response_type": "numerical",
                "difficulty": "medium",
                "category": "salary_query",
                "expected_keywords": ["salary", "product manager", "average", "compensation", "experience", "location"]
            },
            {
                "query": "Compare the benefits offered by tech companies vs consulting firms",
                "reference_answer": "Tech companies and consulting firms offer different benefit packages that reflect their distinct cultures and business models. Tech companies typically provide comprehensive health insurance, generous paid time off (often unlimited PTO), stock options or equity grants, flexible work arrangements including remote work options, free meals and snacks, gym memberships, professional development budgets, and unique perks like pet insurance or fertility benefits. Consulting firms, on the other hand, often offer traditional benefits like health insurance and retirement plans, but may have more structured PTO policies, travel allowances, performance-based bonuses, and extensive training programs. However, consulting firms may require more travel and have less work-life balance flexibility compared to tech companies.",
                "expected_topics": ["benefits", "comparison", "tech companies", "consulting", "work-life balance", "perks"],
                "expected_entities": ["health insurance", "PTO", "stock options", "remote work", "gym memberships"],
                "expected_response_type": "comparison",
                "difficulty": "hard",
                "category": "comparative_analysis",
                "expected_keywords": ["benefits", "tech", "consulting", "health insurance", "PTO", "work-life balance"]
            },
            {
                "query": "What are the career growth opportunities in finance sector?",
                "reference_answer": "The finance sector offers diverse career growth opportunities across various specializations. Traditional paths include progression from analyst to associate, vice president, and managing director roles in investment banking, or from junior to senior positions in commercial banking, asset management, and insurance. Emerging areas like fintech, quantitative finance, and sustainable finance provide new growth avenues. Career advancement typically involves gaining specialized certifications (CFA, FRM, CPA), developing expertise in specific financial products or markets, building strong client relationships, and demonstrating leadership skills. The sector also offers opportunities to transition between different areas like moving from investment banking to private equity, or from traditional finance to fintech startups. Geographic mobility is often high, with opportunities to work in major financial centers globally.",
                "expected_topics": ["career growth", "finance", "opportunities", "advancement", "certifications", "specializations"],
                "expected_entities": ["CFA", "FRM", "CPA", "investment banking", "private equity", "fintech"],
                "expected_response_type": "descriptive",
                "difficulty": "medium",
                "category": "career_guidance",
                "expected_keywords": ["career", "growth", "finance", "opportunities", "advancement", "certifications"]
            },
            {
                "query": "How to prepare for investment banking interviews?",
                "reference_answer": "Preparing for investment banking interviews requires a comprehensive approach covering technical knowledge, behavioral skills, and industry awareness. Technical preparation should include understanding financial statements, valuation methods (DCF, comparable company analysis, precedent transactions), accounting principles, and market knowledge. Practice case studies, modeling exercises, and be ready to walk through deals you've worked on. Behavioral preparation involves developing STAR method responses for leadership, teamwork, and problem-solving scenarios. Research the specific bank, its recent deals, culture, and prepare thoughtful questions. Practice with mock interviews, especially for technical questions and brain teasers. Network with current bankers, attend information sessions, and consider internships or relevant experience. Finally, prepare a compelling story about why you want to work in investment banking and what value you can bring to the team.",
                "expected_topics": ["interview preparation", "investment banking", "tips", "guidance", "technical", "behavioral"],
                "expected_entities": ["DCF", "comparable company analysis", "STAR method", "financial statements"],
                "expected_response_type": "instructional",
                "difficulty": "hard",
                "category": "interview_prep",
                "expected_keywords": ["interview", "preparation", "investment banking", "technical", "behavioral", "case studies"]
            },
            {
                "query": "What are the latest trends in artificial intelligence jobs?",
                "reference_answer": "The latest trends in artificial intelligence jobs reflect the rapid evolution of AI technology and its increasing integration across industries. Key trends include the growing demand for AI engineers specializing in large language models (LLMs) and generative AI, increased focus on AI ethics and responsible AI development, rising opportunities in AI product management and AI strategy roles, and the emergence of specialized positions like prompt engineers and AI safety researchers. Companies are also seeking professionals with expertise in MLOps, AI infrastructure, and AI-human collaboration. The job market shows strong growth in AI roles across healthcare, finance, automotive, and retail sectors, with remote work becoming more common. Salaries for AI professionals continue to rise, with senior AI engineers earning $200,000 to $400,000+ in major tech hubs.",
                "expected_topics": ["AI", "artificial intelligence", "trends", "jobs", "latest", "technology"],
                "expected_entities": ["LLMs", "generative AI", "MLOps", "prompt engineers", "AI safety"],
                "expected_response_type": "trend_analysis",
                "difficulty": "hard",
                "category": "trend_analysis",
                "expected_keywords": ["AI", "artificial intelligence", "trends", "jobs", "technology", "machine learning"]
            },
            {
                "query": "Which companies offer the best work-life balance?",
                "reference_answer": "Companies known for offering excellent work-life balance include tech giants like Google, Microsoft, and Salesforce, which provide flexible work arrangements, generous PTO policies, and comprehensive wellness programs. Consulting firms like Bain & Company and McKinsey have also improved their work-life balance through better project management and reduced travel requirements. Other notable companies include Patagonia (known for environmental activism and flexible schedules), HubSpot (with unlimited vacation and remote work options), and Buffer (a fully remote company with strong work-life balance culture). These companies typically offer flexible hours, remote work options, mental health support, family-friendly policies, and discourage excessive overtime. However, work-life balance can vary significantly by team, role, and individual circumstances, so it's important to research specific departments and speak with current employees.",
                "expected_topics": ["work-life balance", "companies", "benefits", "culture", "flexible work", "wellness"],
                "expected_entities": ["Google", "Microsoft", "Salesforce", "Bain & Company", "McKinsey", "Patagonia"],
                "expected_response_type": "company_list",
                "difficulty": "medium",
                "category": "company_culture",
                "expected_keywords": ["work-life balance", "companies", "flexible", "remote work", "wellness", "culture"]
            },
            {
                "query": "What are the requirements for becoming a management consultant?",
                "reference_answer": "Becoming a management consultant typically requires a strong educational background, analytical skills, and relevant experience. Educational requirements often include an MBA from a top-tier business school or a master's degree in a related field, though some firms accept exceptional candidates with bachelor's degrees. Key skills include strong analytical and problem-solving abilities, excellent communication and presentation skills, proficiency in data analysis tools like Excel and PowerPoint, and the ability to work in teams under pressure. Relevant experience in business, finance, or strategy is highly valued. Many consultants also pursue professional certifications like the CFA or CPA. The application process typically involves case interviews, behavioral interviews, and sometimes written tests. Networking, attending company events, and gaining relevant internship experience can significantly improve your chances of being hired by top consulting firms like McKinsey, Bain, BCG, or Deloitte.",
                "expected_topics": ["management consulting", "requirements", "qualifications", "skills", "education", "experience"],
                "expected_entities": ["MBA", "CFA", "CPA", "McKinsey", "Bain", "BCG", "Deloitte"],
                "expected_response_type": "requirement_list",
                "difficulty": "medium",
                "category": "career_requirements",
                "expected_keywords": ["management consulting", "requirements", "MBA", "skills", "experience", "certifications"]
            },
            {
                "query": "How has remote work affected the job market?",
                "reference_answer": "Remote work has fundamentally transformed the job market, creating both opportunities and challenges. On the positive side, it has expanded job opportunities geographically, allowing companies to access global talent pools and employees to work for companies anywhere in the world. This has led to increased competition for talent and, in some cases, higher salaries as companies compete for the best remote workers. Remote work has also enabled better work-life balance for many employees and reduced commuting costs. However, it has also created challenges such as the need for new management skills, potential isolation and collaboration difficulties, and concerns about career advancement and networking. The job market has seen a surge in remote-first companies and hybrid work models, with many traditional companies adopting flexible work arrangements. This shift has also accelerated digital transformation and increased demand for skills in remote collaboration tools and digital communication.",
                "expected_topics": ["remote work", "job market", "impact", "changes", "opportunities", "challenges"],
                "expected_entities": ["global talent pools", "hybrid work", "digital transformation", "remote collaboration"],
                "expected_response_type": "analysis",
                "difficulty": "hard",
                "category": "market_analysis",
                "expected_keywords": ["remote work", "job market", "impact", "opportunities", "challenges", "digital"]
            }
        ]
        
        return reference_dataset
    
    def evaluate_with_reference(self, query: str, generated_answer: str, 
                              reference_answer: str, expected_topics: List[str] = None) -> Dict[str, float]:
        """Evaluate generated answer against reference answer using multiple metrics"""
        
        if not generated_answer or not reference_answer:
            return self._get_empty_metrics()
        
        # 1. BLEU Score
        bleu_score = self._calculate_bleu_score(generated_answer, reference_answer)
        
        # 2. ROUGE Scores
        rouge_scores = self._calculate_rouge_scores(generated_answer, reference_answer)
        
        # 3. METEOR Score
        meteor_score = self._calculate_meteor_score(generated_answer, reference_answer)
        
        # 4. BERTScore (if available)
        bert_scores = self._calculate_bert_score(generated_answer, reference_answer)
        
        # 5. Semantic Similarity
        semantic_similarity = self._calculate_semantic_similarity(generated_answer, reference_answer)
        
        # 6. Keyword Overlap
        keyword_overlap = self._calculate_keyword_overlap(generated_answer, reference_answer)
        
        # 7. Topic Coverage (if expected topics provided)
        topic_coverage = 0.0
        if expected_topics:
            topic_coverage = self._calculate_topic_coverage(generated_answer, expected_topics)
        
        # 8. Answer Length Ratio
        length_ratio = min(len(generated_answer.split()) / len(reference_answer.split()), 1.0)
        
        # 9. Coherence Score
        coherence_score = self._calculate_coherence_score(generated_answer)
        
        # 10. Factual Accuracy (simplified)
        factual_accuracy = self._calculate_factual_accuracy(generated_answer, reference_answer)
        
        return {
            "bleu_score": bleu_score,
            "rouge_scores": rouge_scores,
            "meteor_score": meteor_score,
            "bert_scores": bert_scores,
            "semantic_similarity": semantic_similarity,
            "keyword_overlap": keyword_overlap,
            "topic_coverage": topic_coverage,
            "length_ratio": length_ratio,
            "coherence_score": coherence_score,
            "factual_accuracy": factual_accuracy
        }
    
    def _calculate_bleu_score(self, generated: str, reference: str) -> float:
        """Calculate BLEU score between generated and reference text"""
        try:
            gen_tokens = word_tokenize(generated.lower())
            ref_tokens = word_tokenize(reference.lower())
            
            # Remove stop words for better comparison
            gen_tokens = [token for token in gen_tokens if token not in self.stop_words]
            ref_tokens = [token for token in ref_tokens if token not in self.stop_words]
            
            if not gen_tokens or not ref_tokens:
                return 0.0
            
            return sentence_bleu([ref_tokens], gen_tokens, smoothing_function=self.smoothing)
        except:
            return 0.0
    
    def _calculate_rouge_scores(self, generated: str, reference: str) -> Dict[str, float]:
        """Calculate ROUGE scores"""
        try:
            scores = self.rouge_scorer.score(reference, generated)
            return {
                "rouge1": scores["rouge1"].fmeasure,
                "rouge2": scores["rouge2"].fmeasure,
                "rougeL": scores["rougeL"].fmeasure
            }
        except:
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    
    def _calculate_meteor_score(self, generated: str, reference: str) -> float:
        """Calculate METEOR score"""
        try:
            gen_tokens = word_tokenize(generated.lower())
            ref_tokens = word_tokenize(reference.lower())
            return meteor_score([ref_tokens], gen_tokens)
        except:
            return 0.0
    
    def _calculate_bert_score(self, generated: str, reference: str) -> Dict[str, float]:
        """Calculate BERTScore if available"""
        if not BERTSCORE_AVAILABLE:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        try:
            P, R, F1 = bert_score([generated], [reference], lang="en", verbose=False)
            return {
                "precision": P.item(),
                "recall": R.item(),
                "f1": F1.item()
            }
        except:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    def _calculate_semantic_similarity(self, generated: str, reference: str) -> float:
        """Calculate semantic similarity using sentence transformers"""
        try:
            gen_embedding = self.sentence_model.encode([generated])
            ref_embedding = self.sentence_model.encode([reference])
            similarity = cosine_similarity(gen_embedding, ref_embedding)[0][0]
            return similarity
        except:
            return 0.0
    
    def _calculate_keyword_overlap(self, generated: str, reference: str) -> float:
        """Calculate keyword overlap between generated and reference text"""
        try:
            gen_words = set(word.lower() for word in word_tokenize(generated) if word.isalpha())
            ref_words = set(word.lower() for word in word_tokenize(reference) if word.isalpha())
            
            # Remove stop words
            gen_words = gen_words - self.stop_words
            ref_words = ref_words - self.stop_words
            
            if not ref_words:
                return 0.0
            
            overlap = len(gen_words.intersection(ref_words))
            return overlap / len(ref_words)
        except:
            return 0.0
    
    def _calculate_topic_coverage(self, generated: str, expected_topics: List[str]) -> float:
        """Calculate how well the generated text covers expected topics"""
        generated_lower = generated.lower()
        covered_topics = sum(1 for topic in expected_topics if topic.lower() in generated_lower)
        return covered_topics / len(expected_topics) if expected_topics else 0.0
    
    def _calculate_coherence_score(self, text: str) -> float:
        """Calculate coherence of the generated text"""
        try:
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if len(sentences) < 2:
                return 1.0
            
            embeddings = self.sentence_model.encode(sentences)
            similarities = []
            
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
                similarities.append(sim)
            
            return np.mean(similarities) if similarities else 0.0
        except:
            return 0.0
    
    def _calculate_factual_accuracy(self, generated: str, reference: str) -> float:
        """Calculate factual accuracy (simplified version)"""
        try:
            # Extract numbers and entities from both texts
            gen_numbers = re.findall(r'\d+', generated)
            ref_numbers = re.findall(r'\d+', reference)
            
            gen_entities = re.findall(r'\b[A-Z][a-z]+\b', generated)
            ref_entities = re.findall(r'\b[A-Z][a-z]+\b', reference)
            
            # Calculate overlap
            number_overlap = len(set(gen_numbers).intersection(set(ref_numbers)))
            entity_overlap = len(set(gen_entities).intersection(set(ref_entities)))
            
            total_ref_items = len(ref_numbers) + len(ref_entities)
            if total_ref_items == 0:
                return 1.0
            
            accuracy = (number_overlap + entity_overlap) / total_ref_items
            return min(accuracy, 1.0)
        except:
            return 0.0
    
    def _get_empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics when evaluation fails"""
        return {
            "bleu_score": 0.0,
            "rouge_scores": {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0},
            "meteor_score": 0.0,
            "bert_scores": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
            "semantic_similarity": 0.0,
            "keyword_overlap": 0.0,
            "topic_coverage": 0.0,
            "length_ratio": 0.0,
            "coherence_score": 0.0,
            "factual_accuracy": 0.0
        }
    
    def run_advanced_evaluation(self) -> Dict[str, Any]:
        """Run advanced evaluation with reference answers"""
        
        print("🚀 Starting Advanced RAG Evaluation with Reference Answers...")
        print("=" * 60)
        
        reference_dataset = self.create_reference_dataset()
        results = []
        
        for i, test_case in enumerate(reference_dataset):
            print(f"📊 Evaluating query {i+1}/{len(reference_dataset)}: {test_case['query'][:50]}...")
            
            start_time = datetime.now()
            
            # Get generated answer
            try:
                generated_answer = route_query(test_case["query"])
            except Exception as e:
                generated_answer = ""
                print(f"   ❌ Generation error: {e}")
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Evaluate with reference
            evaluation_metrics = self.evaluate_with_reference(
                query=test_case["query"],
                generated_answer=generated_answer,
                reference_answer=test_case["reference_answer"],
                expected_topics=test_case.get("expected_topics", [])
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(evaluation_metrics)
            
            result = {
                "query": test_case["query"],
                "reference_answer": test_case["reference_answer"],
                "generated_answer": generated_answer,
                "response_time": response_time,
                "difficulty": test_case["difficulty"],
                "category": test_case["category"],
                "evaluation_metrics": evaluation_metrics,
                "overall_score": overall_score,
                "timestamp": start_time.isoformat()
            }
            
            results.append(result)
            
            # Print quick results
            print(f"   📈 Overall Score: {overall_score:.3f}")
            print(f"   ⏱️  Response Time: {response_time:.2f}s")
            print(f"   🎯 BLEU: {evaluation_metrics['bleu_score']:.3f}")
            print(f"   🔍 ROUGE-L: {evaluation_metrics['rouge_scores']['rougeL']:.3f}")
            print(f"   🧠 Semantic Similarity: {evaluation_metrics['semantic_similarity']:.3f}")
            print()
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_advanced_aggregate_metrics(results)
        
        # Generate comprehensive report
        report = self._generate_advanced_report(results, aggregate_metrics)
        
        return {
            "individual_results": results,
            "aggregate_metrics": aggregate_metrics,
            "report": report,
            "evaluation_timestamp": datetime.now().isoformat()
        }
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall score from all metrics"""
        
        # Weighted combination of different metrics
        weights = {
            "bleu_score": 0.15,
            "rouge_scores": 0.20,  # Will use ROUGE-L
            "meteor_score": 0.10,
            "bert_scores": 0.15,   # Will use F1
            "semantic_similarity": 0.20,
            "keyword_overlap": 0.10,
            "topic_coverage": 0.05,
            "coherence_score": 0.05
        }
        
        overall_score = 0.0
        
        # BLEU score
        overall_score += metrics["bleu_score"] * weights["bleu_score"]
        
        # ROUGE-L score
        overall_score += metrics["rouge_scores"]["rougeL"] * weights["rouge_scores"]
        
        # METEOR score
        overall_score += metrics["meteor_score"] * weights["meteor_score"]
        
        # BERTScore F1
        overall_score += metrics["bert_scores"]["f1"] * weights["bert_scores"]
        
        # Semantic similarity
        overall_score += metrics["semantic_similarity"] * weights["semantic_similarity"]
        
        # Keyword overlap
        overall_score += metrics["keyword_overlap"] * weights["keyword_overlap"]
        
        # Topic coverage
        overall_score += metrics["topic_coverage"] * weights["topic_coverage"]
        
        # Coherence score
        overall_score += metrics["coherence_score"] * weights["coherence_score"]
        
        return min(overall_score, 1.0)
    
    def _calculate_advanced_aggregate_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate advanced aggregate metrics"""
        
        # Extract all metrics
        bleu_scores = [r["evaluation_metrics"]["bleu_score"] for r in results]
        rouge_l_scores = [r["evaluation_metrics"]["rouge_scores"]["rougeL"] for r in results]
        meteor_scores = [r["evaluation_metrics"]["meteor_score"] for r in results]
        bert_f1_scores = [r["evaluation_metrics"]["bert_scores"]["f1"] for r in results]
        semantic_similarities = [r["evaluation_metrics"]["semantic_similarity"] for r in results]
        keyword_overlaps = [r["evaluation_metrics"]["keyword_overlap"] for r in results]
        topic_coverages = [r["evaluation_metrics"]["topic_coverage"] for r in results]
        coherence_scores = [r["evaluation_metrics"]["coherence_score"] for r in results]
        overall_scores = [r["overall_score"] for r in results]
        response_times = [r["response_time"] for r in results]
        
        # Calculate statistics
        def calc_stats(scores):
            return {
                "mean": np.mean(scores),
                "std": np.std(scores),
                "min": np.min(scores),
                "max": np.max(scores),
                "median": np.median(scores)
            }
        
        return {
            "overall": {
                "total_queries": len(results),
                "overall_score": calc_stats(overall_scores),
                "response_time": calc_stats(response_times)
            },
            "individual_metrics": {
                "bleu_score": calc_stats(bleu_scores),
                "rouge_l_score": calc_stats(rouge_l_scores),
                "meteor_score": calc_stats(meteor_scores),
                "bert_f1_score": calc_stats(bert_f1_scores),
                "semantic_similarity": calc_stats(semantic_similarities),
                "keyword_overlap": calc_stats(keyword_overlaps),
                "topic_coverage": calc_stats(topic_coverages),
                "coherence_score": calc_stats(coherence_scores)
            }
        }
    
    def _generate_advanced_report(self, results: List[Dict], aggregate_metrics: Dict) -> str:
        """Generate comprehensive advanced report"""
        
        overall = aggregate_metrics["overall"]
        individual = aggregate_metrics["individual_metrics"]
        
        report = f"""
# Advanced RAG System Benchmark Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Queries Evaluated:** {overall['total_queries']}
- **Overall Performance Score:** {overall['overall_score']['mean']:.3f} ± {overall['overall_score']['std']:.3f}
- **Average Response Time:** {overall['response_time']['mean']:.2f}s ± {overall['response_time']['std']:.2f}s

## Detailed Metrics Analysis

### BLEU Score
- **Mean:** {individual['bleu_score']['mean']:.3f} ± {individual['bleu_score']['std']:.3f}
- **Range:** {individual['bleu_score']['min']:.3f} - {individual['bleu_score']['max']:.3f}
- **Median:** {individual['bleu_score']['median']:.3f}

### ROUGE-L Score
- **Mean:** {individual['rouge_l_score']['mean']:.3f} ± {individual['rouge_l_score']['std']:.3f}
- **Range:** {individual['rouge_l_score']['min']:.3f} - {individual['rouge_l_score']['max']:.3f}
- **Median:** {individual['rouge_l_score']['median']:.3f}

### METEOR Score
- **Mean:** {individual['meteor_score']['mean']:.3f} ± {individual['meteor_score']['std']:.3f}
- **Range:** {individual['meteor_score']['min']:.3f} - {individual['meteor_score']['max']:.3f}
- **Median:** {individual['meteor_score']['median']:.3f}

### BERTScore F1
- **Mean:** {individual['bert_f1_score']['mean']:.3f} ± {individual['bert_f1_score']['std']:.3f}
- **Range:** {individual['bert_f1_score']['min']:.3f} - {individual['bert_f1_score']['max']:.3f}
- **Median:** {individual['bert_f1_score']['median']:.3f}

### Semantic Similarity
- **Mean:** {individual['semantic_similarity']['mean']:.3f} ± {individual['semantic_similarity']['std']:.3f}
- **Range:** {individual['semantic_similarity']['min']:.3f} - {individual['semantic_similarity']['max']:.3f}
- **Median:** {individual['semantic_similarity']['median']:.3f}

### Keyword Overlap
- **Mean:** {individual['keyword_overlap']['mean']:.3f} ± {individual['keyword_overlap']['std']:.3f}
- **Range:** {individual['keyword_overlap']['min']:.3f} - {individual['keyword_overlap']['max']:.3f}
- **Median:** {individual['keyword_overlap']['median']:.3f}

### Topic Coverage
- **Mean:** {individual['topic_coverage']['mean']:.3f} ± {individual['topic_coverage']['std']:.3f}
- **Range:** {individual['topic_coverage']['min']:.3f} - {individual['topic_coverage']['max']:.3f}
- **Median:** {individual['topic_coverage']['median']:.3f}

### Coherence Score
- **Mean:** {individual['coherence_score']['mean']:.3f} ± {individual['coherence_score']['std']:.3f}
- **Range:** {individual['coherence_score']['min']:.3f} - {individual['coherence_score']['max']:.3f}
- **Median:** {individual['coherence_score']['median']:.3f}

## Individual Query Results
"""
        
        for i, result in enumerate(results):
            metrics = result["evaluation_metrics"]
            report += f"""
### Query {i+1}: {result['query'][:60]}...
- **Overall Score:** {result['overall_score']:.3f}
- **Response Time:** {result['response_time']:.2f}s
- **Difficulty:** {result['difficulty']}
- **Category:** {result['category']}

**Detailed Metrics:**
- BLEU: {metrics['bleu_score']:.3f}
- ROUGE-L: {metrics['rouge_scores']['rougeL']:.3f}
- METEOR: {metrics['meteor_score']:.3f}
- BERT F1: {metrics['bert_scores']['f1']:.3f}
- Semantic Similarity: {metrics['semantic_similarity']:.3f}
- Keyword Overlap: {metrics['keyword_overlap']:.3f}
- Topic Coverage: {metrics['topic_coverage']:.3f}
- Coherence: {metrics['coherence_score']:.3f}

**Generated Answer:**
{result['generated_answer'][:300]}{'...' if len(result['generated_answer']) > 300 else ''}

**Reference Answer:**
{result['reference_answer'][:300]}{'...' if len(result['reference_answer']) > 300 else ''}

---
"""
        
        return report

def main():
    """Run the advanced RAG evaluation"""
    evaluator = AdvancedRAGEvaluator()
    
    print("🔍 Advanced RAG System Evaluation Framework")
    print("=" * 60)
    
    # Run advanced evaluation
    evaluation_results = evaluator.run_advanced_evaluation()
    
    # Save results
    results_file = Path("advanced_rag_evaluation_results.json")
    with open(results_file, 'w') as f:
        json.dump(evaluation_results, f, indent=2, default=str)
    
    # Save report
    report_file = Path("advanced_rag_benchmark_report.md")
    with open(report_file, 'w') as f:
        f.write(evaluation_results["report"])
    
    print(f"\n✅ Advanced evaluation complete!")
    print(f"📊 Results saved to: {results_file}")
    print(f"📋 Report saved to: {report_file}")
    
    # Print summary
    overall = evaluation_results["aggregate_metrics"]["overall"]
    print(f"\n📈 Summary:")
    print(f"   Overall Score: {overall['overall_score']['mean']:.3f} ± {overall['overall_score']['std']:.3f}")
    print(f"   Response Time: {overall['response_time']['mean']:.2f}s ± {overall['response_time']['std']:.2f}s")

if __name__ == "__main__":
    main()
