"""
Webots Vehicle Controller
Controller script for Webots vehicle simulation
"""

import sys
import os
import time
import math
import json
import threading
from typing import Dict, Any, Optional

# Add parent directory to path to import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

try:
    from controller import Robot, Motor, Camera, GPS, Compass, DistanceSensor
    WEBOTS_AVAILABLE = True
except ImportError:
    print("❌ Webots controller module not available")
    WEBOTS_AVAILABLE = False
    sys.exit(1)

class WebotsVehicleController:
    """Webots vehicle controller for voice command system"""
    
    def __init__(self):
        # Initialize robot
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        print(f"🚗 Webots Vehicle Controller initialized (timestep: {self.timestep}ms)")
        
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
        self.max_speed = 20.0  # m/s (72 km/h)
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.steering_angle = 0.0
        
        # Command file paths
        self.command_file = os.path.join(parent_dir, "commands", "current_command.json")
        self.status_file = os.path.join(parent_dir, "commands", "vehicle_status.json")
        self.last_command_time = 0
        
        # Initialize sensors and actuators
        self._init_sensors()
        self._init_actuators()
        
        print("✅ Vehicle controller ready")
    
    def _init_sensors(self):
        """Initialize vehicle sensors"""
        try:
            # GPS for position
            self.gps = self.robot.getDevice('gps')
            if self.gps:
                self.gps.enable(self.timestep)
                print("📍 GPS sensor enabled")
            
            # Compass for orientation
            self.compass = self.robot.getDevice('compass')
            if self.compass:
                self.compass.enable(self.timestep)
                print("🧭 Compass sensor enabled")
            
            # Camera for vision
            self.camera = self.robot.getDevice('camera')
            if self.camera:
                self.camera.enable(self.timestep)
                print("📹 Camera sensor enabled")
            
            # Distance sensors
            self.distance_sensors = {}
            sensor_names = ['front_sensor', 'rear_sensor', 'left_sensor', 'right_sensor']
            for name in sensor_names:
                sensor = self.robot.getDevice(name)
                if sensor:
                    sensor.enable(self.timestep)
                    self.distance_sensors[name] = sensor
                    print(f"📏 Distance sensor '{name}' enabled")
            
        except Exception as e:
            print(f"❌ Sensor initialization error: {e}")
    
    def _init_actuators(self):
        """Initialize vehicle actuators"""
        try:
            # Get wheel motors (for car-like vehicle)
            self.front_left_motor = self.robot.getDevice('front_left_motor')
            self.front_right_motor = self.robot.getDevice('front_right_motor')
            self.rear_left_motor = self.robot.getDevice('rear_left_motor')
            self.rear_right_motor = self.robot.getDevice('rear_right_motor')
            
            # Store all motors in a list for easy access
            self.motors = [
                self.front_left_motor,
                self.front_right_motor, 
                self.rear_left_motor,
                self.rear_right_motor
            ]
            
            # Set motors to velocity control mode
            for motor in self.motors:
                if motor:
                    motor.setPosition(float('inf'))  # Set to velocity control
                    motor.setVelocity(0.0)  # Start stationary
            
            print("🚗 Vehicle motors initialized:")
            print(f"   Front Left: {'✅' if self.front_left_motor else '❌'}")
            print(f"   Front Right: {'✅' if self.front_right_motor else '❌'}")
            print(f"   Rear Left: {'✅' if self.rear_left_motor else '❌'}")
            print(f"   Rear Right: {'✅' if self.rear_right_motor else '❌'}")
            
        except Exception as e:
            print(f"❌ Motor initialization error: {e}")
    
    def update_status_file(self):
        """Write current vehicle status to file for overlay"""
        try:
            status_data = {
                'connected': True,
                'position': self.vehicle_state['position'],
                'orientation': self.vehicle_state['orientation'],
                'speed_kmh': self.vehicle_state['speed_kmh'],
                'gear': self.vehicle_state['gear'],
                'target_speed': self.target_speed * 3.6,  # Convert to km/h
                'timestamp': time.time()
            }
            
            with open(self.status_file, 'w') as f:
                import json
                json.dump(status_data, f)
                
        except Exception as e:
            print(f"❌ Status file update error: {e}")
    
    def check_for_commands(self):
        """Check for new commands from overlay"""
        try:
            if os.path.exists(self.command_file):
                # Check if file was modified
                file_time = os.path.getmtime(self.command_file)
                if file_time > self.last_command_time:
                    self.last_command_time = file_time
                    
                    # Read and process command
                    with open(self.command_file, 'r') as f:
                        import json
                        command = json.load(f)
                    
                    print(f"📨 Received command: {command}")
                    self.process_command(command)
                    
        except Exception as e:
            print(f"❌ Command reading error: {e}")
    
    def process_command(self, command: dict):
        """Process command from overlay"""
        action = command.get('action', '')
        
        print(f"🎮 Processing command: {command}")
        
        if action == 'forward':
            speed_kmh = command.get('speed', 20.0)
            self.move_forward(speed_kmh)
        elif action == 'backward':
            speed_kmh = command.get('speed', 10.0)
            self.move_backward(speed_kmh)
        elif action == 'left':
            self.turn_left(20.0)
        elif action == 'right':
            self.turn_right(20.0)
        elif action == 'stop':
            self.stop()
        elif action == 'park':
            self.stop()  # Same as stop for now
            print("🅿️ Vehicle parked")
        else:
            print(f"❓ Unknown command action: {action}")
    
    def update_sensors(self):
        """Update sensor readings"""
        try:
            # Update GPS
            if hasattr(self, 'gps') and self.gps:
                gps_values = self.gps.getValues()
                self.vehicle_state['position'] = {
                    'x': gps_values[0],
                    'y': gps_values[1],
                    'z': gps_values[2]
                }
            
            # Update compass
            if hasattr(self, 'compass') and self.compass:
                compass_values = self.compass.getValues()
                # Calculate heading from compass
                heading = math.atan2(compass_values[0], compass_values[1])
                self.vehicle_state['orientation']['yaw'] = math.degrees(heading)
            
            # Update distance sensors
            obstacle_distances = {}
            for name, sensor in self.distance_sensors.items():
                obstacle_distances[name] = sensor.getValue()
            
            # Calculate current speed
            self.vehicle_state['speed_kmh'] = abs(self.current_speed) * 3.6
            self.vehicle_state['engine_rpm'] = int(abs(self.current_speed) * 1000)
            
        except Exception as e:
            print(f"❌ Sensor update error: {e}")
    
    def set_speed(self, speed_kmh: float):
        """Set vehicle speed in km/h"""
        self.target_speed = min(max(speed_kmh / 3.6, -self.max_speed), self.max_speed)
        
        # Update gear based on direction
        if self.target_speed > 0.1:
            self.vehicle_state['gear'] = 'D'
        elif self.target_speed < -0.1:
            self.vehicle_state['gear'] = 'R'
        else:
            self.vehicle_state['gear'] = 'P'
        
        print(f"🚗 Target speed set to {speed_kmh:.1f} km/h")
    
    def set_steering(self, angle_degrees: float):
        """Set steering angle in degrees (implemented via differential drive)"""
        # Convert to radians and clamp
        angle_rad = math.radians(max(-30, min(30, angle_degrees)))
        self.steering_angle = angle_rad
        print(f"🎛️ Steering set to {angle_degrees:.1f}° (differential drive)")
    
    def apply_motor_control(self):
        """Apply motor control based on current settings"""
        try:
            # Smooth speed control
            speed_diff = self.target_speed - self.current_speed
            max_acceleration = 2.0  # m/s²
            dt = self.timestep / 1000.0  # Convert to seconds
            
            if abs(speed_diff) > max_acceleration * dt:
                if speed_diff > 0:
                    self.current_speed += max_acceleration * dt
                else:
                    self.current_speed -= max_acceleration * dt
            else:
                self.current_speed = self.target_speed
            
            # Convert speed to wheel velocity
            wheel_radius = 0.4  # meters (from world file)
            base_velocity = self.current_speed / wheel_radius
            
            # Apply differential steering
            steering_factor = 0.5  # How much steering affects differential
            left_velocity = base_velocity + (self.steering_angle * steering_factor)
            right_velocity = base_velocity - (self.steering_angle * steering_factor)
            
            # Apply to motors
            if self.front_left_motor:
                self.front_left_motor.setVelocity(left_velocity)
            if self.rear_left_motor:
                self.rear_left_motor.setVelocity(left_velocity)
            if self.front_right_motor:
                self.front_right_motor.setVelocity(right_velocity)
            if self.rear_right_motor:
                self.rear_right_motor.setVelocity(right_velocity)
            
        except Exception as e:
            print(f"❌ Motor control error: {e}")
            
        except Exception as e:
            print(f"❌ Motor control error: {e}")
    
    def move_forward(self, speed_kmh: float = 20.0):
        """Move vehicle forward"""
        self.set_speed(speed_kmh)
        self.set_steering(0.0)
        print(f"⬆️ Moving forward at {speed_kmh} km/h")
    
    def move_backward(self, speed_kmh: float = 10.0):
        """Move vehicle backward"""
        self.set_speed(-speed_kmh)
        self.set_steering(0.0)
        print(f"⬇️ Moving backward at {speed_kmh} km/h")
    
    def turn_left(self, angle: float = 15.0):
        """Turn vehicle left"""
        self.set_steering(angle)
        print(f"⬅️ Turning left {angle}°")
    
    def turn_right(self, angle: float = 15.0):
        """Turn vehicle right"""
        self.set_steering(-angle)
        print(f"➡️ Turning right {angle}°")
    
    def stop(self):
        """Stop the vehicle"""
        self.set_speed(0.0)
        self.set_steering(0.0)
        print("🛑 Vehicle stopped")
    
    def emergency_stop(self):
        """Emergency stop"""
        self.target_speed = 0.0
        self.current_speed = 0.0
        self.set_steering(0.0)
        print("🚨 EMERGENCY STOP!")
    
    def park(self):
        """Park the vehicle"""
        self.stop()
        self.vehicle_state['gear'] = 'P'
        print("🅿️ Vehicle parked")
    
    def run(self):
        """Main control loop"""
        print("🚀 Starting vehicle control loop...")
        
        step_count = 0
        
        # Start with a simple test movement
        print("🧪 Testing vehicle movement - moving forward for 3 seconds...")
        self.move_forward(20.0)  # Move forward at 20 km/h
        
        try:
            while self.robot.step(self.timestep) != -1:
                # Check for new commands from overlay
                self.check_for_commands()
                
                # Update sensors
                self.update_sensors()
                
                # Apply motor control
                self.apply_motor_control()
                
                # Update status file for overlay (every step for real-time updates)
                self.update_status_file()
                
                # Stop test movement after 3 seconds
                if step_count == (3000 // self.timestep):
                    print("🛑 Test movement complete - stopping vehicle")
                    self.stop()
                
                # Print status every 2 seconds
                if step_count % (2000 // self.timestep) == 0:
                    pos = self.vehicle_state['position']
                    print(f"📊 Status: Position({pos['x']:.1f}, {pos['y']:.1f}) "
                          f"Speed: {self.vehicle_state['speed_kmh']:.1f} km/h "
                          f"Target: {self.target_speed * 3.6:.1f} km/h")
                
                step_count += 1
                
                # Demo commands for testing
                if step_count == 100:  # After ~1.6 seconds
                    print("🎮 Demo: Moving forward")
                    self.move_forward(20.0)
                elif step_count == 500:  # After ~8 seconds
                    print("🎮 Demo: Turning left")
                    self.turn_left(15.0)
                elif step_count == 700:  # After ~11.2 seconds
                    print("🎮 Demo: Moving forward again")
                    self.move_forward(15.0)
                elif step_count == 1000:  # After ~16 seconds
                    print("🎮 Demo: Stopping")
                    self.stop()
                
                step_count += 1
                
        except KeyboardInterrupt:
            print("\n🛑 Control loop interrupted")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up controller"""
        try:
            self.emergency_stop()
            print("✅ Controller cleanup completed")
        except Exception as e:
            print(f"❌ Cleanup error: {e}")

def main():
    """Main function"""
    print("🚗 Webots Vehicle Controller Starting...")
    print("=" * 50)
    
    try:
        controller = WebotsVehicleController()
        controller.run()
    except Exception as e:
        print(f"❌ Controller error: {e}")
    finally:
        print("🏁 Controller finished")

if __name__ == "__main__":
    main()
