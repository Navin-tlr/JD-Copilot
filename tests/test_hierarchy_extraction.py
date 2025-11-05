import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from ingest.structured_extractor import StructuredExtractor, CompanyExtraction, Role
from ingest.specialization_detector import detect_specializations
from ingest.level1_mapper import map_level1_roles
from ingest.level2_extractor import extract_level2_roles

# Sample JD texts for testing
SAMPLE_B2B_MARKETING = """
Company: Google
Role: B2B Sales Manager
Specialization: MARKETING
Location: Bangalore

Responsibilities:
- Drive B2B sales strategies
- Manage SDR team and Account Executives
- Focus on enterprise software sales
- Collaborate with marketing on lead generation

Requirements:
- 3+ years in B2B sales
- Experience with CRM tools
- Strong negotiation skills
"""

SAMPLE_FINANCE_FP_A = """
Company: JPMorgan
Role: Financial Analyst
Specialization: FINANCE
Location: Mumbai

Responsibilities:
- Perform financial planning and analysis (FP&A)
- Budget forecasting
- Variance analysis
- Support investment banking deals

Requirements:
- CFA Level 1 preferred
- Excel and financial modeling
- Knowledge of corporate finance
"""

SAMPLE_HYBRID_FINANCIAL_ANALYTICS = """
Company: Deloitte
Role: Financial Analytics Specialist
Specialization: BUSINESS ANALYTICS
Location: Delhi

Responsibilities:
- Conduct financial analytics using Python and SQL
- Build dashboards for FP&A teams
- Predictive modeling for financial risks
- Merge finance insights with data analytics

Requirements:
- Background in finance and analytics
- SQL, Python, Tableau
- Understanding of financial statements
"""

SAMPLE_NO_MATCH = """
Company: Unknown Corp
Role: General Manager
Specialization: HR
Location: Chennai

Responsibilities:
- Oversee daily operations
- Team management

Requirements:
- Leadership experience
"""

SAMPLE_EMPTY = ""

class TestDynamicHierarchy:
    @pytest.fixture
    def mock_llm_responses(self):
        with open('tests/mocks/llm_responses.json', 'r') as f:
            return json.load(f)

    def test_dynamic_specialization_detection(self, mock_llm_responses):
        """Test multi-label specialization detection."""
        with patch('ingest.specialization_detector.OpenRouterWrapper.chat') as mock_chat:
            mock_chat.return_value = mock_llm_responses['specialization_detector']['financial_analytics']
            specs = detect_specializations(SAMPLE_HYBRID_FINANCIAL_ANALYTICS)
            assert len(specs) == 2
            assert any(s['specialization'] == 'Finance' for s in specs)
            assert any(s['specialization'] == 'Business Analytics' for s in specs)
            assert all('confidence' in s and 'evidence' in s for s in specs)
            assert all(s['source'] == 'llm' for s in specs)

    def test_level1_mapping_union_hybrid(self, mock_llm_responses):
        """Test Level 1 mapping for hybrid, asserting union and provenance."""
        specs = [{'specialization': 'Finance'}, {'specialization': 'Business Analytics'}]
        with patch('ingest.level1_mapper.OpenRouterWrapper.chat') as mock_chat:
            mock_chat.return_value = mock_llm_responses['level1_mapper']['hybrid_finance_analytics']
            level1 = map_level1_roles([s['specialization'] for s in specs], SAMPLE_HYBRID_FINANCIAL_ANALYTICS)
            assert len(level1) >= 2
            assert any(l['level1'] == 'FP&A' for l in level1)
            assert any(l['level1'] == 'Data Analytics' for l in level1)
            assert any('Finance' in l['specializations'] for l in level1)
            assert any('Business Analytics' in l['specializations'] for l in level1)
            assert all('confidence' in l and 'rationale' in l for l in level1)
            assert all(l['source'] == 'llm' for l in level1)

    def test_level2_extraction_tied_to_level1(self, mock_llm_responses):
        """Test Level 2 extraction tied to Level 1 candidates."""
        level1_candidates = ['B2B Sales', 'Digital Marketing']
        with patch('ingest.level2_extractor.OpenRouterWrapper.chat') as mock_chat:
            mock_chat.return_value = mock_llm_responses['level2_extractor']['b2b_sales']
            level2 = extract_level2_roles(SAMPLE_B2B_MARKETING, level1_candidates)
            assert len(level2) > 0
            assert any(l['level1'] == 'B2B Sales' for l in level2)
            assert all('level2' in l and 'confidence' in l and 'rationale' in l for l in level2)
            assert all(l['source'] == 'llm' for l in level2)

    def test_edge_case_no_specializations(self):
        """Test empty specs → empty Level 1/2."""
        specs = []
        level1 = map_level1_roles([], SAMPLE_EMPTY)
        assert len(level1) == 0
        level2 = extract_level2_roles(SAMPLE_EMPTY, [])
        assert len(level2) == 0

    def test_edge_case_low_confidence_filter(self):
        """Test filtering low-confidence outputs."""
        # Mock low conf
        with patch('ingest.specialization_detector.OpenRouterWrapper.chat') as mock_chat:
            mock_chat.return_value = '[{"specialization":"Test","confidence":0.1,"evidence":"weak"}]'
            specs = detect_specializations("Low conf text")
            assert len(specs) == 0  # Below default 0.15 threshold

    def test_fallback_modes(self):
        """Test fallback when no LLM (keyword for detector, generic for mappers)."""
        # Disable LLM in detector
        with patch('ingest.specialization_detector.SpecializationDetector.wrapper', None):
            specs = detect_specializations("Marketing and finance keywords.")
            assert len(specs) > 0
            assert any('marketing' in s['specialization'].lower() for s in specs)
            assert all(s['source'] == 'keyword_fallback' for s in specs)

        # Disable for mapper
        with patch('ingest.level1_mapper.Level1Mapper.wrapper', None):
            level1 = map_level1_roles(['Marketing'], "Test")
            assert len(level1) > 0
            assert all(l['source'] == 'fallback' for l in level1)

        # Disable for extractor
        with patch('ingest.level2_extractor.Level2Extractor.wrapper', None):
            level2 = extract_level2_roles("Test", ['B2B Sales'])
            assert len(level2) > 0
            assert all(l['source'] == 'fallback' for l in level2)

    def test_hybrid_structure_in_full_flow(self):
        """Test full dynamic flow for hybrid, asserting merged structure."""
        # Mock chain: detect → map → extract
        mock_responses = json.load(open('tests/mocks/llm_responses.json'))
        with patch('ingest.specialization_detector.OpenRouterWrapper.chat') as mock_detect, \
             patch('ingest.level1_mapper.OpenRouterWrapper.chat') as mock_map, \
             patch('ingest.level2_extractor.OpenRouterWrapper.chat') as mock_extract:
            
            mock_detect.return_value = mock_responses['specialization_detector']['financial_analytics']
            mock_map.return_value = mock_responses['level1_mapper']['hybrid_finance_analytics']
            mock_extract.return_value = mock_responses['level2_extractor']['fp_a']
            
            specs = detect_specializations(SAMPLE_HYBRID_FINANCIAL_ANALYTICS)
            level1 = map_level1_roles([s['specialization'] for s in specs], SAMPLE_HYBRID_FINANCIAL_ANALYTICS)
            level2 = extract_level2_roles(SAMPLE_HYBRID_FINANCIAL_ANALYTICS, [l['level1'] for l in level1])
            
            # Assert structure
            assert len(specs) == 2  # Multi-label
            assert len(level1) >= 2  # Union from multiple specs
            assert any(len(l['specializations']) > 1 for l in level1)  # Provenance merge
            assert len(level2) > 0  # Tied to level1
            assert all(l['level1'] in [item['level1'] for item in level1] for l in level2)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])