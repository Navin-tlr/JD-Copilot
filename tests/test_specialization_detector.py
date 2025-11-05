import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from ingest.specialization_detector import SpecializationDetector, detect_specializations

# Sample JD texts for testing
SAMPLE_FINANCIAL_ANALYTICS = """
Role: Financial Analytics Specialist
Responsibilities: Build forecasting models for FP&A, financial data analytics with Python and SQL, profitability analysis.
"""

SAMPLE_MARKETING_ANALYTICS = """
Role: Marketing Analytics Manager
Responsibilities: Analyze marketing campaign performance, build attribution models, ROI analysis for digital channels.
"""

SAMPLE_PURE_HR = """
Role: Talent Acquisition Specialist
Responsibilities: Campus hiring, lateral recruitment, employer branding initiatives.
"""

SAMPLE_AMBIGUOUS_SHORT = "General operations role."

SAMPLE_GENERAL = "Oversee daily operations, team management."

class TestSpecializationDetector:
    @pytest.fixture
    def detector(self):
        detector = SpecializationDetector()
        # Mock settings
        detector.settings.OPENROUTER_API_KEY = "test_key"
        detector.settings.OPENROUTER_MODEL = "test_model"
        detector.wrapper = MagicMock()
        return detector

    def test_financial_analytics_hybrid(self, detector):
        """Test multi-label for Financial Analytics JD -> both Finance and Business Analytics."""
        mock_response = json.loads(open('tests/mocks/llm_responses.json').read())['specialization_detector']['financial_analytics']
        detector.wrapper.chat.return_value = mock_response
        
        specs = detector.detect_specializations(SAMPLE_FINANCIAL_ANALYTICS)
        assert len(specs) == 2
        assert any(s['specialization'] == 'Finance' for s in specs)
        assert any(s['specialization'] == 'Business Analytics' for s in specs)
        assert all(s['confidence'] >= 0.15 for s in specs)
        assert all(s['source'] == 'llm' for s in specs)

    def test_marketing_analytics_hybrid(self, detector):
        """Test multi-label for Marketing Analytics JD -> both Marketing and Business Analytics."""
        mock_response = json.loads(open('tests/mocks/llm_responses.json').read())['specialization_detector']['marketing_analytics']
        detector.wrapper.chat.return_value = mock_response
        
        specs = detector.detect_specializations(SAMPLE_MARKETING_ANALYTICS)
        assert len(specs) == 2
        assert any(s['specialization'] == 'Marketing' for s in specs)
        assert any(s['specialization'] == 'Business Analytics' for s in specs)
        assert all(s['confidence'] >= 0.15 for s in specs)

    def test_pure_hr(self, detector):
        """Test single-label for pure HR JD -> only HR."""
        mock_response = json.loads(open('tests/mocks/llm_responses.json').read())['specialization_detector']['pure_hr']
        detector.wrapper.chat.return_value = mock_response
        
        specs = detector.detect_specializations(SAMPLE_PURE_HR)
        assert len(specs) == 1
        assert specs[0]['specialization'] == 'HR'
        assert specs[0]['confidence'] >= 0.15

    def test_ambiguous_short(self, detector):
        """Test edge case: ambiguous short JD -> empty or low-confidence list."""
        mock_response = json.loads(open('tests/mocks/llm_responses.json').read())['specialization_detector']['ambiguous_short']
        detector.wrapper.chat.return_value = mock_response
        
        specs = detector.detect_specializations(SAMPLE_AMBIGUOUS_SHORT)
        assert len(specs) == 0  # Below threshold

    def test_general(self, detector):
        """Test general JD -> low-confidence or General."""
        mock_response = json.loads(open('tests/mocks/llm_responses.json').read())['specialization_detector']['general']
        detector.wrapper.chat.return_value = mock_response
        
        specs = detector.detect_specializations(SAMPLE_GENERAL)
        assert len(specs) == 1
        assert specs[0]['specialization'] == 'General'
        assert specs[0]['confidence'] < 0.5  # Low confidence

    def test_fallback_keyword(self, detector):
        """Test fallback to keyword classifier when no LLM."""
        detector.wrapper = None  # Disable LLM
        text = "Marketing campaign analysis with data analytics and SQL."
        specs = detector.detect_specializations(text)
        assert len(specs) > 0
        assert any('marketing' in s['specialization'].lower() or 'analytics' in s['specialization'].lower() for s in specs)
        assert all(s['source'] == 'keyword_fallback' for s in specs)
        assert all(s['confidence'] <= 0.5 for s in specs)  # Capped for fallback

    def test_threshold_filtering(self, detector):
        """Test confidence threshold filtering."""
        # Mock LLM to return low/high conf
        with patch.object(detector, 'wrapper') as mock_wrapper:
            mock_wrapper.chat.return_value = '[{"specialization":"Finance","confidence":0.1,"evidence":"weak"},{"specialization":"HR","confidence":0.3,"evidence":"medium"}]'
            specs = detector.detect_specializations("Test text")
            assert len(specs) == 1  # Only >=0.15 (HR)
            assert specs[0]['confidence'] == 0.3

    def test_top_k_limiting(self, detector):
        """Test top_k limiting (set via settings)."""
        detector.top_k = 2
        with patch.object(detector, 'wrapper') as mock_wrapper:
            mock_wrapper.chat.return_value = '[{"specialization":"A","confidence":0.9},{"specialization":"B","confidence":0.8},{"specialization":"C","confidence":0.7}]'
            specs = detector.detect_specializations("Test text")
            assert len(specs) == 2  # Top 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])