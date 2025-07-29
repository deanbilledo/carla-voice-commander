"""
Gemini AI Agent for voice command interpretation and driving assistance
"""

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google-generativeai not installed. Run: pip install google-generativeai")
    genai = None

from config import Config
from utils.logger import Logger
from nlp.intent_classifier import CommandParser, Intent
import json
import re

class GeminiAgent:
    """Gemini AI agent for natural language processing of driving commands"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.command_parser = CommandParser()
        self.model = None
        self.conversation_history = []
        
        # Try to setup Gemini
        if genai is not None:
            self.setup_gemini()
        else:
            self.logger.warning("Gemini AI not available - using fallback mode")
        
    def setup_gemini(self):
        """Initialize Gemini AI with API key and configuration"""
        try:
            if not Config.GOOGLE_API_KEY or Config.GOOGLE_API_KEY == "your_gemini_api_key_here":
                raise ValueError("Google API key not configured")
            
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            self.logger.info("Gemini AI initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini AI: {e}")
            self.model = None
    
    def get_system_prompt(self):
        """Get the system prompt for the Gemini agent"""
        return """You are an AI assistant for a simulated autonomous driving system called CARLA Voice Commander. 
        Users will speak or type commands related to driving a car inside a simulated city (using CARLA Simulator). 
        
        Your capabilities:
        - Navigate to named destinations (gas stations, malls, parking lots, etc.)
        - Control the car (stop, turn, speed up, slow down)
        - Park or follow other vehicles
        - Provide traffic and navigation assistance
        - Ask follow-up questions for clarification
        
        Response format: Always respond with a JSON object containing:
        {
            "action": "string - the primary action to take",
            "destination": "string - target location if navigating",
            "parameters": "object - additional parameters for the action",
            "response": "string - natural language response to the user",
            "clarification_needed": "boolean - whether you need more information"
        }
        
        Available actions:
        - "navigate": Go to a specific destination
        - "stop": Stop the vehicle
        - "park": Find and go to a parking spot
        - "follow": Follow another vehicle
        - "speed_change": Increase or decrease speed
        - "turn": Make a turn (left/right)
        - "wait": Wait at current location
        - "clarify": Ask for more information
        
        Safety guidelines:
        - Always prioritize safety and traffic rules
        - Ask for clarification when commands are ambiguous
        - Provide helpful and informative responses
        - Use a polite and professional tone
        """
    
    def process_command(self, user_input, vehicle_status=None, environment_info=None):
        """
        Process a voice command and return structured response
        
        Args:
            user_input (str): The user's voice command
            vehicle_status (dict): Current vehicle status (speed, location, etc.)
            environment_info (dict): Current environment information
            
        Returns:
            dict: Structured response with action and parameters
        """
        try:
            # First, try local NLP parsing
            nlp_result = self.command_parser.parse_command(user_input)
            
            if nlp_result["intent"] != Intent.UNKNOWN and nlp_result["confidence"] > 0.7:
                # Use NLP result if confident
                response = self._nlp_to_response(nlp_result)
                self.logger.info(f"Used NLP parsing: {user_input} -> {response['action']}")
            elif self.model is not None:
                # Fall back to Gemini AI
                response = self._process_with_gemini(user_input, vehicle_status, environment_info)
                self.logger.info(f"Used Gemini AI: {user_input} -> {response['action']}")
            else:
                # Fallback to basic parsing
                response = self._fallback_parsing(user_input, nlp_result)
                self.logger.info(f"Used fallback parsing: {user_input} -> {response['action']}")
            
            # Add to conversation history
            self.conversation_history.append({
                "user_input": user_input,
                "ai_response": response,
                "method": "nlp" if nlp_result["confidence"] > 0.7 else "gemini" if self.model else "fallback"
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return self._get_error_response()
    
    def _nlp_to_response(self, nlp_result):
        """Convert NLP parsing result to standard response format"""
        intent = nlp_result["intent"]
        params = nlp_result["parameters"]
        
        if intent == Intent.NAVIGATE:
            destination = params.get("destination", "")
            return {
                "action": "navigate",
                "destination": destination,
                "parameters": params,
                "response": f"I'll navigate to {destination}",
                "clarification_needed": False
            }
        elif intent == Intent.STOP:
            return {
                "action": "stop",
                "destination": "",
                "parameters": params,
                "response": "Stopping the vehicle",
                "clarification_needed": False
            }
        elif intent == Intent.TURN:
            direction = params.get("direction", "left")
            return {
                "action": "turn",
                "destination": "",
                "parameters": params,
                "response": f"Turning {direction}",
                "clarification_needed": False
            }
        elif intent == Intent.SPEED_CHANGE:
            change_type = params.get("change_type", "increase")
            return {
                "action": "speed_change",
                "destination": "",
                "parameters": params,
                "response": f"I'll {change_type} the speed",
                "clarification_needed": False
            }
        elif intent == Intent.PARK:
            return {
                "action": "park",
                "destination": "",
                "parameters": params,
                "response": "I'll find a parking spot",
                "clarification_needed": False
            }
        elif intent == Intent.FOLLOW:
            target = params.get("target", "vehicle")
            return {
                "action": "follow",
                "destination": "",
                "parameters": params,
                "response": f"I'll follow that {target}",
                "clarification_needed": False
            }
        else:
            return self._get_error_response()
    
    def _process_with_gemini(self, user_input, vehicle_status, environment_info):
        """Process command using Gemini AI"""
        # Build context for the AI
        context = self._build_context(vehicle_status, environment_info)
        
        # Create the full prompt
        prompt = f"""
        {self.get_system_prompt()}
        
        Current Context:
        {context}
        
        User Command: "{user_input}"
        
        Please analyze this command and provide a JSON response with the appropriate action.
        """
        
        # Generate response from Gemini
        response = self.model.generate_content(prompt)
        
        # Parse the JSON response
        return self._parse_response(response.text)
    
    def _fallback_parsing(self, user_input, nlp_result):
        """Fallback parsing when Gemini is not available"""
        # Use NLP result even if confidence is low
        if nlp_result["intent"] != Intent.UNKNOWN:
            response = self._nlp_to_response(nlp_result)
            response["response"] += " (using basic parsing)"
            return response
        
        # Very basic keyword matching
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ["stop", "halt", "brake"]):
            return {
                "action": "stop",
                "destination": "",
                "parameters": {},
                "response": "Stopping the vehicle",
                "clarification_needed": False
            }
        elif any(word in user_lower for word in ["go", "drive", "navigate"]):
            return {
                "action": "navigate",
                "destination": "destination",
                "parameters": {},
                "response": "I'll try to navigate, but I need more specific instructions",
                "clarification_needed": True
            }
        else:
            return self._get_error_response()

    def _build_context(self, vehicle_status, environment_info):
        context_parts = []
        
        if vehicle_status:
            context_parts.append(f"Vehicle Status: {json.dumps(vehicle_status, indent=2)}")
        
        if environment_info:
            context_parts.append(f"Environment: {json.dumps(environment_info, indent=2)}")
        
        return "\n".join(context_parts) if context_parts else "No additional context available"
    
    def _parse_response(self, response_text):
        """Parse and validate the Gemini response"""
        try:
            # Extract JSON from response (handle cases where AI adds extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
            else:
                # Fallback if no JSON found
                parsed = {
                    "action": "clarify",
                    "response": response_text,
                    "clarification_needed": True
                }
            
            # Validate required fields
            required_fields = ["action", "response"]
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = ""
            
            # Set defaults for optional fields
            parsed.setdefault("destination", "")
            parsed.setdefault("parameters", {})
            parsed.setdefault("clarification_needed", False)
            
            return parsed
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return self._get_error_response()
    
    def _get_error_response(self):
        """Return a default error response"""
        return {
            "action": "clarify",
            "destination": "",
            "parameters": {},
            "response": "I'm sorry, I didn't understand that command. Could you please rephrase it?",
            "clarification_needed": True
        }
    
    def get_conversation_history(self):
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")

# Example usage and testing
if __name__ == "__main__":
    agent = GeminiAgent()
    
    # Test command
    test_command = "Drive to the nearest gas station"
    vehicle_status = {
        "speed": 25.5,
        "location": {"x": 100, "y": 200, "z": 0.5},
        "fuel": 0.75
    }
    
    response = agent.process_command(test_command, vehicle_status)
    print(json.dumps(response, indent=2))
