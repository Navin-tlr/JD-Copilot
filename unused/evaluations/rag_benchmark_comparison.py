"""
RAG Benchmark Comparison
Compares your RAG system performance against industry benchmarks and standards
"""

import json
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
from pathlib import Path

class RAGBenchmarkComparator:
    """Compare RAG system performance against industry benchmarks"""
    
    def __init__(self):
        # Industry benchmark standards (based on research papers and industry reports)
        self.benchmarks = {
            "excellent": {
                "bleu_score": 0.4,
                "rouge_l": 0.5,
                "meteor_score": 0.6,
                "bert_f1": 0.7,
                "semantic_similarity": 0.8,
                "response_time": 2.0,  # seconds
                "overall_score": 0.8
            },
            "good": {
                "bleu_score": 0.3,
                "rouge_l": 0.4,
                "meteor_score": 0.5,
                "bert_f1": 0.6,
                "semantic_similarity": 0.7,
                "response_time": 3.0,
                "overall_score": 0.7
            },
            "average": {
                "bleu_score": 0.2,
                "rouge_l": 0.3,
                "meteor_score": 0.4,
                "bert_f1": 0.5,
                "semantic_similarity": 0.6,
                "response_time": 4.0,
                "overall_score": 0.6
            },
            "below_average": {
                "bleu_score": 0.1,
                "rouge_l": 0.2,
                "meteor_score": 0.3,
                "bert_f1": 0.4,
                "semantic_similarity": 0.5,
                "response_time": 5.0,
                "overall_score": 0.5
            }
        }
        
        # Specific RAG system benchmarks from literature
        self.rag_benchmarks = {
            "retrieval_quality": {
                "excellent": 0.85,
                "good": 0.75,
                "average": 0.65,
                "below_average": 0.55
            },
            "generation_quality": {
                "excellent": 0.80,
                "good": 0.70,
                "average": 0.60,
                "below_average": 0.50
            },
            "end_to_end_performance": {
                "excellent": 0.82,
                "good": 0.72,
                "average": 0.62,
                "below_average": 0.52
            }
        }
    
    def load_evaluation_results(self, results_file: str) -> Dict[str, Any]:
        """Load evaluation results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Results file {results_file} not found")
            return None
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {results_file}")
            return None
    
    def compare_against_benchmarks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare results against industry benchmarks"""
        
        if not results or "aggregate_metrics" not in results:
            return {"error": "Invalid results format"}
        
        aggregate = results["aggregate_metrics"]
        
        # Extract metrics
        if "individual_metrics" in aggregate:
            # Advanced evaluation results
            individual = aggregate["individual_metrics"]
            metrics = {
                "bleu_score": individual["bleu_score"]["mean"],
                "rouge_l": individual["rouge_l_score"]["mean"],
                "meteor_score": individual["meteor_score"]["mean"],
                "bert_f1": individual["bert_f1_score"]["mean"],
                "semantic_similarity": individual["semantic_similarity"]["mean"],
                "response_time": aggregate["overall"]["response_time"]["mean"],
                "overall_score": aggregate["overall"]["overall_score"]["mean"]
            }
        else:
            # Basic evaluation results
            overall = aggregate["overall"]
            metrics = {
                "overall_score": overall["avg_overall_score"],
                "response_time": overall["avg_response_time"],
                "retrieval_score": overall["avg_retrieval_score"],
                "generation_score": overall["avg_generation_score"]
            }
        
        # Compare against benchmarks
        comparison = {}
        
        for metric_name, value in metrics.items():
            if metric_name in self.benchmarks["excellent"]:
                comparison[metric_name] = self._classify_performance(
                    value, metric_name
                )
        
        # Calculate overall performance grade
        overall_grade = self._calculate_overall_grade(comparison, metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(comparison, metrics)
        
        return {
            "metrics": metrics,
            "comparison": comparison,
            "overall_grade": overall_grade,
            "recommendations": recommendations,
            "benchmark_standards": self.benchmarks
        }
    
    def _classify_performance(self, value: float, metric_name: str) -> Dict[str, Any]:
        """Classify performance level for a specific metric"""
        
        if metric_name not in self.benchmarks["excellent"]:
            return {"level": "unknown", "score": value}
        
        excellent = self.benchmarks["excellent"][metric_name]
        good = self.benchmarks["good"][metric_name]
        average = self.benchmarks["average"][metric_name]
        below_average = self.benchmarks["below_average"][metric_name]
        
        # For response time, lower is better
        if metric_name == "response_time":
            if value <= excellent:
                level = "excellent"
            elif value <= good:
                level = "good"
            elif value <= average:
                level = "average"
            else:
                level = "below_average"
        else:
            # For other metrics, higher is better
            if value >= excellent:
                level = "excellent"
            elif value >= good:
                level = "good"
            elif value >= average:
                level = "average"
            else:
                level = "below_average"
        
        # Calculate percentage of benchmark
        benchmark_value = excellent if level == "excellent" else good if level == "good" else average
        percentage = (value / benchmark_value) * 100 if benchmark_value > 0 else 0
        
        return {
            "level": level,
            "score": value,
            "benchmark": benchmark_value,
            "percentage": min(percentage, 200)  # Cap at 200%
        }
    
    def _calculate_overall_grade(self, comparison: Dict, metrics: Dict) -> Dict[str, Any]:
        """Calculate overall performance grade"""
        
        # Weight different metrics
        weights = {
            "overall_score": 0.3,
            "bleu_score": 0.15,
            "rouge_l": 0.15,
            "semantic_similarity": 0.2,
            "response_time": 0.1,
            "bert_f1": 0.1
        }
        
        weighted_score = 0
        total_weight = 0
        
        for metric, weight in weights.items():
            if metric in comparison:
                level = comparison[metric]["level"]
                level_scores = {"excellent": 4, "good": 3, "average": 2, "below_average": 1}
                weighted_score += level_scores.get(level, 0) * weight
                total_weight += weight
        
        if total_weight == 0:
            return {"grade": "F", "score": 0, "description": "Unable to calculate grade"}
        
        final_score = weighted_score / total_weight
        
        if final_score >= 3.5:
            grade = "A"
            description = "Excellent performance"
        elif final_score >= 3.0:
            grade = "B"
            description = "Good performance"
        elif final_score >= 2.5:
            grade = "C"
            description = "Average performance"
        elif final_score >= 2.0:
            grade = "D"
            description = "Below average performance"
        else:
            grade = "F"
            description = "Poor performance"
        
        return {
            "grade": grade,
            "score": final_score,
            "description": description,
            "percentage": (final_score / 4.0) * 100
        }
    
    def _generate_recommendations(self, comparison: Dict, metrics: Dict) -> List[str]:
        """Generate improvement recommendations based on performance"""
        
        recommendations = []
        
        # Check each metric and provide specific recommendations
        for metric, data in comparison.items():
            if data["level"] in ["below_average", "average"]:
                if metric == "bleu_score":
                    recommendations.append(
                        "Improve text generation quality by fine-tuning the language model "
                        "or using better prompting strategies"
                    )
                elif metric == "rouge_l":
                    recommendations.append(
                        "Enhance answer structure and coherence by improving the generation pipeline"
                    )
                elif metric == "semantic_similarity":
                    recommendations.append(
                        "Improve semantic understanding by using better embedding models "
                        "or fine-tuning on domain-specific data"
                    )
                elif metric == "response_time":
                    recommendations.append(
                        "Optimize system performance by implementing caching, "
                        "using faster models, or improving database queries"
                    )
                elif metric == "bert_f1":
                    recommendations.append(
                        "Enhance answer relevance by improving retrieval quality "
                        "and generation accuracy"
                    )
        
        # General recommendations based on overall performance
        if "overall_score" in metrics:
            overall_score = metrics["overall_score"]
            if overall_score < 0.6:
                recommendations.extend([
                    "Consider implementing a more sophisticated RAG architecture",
                    "Increase the size and quality of your knowledge base",
                    "Fine-tune your language model on domain-specific data",
                    "Implement better retrieval strategies (e.g., hybrid search)"
                ])
            elif overall_score < 0.8:
                recommendations.extend([
                    "Optimize retrieval parameters (top-k, similarity thresholds)",
                    "Implement answer post-processing and validation",
                    "Add more diverse training data for better generalization"
                ])
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def generate_benchmark_report(self, comparison_results: Dict) -> str:
        """Generate comprehensive benchmark comparison report"""
        
        if "error" in comparison_results:
            return f"❌ Error: {comparison_results['error']}"
        
        metrics = comparison_results["metrics"]
        comparison = comparison_results["comparison"]
        overall_grade = comparison_results["overall_grade"]
        recommendations = comparison_results["recommendations"]
        
        report = f"""
# RAG System Benchmark Comparison Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Performance Grade: {overall_grade['grade']} ({overall_grade['percentage']:.1f}%)
**{overall_grade['description']}**

## Detailed Metrics Comparison

| Metric | Your Score | Benchmark | Performance Level | % of Benchmark |
|--------|------------|-----------|-------------------|----------------|
"""
        
        for metric, data in comparison.items():
            report += f"| {metric.replace('_', ' ').title()} | {data['score']:.3f} | {data['benchmark']:.3f} | {data['level'].title()} | {data['percentage']:.1f}% |\n"
        
        report += f"""

## Performance Analysis

### Strengths
"""
        
        # Find strengths
        strengths = []
        for metric, data in comparison.items():
            if data["level"] in ["excellent", "good"]:
                strengths.append(f"- {metric.replace('_', ' ').title()}: {data['level'].title()} performance ({data['percentage']:.1f}% of benchmark)")
        
        if strengths:
            report += "\n".join(strengths)
        else:
            report += "- No significant strengths identified"
        
        report += f"""

### Areas for Improvement
"""
        
        # Find areas for improvement
        improvements = []
        for metric, data in comparison.items():
            if data["level"] in ["below_average", "average"]:
                improvements.append(f"- {metric.replace('_', ' ').title()}: {data['level'].title()} performance ({data['percentage']:.1f}% of benchmark)")
        
        if improvements:
            report += "\n".join(improvements)
        else:
            report += "- All metrics are performing well!"
        
        report += f"""

## Recommendations

"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""

## Benchmark Standards Reference

### Industry Standards
- **Excellent**: BLEU ≥ 0.4, ROUGE-L ≥ 0.5, Response Time ≤ 2s
- **Good**: BLEU ≥ 0.3, ROUGE-L ≥ 0.4, Response Time ≤ 3s  
- **Average**: BLEU ≥ 0.2, ROUGE-L ≥ 0.3, Response Time ≤ 4s
- **Below Average**: BLEU < 0.2, ROUGE-L < 0.3, Response Time > 4s

### Your System Performance
"""
        
        for metric, data in comparison.items():
            benchmark_level = data["benchmark"]
            your_score = data["score"]
            report += f"- **{metric.replace('_', ' ').title()}**: {your_score:.3f} (Benchmark: {benchmark_level:.3f})\n"
        
        report += f"""

## Next Steps

1. **Immediate Actions**: Focus on the lowest-performing metrics first
2. **Short-term**: Implement the top 3 recommendations
3. **Long-term**: Consider architectural improvements for sustained performance
4. **Monitoring**: Set up continuous evaluation to track improvements

---
*This report compares your RAG system against industry benchmarks based on academic research and industry standards.*
"""
        
        return report

def main():
    """Main benchmark comparison function"""
    
    print("🔍 RAG System Benchmark Comparison")
    print("=" * 40)
    
    comparator = RAGBenchmarkComparator()
    
    # Try to load both basic and advanced results
    results_files = [
        "rag_evaluation_results.json",
        "advanced_rag_evaluation_results.json"
    ]
    
    best_results = None
    results_type = None
    
    for results_file in results_files:
        if Path(results_file).exists():
            results = comparator.load_evaluation_results(results_file)
            if results:
                best_results = results
                results_type = results_file
                break
    
    if not best_results:
        print("❌ No evaluation results found. Please run RAG evaluation first.")
        print("   Run: python run_rag_evaluation.py")
        return 1
    
    print(f"📊 Using results from: {results_type}")
    
    # Compare against benchmarks
    comparison_results = comparator.compare_against_benchmarks(best_results)
    
    # Generate report
    report = comparator.generate_benchmark_report(comparison_results)
    
    # Save report
    report_file = "rag_benchmark_comparison_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"✅ Benchmark comparison complete!")
    print(f"📋 Report saved to: {report_file}")
    
    # Print summary
    if "overall_grade" in comparison_results:
        grade = comparison_results["overall_grade"]
        print(f"\n📈 Overall Grade: {grade['grade']} ({grade['percentage']:.1f}%)")
        print(f"   {grade['description']}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
