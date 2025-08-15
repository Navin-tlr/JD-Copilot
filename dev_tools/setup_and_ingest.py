#!/usr/bin/env python3
"""
Complete setup and ingestion script for jd-copilot.
Uses LlamaParse (cloud) and runs ingestion.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.request import urlretrieve


def setup_ssl_env():
    """Configure SSL environment using certifi."""
    try:
        import certifi
        cert_path = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", cert_path)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", cert_path)
        print(f"✓ SSL configured with certifi: {cert_path}")
    except ImportError:
        print("⚠ certifi not available, using system CA bundle")
    
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")


def check_model_exists() -> bool:
    """Docling models no longer required with LlamaParse pipeline."""
    return True


def download_beehive_model():
    """No-op with LlamaParse pipeline."""
    return True


def setup_docling_models():
    """Docling model setup skipped (LlamaParse is used)."""
    return True


def validate_pinecone_config():
    """Check if Pinecone is configured."""
    api_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX_NAME")
    
    if api_key and index_name:
        print(f"✓ Pinecone configured: index={index_name}")
        return True
    else:
        print("⚠ Pinecone not configured (API_KEY or INDEX_NAME missing)")
        return False


def run_ingestion():
    """Run the ingestion pipeline (LlamaParse)."""
    pdf_dir = Path("data/jds")
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created PDF directory: {pdf_dir}")
    
    # Check for PDFs or create sample
    pdf_files = list(pdf_dir.glob("*.pdf")) + list(pdf_dir.glob("*.txt"))
    if not pdf_files:
        # Create a minimal test file
        sample_file = pdf_dir / "sample.txt"
        sample_file.write_text("""
Company: Test Corp
Role: Software Engineer
Year: 2024

Responsibilities:
- Develop Python applications
- Work with machine learning models
- Collaborate with cross-functional teams

Requirements:
- Bachelor's degree in Computer Science
- 3+ years of Python experience
- Knowledge of ML frameworks

Compensation:
Base Salary: $120,000 - $150,000
Bonus: Up to 20%
        """.strip())
        print(f"✓ Created sample file: {sample_file}")
    
    print(f"🚀 Running ingestion on {len(list(pdf_dir.glob('*.*')))} files...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "ingest.pipeline", 
            "--pdf_dir", str(pdf_dir)
        ], check=True, capture_output=True, text=True)
        
        print("✓ Ingestion completed successfully!")
        print("Output:", result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Ingestion failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    """Main setup and ingestion workflow."""
    print("🔧 JD-Copilot Setup & Ingestion")
    print("=" * 40)
    
    # Step 1: Configure environment
    setup_ssl_env()
    
    # Step 2: Validate Pinecone (optional)
    validate_pinecone_config()
    
    # Step 3: Setup Docling models
    if not setup_docling_models():
        print("✗ Failed to setup Docling models")
        sys.exit(1)
    
    # Step 4: Run ingestion
    if not run_ingestion():
        print("✗ Ingestion failed")
        sys.exit(1)
    
    print("🎉 Setup and ingestion completed successfully!")


if __name__ == "__main__":
    main()
