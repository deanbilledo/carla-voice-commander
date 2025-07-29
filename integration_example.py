"""
Example integration script showing how all components work together
"""

import time
import threading
from config import Config
from utils.logger import Logger

# Try to import CARLA interface, but handle gracefully if not available
try:
    from carla_interface import CarlaInterface
    CARLA_AVAILABLE = True
except ImportError:
    print("CARLA interface not available - using simulation mode")
    CarlaInterface = None
    CARLA_AVAILABLE = False

from gemini_agent import GeminiAgent
from voice.speech_recognition import SpeechRecognizer
from voice.text_to_speech import TextToSpeech
from ai_control.autonomous_controller import AutonomousController
from navigation.pathfinding import AStarPathfinder
from ramn.can_simulation import VehicleCANSimulator

class CarlaVoiceCommanderIntegration:
    """Integration example for all CARLA Voice Commander components"""
    
    def __init__(self, use_carla=None):
        self.logger = Logger.get_logger(__name__)
        
        # Auto-detect CARLA availability if not specified
        if use_carla is None:
            use_carla = CARLA_AVAILABLE
        
        # Initialize components
        self.carla_interface = CarlaInterface() if (use_carla and CARLA_AVAILABLE) else None
        self.gemini_agent = GeminiAgent()
        self.speech_recognizer = SpeechRecognizer()
        self.tts = TextToSpeech()
        self.autonomous_controller = AutonomousController()
        self.pathfinder = AStarPathfinder()
        self.can_simulator = VehicleCANSimulator()
        
        # State
        self.is_running = False
        self.current_mode = "manual"  # manual, ai, voice
        
    def start(self):
        """Start all components"""
        self.logger.info("Starting CARLA Voice Commander Integration")
        
        # Start CAN simulation
        self.can_simulator.start()
        
        # Connect to CARLA if available
        if self.carla_interface:
            if not self.carla_interface.connect():
                self.logger.warning("Could not connect to CARLA - using simulation mode")
                self.carla_interface = None
            else:
                self.carla_interface.spawn_vehicle()
        
        # Start voice recognition
        self.speech_recognizer.start_listening(self.on_voice_command)
        
        # Welcome message
        self.tts.speak("CARLA Voice Commander ready. Say 'switch to voice mode' to start voice control.")
        
        self.is_running = True
        self.logger.info("All components started successfully")
    
    def stop(self):
        """Stop all components"""
        self.logger.info("Stopping CARLA Voice Commander")
        
        self.is_running = False
        
        # Stop components
        self.speech_recognizer.stop_listening()
        self.tts.cleanup()
        self.can_simulator.stop()
        
        if self.carla_interface:
            self.carla_interface.cleanup()
        
        self.logger.info("All components stopped")
    
    def on_voice_command(self, command_text):
        """Handle voice commands"""
        self.logger.info(f"Voice command received: {command_text}")
        
        # Check for mode switching commands
        if "switch to voice mode" in command_text.lower():
            self.current_mode = "voice"
            self.tts.speak("Voice control mode activated. I'm listening for driving commands.")
            return
        elif "switch to manual mode" in command_text.lower():
            self.current_mode = "manual"
            self.tts.speak("Manual control mode activated.")
            return
        elif "switch to ai mode" in command_text.lower():
            self.current_mode = "ai"
            self.tts.speak("AI control mode activated.")
            return
        
        # Only process driving commands in voice mode
        if self.current_mode != "voice":
            return
        
        # Get current vehicle state
        vehicle_status = self.get_vehicle_status()
        environment_info = self.get_environment_info()
        
        # Process command with Gemini
        response = self.gemini_agent.process_command(
            command_text, vehicle_status, environment_info
        )
        
        # Speak response
        self.tts.speak(response['response'])
        
        # Execute action
        self.execute_action(response)
    
    def execute_action(self, ai_response):
        """Execute action based on AI response"""
        action = ai_response.get('action', '')
        parameters = ai_response.get('parameters', {})
        
        self.logger.info(f"Executing action: {action}")
        
        if action == "stop":
            self.emergency_stop()
        elif action == "navigate":
            destination = ai_response.get('destination', '')
            self.navigate_to_destination(destination, parameters)
        elif action == "speed_change":
            self.change_speed(parameters)
        elif action == "turn":
            direction = parameters.get('direction', 'left')
            self.execute_turn(direction)
        elif action == "park":
            self.initiate_parking()
        elif action == "follow":
            target = parameters.get('target', '')
            self.follow_target(target)
    
    def emergency_stop(self):
        """Execute emergency stop"""
        self.logger.info("Emergency stop initiated")
        
        if self.carla_interface:
            self.carla_interface.apply_control({"action": "stop"})
        
        # Update CAN simulation
        self.can_simulator.update_vehicle_state(speed=0, brake_pressure=1.0)
        
        self.tts.speak("Emergency stop activated", priority=True)
    
    def navigate_to_destination(self, destination, parameters):
        """Navigate to specified destination"""
        self.logger.info(f"Navigating to: {destination}")
        
        # Mock destination coordinates (in real implementation, would use map service)
        destination_coords = self.get_destination_coordinates(destination)
        
        if destination_coords:
            # Plan path
            current_location = self.get_current_location()
            path = self.pathfinder.find_path(current_location, destination_coords)
            
            if path:
                # Set waypoints for autonomous controller
                self.autonomous_controller.update_waypoints(path)
                self.autonomous_controller.set_behavior(
                    self.autonomous_controller.DrivingBehavior.FOLLOWING_LANE
                )
                
                self.logger.info(f"Path planned with {len(path)} waypoints")
            else:
                self.tts.speak("Sorry, I couldn't find a path to that destination")
        else:
            self.tts.speak("Sorry, I don't know where that location is")
    
    def change_speed(self, parameters):
        """Change vehicle speed"""
        change_type = parameters.get('change_type', 'increase')
        target_speed = parameters.get('target_speed')
        
        current_speed = self.get_vehicle_status().get('speed', 0)
        
        if target_speed:
            new_speed = target_speed
        elif change_type == 'increase':
            new_speed = min(current_speed + 10, Config.MAX_SPEED)
        else:  # decrease
            new_speed = max(current_speed - 10, 0)
        
        self.autonomous_controller.target_speed = new_speed
        self.logger.info(f"Target speed changed to: {new_speed} km/h")
    
    def execute_turn(self, direction):
        """Execute turn maneuver"""
        self.logger.info(f"Executing {direction} turn")
        
        if self.carla_interface:
            self.carla_interface.apply_control({
                "action": "turn",
                "direction": direction
            })
    
    def initiate_parking(self):
        """Initiate parking procedure"""
        self.logger.info("Initiating parking procedure")
        self.autonomous_controller.set_behavior(
            self.autonomous_controller.DrivingBehavior.PARKING
        )
    
    def follow_target(self, target):
        """Follow specified target"""
        self.logger.info(f"Following target: {target}")
        self.autonomous_controller.set_behavior(
            self.autonomous_controller.DrivingBehavior.FOLLOWING_VEHICLE
        )
    
    def get_vehicle_status(self):
        """Get current vehicle status"""
        if self.carla_interface:
            return self.carla_interface.get_vehicle_status()
        else:
            # Return simulated status
            return self.can_simulator.get_vehicle_state()
    
    def get_environment_info(self):
        """Get current environment information"""
        if self.carla_interface:
            return self.carla_interface.get_environment_info()
        else:
            # Return mock environment info
            return {
                "weather": {"cloudiness": 0.3, "precipitation": 0.0},
                "traffic": {"vehicles_count": 5, "pedestrians_count": 2}
            }
    
    def get_current_location(self):
        """Get current vehicle location"""
        status = self.get_vehicle_status()
        location = status.get('location', {'x': 0, 'y': 0})
        return (location['x'], location['y'])
    
    def get_destination_coordinates(self, destination):
        """Get coordinates for destination (mock implementation)"""
        # Mock destination database
        destinations = {
            "gas station": (150, 200),
            "shopping mall": (300, 400),
            "home": (50, 100),
            "work": (500, 300),
            "hospital": (200, 150),
            "parking lot": (100, 250)
        }
        
        destination_lower = destination.lower()
        for place, coords in destinations.items():
            if place in destination_lower:
                return coords
        
        return None
    
    def run_main_loop(self):
        """Main application loop"""
        try:
            while self.is_running:
                # Update vehicle status
                if self.current_mode == "ai":
                    self.run_ai_control_cycle()
                
                # Update CAN simulation with current state
                status = self.get_vehicle_status()
                self.can_simulator.update_vehicle_state(**status)
                
                time.sleep(0.1)  # 10Hz update rate
                
        except KeyboardInterrupt:
            self.logger.info("Main loop interrupted")
    
    def run_ai_control_cycle(self):
        """Run one cycle of AI control"""
        if self.carla_interface:
            vehicle_state = self.carla_interface.get_vehicle_status()
            environment_info = self.carla_interface.get_environment_info()
            
            # Compute control
            control_command = self.autonomous_controller.compute_control(
                vehicle_state, environment_info
            )
            
            # Apply control
            if control_command and control_command.get('action') != 'idle':
                self.carla_interface.apply_control(control_command)

def main():
    """Example main function"""
    # Create integration (auto-detects CARLA availability)
    integration = CarlaVoiceCommanderIntegration()
    
    try:
        # Start all components
        integration.start()
        
        print("🚗 CARLA Voice Commander Integration Example")
        print("=" * 50)
        print("Mode: Simulation" if not integration.carla_interface else "Mode: CARLA Connected")
        print("Voice commands you can try:")
        print("- 'Switch to voice mode'")
        print("- 'Drive to the gas station'")
        print("- 'Stop the car'")
        print("- 'Turn left'")
        print("- 'Park the car'")
        print("- 'Switch to manual mode'")
        print("\nPress Ctrl+C to stop")
        
        # Run main loop
        integration.run_main_loop()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        integration.stop()

if __name__ == "__main__":
    main()
