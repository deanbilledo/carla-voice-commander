"""
CARLA Simulator Interface
Handles connection to CARLA and vehicle control
"""

import carla
import time
import numpy as np
from config import Config
from utils.logger import Logger

class CarlaInterface:
    """Interface for connecting to and controlling CARLA simulator"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.client = None
        self.world = None
        self.vehicle = None
        self.sensors = {}
        self.vehicle_status = {
            "speed": 0.0,
            "location": {"x": 0, "y": 0, "z": 0},
            "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
            "control_mode": "manual",
            "fuel": 1.0,
            "health": 1.0
        }
        
    def connect(self):
        """Connect to CARLA simulator"""
        try:
            self.client = carla.Client(Config.CARLA_HOST, Config.CARLA_PORT)
            self.client.set_timeout(10.0)
            self.world = self.client.get_world()
            
            # Get blueprint library
            self.blueprint_library = self.world.get_blueprint_library()
            
            self.logger.info(f"Connected to CARLA at {Config.CARLA_HOST}:{Config.CARLA_PORT}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to CARLA: {e}")
            return False
    
    def spawn_vehicle(self, vehicle_type='vehicle.tesla.model3'):
        """Spawn a vehicle in the simulation"""
        try:
            # Get vehicle blueprint
            vehicle_bp = self.blueprint_library.filter(vehicle_type)[0]
            
            # Get spawn points
            spawn_points = self.world.get_map().get_spawn_points()
            
            if not spawn_points:
                self.logger.error("No spawn points available")
                return False
            
            # Spawn vehicle at first available spawn point
            spawn_point = spawn_points[0]
            self.vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
            
            # Setup sensors
            self._setup_sensors()
            
            self.logger.info(f"Vehicle spawned: {vehicle_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to spawn vehicle: {e}")
            return False
    
    def _setup_sensors(self):
        """Setup sensors for the vehicle"""
        try:
            # Camera sensor
            camera_bp = self.blueprint_library.find('sensor.camera.rgb')
            camera_bp.set_attribute('image_size_x', '800')
            camera_bp.set_attribute('image_size_y', '600')
            camera_bp.set_attribute('fov', '90')
            
            camera_transform = carla.Transform(carla.Location(x=2.0, z=1.5))
            self.sensors['camera'] = self.world.spawn_actor(
                camera_bp, camera_transform, attach_to=self.vehicle
            )
            
            # GPS sensor
            gps_bp = self.blueprint_library.find('sensor.other.gnss')
            gps_transform = carla.Transform(carla.Location(x=0.0, z=2.0))
            self.sensors['gps'] = self.world.spawn_actor(
                gps_bp, gps_transform, attach_to=self.vehicle
            )
            
            self.logger.info("Sensors setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup sensors: {e}")
    
    def update_vehicle_status(self):
        """Update vehicle status information"""
        if not self.vehicle:
            return
        
        try:
            # Get vehicle physics
            velocity = self.vehicle.get_velocity()
            speed = 3.6 * np.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)  # km/h
            
            # Get location and rotation
            transform = self.vehicle.get_transform()
            location = transform.location
            rotation = transform.rotation
            
            # Update status
            self.vehicle_status.update({
                "speed": round(speed, 1),
                "location": {
                    "x": round(location.x, 2),
                    "y": round(location.y, 2),
                    "z": round(location.z, 2)
                },
                "rotation": {
                    "pitch": round(rotation.pitch, 2),
                    "yaw": round(rotation.yaw, 2),
                    "roll": round(rotation.roll, 2)
                }
            })
            
        except Exception as e:
            self.logger.error(f"Failed to update vehicle status: {e}")
    
    def apply_control(self, control_command):
        """Apply control command to vehicle"""
        if not self.vehicle:
            self.logger.warning("No vehicle available for control")
            return False
        
        try:
            if control_command["action"] == "stop":
                control = carla.VehicleControl(
                    throttle=0.0,
                    brake=1.0,
                    steer=0.0
                )
            elif control_command["action"] == "forward":
                throttle = control_command.get("throttle", 0.5)
                control = carla.VehicleControl(
                    throttle=throttle,
                    brake=0.0,
                    steer=0.0
                )
            elif control_command["action"] == "turn":
                direction = control_command.get("direction", "left")
                steer = -0.5 if direction == "left" else 0.5
                control = carla.VehicleControl(
                    throttle=0.3,
                    brake=0.0,
                    steer=steer
                )
            else:
                self.logger.warning(f"Unknown control action: {control_command['action']}")
                return False
            
            self.vehicle.apply_control(control)
            self.logger.info(f"Applied control: {control_command}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply control: {e}")
            return False
    
    def get_vehicle_status(self):
        """Get current vehicle status"""
        self.update_vehicle_status()
        return self.vehicle_status.copy()
    
    def get_environment_info(self):
        """Get current environment information"""
        if not self.world:
            return {}
        
        try:
            weather = self.world.get_weather()
            actors = self.world.get_actors()
            
            # Count different types of actors
            vehicles = actors.filter('vehicle.*')
            pedestrians = actors.filter('walker.pedestrian.*')
            traffic_lights = actors.filter('traffic.traffic_light')
            
            return {
                "weather": {
                    "cloudiness": weather.cloudiness,
                    "precipitation": weather.precipitation,
                    "wind_intensity": weather.wind_intensity,
                    "sun_azimuth_angle": weather.sun_azimuth_angle
                },
                "traffic": {
                    "vehicles_count": len(vehicles),
                    "pedestrians_count": len(pedestrians),
                    "traffic_lights_count": len(traffic_lights)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get environment info: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup CARLA resources"""
        try:
            # Destroy sensors
            for sensor in self.sensors.values():
                if sensor:
                    sensor.destroy()
            
            # Destroy vehicle
            if self.vehicle:
                self.vehicle.destroy()
            
            self.logger.info("CARLA cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Example usage
if __name__ == "__main__":
    carla_interface = CarlaInterface()
    
    if carla_interface.connect():
        if carla_interface.spawn_vehicle():
            # Test vehicle status
            status = carla_interface.get_vehicle_status()
            print(f"Vehicle status: {status}")
            
            # Test environment info
            env_info = carla_interface.get_environment_info()
            print(f"Environment: {env_info}")
        
        carla_interface.cleanup()
