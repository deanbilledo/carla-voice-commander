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
            self.left_front_motor = self.robot.getDevice('left_front_wheel')
            self.right_front_motor = self.robot.getDevice('right_front_wheel')
            self.left_rear_motor = self.robot.getDevice('left_rear_wheel')
            self.right_rear_motor = self.robot.getDevice('right_rear_wheel')
            
            # Set motors to velocity control
            motors = [self.left_front_motor, self.right_front_motor, 
                     self.left_rear_motor, self.right_rear_motor]
            
            for motor in motors:
                if motor:
                    motor.setPosition(float('inf'))
                    motor.setVelocity(0.0)
            
            print("🔧 Wheel motors initialized")
            
            # Steering motors
            self.left_steering_motor = self.robot.getDevice('left_steering_motor')
            self.right_steering_motor = self.robot.getDevice('right_steering_motor')
            
            if self.left_steering_motor and self.right_steering_motor:
                self.left_steering_motor.setPosition(0.0)
                self.right_steering_motor.setPosition(0.0)
                print("🎛️ Steering motors initialized")
            
        except Exception as e:
            print(f"❌ Actuator initialization error: {e}")
    
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
        """Set steering angle in degrees"""
        # Convert to radians and clamp
        angle_rad = math.radians(max(-30, min(30, angle_degrees)))
        self.steering_angle = angle_rad
        
        try:
            if hasattr(self, 'left_steering_motor') and self.left_steering_motor:
                self.left_steering_motor.setPosition(angle_rad)
            if hasattr(self, 'right_steering_motor') and self.right_steering_motor:
                self.right_steering_motor.setPosition(angle_rad)
            
            print(f"🎛️ Steering set to {angle_degrees:.1f}°")
        except Exception as e:
            print(f"❌ Steering error: {e}")
    
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
            wheel_radius = 0.3  # meters
            wheel_velocity = self.current_speed / wheel_radius
            
            # Apply to motors
            motors = [self.left_front_motor, self.right_front_motor,
                     self.left_rear_motor, self.right_rear_motor]
            
            for motor in motors:
                if motor:
                    motor.setVelocity(wheel_velocity)
            
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
    
    def process_command(self, command: str):
        """Process simple text commands"""
        command = command.lower().strip()
        
        if 'forward' in command or 'ahead' in command:
            self.move_forward(25.0)
        elif 'backward' in command or 'reverse' in command:
            self.move_backward(15.0)
        elif 'left' in command:
            self.turn_left(20.0)
        elif 'right' in command:
            self.turn_right(20.0)
        elif 'stop' in command:
            self.stop()
        elif 'park' in command:
            self.park()
        elif 'fast' in command:
            self.move_forward(40.0)
        elif 'slow' in command:
            self.move_forward(10.0)
        else:
            print(f"❓ Unknown command: {command}")
    
    def run(self):
        """Main control loop"""
        print("🚀 Starting vehicle control loop...")
        
        step_count = 0
        
        try:
            while self.robot.step(self.timestep) != -1:
                # Update sensors
                self.update_sensors()
                
                # Apply motor control
                self.apply_motor_control()
                
                # Print status every 2 seconds
                if step_count % (2000 // self.timestep) == 0:
                    pos = self.vehicle_state['position']
                    print(f"📊 Status: Position({pos['x']:.1f}, {pos['y']:.1f}) "
                          f"Speed: {self.vehicle_state['speed_kmh']:.1f} km/h "
                          f"Gear: {self.vehicle_state['gear']}")
                
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
