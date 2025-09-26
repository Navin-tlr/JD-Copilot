"""
Scaling Optimization for 50 PDFs
Performance optimizations and monitoring
"""

import os
import time
import psutil
import requests
from datetime import datetime

class ScaleOptimizer:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def check_system_resources(self):
        """Check current system resources"""
        print("🔍 SYSTEM RESOURCE CHECK")
        print("=" * 40)
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU Usage: {cpu_percent}%")
        
        # Memory Usage
        memory = psutil.virtual_memory()
        print(f"Memory Usage: {memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        print(f"Disk Usage: {disk.percent}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)")
        
        # Available Memory for scaling
        available_memory_gb = (memory.total - memory.used) / (1024**3)
        print(f"Available Memory: {available_memory_gb:.1f}GB")
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "available_memory_gb": available_memory_gb,
            "disk_percent": disk.percent
        }
    
    def test_response_times(self, num_queries=5):
        """Test current response times"""
        print(f"\n⏱️ RESPONSE TIME TEST ({num_queries} queries)")
        print("=" * 40)
        
        test_queries = [
            "How many companies are offering finance roles?",
            "What are the most in-demand skills across all companies?",
            "Which companies are hiring for HR roles?",
            "What tools are mentioned in the job descriptions?",
            "Which jobs are based in Bangalore?"
        ]
        
        response_times = []
        
        for i, query in enumerate(test_queries[:num_queries], 1):
            print(f"Query {i}: {query[:50]}...")
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/chat/send",
                    json={
                        "content": query,
                        "session_id": f"scale_test_{i}",
                        "user_id": "scale_test_user"
                    },
                    timeout=120
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = end_time - start_time
                    response_times.append(response_time)
                    print(f"  ✅ {response_time:.1f}s")
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                end_time = time.time()
                print(f"  ❌ Error: {str(e)}")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\nResponse Time Summary:")
            print(f"  Average: {avg_time:.1f}s")
            print(f"  Fastest: {min_time:.1f}s")
            print(f"  Slowest: {max_time:.1f}s")
            
            return {
                "average_time": avg_time,
                "max_time": max_time,
                "min_time": min_time,
                "response_times": response_times
            }
        
        return None
    
    def estimate_scaling_requirements(self, target_pdfs=50):
        """Estimate requirements for scaling to target PDFs"""
        print(f"\n📊 SCALING ESTIMATES FOR {target_pdfs} PDFs")
        print("=" * 40)
        
        # Current metrics
        current_pdfs = 7
        current_data_size = 343  # MB
        current_vectors = 1000  # Estimated
        
        # Scaling factors
        pdf_ratio = target_pdfs / current_pdfs
        estimated_data_size = current_data_size * pdf_ratio
        estimated_vectors = current_vectors * pdf_ratio
        
        print(f"Current: {current_pdfs} PDFs, {current_data_size}MB, ~{current_vectors} vectors")
        print(f"Target: {target_pdfs} PDFs, {estimated_data_size:.0f}MB, ~{estimated_vectors:.0f} vectors")
        print(f"Scaling Factor: {pdf_ratio:.1f}x")
        
        # Memory requirements
        vector_memory_mb = estimated_vectors * 0.5  # ~0.5MB per 1000 vectors
        total_memory_gb = (estimated_data_size + vector_memory_mb) / 1024
        
        print(f"\nMemory Requirements:")
        print(f"  Data Storage: {estimated_data_size:.0f}MB")
        print(f"  Vector Index: {vector_memory_mb:.0f}MB")
        print(f"  Total Estimated: {total_memory_gb:.1f}GB")
        
        # Response time estimates
        current_avg_time = 45  # seconds (from our tests)
        estimated_avg_time = current_avg_time * (pdf_ratio ** 0.5)  # Square root scaling
        
        print(f"\nPerformance Estimates:")
        print(f"  Current Avg Response: {current_avg_time}s")
        print(f"  Estimated Avg Response: {estimated_avg_time:.1f}s")
        print(f"  Target Response Time: <30s")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if total_memory_gb > 4:
            print(f"  ⚠️ Consider memory optimization (estimated {total_memory_gb:.1f}GB)")
        if estimated_avg_time > 30:
            print(f"  ⚠️ Consider response time optimization (estimated {estimated_avg_time:.1f}s)")
        if pdf_ratio > 5:
            print(f"  ⚠️ Consider batch processing for ingestion")
        
        return {
            "estimated_data_size_mb": estimated_data_size,
            "estimated_vectors": estimated_vectors,
            "estimated_memory_gb": total_memory_gb,
            "estimated_response_time": estimated_avg_time
        }
    
    def generate_optimization_recommendations(self):
        """Generate specific optimization recommendations"""
        print(f"\n🔧 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 40)
        
        recommendations = [
            {
                "category": "Memory Optimization",
                "priority": "High",
                "actions": [
                    "Implement vector chunking strategy",
                    "Add memory monitoring and cleanup",
                    "Optimize embedding storage",
                    "Consider vector compression"
                ]
            },
            {
                "category": "Response Time Optimization", 
                "priority": "High",
                "actions": [
                    "Add response caching for common queries",
                    "Implement query result caching",
                    "Optimize LLM model selection",
                    "Add query preprocessing"
                ]
            },
            {
                "category": "Database Optimization",
                "priority": "Medium", 
                "actions": [
                    "Add database indexing",
                    "Implement connection pooling",
                    "Optimize SQL queries",
                    "Add query result caching"
                ]
            },
            {
                "category": "Ingestion Optimization",
                "priority": "Medium",
                "actions": [
                    "Implement batch PDF processing",
                    "Add parallel processing",
                    "Optimize PDF parsing",
                    "Add progress tracking"
                ]
            },
            {
                "category": "Monitoring & Alerting",
                "priority": "Low",
                "actions": [
                    "Add performance monitoring",
                    "Implement health checks",
                    "Add resource usage alerts",
                    "Create performance dashboards"
                ]
            }
        ]
        
        for rec in recommendations:
            print(f"\n{rec['category']} ({rec['priority']} Priority):")
            for action in rec['actions']:
                print(f"  • {action}")
        
        return recommendations
    
    def run_scaling_analysis(self):
        """Run complete scaling analysis"""
        print("🚀 RAG SYSTEM SCALING ANALYSIS")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Check current resources
        resources = self.check_system_resources()
        
        # Test current performance
        performance = self.test_response_times(3)
        
        # Estimate scaling requirements
        estimates = self.estimate_scaling_requirements(50)
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations()
        
        # Overall assessment
        print(f"\n📋 OVERALL ASSESSMENT")
        print("=" * 40)
        
        if resources['available_memory_gb'] > estimates['estimated_memory_gb']:
            print("✅ Memory: Sufficient for scaling")
        else:
            print("⚠️ Memory: May need optimization")
        
        if performance and performance['average_time'] < 30:
            print("✅ Performance: Good baseline")
        else:
            print("⚠️ Performance: Needs optimization")
        
        if estimates['estimated_response_time'] < 30:
            print("✅ Scaling: Projected performance acceptable")
        else:
            print("⚠️ Scaling: Projected performance may be slow")
        
        print(f"\n🎯 READY FOR SCALING: {'YES' if resources['available_memory_gb'] > estimates['estimated_memory_gb'] else 'NEEDS OPTIMIZATION'}")
        
        return {
            "resources": resources,
            "performance": performance,
            "estimates": estimates,
            "recommendations": recommendations
        }

if __name__ == "__main__":
    optimizer = ScaleOptimizer()
    optimizer.run_scaling_analysis()
