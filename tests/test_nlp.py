"""
Test cases for NLP Intent Classifier
"""

import unittest
from nlp.intent_classifier import CommandParser, Intent, LocationType

class TestCommandParser(unittest.TestCase):
    """Test cases for CommandParser class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = CommandParser()
    
    def test_navigate_command(self):
        """Test navigation command parsing"""
        command = "Drive to the nearest gas station"
        result = self.parser.parse_command(command)
        
        self.assertEqual(result["intent"], Intent.NAVIGATE)
        self.assertGreater(result["confidence"], 0.8)
        self.assertEqual(result["parameters"]["location_type"], LocationType.GAS_STATION)
    
    def test_stop_command(self):
        """Test stop command parsing"""
        command = "Stop the car"
        result = self.parser.parse_command(command)
        
        self.assertEqual(result["intent"], Intent.STOP)
        self.assertGreater(result["confidence"], 0.9)
    
    def test_turn_command(self):
        """Test turn command parsing"""
        command = "Turn left at the intersection"
        result = self.parser.parse_command(command)
        
        self.assertEqual(result["intent"], Intent.TURN)
        self.assertEqual(result["parameters"]["direction"], "left")
        self.assertEqual(result["parameters"]["at_location"], "the intersection")
    
    def test_speed_command(self):
        """Test speed change command parsing"""
        command = "Speed up"
        result = self.parser.parse_command(command)
        
        self.assertEqual(result["intent"], Intent.SPEED_CHANGE)
        self.assertEqual(result["parameters"]["change_type"], "increase")
    
    def test_parking_command(self):
        """Test parking command parsing"""
        command = "Park the car"
        result = self.parser.parse_command(command)
        
        self.assertEqual(result["intent"], Intent.PARK)
        self.assertGreater(result["confidence"], 0.8)
    
    def test_follow_command(self):
        """Test follow command parsing"""
        command = "Follow that blue car"
        result = self.parser.parse_command(command)
        
        self.assertEqual(result["intent"], Intent.FOLLOW)
        self.assertEqual(result["parameters"]["target"], "blue car")
        self.assertEqual(result["parameters"]["target_type"], "colored_vehicle")
    
    def test_unknown_command(self):
        """Test unknown command parsing"""
        command = "Fly to the moon"
        result = self.parser.parse_command(command)
        
        self.assertEqual(result["intent"], Intent.UNKNOWN)
        self.assertEqual(result["confidence"], 0.0)
    
    def test_location_classification(self):
        """Test location type classification"""
        test_cases = [
            ("gas station", LocationType.GAS_STATION),
            ("shopping mall", LocationType.SHOPPING_MALL),
            ("hospital", LocationType.HOSPITAL),
            ("home", LocationType.HOME),
            ("random place", LocationType.UNKNOWN)
        ]
        
        for location_text, expected_type in test_cases:
            result = self.parser._classify_location(location_text)
            self.assertEqual(result, expected_type)

if __name__ == "__main__":
    unittest.main()
