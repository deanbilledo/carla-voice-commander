"""
🎮 CARLA Overlay GUI - Transparent Control Interface
Overlay interface that sits on top of the CARLA 3D window
"""

import sys
import os
import time
import math
import threading
import glob
import random
import importlib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QTextEdit, QLineEdit,
                             QGroupBox, QGridLayout, QFrame, QSlider, QComboBox,
                             QTabWidget, QSplitter, QProgressBar)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QBrush, QPixmap, QImage

# Import CARLA
try:
    import carla
    CARLA_AVAILABLE = True
    print("✅ CARLA overlay ready!")
except ImportError:
    CARLA_AVAILABLE = False
    carla = None
    print("❌ CARLA not available for overlay")

# Import project modules (with fallbacks)
try:
    from config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = "demo"

try:
    from utils.logger import Logger
except ImportError:
    class Logger:
        @staticmethod
        def info(msg): print(f"ℹ️ {msg}")
        @staticmethod
        def error(msg): print(f"❌ {msg}")

try:
    from gemini_agent import GeminiAgent
except ImportError:
    class GeminiAgent:
        def process_command(self, text, context, state):
            return f"Demo response for: {text}"

try:
    from ramn.can_simulation import VehicleCANSimulator
except ImportError:
    class VehicleCANSimulator:
        def start(self): pass
        def stop(self): pass

class OverlayControlPanel(QFrame):
    """Compact overlay control panel"""
    
    vehicle_command = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 400)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 180);
                border: 2px solid #00ffff;
                border-radius: 15px;
            }
            QPushButton {
                background: rgba(255, 0, 110, 200);
                color: white;
                border: 1px solid #00ffff;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 0, 110, 255);
                border: 2px solid #ffff00;
            }
            QLabel {
                color: #00ffff;
                font-weight: bold;
                font-size: 10px;
            }
            QLineEdit {
                background: rgba(0, 0, 0, 200);
                border: 1px solid #ff006e;
                border-radius: 5px;
                color: #ffff00;
                padding: 5px;
                font-weight: bold;
            }
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 50);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ffff;
                width: 18px;
                border-radius: 9px;
            }
        """)
        self.init_ui()
        self.make_draggable()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("🎮 CARLA RACING OVERLAY")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffff00; font-size: 12px; font-weight: bold;")
        layout.addWidget(title)
        
        # AI Command input
        cmd_layout = QVBoxLayout()
        cmd_layout.addWidget(QLabel("🤖 AI Command:"))
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("'drive forward', 'turn left'...")
        self.command_input.returnPressed.connect(self.send_ai_command)
        cmd_layout.addWidget(self.command_input)
        
        ai_btn = QPushButton("🤖 Send to AI")
        ai_btn.clicked.connect(self.send_ai_command)
        cmd_layout.addWidget(ai_btn)
        layout.addLayout(cmd_layout)
        
        # Quick controls
        controls_layout = QGridLayout()
        controls = [
            ("⬆️ Forward", {"action": "forward", "speed": 50}),
            ("⬇️ Reverse", {"action": "reverse", "speed": 30}),
            ("⬅️ Left", {"action": "turn", "direction": "left"}),
            ("➡️ Right", {"action": "turn", "direction": "right"}),
            ("🛑 Stop", {"action": "emergency_stop"}),
            ("🅿️ Park", {"action": "park"})
        ]
        
        for i, (label, cmd) in enumerate(controls):
            btn = QPushButton(label)
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, command=cmd: self.vehicle_command.emit(command))
            controls_layout.addWidget(btn, i // 2, i % 2)
        
        layout.addLayout(controls_layout)
        
        # Speed control
        speed_layout = QVBoxLayout()
        speed_layout.addWidget(QLabel("⚡ Speed Control:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(0)
        self.speed_slider.valueChanged.connect(self.speed_changed)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("0 km/h")
        self.speed_label.setAlignment(Qt.AlignCenter)
        speed_layout.addWidget(self.speed_label)
        layout.addLayout(speed_layout)
        
        # Weather control
        weather_layout = QVBoxLayout()
        weather_layout.addWidget(QLabel("🌤️ Weather:"))
        self.weather_combo = QComboBox()
        self.weather_combo.addItems(["Clear", "Cloudy", "Rainy", "Foggy", "Night"])
        self.weather_combo.currentTextChanged.connect(self.weather_changed)
        self.weather_combo.setStyleSheet("""
            QComboBox {
                background: rgba(0, 0, 0, 200);
                border: 1px solid #00ffff;
                border-radius: 5px;
                color: #ffff00;
                padding: 5px;
            }
        """)
        weather_layout.addWidget(self.weather_combo)
        layout.addLayout(weather_layout)
        
        # Close button
        close_btn = QPushButton("✖️ Close Overlay")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 0, 0, 200);
                color: white;
            }
            QPushButton:hover {
                background: rgba(255, 0, 0, 255);
            }
        """)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def make_draggable(self):
        """Make the overlay draggable"""
        self.drag_position = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def send_ai_command(self):
        text = self.command_input.text().strip()
        if text:
            self.vehicle_command.emit({"action": "ai_command", "text": text})
            self.command_input.clear()
    
    def speed_changed(self, value):
        self.speed_label.setText(f"{value} km/h")
        self.vehicle_command.emit({"action": "set_speed", "speed": value})
    
    def weather_changed(self, weather):
        self.vehicle_command.emit({"action": "set_weather", "weather": weather.lower()})

class StatusOverlay(QFrame):
    """Compact status display overlay"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(250, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 150);
                border: 2px solid #ff006e;
                border-radius: 10px;
            }
            QLabel {
                color: #00ffff;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.init_ui()
        self.make_draggable()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("📊 VEHICLE STATUS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffff00; font-size: 12px; font-weight: bold;")
        layout.addWidget(title)
        
        # Status labels
        self.status_labels = {}
        status_items = [
            ("speed", "⚡ Speed: 0 km/h"),
            ("position", "📍 Position: (0, 0)"),
            ("heading", "🧭 Heading: 0°"),
            ("gear", "⚙️ Gear: P"),
            ("engine", "🔥 Engine: IDLE")
        ]
        
        for key, initial in status_items:
            label = QLabel(initial)
            self.status_labels[key] = label
            layout.addWidget(label)
        
        # CARLA status
        self.carla_status = QLabel("🎮 CARLA: Connecting...")
        self.carla_status.setStyleSheet("color: #ffff00;")
        layout.addWidget(self.carla_status)
        
        self.setLayout(layout)
    
    def make_draggable(self):
        self.drag_position = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def update_status(self, speed, position, heading, gear, engine_state, carla_connected):
        self.status_labels["speed"].setText(f"⚡ Speed: {speed:.1f} km/h")
        self.status_labels["position"].setText(f"📍 Position: ({position[0]:.0f}, {position[1]:.0f})")
        self.status_labels["heading"].setText(f"🧭 Heading: {heading:.0f}°")
        self.status_labels["gear"].setText(f"⚙️ Gear: {gear}")
        self.status_labels["engine"].setText(f"🔥 Engine: {engine_state}")
        
        if carla_connected:
            self.carla_status.setText("✅ CARLA: Connected")
            self.carla_status.setStyleSheet("color: #00ff00;")
        else:
            self.carla_status.setText("❌ CARLA: Disconnected")
            self.carla_status.setStyleSheet("color: #ff0000;")

class CARLAOverlayManager:
    """Manages CARLA connection and vehicle control for overlay"""
    
    def __init__(self):
        self.carla_client = None
        self.carla_world = None
        self.vehicle = None
        self.camera_sensor = None
        self.connected = False
        
        # Vehicle state
        self.vehicle_x = 0
        self.vehicle_y = 0
        self.vehicle_heading = 0
        self.vehicle_speed = 0
        
        # Initialize components
        self.can_simulator = VehicleCANSimulator()
        self.gemini_agent = GeminiAgent()
        
        self.can_simulator.start()
        self.connect_to_carla()
    
    def connect_to_carla(self):
        """Connect to running CARLA instance"""
        if not CARLA_AVAILABLE:
            print("❌ CARLA module not available")
            return False
        
        try:
            self.carla_client = carla.Client('localhost', 2000)
            self.carla_client.set_timeout(10.0)
            self.carla_world = self.carla_client.get_world()
            
            # Get existing vehicle or spawn one
            vehicles = self.carla_world.get_actors().filter('vehicle.*')
            if vehicles:
                self.vehicle = vehicles[0]
                print(f"✅ Connected to existing vehicle: {self.vehicle.type_id}")
            else:
                # Spawn new vehicle
                self.spawn_vehicle()
            
            self.connected = True
            print("✅ CARLA overlay connected successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to CARLA: {e}")
            self.connected = False
            return False
    
    def spawn_vehicle(self):
        """Spawn a new vehicle in CARLA"""
        try:
            blueprint_library = self.carla_world.get_blueprint_library()
            vehicle_bp = blueprint_library.filter('vehicle.tesla.model3')[0]
            
            # Set red color for racing
            if vehicle_bp.has_attribute('color'):
                vehicle_bp.set_attribute('color', '255,0,0')
            
            spawn_points = self.carla_world.get_map().get_spawn_points()
            if spawn_points:
                self.vehicle = self.carla_world.spawn_actor(vehicle_bp, spawn_points[0])
                print(f"✅ Spawned new vehicle: {vehicle_bp.id}")
        except Exception as e:
            print(f"❌ Failed to spawn vehicle: {e}")
    
    def handle_command(self, command):
        """Handle vehicle commands from overlay"""
        if not self.connected or not self.vehicle:
            print("❌ CARLA not connected - command ignored")
            return
        
        action = command["action"]
        
        try:
            if action == "forward":
                speed = command.get("speed", 50)
                control = carla.VehicleControl()
                control.throttle = min(speed / 100.0, 1.0)
                control.brake = 0.0
                control.steer = 0.0
                self.vehicle.apply_control(control)
                print(f"🎮 CARLA: Moving forward at {speed} km/h")
                
            elif action == "reverse":
                speed = command.get("speed", 30)
                control = carla.VehicleControl()
                control.throttle = 0.0
                control.brake = 0.0
                control.reverse = True
                control.throttle = min(speed / 100.0, 1.0)
                control.steer = 0.0
                self.vehicle.apply_control(control)
                print(f"🎮 CARLA: Reversing at {speed} km/h")
                
            elif action == "turn":
                direction = command["direction"]
                control = carla.VehicleControl()
                control.throttle = 0.2
                control.brake = 0.0
                control.steer = -0.5 if direction == "left" else 0.5
                self.vehicle.apply_control(control)
                print(f"🎮 CARLA: Turning {direction}")
                
                # Reset steering after 1 second
                def reset_steering():
                    if self.vehicle:
                        reset_control = carla.VehicleControl()
                        reset_control.throttle = 0.0
                        reset_control.steer = 0.0
                        self.vehicle.apply_control(reset_control)
                
                threading.Timer(1.0, reset_steering).start()
                
            elif action == "emergency_stop":
                control = carla.VehicleControl()
                control.throttle = 0.0
                control.brake = 1.0
                control.hand_brake = True
                control.steer = 0.0
                self.vehicle.apply_control(control)
                print("🚨 CARLA: Emergency stop activated!")
                
            elif action == "park":
                control = carla.VehicleControl()
                control.throttle = 0.0
                control.brake = 1.0
                control.hand_brake = True
                self.vehicle.apply_control(control)
                print("🅿️ CARLA: Vehicle parked")
                
            elif action == "set_speed":
                speed = command["speed"]
                control = carla.VehicleControl()
                if speed > 0:
                    control.throttle = min(speed / 100.0, 1.0)
                    control.brake = 0.0
                else:
                    control.throttle = 0.0
                    control.brake = 1.0
                control.steer = 0.0
                self.vehicle.apply_control(control)
                print(f"🎮 CARLA: Speed set to {speed} km/h")
                
            elif action == "set_weather":
                weather_name = command["weather"]
                weather_presets = {
                    "clear": carla.WeatherParameters(cloudiness=10.0, precipitation=0.0, sun_altitude_angle=60.0),
                    "cloudy": carla.WeatherParameters(cloudiness=80.0, precipitation=0.0, sun_altitude_angle=45.0),
                    "rainy": carla.WeatherParameters(cloudiness=90.0, precipitation=70.0, sun_altitude_angle=30.0),
                    "foggy": carla.WeatherParameters(cloudiness=60.0, precipitation=0.0, fog_density=80.0),
                    "night": carla.WeatherParameters(cloudiness=30.0, precipitation=0.0, sun_altitude_angle=-30.0)
                }
                
                if weather_name in weather_presets:
                    self.carla_world.set_weather(weather_presets[weather_name])
                    print(f"🌤️ CARLA: Weather changed to {weather_name}")
                    
            elif action == "ai_command":
                text = command["text"]
                print(f"🤖 Processing AI command: {text}")
                # Process with Gemini AI
                response = self.gemini_agent.process_command(text, {}, {})
                print(f"🧠 AI Response: {response}")
                
        except Exception as e:
            print(f"❌ Command failed: {e}")
    
    def update_vehicle_state(self):
        """Update vehicle state from CARLA"""
        if not self.connected or not self.vehicle:
            return
        
        try:
            transform = self.vehicle.get_transform()
            velocity = self.vehicle.get_velocity()
            
            self.vehicle_x = transform.location.x
            self.vehicle_y = transform.location.y
            self.vehicle_heading = transform.rotation.yaw
            self.vehicle_speed = 3.6 * (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
            
        except Exception as e:
            print(f"❌ Failed to update vehicle state: {e}")
            self.connected = False
    
    def cleanup(self):
        """Clean up CARLA resources"""
        try:
            if self.camera_sensor:
                self.camera_sensor.destroy()
            if self.vehicle:
                self.vehicle.destroy()
            self.can_simulator.stop()
        except:
            pass

def main():
    """Main overlay application"""
    app = QApplication(sys.argv)
    
    print("🎮 CARLA Overlay Interface")
    print("=" * 40)
    print("Starting transparent overlay for CARLA...")
    
    # Initialize CARLA manager
    carla_manager = CARLAOverlayManager()
    
    # Create overlay windows
    control_panel = OverlayControlPanel()
    status_overlay = StatusOverlay()
    
    # Position overlays
    screen = app.primaryScreen().geometry()
    control_panel.move(screen.width() - 320, 50)  # Top right
    status_overlay.move(20, screen.height() - 250)  # Bottom left
    
    # Connect signals
    control_panel.vehicle_command.connect(carla_manager.handle_command)
    
    # Show overlays
    control_panel.show()
    status_overlay.show()
    
    # Update timer
    def update_status():
        carla_manager.update_vehicle_state()
        status_overlay.update_status(
            carla_manager.vehicle_speed,
            (carla_manager.vehicle_x, carla_manager.vehicle_y),
            carla_manager.vehicle_heading,
            "D",
            "RACING" if carla_manager.vehicle_speed > 50 else "CRUISING" if carla_manager.vehicle_speed > 0 else "IDLE",
            carla_manager.connected
        )
    
    timer = QTimer()
    timer.timeout.connect(update_status)
    timer.start(100)  # 10 FPS
    
    print("✅ Overlay interface active!")
    print("🎮 Use the transparent controls over CARLA window")
    print("📱 Drag the panels to reposition them")
    
    # Cleanup on exit
    def cleanup():
        carla_manager.cleanup()
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
