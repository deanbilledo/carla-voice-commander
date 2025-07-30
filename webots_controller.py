"""
🚗 Webots Vehicle Simulation Interface
Main interface for controlling vehicles in Webots simulator
"""

import sys
import os
import time
import math
import threading
from typing import Dict, Any, Optional

# Import Webots controller
try:
    from controller import Robot, Motor, Camera, GPS, Compass, DistanceSensor
    WEBOTS_AVAILABLE = True
    print("✅ Webots controller available")
except ImportError:
    WEBOTS_AVAILABLE = False
    print("❌ Webots controller not available - install Webots and webots-controller package")

from config import Config
from utils.logger import Logger
from gemini_agent import GeminiAgent
from ramn.can_simulation import VehicleCANSimulator

class WebotsVehicleController:
    """Webots vehicle controller with sensor integration"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        
        # Initialize Webots robot
        if WEBOTS_AVAILABLE:
            self.robot = Robot()
            self.timestep = int(self.robot.getBasicTimeStep())
            self._init_sensors()
            self._init_actuators()
        else:
            self.robot = None
            self.timestep = 64
        
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
        self.max_speed = 30.0  # m/s
        self.max_steering_angle = 0.5  # radians
        self.current_speed = 0.0
        self.current_steering = 0.0
        
        # Initialize AI and CAN
        self.gemini_agent = GeminiAgent()
        self.can_simulator = VehicleCANSimulator()
        self.can_simulator.start()
        
        self.logger.info("Webots vehicle controller initialized")
    
    def _init_sensors(self):
        """Initialize Webots sensors"""
        if not self.robot:
            return
        
        try:
            # GPS for position tracking
            self.gps = self.robot.getDevice('gps')
            if self.gps:
                self.gps.enable(self.timestep)
                self.logger.info("GPS sensor enabled")
            
            # Compass for orientation
            self.compass = self.robot.getDevice('compass')
            if self.compass:
                self.compass.enable(self.timestep)
                self.logger.info("Compass sensor enabled")
            
            # Camera for vision
            self.camera = self.robot.getDevice('camera')
            if self.camera:
                self.camera.enable(self.timestep)
                self.logger.info("Camera sensor enabled")
            
            # Distance sensors for obstacle detection
            self.distance_sensors = {}
            sensor_names = ['front_sensor', 'rear_sensor', 'left_sensor', 'right_sensor']
            for name in sensor_names:
                sensor = self.robot.getDevice(name)
                if sensor:
                    sensor.enable(self.timestep)
                    self.distance_sensors[name] = sensor
                    self.logger.info(f"Distance sensor {name} enabled")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sensors: {e}")
    
    def _init_actuators(self):
        """Initialize Webots actuators"""
        if not self.robot:
            return
        
        try:
            # Wheel motors for movement
            self.left_motor = self.robot.getDevice('left_wheel_motor')
            self.right_motor = self.robot.getDevice('right_wheel_motor')
            
            if self.left_motor and self.right_motor:
                self.left_motor.setPosition(float('inf'))  # Velocity control
                self.right_motor.setPosition(float('inf'))
                self.left_motor.setVelocity(0.0)
                self.right_motor.setVelocity(0.0)
                self.logger.info("Wheel motors initialized")
            
            # Steering motor (for car-like vehicles)
            self.steering_motor = self.robot.getDevice('steering_motor')
            if self.steering_motor:
                self.steering_motor.setPosition(0.0)
                self.logger.info("Steering motor initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize actuators: {e}")
    
    def update_sensors(self):
        """Update sensor readings and vehicle state"""
        if not self.robot:
            return
        
        try:
            # Update GPS position
            if hasattr(self, 'gps') and self.gps:
                gps_values = self.gps.getValues()
                if gps_values:
                    self.vehicle_state['position'] = {
                        'x': gps_values[0],
                        'y': gps_values[1], 
                        'z': gps_values[2]
                    }
            
            # Update compass orientation
            if hasattr(self, 'compass') and self.compass:
                compass_values = self.compass.getValues()
                if compass_values:
                    # Calculate yaw from compass
                    yaw = math.atan2(compass_values[0], compass_values[1])
                    self.vehicle_state['orientation']['yaw'] = yaw
            
            # Update distance sensors
            sensor_readings = {}
            for name, sensor in self.distance_sensors.items():
                sensor_readings[name] = sensor.getValue()
            
            # Calculate speed (simplified)
            self.vehicle_state['speed_kmh'] = abs(self.current_speed) * 3.6
            
            # Update CAN simulator with current state
            self.can_simulator.update_vehicle_state(
                speed=self.vehicle_state['speed_kmh'],
                gear=self.vehicle_state['gear'],
                engine_rpm=int(abs(self.current_speed) * 1000),
                fuel_level=self.vehicle_state['fuel_level']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update sensors: {e}")
    
    def set_velocity(self, linear_velocity: float, angular_velocity: float = 0.0):
        """Set vehicle velocity"""
        if not self.robot or not hasattr(self, 'left_motor') or not hasattr(self, 'right_motor'):
            self.logger.warning("Motors not available")
            return
        
        try:
            # Clamp velocities
            linear_velocity = max(-self.max_speed, min(self.max_speed, linear_velocity))
            angular_velocity = max(-2.0, min(2.0, angular_velocity))
            
            # Differential drive calculation
            wheel_radius = 0.2  # meters
            wheel_separation = 1.0  # meters
            
            left_speed = (linear_velocity - angular_velocity * wheel_separation / 2) / wheel_radius
            right_speed = (linear_velocity + angular_velocity * wheel_separation / 2) / wheel_radius
            
            self.left_motor.setVelocity(left_speed)
            self.right_motor.setVelocity(right_speed)
            
            self.current_speed = linear_velocity
            self.vehicle_state['velocity']['linear'] = linear_velocity
            self.vehicle_state['velocity']['angular'] = angular_velocity
            
            # Update gear based on direction
            if linear_velocity > 0.1:
                self.vehicle_state['gear'] = 'D'
            elif linear_velocity < -0.1:
                self.vehicle_state['gear'] = 'R'
            else:
                self.vehicle_state['gear'] = 'P'
            
            self.logger.info(f"Velocity set: linear={linear_velocity:.2f}, angular={angular_velocity:.2f}")
            
        except Exception as e:
            self.logger.error(f"Failed to set velocity: {e}")
    
    def set_steering(self, angle: float):
        """Set steering angle (for car-like vehicles)"""
        if not hasattr(self, 'steering_motor') or not self.steering_motor:
            return
        
        try:
            # Clamp steering angle
            angle = max(-self.max_steering_angle, min(self.max_steering_angle, angle))
            self.steering_motor.setPosition(angle)
            self.current_steering = angle
            self.logger.info(f"Steering set to {math.degrees(angle):.1f} degrees")
            
        except Exception as e:
            self.logger.error(f"Failed to set steering: {e}")
    
    def emergency_stop(self):
        """Emergency stop the vehicle"""
        self.set_velocity(0.0, 0.0)
        self.set_steering(0.0)
        self.vehicle_state['gear'] = 'P'
        self.logger.warning("EMERGENCY STOP ACTIVATED")
    
    def move_forward(self, speed_kmh: float = 20.0):
        """Move vehicle forward"""
        speed_ms = speed_kmh / 3.6  # Convert km/h to m/s
        self.set_velocity(speed_ms, 0.0)
        self.logger.info(f"Moving forward at {speed_kmh} km/h")
    
    def move_backward(self, speed_kmh: float = 10.0):
        """Move vehicle backward"""
        speed_ms = -speed_kmh / 3.6  # Convert km/h to m/s
        self.set_velocity(speed_ms, 0.0)
        self.logger.info(f"Moving backward at {speed_kmh} km/h")
    
    def turn_left(self, angular_speed: float = 0.5):
        """Turn vehicle left"""
        self.set_velocity(self.current_speed, angular_speed)
        self.logger.info("Turning left")
    
    def turn_right(self, angular_speed: float = 0.5):
        """Turn vehicle right"""
        self.set_velocity(self.current_speed, -angular_speed)
        self.logger.info("Turning right")
    
    def park(self):
        """Park the vehicle"""
        self.emergency_stop()
        self.logger.info("Vehicle parked")
    
    def process_ai_command(self, command: str) -> Dict[str, Any]:
        """Process AI command using Gemini"""
        self.logger.info(f"Processing AI command: {command}")
        
        # Get current sensor data for context
        context = {
            'vehicle_state': self.vehicle_state,
            'sensor_readings': self._get_sensor_summary()
        }
        
        response = self.gemini_agent.process_command(command, context, self.vehicle_state)
        
        if response and not response.get('clarification_needed', False):
            self._execute_ai_action(response)
        
        return response
    
    def _get_sensor_summary(self) -> Dict[str, Any]:
        """Get summary of current sensor readings"""
        summary = {
            'position': self.vehicle_state['position'],
            'orientation': self.vehicle_state['orientation'],
            'speed': self.vehicle_state['speed_kmh'],
            'obstacles': {}
        }
        
        # Add distance sensor readings
        for name, sensor in self.distance_sensors.items():
            try:
                distance = sensor.getValue()
                summary['obstacles'][name] = distance
            except:
                summary['obstacles'][name] = float('inf')
        
        return summary
    
    def _execute_ai_action(self, ai_response: Dict[str, Any]):
        """Execute action from AI response"""
        action = ai_response.get('action', '')
        parameters = ai_response.get('parameters', {})
        
        try:
            if action == 'move_forward':
                speed = parameters.get('speed', 20.0)
                self.move_forward(speed)
            elif action == 'move_backward':
                speed = parameters.get('speed', 10.0)
                self.move_backward(speed)
            elif action == 'turn_left':
                self.turn_left()
            elif action == 'turn_right':
                self.turn_right()
            elif action == 'stop':
                self.emergency_stop()
            elif action == 'park':
                self.park()
            elif action == 'set_speed':
                speed = parameters.get('speed', 0.0)
                if speed > 0:
                    self.move_forward(speed)
                elif speed < 0:
                    self.move_backward(abs(speed))
                else:
                    self.emergency_stop()
            else:
                self.logger.warning(f"Unknown action: {action}")
        
        except Exception as e:
            self.logger.error(f"Failed to execute AI action: {e}")
    
    def step(self):
        """Single simulation step"""
        if self.robot:
            result = self.robot.step(self.timestep)
            if result == -1:
                return False  # Simulation ended
        
        self.update_sensors()
        return True
    
    def run_simulation_loop(self):
        """Main simulation loop"""
        self.logger.info("Starting Webots simulation loop")
        
        try:
            while self.step():
                # Simulation continues
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
        except KeyboardInterrupt:
            self.logger.info("Simulation interrupted by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.robot:
                self.emergency_stop()
            self.can_simulator.stop()
            self.logger.info("Webots controller cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def get_vehicle_state(self) -> Dict[str, Any]:
        """Get current vehicle state"""
        return self.vehicle_state.copy()
    
    def get_camera_image(self) -> Optional[bytes]:
        """Get current camera image"""
        if hasattr(self, 'camera') and self.camera:
            try:
                return self.camera.getImage()
            except:
                return None
        return None

def main():
    """Main function for testing Webots controller"""
    print("🚗 Webots Vehicle Controller Test")
    print("=" * 40)
    
    if not WEBOTS_AVAILABLE:
        print("❌ Webots not available. Please install Webots and run this script from within Webots.")
        return
    
    controller = WebotsVehicleController()
    
    try:
        # Test basic movements
        print("Testing forward movement...")
        controller.move_forward(15.0)
        
        # Run for a few seconds
        for _ in range(50):
            if not controller.step():
                break
            time.sleep(0.1)
        
        print("Testing turn...")
        controller.turn_left()
        
        for _ in range(30):
            if not controller.step():
                break
            time.sleep(0.1)
        
        print("Testing stop...")
        controller.emergency_stop()
        
        print("✅ Basic tests completed")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()
