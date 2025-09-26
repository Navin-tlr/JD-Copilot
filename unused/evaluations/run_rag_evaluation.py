#!/usr/bin/env python3
"""
RAG Evaluation Runner
Runs comprehensive RAG system evaluation with multiple metrics and benchmark reports
"""

import sys
import subprocess
import argparse
from pathlib import Path

def install_dependencies():
    """Install required dependencies for RAG evaluation"""
    print("📦 Installing RAG evaluation dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "rag_eval_requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_basic_evaluation():
    """Run basic RAG evaluation"""
    print("\n🚀 Running Basic RAG Evaluation...")
    print("=" * 50)
    
    try:
        from rag_evaluation import main as basic_main
        basic_main()
        return True
    except Exception as e:
        print(f"❌ Basic evaluation failed: {e}")
        return False

def run_advanced_evaluation():
    """Run advanced RAG evaluation with reference answers"""
    print("\n🚀 Running Advanced RAG Evaluation...")
    print("=" * 50)
    
    try:
        from advanced_rag_evaluation import main as advanced_main
        advanced_main()
        return True
    except Exception as e:
        print(f"❌ Advanced evaluation failed: {e}")
        return False

def main():
    """Main evaluation runner"""
    parser = argparse.ArgumentParser(description="RAG System Evaluation Runner")
    parser.add_argument("--mode", choices=["basic", "advanced", "both"], default="both",
                       help="Evaluation mode: basic, advanced, or both")
    parser.add_argument("--install-deps", action="store_true",
                       help="Install required dependencies")
    parser.add_argument("--skip-install", action="store_true",
                       help="Skip dependency installation")
    
    args = parser.parse_args()
    
    print("🔍 RAG System Evaluation Runner")
    print("=" * 40)
    
    # Install dependencies if requested
    if args.install_deps and not args.skip_install:
        if not install_dependencies():
            print("❌ Cannot proceed without dependencies")
            return 1
    
    success_count = 0
    total_tests = 0
    
    # Run basic evaluation
    if args.mode in ["basic", "both"]:
        total_tests += 1
        if run_basic_evaluation():
            success_count += 1
            print("✅ Basic evaluation completed successfully!")
        else:
            print("❌ Basic evaluation failed!")
    
    # Run advanced evaluation
    if args.mode in ["advanced", "both"]:
        total_tests += 1
        if run_advanced_evaluation():
            success_count += 1
            print("✅ Advanced evaluation completed successfully!")
        else:
            print("❌ Advanced evaluation failed!")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Tests Run: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All evaluations completed successfully!")
        print("\n📁 Generated Files:")
        
        # List generated files
        files_to_check = [
            "rag_evaluation_results.json",
            "rag_benchmark_report.md",
            "advanced_rag_evaluation_results.json",
            "advanced_rag_benchmark_report.md"
        ]
        
        for file_path in files_to_check:
            if Path(file_path).exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} (not found)")
        
        print("\n📈 Next Steps:")
        print("   1. Review the benchmark reports for detailed metrics")
        print("   2. Analyze individual query results for improvement areas")
        print("   3. Compare metrics against industry benchmarks")
        print("   4. Use results to optimize your RAG system")
        
        return 0
    else:
        print("❌ Some evaluations failed. Check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
