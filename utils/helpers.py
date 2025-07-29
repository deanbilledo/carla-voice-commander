"""
Utility functions for CARLA Voice Commander
"""

import math
import numpy as np
from typing import Tuple, List, Dict, Any

def calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def normalize_angle(angle: float) -> float:
    """Normalize angle to [-pi, pi] range"""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle

def deg_to_rad(degrees: float) -> float:
    """Convert degrees to radians"""
    return degrees * math.pi / 180.0

def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees"""
    return radians * 180.0 / math.pi

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t"""
    return a + t * (b - a)

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value for division by zero"""
    return numerator / denominator if denominator != 0 else default

def format_location(location: Dict[str, float]) -> str:
    """Format location dictionary for display"""
    return f"({location.get('x', 0):.2f}, {location.get('y', 0):.2f}, {location.get('z', 0):.2f})"

def format_rotation(rotation: Dict[str, float]) -> str:
    """Format rotation dictionary for display"""
    return f"Pitch: {rotation.get('pitch', 0):.1f}°, Yaw: {rotation.get('yaw', 0):.1f}°, Roll: {rotation.get('roll', 0):.1f}°"

def parse_coordinates(coord_string: str) -> Tuple[float, float]:
    """Parse coordinate string like '100,200' into tuple"""
    try:
        parts = coord_string.split(',')
        if len(parts) == 2:
            return float(parts[0].strip()), float(parts[1].strip())
    except (ValueError, IndexError):
        pass
    return 0.0, 0.0

def create_waypoint(x: float, y: float, z: float = 0.0) -> Dict[str, float]:
    """Create a waypoint dictionary"""
    return {"x": x, "y": y, "z": z}

def smooth_value(current: float, target: float, smoothing: float = 0.1) -> float:
    """Smooth transition between current and target value"""
    return current + (target - current) * smoothing

class MovingAverage:
    """Simple moving average calculator"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.values = []
    
    def add_value(self, value: float) -> float:
        """Add value and return current average"""
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
        return sum(self.values) / len(self.values)
    
    def get_average(self) -> float:
        """Get current average"""
        return sum(self.values) / len(self.values) if self.values else 0.0
    
    def reset(self):
        """Reset the moving average"""
        self.values.clear()

class Timer:
    """Simple timer utility"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer"""
        import time
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self) -> float:
        """Stop the timer and return elapsed time"""
        import time
        self.end_time = time.time()
        return self.get_elapsed()
    
    def get_elapsed(self) -> float:
        """Get elapsed time (without stopping)"""
        import time
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

def validate_config_value(value: Any, expected_type: type, default: Any) -> Any:
    """Validate configuration value and return default if invalid"""
    try:
        if isinstance(value, expected_type):
            return value
        elif expected_type == bool and isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif expected_type in (int, float):
            return expected_type(value)
        else:
            return default
    except (ValueError, TypeError):
        return default
