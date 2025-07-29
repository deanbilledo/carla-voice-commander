"""
CAN Bus simulation for RAMN protocol
Simulates automotive ECUs and CAN message types
"""

import time
import threading
import struct
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from utils.logger import Logger

class ECUType(Enum):
    """Electronic Control Unit types"""
    ENGINE = "engine"
    TRANSMISSION = "transmission"
    BRAKE = "brake"
    STEERING = "steering"
    BODY = "body"
    INFOTAINMENT = "infotainment"
    AIRBAG = "airbag"
    ABS = "abs"

class MessageType(Enum):
    """CAN message types"""
    ENGINE_RPM = 0x100
    VEHICLE_SPEED = 0x101
    BRAKE_PRESSURE = 0x102
    STEERING_ANGLE = 0x103
    GEAR_POSITION = 0x104
    FUEL_LEVEL = 0x105
    ENGINE_TEMP = 0x106
    BATTERY_VOLTAGE = 0x107
    TIRE_PRESSURE = 0x108
    DOOR_STATUS = 0x109
    AIRBAG_STATUS = 0x10A
    ABS_STATUS = 0x10B

@dataclass
class CANMessage:
    """CAN message structure"""
    message_id: int
    data: bytes
    timestamp: float
    source_ecu: ECUType
    priority: int = 0

class ECU:
    """Electronic Control Unit simulation"""
    
    def __init__(self, ecu_type: ECUType, can_bus):
        self.ecu_type = ecu_type
        self.can_bus = can_bus
        self.logger = Logger.get_logger(f"ECU_{ecu_type.value}")
        self.is_active = False
        self.message_handlers = {}
        self.periodic_messages = {}
        self.thread = None
        
    def start(self):
        """Start ECU operation"""
        self.is_active = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info(f"ECU {self.ecu_type.value} started")
    
    def stop(self):
        """Stop ECU operation"""
        self.is_active = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        self.logger.info(f"ECU {self.ecu_type.value} stopped")
    
    def add_message_handler(self, message_type: MessageType, handler: Callable):
        """Add handler for incoming messages"""
        self.message_handlers[message_type] = handler
    
    def add_periodic_message(self, message_type: MessageType, interval: float, data_func: Callable):
        """Add periodic message transmission"""
        self.periodic_messages[message_type] = {
            'interval': interval,
            'data_func': data_func,
            'last_sent': 0
        }
    
    def send_message(self, message_type: MessageType, data: bytes):
        """Send CAN message"""
        message = CANMessage(
            message_id=message_type.value,
            data=data,
            timestamp=time.time(),
            source_ecu=self.ecu_type
        )
        self.can_bus.send_message(message)
    
    def handle_message(self, message: CANMessage):
        """Handle incoming CAN message"""
        message_type = MessageType(message.message_id)
        if message_type in self.message_handlers:
            self.message_handlers[message_type](message)
    
    def _run_loop(self):
        """Main ECU execution loop"""
        while self.is_active:
            current_time = time.time()
            
            # Send periodic messages
            for message_type, config in self.periodic_messages.items():
                if current_time - config['last_sent'] >= config['interval']:
                    data = config['data_func']()
                    self.send_message(message_type, data)
                    config['last_sent'] = current_time
            
            time.sleep(0.01)  # 10ms cycle

class CANBus:
    """CAN Bus simulation"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.ecus: Dict[ECUType, ECU] = {}
        self.message_log: List[CANMessage] = []
        self.message_subscribers: Dict[MessageType, List[Callable]] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
    def add_ecu(self, ecu_type: ECUType) -> ECU:
        """Add ECU to the bus"""
        ecu = ECU(ecu_type, self)
        self.ecus[ecu_type] = ecu
        self.logger.info(f"Added ECU: {ecu_type.value}")
        return ecu
    
    def start(self):
        """Start CAN bus operation"""
        self.is_running = True
        
        # Start all ECUs
        for ecu in self.ecus.values():
            ecu.start()
        
        self.logger.info("CAN bus started")
    
    def stop(self):
        """Stop CAN bus operation"""
        self.is_running = False
        
        # Stop all ECUs
        for ecu in self.ecus.values():
            ecu.stop()
        
        self.logger.info("CAN bus stopped")
    
    def send_message(self, message: CANMessage):
        """Send message on the bus"""
        with self.lock:
            # Add to log
            self.message_log.append(message)
            
            # Keep log size manageable
            if len(self.message_log) > 10000:
                self.message_log = self.message_log[-5000:]
            
            # Notify subscribers
            message_type = MessageType(message.message_id)
            if message_type in self.message_subscribers:
                for callback in self.message_subscribers[message_type]:
                    try:
                        callback(message)
                    except Exception as e:
                        self.logger.error(f"Error in message subscriber: {e}")
            
            # Send to all ECUs except sender
            for ecu in self.ecus.values():
                if ecu.ecu_type != message.source_ecu:
                    ecu.handle_message(message)
    
    def subscribe_to_message(self, message_type: MessageType, callback: Callable):
        """Subscribe to specific message type"""
        if message_type not in self.message_subscribers:
            self.message_subscribers[message_type] = []
        self.message_subscribers[message_type].append(callback)
    
    def get_recent_messages(self, message_type: Optional[MessageType] = None, count: int = 100):
        """Get recent messages"""
        with self.lock:
            if message_type:
                filtered = [msg for msg in self.message_log 
                           if msg.message_id == message_type.value]
                return filtered[-count:]
            else:
                return self.message_log[-count:]

class VehicleCANSimulator:
    """Complete vehicle CAN bus simulator"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.can_bus = CANBus()
        self.vehicle_state = {
            'speed': 0.0,
            'rpm': 800,
            'gear': 'P',
            'fuel_level': 1.0,
            'engine_temp': 90.0,
            'battery_voltage': 12.6,
            'brake_pressure': 0.0,
            'steering_angle': 0.0
        }
        
        self._setup_ecus()
    
    def _setup_ecus(self):
        """Setup all vehicle ECUs"""
        # Engine ECU
        engine_ecu = self.can_bus.add_ecu(ECUType.ENGINE)
        engine_ecu.add_periodic_message(
            MessageType.ENGINE_RPM, 
            0.1, 
            lambda: struct.pack('>H', int(self.vehicle_state['rpm']))
        )
        engine_ecu.add_periodic_message(
            MessageType.ENGINE_TEMP, 
            1.0, 
            lambda: struct.pack('>f', self.vehicle_state['engine_temp'])
        )
        
        # Body ECU
        body_ecu = self.can_bus.add_ecu(ECUType.BODY)
        body_ecu.add_periodic_message(
            MessageType.VEHICLE_SPEED, 
            0.1, 
            lambda: struct.pack('>f', self.vehicle_state['speed'])
        )
        body_ecu.add_periodic_message(
            MessageType.FUEL_LEVEL, 
            5.0, 
            lambda: struct.pack('>f', self.vehicle_state['fuel_level'])
        )
        body_ecu.add_periodic_message(
            MessageType.BATTERY_VOLTAGE, 
            2.0, 
            lambda: struct.pack('>f', self.vehicle_state['battery_voltage'])
        )
        
        # Brake ECU
        brake_ecu = self.can_bus.add_ecu(ECUType.BRAKE)
        brake_ecu.add_periodic_message(
            MessageType.BRAKE_PRESSURE, 
            0.05, 
            lambda: struct.pack('>f', self.vehicle_state['brake_pressure'])
        )
        
        # Steering ECU
        steering_ecu = self.can_bus.add_ecu(ECUType.STEERING)
        steering_ecu.add_periodic_message(
            MessageType.STEERING_ANGLE, 
            0.05, 
            lambda: struct.pack('>f', self.vehicle_state['steering_angle'])
        )
        
        # Transmission ECU
        transmission_ecu = self.can_bus.add_ecu(ECUType.TRANSMISSION)
        transmission_ecu.add_periodic_message(
            MessageType.GEAR_POSITION, 
            0.5, 
            lambda: self.vehicle_state['gear'].encode('utf-8')
        )
    
    def start(self):
        """Start the vehicle CAN simulation"""
        self.can_bus.start()
        self.logger.info("Vehicle CAN simulation started")
    
    def stop(self):
        """Stop the vehicle CAN simulation"""
        self.can_bus.stop()
        self.logger.info("Vehicle CAN simulation stopped")
    
    def update_vehicle_state(self, **kwargs):
        """Update vehicle state parameters"""
        for key, value in kwargs.items():
            if key in self.vehicle_state:
                self.vehicle_state[key] = value
    
    def get_vehicle_state(self):
        """Get current vehicle state"""
        return self.vehicle_state.copy()
    
    def subscribe_to_message_type(self, message_type: MessageType, callback: Callable):
        """Subscribe to specific CAN message type"""
        self.can_bus.subscribe_to_message(message_type, callback)

# Example usage
if __name__ == "__main__":
    # Create vehicle CAN simulator
    vehicle_can = VehicleCANSimulator()
    
    # Subscribe to some messages
    def on_speed_message(message):
        speed = struct.unpack('>f', message.data)[0]
        print(f"Speed: {speed:.1f} km/h")
    
    def on_rpm_message(message):
        rpm = struct.unpack('>H', message.data)[0]
        print(f"RPM: {rpm}")
    
    vehicle_can.subscribe_to_message_type(MessageType.VEHICLE_SPEED, on_speed_message)
    vehicle_can.subscribe_to_message_type(MessageType.ENGINE_RPM, on_rpm_message)
    
    # Start simulation
    vehicle_can.start()
    
    try:
        # Simulate driving
        for i in range(10):
            vehicle_can.update_vehicle_state(
                speed=i * 10,
                rpm=800 + i * 200
            )
            time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    
    # Stop simulation
    vehicle_can.stop()
