"""
Autonomous driving controller with behavior planning and execution
"""

import math
import numpy as np
from enum import Enum
from config import Config
from utils.logger import Logger

class DrivingBehavior(Enum):
    """Driving behavior states"""
    IDLE = "idle"
    FOLLOWING_LANE = "following_lane"
    CHANGING_LANE = "changing_lane"
    PARKING = "parking"
    FOLLOWING_VEHICLE = "following_vehicle"
    EMERGENCY_STOP = "emergency_stop"
    TURNING = "turning"

class AutonomousController:
    """AI-based autonomous driving controller"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.current_behavior = DrivingBehavior.IDLE
        self.target_speed = 30.0  # km/h
        self.target_location = None
        self.waypoints = []
        self.current_waypoint_index = 0
        
        # Safety parameters
        self.safe_distance = Config.SAFETY_DISTANCE
        self.max_speed = Config.MAX_SPEED
        self.reaction_time = Config.REACTION_TIME
        
        # Control parameters
        self.steering_pid = PIDController(0.5, 0.1, 0.2)
        self.speed_pid = PIDController(0.3, 0.05, 0.1)
        
        self.logger.info("Autonomous controller initialized")
    
    def set_destination(self, destination_location):
        """Set destination for autonomous navigation"""
        self.target_location = destination_location
        self.current_behavior = DrivingBehavior.FOLLOWING_LANE
        self.logger.info(f"Destination set: {destination_location}")
    
    def set_behavior(self, behavior):
        """Set driving behavior"""
        self.current_behavior = behavior
        self.logger.info(f"Behavior changed to: {behavior.value}")
    
    def update_waypoints(self, waypoints):
        """Update navigation waypoints"""
        self.waypoints = waypoints
        self.current_waypoint_index = 0
        self.logger.info(f"Updated waypoints: {len(waypoints)} points")
    
    def compute_control(self, vehicle_state, environment_info):
        """
        Compute vehicle control based on current state and behavior
        
        Args:
            vehicle_state (dict): Current vehicle state
            environment_info (dict): Current environment information
            
        Returns:
            dict: Control commands (throttle, brake, steer)
        """
        try:
            # Safety check first
            if self._emergency_stop_required(vehicle_state, environment_info):
                return self._emergency_stop()
            
            # Behavior-based control
            if self.current_behavior == DrivingBehavior.IDLE:
                return self._idle_control()
            elif self.current_behavior == DrivingBehavior.FOLLOWING_LANE:
                return self._lane_following_control(vehicle_state, environment_info)
            elif self.current_behavior == DrivingBehavior.PARKING:
                return self._parking_control(vehicle_state, environment_info)
            elif self.current_behavior == DrivingBehavior.FOLLOWING_VEHICLE:
                return self._vehicle_following_control(vehicle_state, environment_info)
            elif self.current_behavior == DrivingBehavior.TURNING:
                return self._turning_control(vehicle_state, environment_info)
            else:
                return self._idle_control()
                
        except Exception as e:
            self.logger.error(f"Error computing control: {e}")
            return self._emergency_stop()
    
    def _emergency_stop_required(self, vehicle_state, environment_info):
        """Check if emergency stop is required"""
        # Check for obstacles too close
        # TODO: Implement obstacle detection logic
        return False
    
    def _emergency_stop(self):
        """Emergency stop control"""
        self.current_behavior = DrivingBehavior.EMERGENCY_STOP
        return {
            "action": "stop",
            "throttle": 0.0,
            "brake": 1.0,
            "steer": 0.0
        }
    
    def _idle_control(self):
        """Idle state control"""
        return {
            "action": "idle",
            "throttle": 0.0,
            "brake": 0.3,
            "steer": 0.0
        }
    
    def _lane_following_control(self, vehicle_state, environment_info):
        """Lane following control logic"""
        if not self.waypoints:
            return self._idle_control()
        
        # Get current and target waypoint
        current_location = vehicle_state.get('location', {})
        current_pos = np.array([current_location.get('x', 0), current_location.get('y', 0)])
        
        if self.current_waypoint_index < len(self.waypoints):
            target_waypoint = self.waypoints[self.current_waypoint_index]
            target_pos = np.array([target_waypoint['x'], target_waypoint['y']])
            
            # Calculate distance to target
            distance = np.linalg.norm(target_pos - current_pos)
            
            # Move to next waypoint if close enough
            if distance < 3.0:  # 3 meters threshold
                self.current_waypoint_index += 1
                if self.current_waypoint_index >= len(self.waypoints):
                    # Reached destination
                    self.current_behavior = DrivingBehavior.IDLE
                    return self._idle_control()
            
            # Calculate steering
            vehicle_yaw = math.radians(vehicle_state.get('rotation', {}).get('yaw', 0))
            target_angle = math.atan2(target_pos[1] - current_pos[1], target_pos[0] - current_pos[0])
            angle_diff = self._normalize_angle(target_angle - vehicle_yaw)
            
            steer = self.steering_pid.update(angle_diff)
            steer = np.clip(steer, -1.0, 1.0)
            
            # Calculate throttle/brake
            current_speed = vehicle_state.get('speed', 0)
            speed_error = self.target_speed - current_speed
            
            if speed_error > 0:
                throttle = self.speed_pid.update(speed_error) / 100.0
                throttle = np.clip(throttle, 0.0, 1.0)
                brake = 0.0
            else:
                throttle = 0.0
                brake = np.clip(-speed_error / 50.0, 0.0, 1.0)
            
            return {
                "action": "navigate",
                "throttle": throttle,
                "brake": brake,
                "steer": steer
            }
        
        return self._idle_control()
    
    def _parking_control(self, vehicle_state, environment_info):
        """Parking maneuver control"""
        # TODO: Implement parking logic
        return self._idle_control()
    
    def _vehicle_following_control(self, vehicle_state, environment_info):
        """Vehicle following control"""
        # TODO: Implement vehicle following logic
        return self._lane_following_control(vehicle_state, environment_info)
    
    def _turning_control(self, vehicle_state, environment_info):
        """Turning maneuver control"""
        # TODO: Implement turning logic
        return self._lane_following_control(vehicle_state, environment_info)
    
    def _normalize_angle(self, angle):
        """Normalize angle to [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

class PIDController:
    """Simple PID controller"""
    
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.last_error = 0
        self.integral = 0
    
    def update(self, error, dt=0.1):
        """Update PID controller"""
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        
        output = (self.kp * error + 
                 self.ki * self.integral + 
                 self.kd * derivative)
        
        self.last_error = error
        return output
    
    def reset(self):
        """Reset PID controller"""
        self.last_error = 0
        self.integral = 0

# Example usage
if __name__ == "__main__":
    controller = AutonomousController()
    
    # Test waypoints
    waypoints = [
        {"x": 100, "y": 200},
        {"x": 150, "y": 250},
        {"x": 200, "y": 300}
    ]
    
    controller.update_waypoints(waypoints)
    controller.set_behavior(DrivingBehavior.FOLLOWING_LANE)
    
    # Test control computation
    vehicle_state = {
        "speed": 25,
        "location": {"x": 90, "y": 190, "z": 0.5},
        "rotation": {"yaw": 45, "pitch": 0, "roll": 0}
    }
    
    control = controller.compute_control(vehicle_state, {})
    print(f"Control output: {control}")
