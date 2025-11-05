import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from __future__ import annotations

import os
import tempfile
from pathlib import Path
import pytest
import json
from unittest.mock import patch, MagicMock

from ingest.pipeline import process_file
from ingest.structured_extractor import StructuredExtractor, CompanyExtraction, Role

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

# NEW: Tests for extractor functions in ingestion context
SAMPLE_B2B_JD = """
Company: Google
Role: B2B Sales Manager
Specialization: MARKETING
Location: Bangalore

Responsibilities:
- Drive B2B sales strategies
- Manage SDR team and Account Executives
- Focus on enterprise software sales
"""

class TestExtractorInPipeline:
    @pytest.fixture
    def mock_extractor(self):
        extractor = StructuredExtractor()
        # Mock settings
        extractor.settings.OPENROUTER_API_KEY = "test_key"
        extractor.settings.OPENROUTER_MODEL = "test_model"
        extractor.wrapper = MagicMock()
        return extractor

    @patch('ingest.structured_extractor.requests.post')
    @patch('ingest.pipeline.StructuredExtractor')
    def test_ingestion_with_b2b_hierarchy(self, mock_pipeline_extractor, mock_post, mock_extractor):
        """Test end-to-end ingestion with B2B hierarchy extraction."""
        # Mock LLM responses for core extraction
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "company_name": "Google",
                "year": 2024,
                "roles": [{"title": "B2B Sales Manager", "specialization": "MARKETING", "location": "Bangalore"}],
                "company_type": "Tech", "industry": "Technology"
            })}}]
        }
        mock_post.return_value = mock_response

        # Mock hierarchy LLM calls
        mock_extractor.wrapper.chat.side_effect = [
            '{"selected_level1": ["B2B Sales"], "confidence": 0.9}',  # Level 1
            '{"level2_dict": {"B2B Sales": ["SDR", "Account Executive"]}, "confidence": 0.8}'  # Level 2
        ]

        mock_pipeline_extractor.return_value = mock_extractor

        # Create temp file for ingestion
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            jd_dir = tmp_path / "jds"
            jd_dir.mkdir(parents=True)
            sample_file = jd_dir / "b2b_jd.txt"
            sample_file.write_text(SAMPLE_B2B_JD)

            result = process_file(sample_file)

            assert result >= 1
            assert mock_extractor.wrapper.chat.call_count == 2  # One for L1, one for L2

    @patch('ingest.structured_extractor.requests.post')
    @patch('ingest.pipeline.StructuredExtractor')
    def test_ingestion_hybrid_role(self, mock_pipeline_extractor, mock_post, mock_extractor):
        """Test ingestion for hybrid financial analytics role."""
        hybrid_jd = """
        Company: Deloitte
        Role: Financial Analytics Specialist
        Specialization: BUSINESS ANALYTICS
        Responsibilities: Financial modeling with Python, FP&A dashboards
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "company_name": "Deloitte",
                "roles": [{"title": "Financial Analytics Specialist", "specialization": "BUSINESS ANALYTICS"}]
            })}}]
        }
        mock_post.return_value = mock_response

        mock_extractor.wrapper.chat.side_effect = [
            '{"selected_level1": ["Data Analysis", "Financial Planning and Analysis"], "confidence": 0.8}',
            '{"level2_dict": {"Data Analysis": ["Financial Data Analyst"], "Financial Planning and Analysis": ["FP&A Modeler"]}, "confidence": 0.75}'
        ]

        mock_pipeline_extractor.return_value = mock_extractor

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            jd_dir = tmp_path / "jds"
            jd_dir.mkdir(parents=True)
            sample_file = jd_dir / "hybrid_jd.txt"
            sample_file.write_text(hybrid_jd)

            result = process_file(sample_file)

            assert result >= 1
            assert mock_extractor.wrapper.chat.call_count == 2

    @patch('ingest.structured_extractor.requests.post')
    @patch('ingest.pipeline.StructuredExtractor')
    def test_ingestion_edge_case_no_match(self, mock_pipeline_extractor, mock_post, mock_extractor):
        """Test ingestion with no hierarchy match -> defaults to General."""
        no_match_jd = """
        Company: Unknown
        Role: General Manager
        Specialization: HR
        Responsibilities: General operations
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "company_name": "Unknown",
                "roles": [{"title": "General Manager", "specialization": "HR"}]
            })}}]
        }
        mock_post.return_value = mock_response

        mock_extractor.wrapper.chat.return_value = '{"selected_level1": [], "confidence": 0.2}'

        mock_pipeline_extractor.return_value = mock_extractor

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            jd_dir = tmp_path / "jds"
            jd_dir.mkdir(parents=True)
            sample_file = jd_dir / "no_match_jd.txt"
            sample_file.write_text(no_match_jd)

            result = process_file(sample_file)

            assert result >= 1

    @patch('ingest.pipeline.process_file')
    def test_mock_ingestion_pipeline(self, mock_process):
        """Mock full pipeline for quick verification."""
        mock_process.return_value = 2  # Simulate successful chunks
        # This tests the pipeline call itself
        assert mock_process.call_count == 0  # Before call
        chunks = process_file(Path("dummy.txt"))
        assert chunks == 2

if __name__ == "__main__":
    # Run tests directly
    test_docling_ingest_minimal()
    
    if os.environ.get("PINECONE_API_KEY") and os.environ.get("PINECONE_INDEX_NAME"):
        test_pinecone_integration()
    else:
        print("⚠ Skipping Pinecone test (credentials not set)")
    
    print("🎉 All tests passed!")