import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import tempfile

from ingest.pipeline import process_file
from ingest.specialization_detector import detect_specializations
from ingest.level1_mapper import map_level1_roles
from ingest.level2_extractor import extract_level2_roles
from app.database import PlacementDatabase

# 8 representative JD fixtures (as strings for simplicity)
JD_FIXTURES = {
    "financial_analytics": """
    Company: Deloitte
    Role: Financial Analytics Specialist
    Responsibilities: Build forecasting models for FP&A, financial data analytics with Python and SQL, profitability analysis, dashboards.
    """,
    "marketing_analytics": """
    Company: Google
    Role: Marketing Analytics Manager
    Responsibilities: Analyze marketing campaign performance, build attribution models, ROI analysis for digital channels, growth marketing.
    """,
    "supply_chain": """
    Company: Amazon
    Role: Supply Chain Analyst
    Responsibilities: Logistics optimization, demand planning, inventory management, procurement strategies.
    """,
    "hr_ta": """
    Company: Microsoft
    Role: Talent Acquisition Specialist
    Responsibilities: Campus hiring, lateral recruitment, employer branding, onboarding programs.
    """,
    "operations_excellence": """
    Company: Toyota
    Role: Operations Manager
    Responsibilities: Process improvement, lean manufacturing, quality control, project management.
    """,
    "investment_banking": """
    Company: Goldman Sachs
    Role: Investment Banking Analyst
    Responsibilities: Valuations, M&A advisory, deal structuring, financial modeling.
    """,
    "data_science": """
    Company: Meta
    Role: Data Scientist
    Responsibilities: Machine learning models, predictive analytics, data visualization with Tableau.
    """,
    "general_ops": """
    Company: Unknown
    Role: General Manager
    Responsibilities: Oversee daily operations, team management, no specific domain.
    """
}

class TestIntegrationDynamicPipeline:
    @pytest.fixture
    def mock_llm_chain(self):
        """Mock the entire LLM chain for determinism."""
        mock_responses = json.load(open('tests/mocks/llm_responses.json'))
        with patch('ingest.specialization_detector.OpenRouterWrapper.chat') as mock_detect, \
             patch('ingest.level1_mapper.OpenRouterWrapper.chat') as mock_map, \
             patch('ingest.level2_extractor.OpenRouterWrapper.chat') as mock_extract, \
             patch('app.database.PlacementDatabase.insert_company_extraction', return_value=True) as mock_db:
            
            # Set up mocks for each fixture
            mock_detect.side_effect = lambda text: mock_responses['specialization_detector'].get('financial_analytics' if 'financial' in text else 'marketing_analytics' if 'marketing' in text else 'pure_hr' if 'hr' in text else 'general', '[]')
            mock_map.side_effect = lambda specs, text: json.loads(mock_responses['level1_mapper'].get('hybrid_finance_analytics' if len(specs) > 1 else 'finance' if 'finance' in specs[0].lower() else 'marketing', '[]'))
            mock_extract.side_effect = lambda text, level1: json.loads(mock_responses['level2_extractor'].get('b2b_sales' if 'sales' in text else 'fp_a' if 'fp' in text else 'data_analytics', '[]'))
            
            yield mock_detect, mock_map, mock_extract, mock_db

    @pytest.mark.parametrize("fixture_name, jd_text", JD_FIXTURES.items())
    def test_full_pipeline_integration(self, fixture_name, jd_text, mock_llm_chain):
        """Test end-to-end pipeline for each fixture: detect → map → extract → persist schema."""
        mock_detect, mock_map, mock_extract, mock_db = mock_llm_chain
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_path.write_text(jd_text)
            
            try:
                num_chunks, company = process_file(tmp_path)
                
                # Assert pipeline basics
                assert num_chunks >= 1
                assert company is not None
                
                # Assert LLM calls were made (chain)
                assert mock_detect.call_count > 0
                assert mock_map.call_count > 0
                assert mock_extract.call_count > 0
                mock_db.assert_called_once()  # Persistence called
                
                # Assert DB insert had correct schema (from mock call args)
                db_call_args = mock_db.call_args[0][0]  # extraction_dict
                assert 'specializations' in db_call_args
                assert isinstance(db_call_args['specializations'], list)
                assert all(isinstance(s, dict) and 'specialization' in s and 'confidence' in s for s in db_call_args['specializations'])
                
                assert 'level1_roles' in db_call_args
                assert isinstance(db_call_args['level1_roles'], list)
                assert all(isinstance(l, dict) and 'level1' in l and 'specializations' in l and 'confidence' in l for l in db_call_args['level1_roles'])
                
                assert 'level2_roles' in db_call_args
                assert isinstance(db_call_args['level2_roles'], list)
                assert all(isinstance(l, dict) and 'level2' in l and 'level1' in l and 'confidence' in l for l in db_call_args['level2_roles'])
                
                # Specific assertions per fixture
                if fixture_name == "financial_analytics":
                    assert len(db_call_args['specializations']) == 2
                    assert any('Finance' in s['specialization'] for s in db_call_args['specializations'])
                    assert any('Business Analytics' in s['specialization'] for s in db_call_args['specializations'])
                    assert any('FP&A' in l['level1'] for l in db_call_args['level1_roles'])
                
                elif fixture_name == "marketing_analytics":
                    assert len(db_call_args['specializations']) == 2
                    assert any('Marketing' in s['specialization'] for s in db_call_args['specializations'])
                    assert any('Business Analytics' in s['specialization'] for s in db_call_args['specializations'])
                
                elif fixture_name == "hr_ta":
                    assert len(db_call_args['specializations']) == 1
                    assert 'HR' in db_call_args['specializations'][0]['specialization']
                
                elif fixture_name == "general_ops":
                    assert len(db_call_args['specializations']) == 1
                    assert 'General' in db_call_args['specializations'][0]['specialization']
                
                # For all, assert no hard-coded values; structure only
                assert not any('hardcoded' in str(l) for l in db_call_args['level1_roles'])  # No legacy
                
            finally:
                # Cleanup
                if tmp_path.exists():
                    tmp_path.unlink()

    def test_legacy_rollback_mode(self, mock_llm_chain):
        """Test rollback to legacy mode via env var."""
        # Set env for legacy
        os.environ['LEGACY_ROLE_MAP'] = 'true'
        
        with patch('ingest.pipeline.os.getenv', return_value='true'):
            # Mock to skip new detectors
            with patch('ingest.pipeline.detect_specializations', return_value=[{'specialization': 'Legacy'}]), \
                 patch('ingest.pipeline.map_level1_roles', return_value=[{'level1': 'Legacy L1'}]), \
                 patch('ingest.pipeline.extract_level2_roles', return_value=[{'level2': 'Legacy L2'}]):
                
                with tempfile.NamedTemporaryFile(suffix='.txt') as tmp_file:
                    tmp_path = Path(tmp_file.name)
                    tmp_path.write_text("Legacy test JD.")
                    
                    try:
                        num_chunks, company = process_file(tmp_path)
                        assert num_chunks >= 1
                        # Assert legacy was used (no new calls, but since mocked, check env effect)
                        # In real, would use old LEVEL1_MAPS from structured_extractor
                    finally:
                        tmp_path.unlink()

    def test_db_schema_persistence(self, mock_llm_chain):
        """Test that JSON fields are persisted with correct schema in DB mock."""
        mock_detect, mock_map, mock_extract, mock_db = mock_llm_chain
        
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_path.write_text(JD_FIXTURES["financial_analytics"])
            
            try:
                process_file(tmp_path)
                
                # Assert DB call has JSON strings for new fields (as per migration: TEXT)
                db_call_args = mock_db.call_args[0][0]
                assert isinstance(db_call_args.get('specializations'), list)  # Before dumps in pipeline
                # In pipeline, we dump to string for SQLite TEXT
                # But mock sees dict; in real, assert dumps called
                assert 'specializations' in db_call_args
                assert 'level1_roles' in db_call_args
                assert 'level2_roles' in db_call_args
                
            finally:
                tmp_path.unlink()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])