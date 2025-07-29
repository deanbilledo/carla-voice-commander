"""
Intent classification and command parsing for voice commands
"""

import re
from enum import Enum
from utils.logger import Logger

class Intent(Enum):
    """Supported command intents"""
    NAVIGATE = "navigate"
    STOP = "stop"
    SPEED_CHANGE = "speed_change"
    TURN = "turn"
    PARK = "park"
    FOLLOW = "follow"
    WAIT = "wait"
    UNKNOWN = "unknown"

class LocationType(Enum):
    """Types of locations"""
    GAS_STATION = "gas_station"
    SHOPPING_MALL = "shopping_mall"
    PARKING_LOT = "parking_lot"
    RESTAURANT = "restaurant"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    HOME = "home"
    WORK = "work"
    INTERSECTION = "intersection"
    TRAFFIC_LIGHT = "traffic_light"
    UNKNOWN = "unknown"

class CommandParser:
    """Parse voice commands and extract intent and parameters"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize regex patterns for command recognition"""
        self.navigation_patterns = [
            r"(?:go|drive|navigate|head|take me)\s+to\s+(?:the\s+)?(.+)",
            r"(?:drive|go)\s+to\s+(?:the\s+)?(.+)",
            r"take me to\s+(?:the\s+)?(.+)",
            r"I (?:want to|need to) go to\s+(?:the\s+)?(.+)",
            r"let's go to\s+(?:the\s+)?(.+)"
        ]
        
        self.stop_patterns = [
            r"stop(?:\s+(?:the\s+)?car)?",
            r"halt",
            r"brake",
            r"emergency stop",
            r"stop now",
            r"stop immediately"
        ]
        
        self.speed_patterns = [
            r"(?:speed up|go faster|accelerate)",
            r"(?:slow down|go slower|decelerate)",
            r"(?:set speed to|drive at)\s+(\d+)",
            r"(?:increase|decrease)\s+speed"
        ]
        
        self.turn_patterns = [
            r"turn\s+(left|right)(?:\s+at\s+(.+))?",
            r"(?:make a|take a)\s+(left|right)\s+turn(?:\s+at\s+(.+))?",
            r"go\s+(left|right)(?:\s+at\s+(.+))?"
        ]
        
        self.parking_patterns = [
            r"park(?:\s+(?:the\s+)?car)?",
            r"find (?:a\s+)?parking (?:spot|space)",
            r"I (?:want to|need to) park",
            r"let's park"
        ]
        
        self.follow_patterns = [
            r"follow (?:that\s+)?(.+)",
            r"chase (?:that\s+)?(.+)"
        ]
        
        # Location type patterns
        self.location_patterns = {
            LocationType.GAS_STATION: [
                r"gas station", r"fuel station", r"petrol station",
                r"shell", r"bp", r"chevron", r"exxon", r"mobil"
            ],
            LocationType.SHOPPING_MALL: [
                r"(?:shopping\s+)?mall", r"shopping center", r"marketplace",
                r"walmart", r"target", r"costco"
            ],
            LocationType.PARKING_LOT: [
                r"parking lot", r"parking garage", r"car park"
            ],
            LocationType.RESTAURANT: [
                r"restaurant", r"cafe", r"diner", r"fast food",
                r"mcdonald", r"burger king", r"starbucks"
            ],
            LocationType.HOSPITAL: [
                r"hospital", r"medical center", r"clinic"
            ],
            LocationType.SCHOOL: [
                r"school", r"university", r"college", r"campus"
            ],
            LocationType.HOME: [
                r"home", r"house", r"my place"
            ],
            LocationType.WORK: [
                r"work", r"office", r"workplace", r"job"
            ],
            LocationType.INTERSECTION: [
                r"intersection", r"crossroads", r"junction"
            ],
            LocationType.TRAFFIC_LIGHT: [
                r"traffic light", r"red light", r"green light", r"stop light"
            ]
        }
    
    def parse_command(self, command_text):
        """
        Parse voice command and extract intent and parameters
        
        Args:
            command_text (str): The voice command text
            
        Returns:
            dict: Parsed command with intent and parameters
        """
        command_text = command_text.lower().strip()
        self.logger.info(f"Parsing command: {command_text}")
        
        # Try to match different intents
        result = self._try_navigation(command_text)
        if result:
            return result
        
        result = self._try_stop(command_text)
        if result:
            return result
        
        result = self._try_speed_change(command_text)
        if result:
            return result
        
        result = self._try_turn(command_text)
        if result:
            return result
        
        result = self._try_parking(command_text)
        if result:
            return result
        
        result = self._try_follow(command_text)
        if result:
            return result
        
        # Default to unknown intent
        return {
            "intent": Intent.UNKNOWN,
            "confidence": 0.0,
            "parameters": {},
            "raw_command": command_text
        }
    
    def _try_navigation(self, command_text):
        """Try to match navigation patterns"""
        for pattern in self.navigation_patterns:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                destination = match.group(1).strip()
                location_type = self._classify_location(destination)
                
                return {
                    "intent": Intent.NAVIGATE,
                    "confidence": 0.9,
                    "parameters": {
                        "destination": destination,
                        "location_type": location_type,
                        "specific_location": self._extract_specific_location(destination)
                    },
                    "raw_command": command_text
                }
        return None
    
    def _try_stop(self, command_text):
        """Try to match stop patterns"""
        for pattern in self.stop_patterns:
            if re.search(pattern, command_text, re.IGNORECASE):
                return {
                    "intent": Intent.STOP,
                    "confidence": 0.95,
                    "parameters": {
                        "immediate": "emergency" in command_text or "now" in command_text
                    },
                    "raw_command": command_text
                }
        return None
    
    def _try_speed_change(self, command_text):
        """Try to match speed change patterns"""
        for pattern in self.speed_patterns:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                speed_change = "increase"
                target_speed = None
                
                if "slow" in command_text or "decrease" in command_text:
                    speed_change = "decrease"
                elif "speed up" in command_text or "faster" in command_text:
                    speed_change = "increase"
                
                # Try to extract specific speed
                speed_match = re.search(r"(\d+)", command_text)
                if speed_match:
                    target_speed = int(speed_match.group(1))
                
                return {
                    "intent": Intent.SPEED_CHANGE,
                    "confidence": 0.8,
                    "parameters": {
                        "change_type": speed_change,
                        "target_speed": target_speed
                    },
                    "raw_command": command_text
                }
        return None
    
    def _try_turn(self, command_text):
        """Try to match turn patterns"""
        for pattern in self.turn_patterns:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                direction = match.group(1).lower()
                location = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                
                return {
                    "intent": Intent.TURN,
                    "confidence": 0.85,
                    "parameters": {
                        "direction": direction,
                        "at_location": location
                    },
                    "raw_command": command_text
                }
        return None
    
    def _try_parking(self, command_text):
        """Try to match parking patterns"""
        for pattern in self.parking_patterns:
            if re.search(pattern, command_text, re.IGNORECASE):
                return {
                    "intent": Intent.PARK,
                    "confidence": 0.9,
                    "parameters": {},
                    "raw_command": command_text
                }
        return None
    
    def _try_follow(self, command_text):
        """Try to match follow patterns"""
        for pattern in self.follow_patterns:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                
                return {
                    "intent": Intent.FOLLOW,
                    "confidence": 0.8,
                    "parameters": {
                        "target": target,
                        "target_type": self._classify_follow_target(target)
                    },
                    "raw_command": command_text
                }
        return None
    
    def _classify_location(self, location_text):
        """Classify the type of location"""
        location_text = location_text.lower()
        
        for location_type, patterns in self.location_patterns.items():
            for pattern in patterns:
                if re.search(pattern, location_text, re.IGNORECASE):
                    return location_type
        
        return LocationType.UNKNOWN
    
    def _extract_specific_location(self, location_text):
        """Extract specific location details"""
        # Look for modifiers like "nearest", "closest", "next"
        modifiers = []
        if re.search(r"nearest|closest", location_text, re.IGNORECASE):
            modifiers.append("nearest")
        if re.search(r"next", location_text, re.IGNORECASE):
            modifiers.append("next")
        
        return {
            "raw_text": location_text,
            "modifiers": modifiers
        }
    
    def _classify_follow_target(self, target_text):
        """Classify the type of follow target"""
        target_text = target_text.lower()
        
        if re.search(r"red|blue|white|black|green|yellow", target_text):
            return "colored_vehicle"
        elif re.search(r"car|vehicle|truck|bus", target_text):
            return "vehicle"
        elif re.search(r"person|pedestrian|man|woman", target_text):
            return "pedestrian"
        else:
            return "unknown"

# Example usage
if __name__ == "__main__":
    parser = CommandParser()
    
    test_commands = [
        "Drive to the nearest gas station",
        "Stop the car",
        "Turn left at the intersection", 
        "Speed up",
        "Park the car",
        "Follow that blue car",
        "Take me home",
        "Go to Walmart"
    ]
    
    for command in test_commands:
        result = parser.parse_command(command)
        print(f"\nCommand: {command}")
        print(f"Intent: {result['intent'].value}")
        print(f"Confidence: {result['confidence']}")
        print(f"Parameters: {result['parameters']}")
