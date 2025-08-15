from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


def test_docling_ingest_minimal():
    """Test minimal ingestion with text file (bypasses Docling model requirement)."""
    # Use temp directory for test isolation
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Set test environment
        os.environ["DOCLING_MODELS_DIR"] = str(tmp_path / "docling_models")
        os.environ["DOCLING_JSON_DIR"] = str(tmp_path / "docling_json")
        os.environ["LANGEXT_JSON_DIR"] = str(tmp_path / "langext_json")
        os.environ["LANGEXT_HTML_DIR"] = str(tmp_path / "langext_html")
        
        # Create test input
        jd_dir = tmp_path / "jds"
        jd_dir.mkdir(parents=True)
        sample_file = jd_dir / "test_jd.txt"
        sample_file.write_text("""
Company: TestCorp
Role: Software Engineer
Year: 2024

Responsibilities:
- Develop Python applications
- Work with ML models
- Build REST APIs

Requirements:
- 3+ years Python experience
- Knowledge of FastAPI
- Experience with vector databases

Compensation:
Base Salary: $120,000 - $150,000
Bonus: Up to 20%
""".strip())
        
        # Test the ingestion pipeline (text path, no Docling models needed)
        from ingest.pipeline import process_file
        
        # Should succeed with text file (bypasses PDF model requirements)
        result = process_file(sample_file)
        
        # For text files, we expect at least 1 chunk
        assert result >= 1
        
        print(f"✓ Text ingestion test passed: {result} chunks processed")


@pytest.mark.skipif(
    not (os.environ.get("PINECONE_API_KEY") and os.environ.get("PINECONE_INDEX_NAME")),
    reason="Pinecone credentials not available"
)
def test_pinecone_integration():
    """Test Pinecone integration if credentials are available."""
    from pinecone import Pinecone
    
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
    
    # Check if index exists and has vectors
    stats = index.describe_index_stats()
    vector_count = stats.get("total_vector_count", 0)
    
    print(f"✓ Pinecone index '{os.environ['PINECONE_INDEX_NAME']}' has {vector_count} vectors")
    assert isinstance(vector_count, (int, float))


if __name__ == "__main__":
    # Run tests directly
    test_docling_ingest_minimal()
    
    if os.environ.get("PINECONE_API_KEY") and os.environ.get("PINECONE_INDEX_NAME"):
        test_pinecone_integration()
    else:
        print("⚠ Skipping Pinecone test (credentials not set)")
    
    print("🎉 All tests passed!")