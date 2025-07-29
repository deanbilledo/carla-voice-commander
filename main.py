"""
Main entry point for CARLA Voice Commander
"""

import sys
import argparse
from config import Config
from utils.logger import Logger
from ui_dashboard import main as run_dashboard

def main():
    """Main application entry point"""
    logger = Logger.get_logger(__name__)
    logger.info("Starting CARLA Voice Commander")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="CARLA Voice Commander")
    parser.add_argument(
        "--mode", 
        choices=["dashboard", "headless"], 
        default="dashboard",
        help="Run mode: dashboard (GUI) or headless (command line)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    args = parser.parse_args()
    
    # Override debug mode if specified
    if args.debug:
        Config.DEBUG_MODE = True
        logger.info("Debug mode enabled")
    
    try:
        if args.mode == "dashboard":
            logger.info("Starting dashboard mode")
            run_dashboard()
        else:
            logger.info("Starting headless mode")
            run_headless()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        if Config.DEBUG_MODE:
            raise
    finally:
        logger.info("CARLA Voice Commander shutdown complete")

def run_headless():
    """Run in headless mode (command line interface)"""
    from carla_interface import CarlaInterface
    from gemini_agent import GeminiAgent
    from voice.speech_recognition import SpeechRecognizer
    from voice.text_to_speech import TextToSpeech
    
    logger = Logger.get_logger(__name__)
    
    # Initialize components
    carla_interface = CarlaInterface()
    gemini_agent = GeminiAgent()
    speech_recognizer = SpeechRecognizer()
    tts = TextToSpeech()
    
    try:
        # Connect to CARLA
        if not carla_interface.connect():
            logger.error("Failed to connect to CARLA")
            return
        
        if not carla_interface.spawn_vehicle():
            logger.error("Failed to spawn vehicle")
            return
        
        logger.info("CARLA Voice Commander ready - headless mode")
        tts.speak("CARLA Voice Commander ready. You can start giving voice commands.")
        
        # Voice command loop
        def on_voice_command(command_text):
            logger.info(f"Voice command: {command_text}")
            
            # Get current status
            vehicle_status = carla_interface.get_vehicle_status()
            environment_info = carla_interface.get_environment_info()
            
            # Process with Gemini
            response = gemini_agent.process_command(
                command_text, vehicle_status, environment_info
            )
            
            logger.info(f"AI response: {response['response']}")
            tts.speak(response['response'])
            
            # Execute action
            if not response.get('clarification_needed', False):
                execute_ai_action(carla_interface, response)
        
        # Start listening
        speech_recognizer.start_listening(on_voice_command)
        
        # Keep running until interrupted
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Headless mode interrupted")
    finally:
        # Cleanup
        speech_recognizer.stop_listening()
        tts.cleanup()
        carla_interface.cleanup()

def execute_ai_action(carla_interface, ai_response):
    """Execute action based on AI response"""
    logger = Logger.get_logger(__name__)
    action = ai_response.get('action', '')
    parameters = ai_response.get('parameters', {})
    
    if action == "stop":
        carla_interface.apply_control({"action": "stop"})
    elif action == "navigate":
        destination = ai_response.get('destination', '')
        logger.info(f"Navigation to: {destination}")
        # TODO: Implement navigation logic
    elif action == "speed_change":
        # TODO: Implement speed control
        pass
    elif action == "turn":
        direction = parameters.get('direction', 'left')
        carla_interface.apply_control({"action": "turn", "direction": direction})
    
    logger.info(f"Executed action: {action}")

if __name__ == "__main__":
    main()
