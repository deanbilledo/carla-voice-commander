"""
Gemini AI Agent for voice command interpretation and driving assistance
"""

import google.generativeai as genai
from config import Config
from utils.logger import Logger
import json
import re

class GeminiAgent:
    """Gemini AI agent for natural language processing of driving commands"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.setup_gemini()
        self.conversation_history = []
        
    def setup_gemini(self):
        """Initialize Gemini AI with API key and configuration"""
        try:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            self.logger.info("Gemini AI initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini AI: {e}")
            raise
    
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
            parsed_response = self._parse_response(response.text)
            
            # Add to conversation history
            self.conversation_history.append({
                "user_input": user_input,
                "ai_response": parsed_response,
                "context": context
            })
            
            self.logger.info(f"Processed command: {user_input} -> {parsed_response['action']}")
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return self._get_error_response()
    
    def _build_context(self, vehicle_status, environment_info):
        """Build context string from vehicle and environment data"""
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
