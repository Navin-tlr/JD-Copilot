
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock dependencies that might be missing or require API keys
sys.modules['httpx'] = MagicMock()
sys.modules['llama_parse'] = MagicMock()
sys.modules['pinecone'] = MagicMock()
sys.modules['app.config'] = MagicMock()
sys.modules['app.rag'] = MagicMock()
sys.modules['app.database'] = MagicMock()
sys.modules['app.utils'] = MagicMock()
sys.modules['ingest.company_extractor'] = MagicMock()
sys.modules['ingest.structured_extractor'] = MagicMock()
sys.modules['ingest.specialization_detector'] = MagicMock()
sys.modules['ingest.level2_extractor'] = MagicMock()
sys.modules['app.role_type_classifier'] = MagicMock()
sys.modules['app.llm_role_type_classifier'] = MagicMock()
sys.modules['ingest.metadata_normalize'] = MagicMock()
sys.modules['langchain_text_splitters'] = MagicMock()
sys.modules['app.navigation_map'] = MagicMock()
sys.modules['app.hierarchical_navigation_map'] = MagicMock()
sys.modules['app.specialization_classifier'] = MagicMock()

# Mock the mapper module specifically to verify it's called
mock_mapper = MagicMock()
sys.modules['ingest.level1_mapper'] = mock_mapper

# Now import the module under test
from ingest import pipeline

class TestPipelineLevel1(unittest.TestCase):
    @patch('ingest.pipeline.detect_specializations')
    @patch('ingest.pipeline.map_level1_roles')
    @patch('ingest.pipeline.extract_level2_roles')
    @patch('ingest.pipeline._read_text_from_path')
    @patch('ingest.pipeline._fallback_company_from_filename')
    @patch('ingest.pipeline.StructuredExtractor')
    def test_process_file_uses_mapper(self, mock_struct, mock_fallback, mock_read, mock_l2, mock_map_l1, mock_detect):
        # Setup mocks
        mock_read.return_value = "Sample JD Text"
        mock_fallback.return_value = "Test Company"
        mock_detect.return_value = [{'specialization': 'Marketing', 'confidence': 0.9}]
        
        # Mock map_level1_roles to return a specific subset
        mock_map_l1.return_value = ['FMCG']
        
        # Mock StructuredExtractor to fail so it goes to dynamic path
        mock_struct_instance = mock_struct.return_value
        mock_struct_instance.extract_structured_data.return_value = None
        
        # Run the function
        from pathlib import Path
        pipeline.process_file(Path("test.pdf"))
        
        # Verify map_level1_roles was called
        mock_map_l1.assert_called_once()
        
        # Verify the result from mapper was used (we can't easily check internal variables, 
        # but we can check if it was passed to extract_level2_roles)
        mock_l2.assert_called_once()
        args, _ = mock_l2.call_args
        self.assertEqual(args[1], ['FMCG'])
        print("\nSUCCESS: process_file correctly called map_level1_roles and passed its result to extract_level2_roles")

if __name__ == '__main__':
    unittest.main()
