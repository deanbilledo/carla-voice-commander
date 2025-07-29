"""
Test cases for Gemini Agent
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock

class TestGeminiAgent(unittest.TestCase):
    """Test cases for GeminiAgent class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the entire gemini_agent module imports
        with patch.dict('sys.modules', {
            'google.generativeai': MagicMock(),
            'google': MagicMock()
        }):
            from gemini_agent import GeminiAgent
            self.agent = GeminiAgent()
    
    def test_build_context(self):
        """Test context building"""
        vehicle_status = {"speed": 30, "location": {"x": 100, "y": 200}}
        environment_info = {"weather": {"cloudiness": 0.5}}
        
        context = self.agent._build_context(vehicle_status, environment_info)
        
        self.assertIn("speed", context)
        self.assertIn("location", context)
        self.assertIn("weather", context)
    
    def test_parse_response_valid_json(self):
        """Test parsing valid JSON response"""
        response_text = '''
        {
            "action": "navigate",
            "destination": "gas station",
            "parameters": {"distance": "nearest"},
            "response": "I'll take you to the nearest gas station",
            "clarification_needed": false
        }
        '''
        
        parsed = self.agent._parse_response(response_text)
        
        self.assertEqual(parsed["action"], "navigate")
        self.assertEqual(parsed["destination"], "gas station")
        self.assertFalse(parsed["clarification_needed"])
    
    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON response"""
        response_text = "This is not JSON"
        
        parsed = self.agent._parse_response(response_text)
        
        self.assertEqual(parsed["action"], "clarify")
        self.assertTrue(parsed["clarification_needed"])
    
    def test_get_error_response(self):
        """Test error response generation"""
        error_response = self.agent._get_error_response()
        
        self.assertEqual(error_response["action"], "clarify")
        self.assertTrue(error_response["clarification_needed"])
        self.assertIn("didn't understand", error_response["response"])

if __name__ == "__main__":
    unittest.main()
