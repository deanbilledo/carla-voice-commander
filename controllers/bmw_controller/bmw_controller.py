"""
Webots BmwX5 Vehicle Controller
Controller script for BmwX5 vehicle using Webots vehicle library
"""

import sys
import os
import time
import math
import json
from typing import Dict, Any, Optional

# Add parent directory to path to import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

try:
    from vehicle import Driver
    WEBOTS_AVAILABLE = True
    print("✅ Webots vehicle library available")
except ImportError:
    print("❌ Webots vehicle library not available")
    WEBOTS_AVAILABLE = False
    sys.exit(1)

class BmwX5Controller:
    """BmwX5 vehicle controller for voice command system"""
    
    def __init__(self):
        # Initialize driver
        self.driver = Driver()
        self.timestep = 64  # Standard vehicle timestep
        
        print(f"🚗 BmwX5 Vehicle Controller initialized")
        
        # Vehicle state
        self.vehicle_state = {
            'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'orientation': {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0},
            'velocity': {'linear': 0.0, 'angular': 0.0},
            'speed_kmh': 0.0,
            'gear': 'P',
            'engine_rpm': 0,
            'fuel_level': 1.0
        }
        
        # Control parameters
        self.max_speed = 50.0  # km/h
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.steering_angle = 0.0
        
        # Command file paths
        self.command_file = os.path.join(parent_dir, "commands", "current_command.json")
        self.status_file = os.path.join(parent_dir, "commands", "vehicle_status.json")
        self.last_command_time = 0
        
        # Initialize sensors
        self._init_sensors()
        
        # Set initial driving parameters
        self.driver.setCruisingSpeed(0.0)
        self.driver.setSteeringAngle(0.0)
        
        print("✅ BmwX5 controller ready")
    
    def _init_sensors(self):
        """Initialize vehicle sensors"""
        try:
            # Get GPS sensor
            self.gps = self.driver.getDevice("gps")
            if self.gps:
                self.gps.enable(self.timestep)
                print("📍 GPS sensor enabled")
            
            # Get Compass sensor
            self.compass = self.driver.getDevice("compass")
            if self.compass:
                self.compass.enable(self.timestep)
                print("🧭 Compass sensor enabled")
            
            # Get Camera sensor
            self.camera = self.driver.getDevice("camera")
            if self.camera:
                self.camera.enable(self.timestep)
                print("📹 Camera sensor enabled")
            
        except Exception as e:
            print(f"❌ Sensor initialization error: {e}")
    
    def update_sensors(self):
        """Update sensor readings and vehicle state"""
        try:
            # Update GPS position
            if self.gps:
                gps_values = self.gps.getValues()
                if gps_values and len(gps_values) >= 3:
                    self.vehicle_state['position']['x'] = gps_values[0]
                    self.vehicle_state['position']['y'] = gps_values[1]
                    self.vehicle_state['position']['z'] = gps_values[2]
            
            # Update compass orientation
            if self.compass:
                compass_values = self.compass.getValues()
                if compass_values and len(compass_values) >= 3:
                    # Calculate heading from compass
                    heading = math.atan2(compass_values[0], compass_values[1])
                    self.vehicle_state['orientation']['yaw'] = math.degrees(heading)
            
            # Update speed
            current_speed = self.driver.getCurrentSpeed()
            self.vehicle_state['speed_kmh'] = current_speed
            self.current_speed = current_speed
            
            # Update gear based on speed and direction
            if current_speed > 0.1:
                self.vehicle_state['gear'] = 'D'
            elif current_speed < -0.1:
                self.vehicle_state['gear'] = 'R'
            else:
                self.vehicle_state['gear'] = 'P'
            
        except Exception as e:
            print(f"❌ Sensor update error: {e}")
    
    def update_status_file(self):
        """Write current vehicle status to file for overlay"""
        try:
            status_data = {
                'connected': True,
                'position': self.vehicle_state['position'],
                'orientation': self.vehicle_state['orientation'],
                'speed_kmh': self.vehicle_state['speed_kmh'],
                'gear': self.vehicle_state['gear'],
                'target_speed': self.target_speed,
                'steering_angle': self.steering_angle,
                'timestamp': time.time()
            }
            
            # Ensure commands directory exists
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Status file update error: {e}")
    
    def check_for_commands(self):
        """Check for new commands from overlay"""
        try:
            if not os.path.exists(self.command_file):
                return
            
            # Check file size to avoid reading empty files
            file_size = os.path.getsize(self.command_file)
            if file_size == 0:
                return
            
            # Get file modification time
            mod_time = os.path.getmtime(self.command_file)
            
            # Only process if file is newer than last command
            if mod_time <= self.last_command_time:
                return
            
            # Read command file with error handling
            try:
                with open(self.command_file, 'r') as f:
                    content = f.read().strip()
                    if not content:  # Empty content
                        return
                    command_data = json.loads(content)
            except json.JSONDecodeError as je:
                print(f"⚠️ Invalid JSON in command file: {je}")
                return
            except Exception as fe:
                print(f"⚠️ Error reading command file: {fe}")
                return
            
            # Process command
            command = None
            if 'command' in command_data:
                command = command_data['command']
            elif 'action' in command_data:
                command = command_data['action']
            
            if command:
                self.process_command(command)
                self.last_command_time = mod_time
                print(f"🎮 Processed command: {command}")
            
        except Exception as e:
            print(f"❌ Command processing error: {e}")
    
    def process_command(self, command: str):
        """Process vehicle command"""
        command = command.lower().strip()
        
        if command in ['forward', 'move_forward']:
            self.target_speed = 30.0  # 30 km/h
            self.steering_angle = 0.0
            self.driver.setCruisingSpeed(self.target_speed)
            self.driver.setSteeringAngle(self.steering_angle)
            
        elif command in ['backward', 'move_backward']:
            self.target_speed = -20.0  # Reverse at 20 km/h
            self.steering_angle = 0.0
            self.driver.setCruisingSpeed(self.target_speed)
            self.driver.setSteeringAngle(self.steering_angle)
            
        elif command in ['left', 'turn_left']:
            # Turn left while maintaining current speed
            self.steering_angle = -0.5  # Left turn
            self.driver.setSteeringAngle(self.steering_angle)
            if abs(self.current_speed) < 5:  # If nearly stopped, move forward
                self.target_speed = 20.0
                self.driver.setCruisingSpeed(self.target_speed)
            
        elif command in ['right', 'turn_right']:
            # Turn right while maintaining current speed
            self.steering_angle = 0.5  # Right turn
            self.driver.setSteeringAngle(self.steering_angle)
            if abs(self.current_speed) < 5:  # If nearly stopped, move forward
                self.target_speed = 20.0
                self.driver.setCruisingSpeed(self.target_speed)
            
        elif command == 'stop':
            self.target_speed = 0.0
            self.steering_angle = 0.0
            self.driver.setCruisingSpeed(self.target_speed)
            self.driver.setSteeringAngle(self.steering_angle)
            
        else:
            print(f"⚠️ Unknown command: {command}")
    
    def run(self):
        """Main control loop"""
        print("🚀 Starting BmwX5 control loop...")
        
        # Create commands directory if it doesn't exist
        os.makedirs(os.path.dirname(self.command_file), exist_ok=True)
        
        while self.driver.step() != -1:
            # Update sensors
            self.update_sensors()
            
            # Check for new commands (less frequently to avoid JSON errors)
            if int(time.time() * 10) % 5 == 0:  # Check every 0.5 seconds
                self.check_for_commands()
            
            # Update status file for overlay
            self.update_status_file()
            
            # Small delay to prevent excessive file I/O
            time.sleep(0.05)

# Main execution
if __name__ == "__main__":
    print("🚗 Starting BmwX5 Vehicle Controller...")
    
    try:
        controller = BmwX5Controller()
        controller.run()
    except KeyboardInterrupt:
        print("🛑 Controller stopped by user")
    except Exception as e:
        print(f"💥 Controller error: {e}")
        import traceback
        traceback.print_exc()
