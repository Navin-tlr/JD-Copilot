"""
RAG System Evaluation Framework
Comprehensive evaluation of retrieval, generation, and overall RAG performance
"""

import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from pathlib import Path
import logging

# Evaluation metrics
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# RAG components
from app.rag import retrieve_snippets, synthesize_answer
from app.agent import route_query
from app.database import PlacementDatabase

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

class RAGEvaluator:
    """Comprehensive RAG system evaluator with multiple metrics"""
    
    def __init__(self):
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        self.smoothing = SmoothingFunction().method4
        self.stop_words = set(stopwords.words('english'))
        
        # Initialize database for context
        self.db = PlacementDatabase()
        
    def create_test_dataset(self) -> List[Dict[str, Any]]:
        """Create comprehensive test dataset with ground truth answers"""
        
        test_queries = [
            {
                "query": "What are the top companies hiring for software engineering roles?",
                "expected_topics": ["companies", "software engineering", "hiring", "technology"],
                "expected_companies": ["Google", "Microsoft", "Amazon", "Apple", "Meta"],
                "expected_response_type": "list_companies",
                "difficulty": "easy",
                "category": "company_search"
            },
            {
                "query": "What skills are required for data science positions?",
                "expected_topics": ["data science", "skills", "requirements", "technical"],
                "expected_skills": ["Python", "R", "SQL", "machine learning", "statistics"],
                "expected_response_type": "skill_list",
                "difficulty": "medium",
                "category": "skill_analysis"
            },
            {
                "query": "What is the average salary for product manager roles?",
                "expected_topics": ["salary", "product manager", "compensation", "average"],
                "expected_response_type": "numerical",
                "difficulty": "medium",
                "category": "salary_query"
            },
            {
                "query": "Compare the benefits offered by tech companies vs consulting firms",
                "expected_topics": ["benefits", "comparison", "tech companies", "consulting"],
                "expected_response_type": "comparison",
                "difficulty": "hard",
                "category": "comparative_analysis"
            },
            {
                "query": "What are the career growth opportunities in finance sector?",
                "expected_topics": ["career growth", "finance", "opportunities", "advancement"],
                "expected_response_type": "descriptive",
                "difficulty": "medium",
                "category": "career_guidance"
            },
            {
                "query": "How to prepare for investment banking interviews?",
                "expected_topics": ["interview preparation", "investment banking", "tips", "guidance"],
                "expected_response_type": "instructional",
                "difficulty": "hard",
                "category": "interview_prep"
            },
            {
                "query": "What are the latest trends in artificial intelligence jobs?",
                "expected_topics": ["AI", "artificial intelligence", "trends", "jobs", "latest"],
                "expected_response_type": "trend_analysis",
                "difficulty": "hard",
                "category": "trend_analysis"
            },
            {
                "query": "Which companies offer the best work-life balance?",
                "expected_topics": ["work-life balance", "companies", "benefits", "culture"],
                "expected_response_type": "company_list",
                "difficulty": "medium",
                "category": "company_culture"
            },
            {
                "query": "What are the requirements for becoming a management consultant?",
                "expected_topics": ["management consulting", "requirements", "qualifications", "skills"],
                "expected_response_type": "requirement_list",
                "difficulty": "medium",
                "category": "career_requirements"
            },
            {
                "query": "How has remote work affected the job market?",
                "expected_topics": ["remote work", "job market", "impact", "changes"],
                "expected_response_type": "analysis",
                "difficulty": "hard",
                "category": "market_analysis"
            }
        ]
        
        return test_queries
    
    def evaluate_retrieval_quality(self, query: str, retrieved_snippets: List[Dict]) -> Dict[str, float]:
        """Evaluate the quality of retrieved documents"""
        
        if not retrieved_snippets:
            return {
                "retrieval_success": 0.0,
                "avg_relevance_score": 0.0,
                "coverage_score": 0.0,
                "diversity_score": 0.0
            }
        
        # 1. Retrieval Success Rate
        retrieval_success = 1.0 if len(retrieved_snippets) > 0 else 0.0
        
        # 2. Relevance Score (semantic similarity)
        query_embedding = self.sentence_model.encode([query])
        relevance_scores = []
        
        for snippet in retrieved_snippets:
            snippet_text = snippet.get('text', '')
            if snippet_text:
                snippet_embedding = self.sentence_model.encode([snippet_text])
                similarity = cosine_similarity(query_embedding, snippet_embedding)[0][0]
                relevance_scores.append(similarity)
        
        avg_relevance_score = np.mean(relevance_scores) if relevance_scores else 0.0
        
        # 3. Coverage Score (how well snippets cover the query)
        all_text = " ".join([snippet.get('text', '') for snippet in retrieved_snippets])
        coverage_score = self._calculate_coverage_score(query, all_text)
        
        # 4. Diversity Score (how diverse are the retrieved snippets)
        diversity_score = self._calculate_diversity_score(retrieved_snippets)
        
        return {
            "retrieval_success": retrieval_success,
            "avg_relevance_score": avg_relevance_score,
            "coverage_score": coverage_score,
            "diversity_score": diversity_score
        }
    
    def evaluate_generation_quality(self, query: str, generated_answer: str, 
                                  expected_topics: List[str] = None) -> Dict[str, float]:
        """Evaluate the quality of generated answers"""
        
        if not generated_answer:
            return {
                "answer_length": 0.0,
                "coherence_score": 0.0,
                "relevance_score": 0.0,
                "completeness_score": 0.0,
                "bleu_score": 0.0,
                "rouge_scores": {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
            }
        
        # 1. Answer Length (normalized)
        answer_length = min(len(generated_answer.split()) / 100, 1.0)
        
        # 2. Coherence Score (semantic consistency)
        coherence_score = self._calculate_coherence_score(generated_answer)
        
        # 3. Relevance Score (how relevant to the query)
        relevance_score = self._calculate_relevance_score(query, generated_answer)
        
        # 4. Completeness Score (covers expected topics)
        completeness_score = 0.0
        if expected_topics:
            completeness_score = self._calculate_completeness_score(generated_answer, expected_topics)
        
        # 5. BLEU Score (if we had reference answers)
        bleu_score = 0.0  # Would need reference answers for this
        
        # 6. ROUGE Scores (if we had reference answers)
        rouge_scores = {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
        # Would need reference answers for this
        
        return {
            "answer_length": answer_length,
            "coherence_score": coherence_score,
            "relevance_score": relevance_score,
            "completeness_score": completeness_score,
            "bleu_score": bleu_score,
            "rouge_scores": rouge_scores
        }
    
    def evaluate_end_to_end_rag(self, query: str, expected_response_type: str, 
                               expected_topics: List[str] = None) -> Dict[str, Any]:
        """Evaluate the complete RAG pipeline"""
        
        start_time = datetime.now()
        
        # 1. Retrieve snippets
        try:
            retrieved_snippets = retrieve_snippets(query, top_k=5, filters={})
        except Exception as e:
            retrieved_snippets = []
            print(f"Retrieval error: {e}")
        
        # 2. Generate answer
        try:
            generated_answer = route_query(query)
        except Exception as e:
            generated_answer = ""
            print(f"Generation error: {e}")
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # 3. Evaluate retrieval quality
        retrieval_metrics = self.evaluate_retrieval_quality(query, retrieved_snippets)
        
        # 4. Evaluate generation quality
        generation_metrics = self.evaluate_generation_quality(query, generated_answer, expected_topics)
        
        # 5. Overall RAG score
        overall_score = self._calculate_overall_rag_score(retrieval_metrics, generation_metrics)
        
        return {
            "query": query,
            "expected_response_type": expected_response_type,
            "retrieved_snippets_count": len(retrieved_snippets),
            "generated_answer": generated_answer,
            "response_time": response_time,
            "retrieval_metrics": retrieval_metrics,
            "generation_metrics": generation_metrics,
            "overall_score": overall_score,
            "timestamp": start_time.isoformat()
        }
    
    def _calculate_coverage_score(self, query: str, text: str) -> float:
        """Calculate how well the text covers the query topics"""
        query_words = set(word.lower() for word in word_tokenize(query) if word.isalpha())
        text_words = set(word.lower() for word in word_tokenize(text) if word.isalpha())
        
        if not query_words:
            return 0.0
        
        coverage = len(query_words.intersection(text_words)) / len(query_words)
        return min(coverage, 1.0)
    
    def _calculate_diversity_score(self, snippets: List[Dict]) -> float:
        """Calculate diversity of retrieved snippets"""
        if len(snippets) <= 1:
            return 0.0
        
        texts = [snippet.get('text', '') for snippet in snippets]
        embeddings = self.sentence_model.encode(texts)
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                similarities.append(sim)
        
        # Diversity is inverse of average similarity
        avg_similarity = np.mean(similarities) if similarities else 0.0
        diversity = 1.0 - avg_similarity
        return max(0.0, diversity)
    
    def _calculate_coherence_score(self, text: str) -> float:
        """Calculate coherence of the generated text"""
        sentences = text.split('.')
        if len(sentences) < 2:
            return 1.0
        
        # Simple coherence based on sentence similarity
        embeddings = self.sentence_model.encode(sentences)
        similarities = []
        
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _calculate_relevance_score(self, query: str, answer: str) -> float:
        """Calculate relevance of answer to query"""
        query_embedding = self.sentence_model.encode([query])
        answer_embedding = self.sentence_model.encode([answer])
        
        similarity = cosine_similarity(query_embedding, answer_embedding)[0][0]
        return similarity
    
    def _calculate_completeness_score(self, answer: str, expected_topics: List[str]) -> float:
        """Calculate how completely the answer covers expected topics"""
        answer_lower = answer.lower()
        covered_topics = sum(1 for topic in expected_topics if topic.lower() in answer_lower)
        return covered_topics / len(expected_topics) if expected_topics else 0.0
    
    def _calculate_overall_rag_score(self, retrieval_metrics: Dict, generation_metrics: Dict) -> float:
        """Calculate overall RAG performance score"""
        # Weighted combination of retrieval and generation metrics
        retrieval_weight = 0.4
        generation_weight = 0.6
        
        retrieval_score = (
            retrieval_metrics["retrieval_success"] * 0.3 +
            retrieval_metrics["avg_relevance_score"] * 0.3 +
            retrieval_metrics["coverage_score"] * 0.2 +
            retrieval_metrics["diversity_score"] * 0.2
        )
        
        generation_score = (
            generation_metrics["coherence_score"] * 0.3 +
            generation_metrics["relevance_score"] * 0.3 +
            generation_metrics["completeness_score"] * 0.2 +
            generation_metrics["answer_length"] * 0.2
        )
        
        overall_score = (retrieval_score * retrieval_weight + 
                        generation_score * generation_weight)
        
        return min(overall_score, 1.0)
    
    def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive evaluation on all test queries"""
        
        print("🚀 Starting comprehensive RAG evaluation...")
        
        test_dataset = self.create_test_dataset()
        results = []
        
        for i, test_case in enumerate(test_dataset):
            print(f"📊 Evaluating query {i+1}/{len(test_dataset)}: {test_case['query'][:50]}...")
            
            result = self.evaluate_end_to_end_rag(
                query=test_case["query"],
                expected_response_type=test_case["expected_response_type"],
                expected_topics=test_case.get("expected_topics", [])
            )
            
            result.update({
                "difficulty": test_case["difficulty"],
                "category": test_case["category"]
            })
            
            results.append(result)
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(results)
        
        # Generate benchmark report
        benchmark_report = self._generate_benchmark_report(results, aggregate_metrics)
        
        return {
            "individual_results": results,
            "aggregate_metrics": aggregate_metrics,
            "benchmark_report": benchmark_report,
            "evaluation_timestamp": datetime.now().isoformat()
        }
    
    def _calculate_aggregate_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate metrics across all test cases"""
        
        # Overall scores
        overall_scores = [r["overall_score"] for r in results]
        retrieval_scores = [r["retrieval_metrics"]["avg_relevance_score"] for r in results]
        generation_scores = [r["generation_metrics"]["relevance_score"] for r in results]
        response_times = [r["response_time"] for r in results]
        
        # By difficulty
        difficulty_metrics = {}
        for difficulty in ["easy", "medium", "hard"]:
            diff_results = [r for r in results if r["difficulty"] == difficulty]
            if diff_results:
                difficulty_metrics[difficulty] = {
                    "count": len(diff_results),
                    "avg_overall_score": np.mean([r["overall_score"] for r in diff_results]),
                    "avg_response_time": np.mean([r["response_time"] for r in diff_results])
                }
        
        # By category
        category_metrics = {}
        for category in set(r["category"] for r in results):
            cat_results = [r for r in results if r["category"] == category]
            if cat_results:
                category_metrics[category] = {
                    "count": len(cat_results),
                    "avg_overall_score": np.mean([r["overall_score"] for r in cat_results]),
                    "avg_response_time": np.mean([r["response_time"] for r in cat_results])
                }
        
        return {
            "overall": {
                "total_queries": len(results),
                "avg_overall_score": np.mean(overall_scores),
                "std_overall_score": np.std(overall_scores),
                "avg_retrieval_score": np.mean(retrieval_scores),
                "avg_generation_score": np.mean(generation_scores),
                "avg_response_time": np.mean(response_times),
                "std_response_time": np.std(response_times)
            },
            "by_difficulty": difficulty_metrics,
            "by_category": category_metrics
        }
    
    def _generate_benchmark_report(self, results: List[Dict], aggregate_metrics: Dict) -> str:
        """Generate a comprehensive benchmark report"""
        
        report = f"""
# RAG System Benchmark Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Queries Evaluated:** {aggregate_metrics['overall']['total_queries']}
- **Overall Performance Score:** {aggregate_metrics['overall']['avg_overall_score']:.3f}
- **Average Response Time:** {aggregate_metrics['overall']['avg_response_time']:.2f}s
- **Retrieval Quality:** {aggregate_metrics['overall']['avg_retrieval_score']:.3f}
- **Generation Quality:** {aggregate_metrics['overall']['avg_generation_score']:.3f}

## Performance by Difficulty
"""
        
        for difficulty, metrics in aggregate_metrics['by_difficulty'].items():
            report += f"""
### {difficulty.title()} Queries ({metrics['count']} queries)
- Average Score: {metrics['avg_overall_score']:.3f}
- Average Response Time: {metrics['avg_response_time']:.2f}s
"""
        
        report += "\n## Performance by Category\n"
        
        for category, metrics in aggregate_metrics['by_category'].items():
            report += f"""
### {category.replace('_', ' ').title()} ({metrics['count']} queries)
- Average Score: {metrics['avg_overall_score']:.3f}
- Average Response Time: {metrics['avg_response_time']:.2f}s
"""
        
        report += f"""

## Detailed Results
"""
        
        for i, result in enumerate(results):
            report += f"""
### Query {i+1}: {result['query'][:60]}...
- **Difficulty:** {result['difficulty']}
- **Category:** {result['category']}
- **Overall Score:** {result['overall_score']:.3f}
- **Response Time:** {result['response_time']:.2f}s
- **Retrieved Snippets:** {result['retrieved_snippets_count']}
- **Answer Length:** {len(result['generated_answer'].split())} words

**Retrieval Metrics:**
- Success Rate: {result['retrieval_metrics']['retrieval_success']:.3f}
- Relevance Score: {result['retrieval_metrics']['avg_relevance_score']:.3f}
- Coverage Score: {result['retrieval_metrics']['coverage_score']:.3f}
- Diversity Score: {result['retrieval_metrics']['diversity_score']:.3f}

**Generation Metrics:**
- Coherence Score: {result['generation_metrics']['coherence_score']:.3f}
- Relevance Score: {result['generation_metrics']['relevance_score']:.3f}
- Completeness Score: {result['generation_metrics']['completeness_score']:.3f}

**Generated Answer:**
{result['generated_answer'][:200]}{'...' if len(result['generated_answer']) > 200 else ''}
"""
        
        return report

def main():
    """Run the RAG evaluation"""
    evaluator = RAGEvaluator()
    
    print("🔍 RAG System Evaluation Framework")
    print("=" * 50)
    
    # Run comprehensive evaluation
    evaluation_results = evaluator.run_comprehensive_evaluation()
    
    # Save results
    results_file = Path("rag_evaluation_results.json")
    with open(results_file, 'w') as f:
        json.dump(evaluation_results, f, indent=2, default=str)
    
    # Save benchmark report
    report_file = Path("rag_benchmark_report.md")
    with open(report_file, 'w') as f:
        f.write(evaluation_results["benchmark_report"])
    
    print(f"\n✅ Evaluation complete!")
    print(f"📊 Results saved to: {results_file}")
    print(f"📋 Report saved to: {report_file}")
    
    # Print summary
    overall = evaluation_results["aggregate_metrics"]["overall"]
    print(f"\n📈 Summary:")
    print(f"   Overall Score: {overall['avg_overall_score']:.3f}")
    print(f"   Response Time: {overall['avg_response_time']:.2f}s")
    print(f"   Retrieval Quality: {overall['avg_retrieval_score']:.3f}")
    print(f"   Generation Quality: {overall['avg_generation_score']:.3f}")

if __name__ == "__main__":
    main()
