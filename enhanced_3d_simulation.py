"""
Enhanced 3D CARLA Vehicle Simulation - Simplified Version
Professional-grade vehicle simulation with CARLA integration
"""

import sys
import os
import time
import math
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QTextEdit, QLineEdit,
                             QGroupBox, QGridLayout, QFrame, QSlider, QComboBox,
                             QTabWidget, QSplitter, QProgressBar)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QBrush, QPixmap, QImage

# Add CARLA path
carla_path = r"C:\Carla-0.10.0-Win64-Shipping\PythonAPI\carla"
if carla_path not in sys.path:
    sys.path.append(carla_path)

# Try to import CARLA
try:
    import carla
    CARLA_AVAILABLE = True
    print("✅ CARLA 0.10.0 imported successfully!")
except ImportError:
    print("❌ CARLA not available. Running in simulation mode.")
    CARLA_AVAILABLE = False
    carla = None

from config import Config
from utils.logger import Logger
from gemini_agent import GeminiAgent
from ramn.can_simulation import VehicleCANSimulator

class CameraWidget(QFrame):
    """Widget for displaying CARLA camera feed"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(640, 480)
        self.setFrameStyle(QFrame.Box)
        self.image = None
        
    def update_image(self, image_data):
        """Update camera image"""
        if image_data is not None and CARLA_AVAILABLE:
            try:
                import numpy as np
                # Convert CARLA image to QImage
                array = np.frombuffer(image_data.raw_data, dtype=np.dtype("uint8"))
                array = np.reshape(array, (image_data.height, image_data.width, 4))
                array = array[:, :, :3]  # Remove alpha channel
                array = array[:, :, ::-1]  # BGR to RGB
                
                height, width, channel = array.shape
                bytes_per_line = 3 * width
                q_image = QImage(array.data, width, height, bytes_per_line, QImage.Format_RGB888)
                self.image = QPixmap.fromImage(q_image)
                self.update()
            except Exception as e:
                pass  # Silent fallback
    
    def paintEvent(self, event):
        """Paint the camera image"""
        painter = QPainter(self)
        
        if self.image:
            painter.drawPixmap(self.rect(), self.image, self.image.rect())
        else:
            # Draw placeholder
            painter.fillRect(self.rect(), QColor(50, 50, 50))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            if CARLA_AVAILABLE:
                painter.drawText(self.rect(), Qt.AlignCenter, "Camera Feed\n(Start CARLA server to connect)")
            else:
                painter.drawText(self.rect(), Qt.AlignCenter, "CARLA Camera\n(Simulation Mode)")

class Enhanced3DMapWidget(QFrame):
    """Enhanced 3D-style map visualization"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(600, 400)
        self.setFrameStyle(QFrame.Box)
        
        # Vehicle state
        self.vehicle_x = 300
        self.vehicle_y = 200
        self.vehicle_heading = 0
        self.vehicle_speed = 0
        self.trail_points = []
        
        # Environment
        self.buildings = self._generate_3d_buildings()
        self.roads = self._generate_road_network()
        self.traffic_lights = self._generate_traffic_system()
        self.weather = {"time": 12.0, "clouds": 0.3, "rain": 0.0}
        
        # Animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_environment)
        self.animation_timer.start(50)
        
    def _generate_3d_buildings(self):
        """Generate 3D-style buildings"""
        import random
        buildings = []
        for _ in range(25):
            x = random.randint(50, 550)
            y = random.randint(50, 350)
            w = random.randint(40, 80)
            h = random.randint(40, 80)
            height = random.randint(3, 8)
            buildings.append({
                "x": x, "y": y, "width": w, "height": h,
                "building_height": height, "color": random.choice([
                    QColor(100, 100, 120), QColor(120, 100, 100), 
                    QColor(100, 120, 100), QColor(90, 90, 90)
                ])
            })
        return buildings
    
    def _generate_road_network(self):
        """Generate complex road network"""
        return [
            # Main roads
            {"type": "horizontal", "y": 200, "x1": 0, "x2": 600, "width": 60, "lanes": 4},
            {"type": "horizontal", "y": 100, "x1": 0, "x2": 600, "width": 40, "lanes": 2},
            {"type": "horizontal", "y": 300, "x1": 0, "x2": 600, "width": 40, "lanes": 2},
            {"type": "vertical", "x": 300, "y1": 0, "y2": 400, "width": 60, "lanes": 4},
            {"type": "vertical", "x": 150, "y1": 0, "y2": 400, "width": 40, "lanes": 2},
            {"type": "vertical", "x": 450, "y1": 0, "y2": 400, "width": 40, "lanes": 2},
        ]
    
    def _generate_traffic_system(self):
        """Generate intelligent traffic light system"""
        return [
            {"x": 280, "y": 180, "state": "green", "timer": 0, "cycle": 120},
            {"x": 320, "y": 220, "state": "red", "timer": 60, "cycle": 120},
            {"x": 130, "y": 180, "state": "yellow", "timer": 90, "cycle": 120},
            {"x": 470, "y": 220, "state": "green", "timer": 30, "cycle": 120},
        ]
    
    def update_vehicle_state(self, x, y, heading, speed):
        """Update vehicle state with trail"""
        self.vehicle_x = x
        self.vehicle_y = y
        self.vehicle_heading = heading
        self.vehicle_speed = speed
        
        # Add to trail
        self.trail_points.append((x, y))
        if len(self.trail_points) > 50:
            self.trail_points.pop(0)
        
        self.update()
    
    def update_environment(self):
        """Update dynamic environment elements"""
        # Update traffic lights
        for light in self.traffic_lights:
            light["timer"] += 1
            if light["timer"] >= light["cycle"]:
                light["timer"] = 0
                # Cycle through states
                if light["state"] == "green":
                    light["state"] = "yellow"
                elif light["state"] == "yellow":
                    light["state"] = "red"
                else:
                    light["state"] = "green"
        
        # Update weather
        self.weather["time"] += 0.01
        if self.weather["time"] >= 24:
            self.weather["time"] = 0
            
        self.update()
    
    def paintEvent(self, event):
        """Paint enhanced 3D-style visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Sky gradient based on time
        sky_color = self._get_sky_color()
        painter.fillRect(self.rect(), sky_color)
        
        # Draw roads with 3D effect
        self._draw_roads_3d(painter)
        
        # Draw buildings with 3D effect
        self._draw_buildings_3d(painter)
        
        # Draw traffic lights
        self._draw_traffic_lights(painter)
        
        # Draw vehicle trail
        self._draw_vehicle_trail(painter)
        
        # Draw vehicle with 3D effect
        self._draw_vehicle_3d(painter)
        
        # Draw HUD
        self._draw_hud(painter)
    
    def _get_sky_color(self):
        """Get sky color based on time of day"""
        time_norm = (self.weather["time"] % 24) / 24
        if 0.25 <= time_norm <= 0.75:  # Day
            return QColor(135, 206, 235)
        elif 0.75 < time_norm <= 0.9 or 0.1 <= time_norm < 0.25:  # Sunset/sunrise
            return QColor(255, 165, 0)
        else:  # Night
            return QColor(25, 25, 112)
    
    def _draw_roads_3d(self, painter):
        """Draw roads with 3D perspective"""
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        
        for road in self.roads:
            if road["type"] == "horizontal":
                # Main road surface
                painter.fillRect(0, road["y"] - road["width"]//2, 600, road["width"], QColor(60, 60, 60))
                
                # Lane markings
                painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
                for i in range(1, road["lanes"]):
                    y = road["y"] - road["width"]//2 + (road["width"] * i // road["lanes"])
                    painter.drawLine(0, y, 600, y)
                
                # Road edges
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                painter.drawLine(0, road["y"] - road["width"]//2, 600, road["y"] - road["width"]//2)
                painter.drawLine(0, road["y"] + road["width"]//2, 600, road["y"] + road["width"]//2)
                
            else:  # vertical
                painter.fillRect(road["x"] - road["width"]//2, 0, road["width"], 400, QColor(60, 60, 60))
                
                painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
                for i in range(1, road["lanes"]):
                    x = road["x"] - road["width"]//2 + (road["width"] * i // road["lanes"])
                    painter.drawLine(x, 0, x, 400)
                
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                painter.drawLine(road["x"] - road["width"]//2, 0, road["x"] - road["width"]//2, 400)
                painter.drawLine(road["x"] + road["width"]//2, 0, road["x"] + road["width"]//2, 400)
    
    def _draw_buildings_3d(self, painter):
        """Draw buildings with 3D effect"""
        for building in self.buildings:
            # Building shadow (3D effect)
            shadow_offset = building["building_height"] * 2
            painter.setBrush(QBrush(QColor(30, 30, 30, 100)))
            painter.drawRect(
                building["x"] + shadow_offset, building["y"] + shadow_offset,
                building["width"], building["height"]
            )
            
            # Main building
            painter.setBrush(QBrush(building["color"]))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRect(building["x"], building["y"], building["width"], building["height"])
            
            # Building top (3D effect)
            painter.setBrush(QBrush(building["color"].lighter(120)))
            
            # Windows
            painter.setBrush(QBrush(QColor(255, 255, 200, 150)))
            for i in range(2, building["width"] - 10, 15):
                for j in range(10, building["height"] - 10, 20):
                    painter.drawRect(building["x"] + i, building["y"] + j, 8, 12)
    
    def _draw_traffic_lights(self, painter):
        """Draw traffic lights"""
        for light in self.traffic_lights:
            # Traffic light pole
            painter.setBrush(QBrush(QColor(80, 80, 80)))
            painter.drawRect(light["x"]-2, light["y"]-15, 4, 30)
            
            # Light housing
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.drawRect(light["x"]-8, light["y"]-12, 16, 24)
            
            # Light states
            colors = {"red": QColor(255, 0, 0), "yellow": QColor(255, 255, 0), "green": QColor(0, 255, 0)}
            
            for i, state in enumerate(["red", "yellow", "green"]):
                y_offset = light["y"] - 8 + i * 8
                if light["state"] == state:
                    painter.setBrush(QBrush(colors[state]))
                else:
                    painter.setBrush(QBrush(QColor(100, 100, 100)))
                painter.drawEllipse(light["x"]-3, y_offset, 6, 6)
    
    def _draw_vehicle_trail(self, painter):
        """Draw vehicle movement trail"""
        if len(self.trail_points) > 1:
            painter.setPen(QPen(QColor(0, 255, 255, 100), 3))
            for i in range(1, len(self.trail_points)):
                x1, y1 = self.trail_points[i-1]
                x2, y2 = self.trail_points[i]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_vehicle_3d(self, painter):
        """Draw vehicle with 3D effect"""
        painter.save()
        painter.translate(self.vehicle_x, self.vehicle_y)
        painter.rotate(self.vehicle_heading)
        
        # Vehicle shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.drawRect(-18, -10, 36, 20)
        
        # Main vehicle body
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(QPen(QColor(200, 0, 0), 2))
        painter.drawRect(-15, -8, 30, 16)
        
        # Vehicle windows
        painter.setBrush(QBrush(QColor(150, 150, 255, 200)))
        painter.drawRect(-10, -6, 20, 12)
        
        # Headlights
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(12, -6, 4, 4)
        painter.drawEllipse(12, 2, 4, 4)
        
        # Speed indicator
        if self.vehicle_speed > 0:
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            for i in range(3):
                painter.drawLine(-20 - i*5, 0, -25 - i*5, 0)
        
        painter.restore()
    
    def _draw_hud(self, painter):
        """Draw heads-up display"""
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(10, 20, f"🌍 Enhanced 3D CARLA Simulation")
        painter.drawText(10, 40, f"⏰ Time: {self.weather['time']:.1f}:00")
        painter.drawText(10, 60, f"🚗 Speed: {self.vehicle_speed:.1f} km/h")
        painter.drawText(10, 80, f"📍 Pos: ({self.vehicle_x:.0f}, {self.vehicle_y:.0f})")
        painter.drawText(10, 100, f"🧭 Heading: {self.vehicle_heading:.0f}°")
        
        if CARLA_AVAILABLE:
            painter.drawText(10, 380, "✅ CARLA Ready (Start server to connect)")
        else:
            painter.drawText(10, 380, "⚠️ CARLA Simulation Mode")

class VehicleControlPanel(QGroupBox):
    """Advanced vehicle control panel"""
    
    vehicle_command = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__("🎮 Enhanced Vehicle Control")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tabs for different control modes
        tabs = QTabWidget()
        
        # Basic controls tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        
        # Command input
        cmd_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter AI command: 'drive to downtown', 'park at intersection'")
        self.command_input.returnPressed.connect(self.send_ai_command)
        
        ai_btn = QPushButton("🤖 Send to AI")
        ai_btn.clicked.connect(self.send_ai_command)
        
        cmd_layout.addWidget(QLabel("AI Command:"))
        cmd_layout.addWidget(self.command_input)
        cmd_layout.addWidget(ai_btn)
        basic_layout.addLayout(cmd_layout)
        
        # Quick controls
        quick_layout = QGridLayout()
        controls = [
            ("⬆️ Forward", {"action": "forward", "speed": 40}),
            ("⬇️ Reverse", {"action": "reverse", "speed": 20}),
            ("⬅️ Turn Left", {"action": "turn", "direction": "left"}),
            ("➡️ Turn Right", {"action": "turn", "direction": "right"}),
            ("🛑 Emergency Stop", {"action": "emergency_stop"}),
            ("🅿️ Park", {"action": "park"}),
            ("🏎️ Sport Mode", {"action": "sport_mode"}),
            ("🐌 Eco Mode", {"action": "eco_mode"})
        ]
        
        for i, (label, cmd) in enumerate(controls):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, command=cmd: self.vehicle_command.emit(command))
            quick_layout.addWidget(btn, i // 4, i % 4)
        
        quick_widget = QWidget()
        quick_widget.setLayout(quick_layout)
        basic_layout.addWidget(QLabel("Quick Controls:"))
        basic_layout.addWidget(quick_widget)
        basic_tab.setLayout(basic_layout)
        tabs.addTab(basic_tab, "Basic Controls")
        
        # Advanced controls tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout()
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(0)
        self.speed_slider.valueChanged.connect(self.speed_changed)
        self.speed_label = QLabel("0 km/h")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        advanced_layout.addLayout(speed_layout)
        
        # Steering control
        steering_layout = QHBoxLayout()
        steering_layout.addWidget(QLabel("Steering:"))
        self.steering_slider = QSlider(Qt.Horizontal)
        self.steering_slider.setRange(-100, 100)
        self.steering_slider.setValue(0)
        self.steering_slider.valueChanged.connect(self.steering_changed)
        self.steering_label = QLabel("0°")
        steering_layout.addWidget(self.steering_slider)
        steering_layout.addWidget(self.steering_label)
        advanced_layout.addLayout(steering_layout)
        
        # Weather controls
        weather_layout = QGridLayout()
        weather_layout.addWidget(QLabel("Weather:"), 0, 0)
        
        self.weather_combo = QComboBox()
        self.weather_combo.addItems(["Clear", "Cloudy", "Rainy", "Foggy", "Night"])
        self.weather_combo.currentTextChanged.connect(self.weather_changed)
        weather_layout.addWidget(self.weather_combo, 0, 1)
        
        weather_widget = QWidget()
        weather_widget.setLayout(weather_layout)
        advanced_layout.addWidget(weather_widget)
        
        advanced_tab.setLayout(advanced_layout)
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def send_ai_command(self):
        """Send AI command"""
        text = self.command_input.text().strip()
        if text:
            self.vehicle_command.emit({"action": "ai_command", "text": text})
            self.command_input.clear()
    
    def speed_changed(self, value):
        """Handle speed slider change"""
        self.speed_label.setText(f"{value} km/h")
        self.vehicle_command.emit({"action": "set_speed", "speed": value})
    
    def steering_changed(self, value):
        """Handle steering slider change"""
        self.steering_label.setText(f"{value}°")
        self.vehicle_command.emit({"action": "set_steering", "angle": value})
    
    def weather_changed(self, weather):
        """Handle weather change"""
        self.vehicle_command.emit({"action": "set_weather", "weather": weather.lower()})

class Enhanced3DSimulation(QMainWindow):
    """Main enhanced 3D simulation window"""
    
    def __init__(self):
        super().__init__()
        self.logger = Logger.get_logger(__name__)
        
        # Initialize components
        self.gemini_agent = GeminiAgent()
        self.can_simulator = VehicleCANSimulator()
        self.carla_client = None
        self.carla_world = None
        self.vehicle = None
        self.camera_sensor = None
        
        # State
        self.vehicle_x = 300
        self.vehicle_y = 200
        self.vehicle_heading = 0
        self.vehicle_speed = 0
        
        self.init_ui()
        self.init_carla()
        self.can_simulator.start()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_simulation)
        self.update_timer.start(50)  # 20 FPS
        
    def init_ui(self):
        """Initialize enhanced UI"""
        self.setWindowTitle("🚗 Enhanced 3D CARLA Vehicle Simulation - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget.setLayout(QHBoxLayout())
        central_widget.layout().addWidget(main_splitter)
        
        # Left panel - Camera and map
        left_panel = QSplitter(Qt.Vertical)
        
        # Camera feed
        camera_group = QGroupBox("📹 Vehicle Camera (CARLA)")
        camera_layout = QVBoxLayout()
        self.camera_widget = CameraWidget()
        camera_layout.addWidget(self.camera_widget)
        camera_group.setLayout(camera_layout)
        left_panel.addWidget(camera_group)
        
        # 3D Map
        map_group = QGroupBox("🗺️ Enhanced 3D Map View")
        map_layout = QVBoxLayout()
        self.map_widget = Enhanced3DMapWidget()
        map_layout.addWidget(self.map_widget)
        map_group.setLayout(map_layout)
        left_panel.addWidget(map_group)
        
        main_splitter.addWidget(left_panel)
        
        # Right panel - Controls and status
        right_panel = QSplitter(Qt.Vertical)
        
        # Control panel
        self.control_panel = VehicleControlPanel()
        self.control_panel.vehicle_command.connect(self.handle_vehicle_command)
        right_panel.addWidget(self.control_panel)
        
        # Status and logs
        status_group = QGroupBox("📊 Vehicle Status & Activity Log")
        status_layout = QVBoxLayout()
        
        # Status display
        status_grid = QGridLayout()
        
        self.status_labels = {}
        status_items = [
            ("speed", "Speed: 0 km/h"),
            ("position", "Position: (300, 200)"),
            ("heading", "Heading: 0°"),
            ("gear", "Gear: P"),
            ("fuel", "Fuel: 100%"),
            ("engine", "Engine: Off")
        ]
        
        for i, (key, initial) in enumerate(status_items):
            label = QLabel(initial)
            label.setFont(QFont("Arial", 10))
            self.status_labels[key] = label
            status_grid.addWidget(label, i // 2, i % 2)
        
        status_widget = QWidget()
        status_widget.setLayout(status_grid)
        status_layout.addWidget(status_widget)
        
        # Activity log
        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setReadOnly(True)
        status_layout.addWidget(QLabel("Activity Log:"))
        status_layout.addWidget(self.activity_log)
        
        # Clear log button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.activity_log.clear)
        status_layout.addWidget(clear_btn)
        
        status_group.setLayout(status_layout)
        right_panel.addWidget(status_group)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([800, 600])
        left_panel.setSizes([400, 400])
        right_panel.setSizes([400, 500])
        
        # Initial log message
        self.add_log("info", "🚗 Enhanced 3D CARLA Simulation initialized")
        if CARLA_AVAILABLE:
            self.add_log("info", "✅ CARLA ready for connection")
        else:
            self.add_log("warning", "⚠️ CARLA not available - running in enhanced simulation mode")
    
    def init_carla(self):
        """Initialize CARLA connection"""
        if not CARLA_AVAILABLE:
            return
        
        try:
            self.carla_client = carla.Client('localhost', 2000)
            self.carla_client.set_timeout(10.0)
            self.carla_world = self.carla_client.get_world()
            
            # Spawn vehicle
            blueprint_library = self.carla_world.get_blueprint_library()
            vehicle_bp = blueprint_library.filter('vehicle.tesla.model3')[0]
            spawn_points = self.carla_world.get_map().get_spawn_points()
            
            if spawn_points:
                self.vehicle = self.carla_world.spawn_actor(vehicle_bp, spawn_points[0])
                
                # Add camera sensor
                camera_bp = blueprint_library.find('sensor.camera.rgb')
                camera_bp.set_attribute('image_size_x', '640')
                camera_bp.set_attribute('image_size_y', '480')
                camera_bp.set_attribute('fov', '90')
                
                camera_transform = carla.Transform(carla.Location(x=2.0, z=1.5))
                self.camera_sensor = self.carla_world.spawn_actor(
                    camera_bp, camera_transform, attach_to=self.vehicle
                )
                self.camera_sensor.listen(self.camera_widget.update_image)
                
                self.add_log("success", "✅ CARLA vehicle spawned successfully")
            
        except Exception as e:
            self.add_log("error", f"❌ CARLA connection failed: {e}")
            self.add_log("info", "🔄 Continuing in simulation mode")
    
    def handle_vehicle_command(self, command):
        """Handle vehicle control commands"""
        action = command["action"]
        
        self.add_log("command", f"🎮 {action}: {command}")
        
        if action == "ai_command":
            self.process_ai_command(command["text"])
        elif action == "forward":
            self.execute_movement("forward", command.get("speed", 40))
        elif action == "reverse":
            self.execute_movement("reverse", command.get("speed", 20))
        elif action == "turn":
            self.execute_turn(command["direction"])
        elif action == "emergency_stop":
            self.execute_emergency_stop()
        elif action == "park":
            self.execute_parking()
        elif action == "set_speed":
            self.set_vehicle_speed(command["speed"])
        elif action == "set_steering":
            self.set_vehicle_steering(command["angle"])
        elif action == "set_weather":
            self.set_weather(command["weather"])
    
    def process_ai_command(self, text):
        """Process AI command with Gemini"""
        self.add_log("ai", f"🤖 Processing: {text}")
        
        vehicle_status = self.can_simulator.get_vehicle_state()
        environment_info = {
            "weather": {"cloudiness": 0.3, "precipitation": 0.0},
            "traffic": {"vehicles_count": 3, "pedestrians_count": 2}
        }
        
        response = self.gemini_agent.process_command(text, vehicle_status, environment_info)
        self.add_log("ai", f"🧠 AI Response: {response['response']}")
        
        if not response.get('clarification_needed', False):
            self.execute_ai_action(response)
    
    def execute_movement(self, direction, speed):
        """Execute vehicle movement"""
        if direction == "forward":
            self.vehicle_speed = speed
            self.update_vehicle_position(speed, 0)
        elif direction == "reverse":
            self.vehicle_speed = -speed
            self.update_vehicle_position(-speed, 0)
        
        self.can_simulator.update_vehicle_state(speed=abs(self.vehicle_speed), gear='D' if speed > 0 else 'R')
    
    def execute_turn(self, direction):
        """Execute vehicle turn"""
        turn_angle = -30 if direction == "left" else 30
        self.vehicle_heading = (self.vehicle_heading + turn_angle) % 360
        self.can_simulator.update_vehicle_state(steering_angle=turn_angle)
        
        # Reset steering after delay
        QTimer.singleShot(1000, lambda: self.can_simulator.update_vehicle_state(steering_angle=0))
    
    def execute_emergency_stop(self):
        """Execute emergency stop"""
        self.vehicle_speed = 0
        self.can_simulator.update_vehicle_state(speed=0, brake_pressure=1.0, gear='P')
        self.add_log("warning", "🚨 EMERGENCY STOP ACTIVATED")
    
    def execute_parking(self):
        """Execute parking maneuver"""
        self.vehicle_speed = 0
        self.can_simulator.update_vehicle_state(speed=0, gear='P')
        self.add_log("info", "🅿️ Vehicle parked successfully")
    
    def set_vehicle_speed(self, speed):
        """Set vehicle speed directly"""
        self.vehicle_speed = speed
        self.update_vehicle_position(speed, 0)
        self.can_simulator.update_vehicle_state(speed=speed)
    
    def set_vehicle_steering(self, angle):
        """Set vehicle steering angle"""
        self.vehicle_heading = (self.vehicle_heading + angle * 0.1) % 360
        self.can_simulator.update_vehicle_state(steering_angle=angle)
    
    def set_weather(self, weather):
        """Set weather conditions"""
        self.add_log("info", f"🌤️ Weather changed to: {weather}")
        # Update map widget weather
        if hasattr(self.map_widget, 'weather'):
            weather_settings = {
                "clear": {"clouds": 0.1, "rain": 0.0},
                "cloudy": {"clouds": 0.8, "rain": 0.0},
                "rainy": {"clouds": 0.9, "rain": 0.7},
                "foggy": {"clouds": 0.9, "rain": 0.0},
                "night": {"clouds": 0.3, "rain": 0.0, "time": 22.0}
            }
            if weather in weather_settings:
                self.map_widget.weather.update(weather_settings[weather])
    
    def execute_ai_action(self, ai_response):
        """Execute AI-generated action"""
        action = ai_response.get('action', '')
        parameters = ai_response.get('parameters', {})
        
        if action == "stop":
            self.execute_emergency_stop()
        elif action == "navigate":
            destination = ai_response.get('destination', '')
            self.add_log("nav", f"🗺️ Navigating to: {destination}")
            self.execute_movement("forward", 35)
        elif action == "speed_change":
            change_type = parameters.get('change_type', 'increase')
            if change_type == 'increase':
                new_speed = min(self.vehicle_speed + 20, 80)
            else:
                new_speed = max(self.vehicle_speed - 20, 0)
            self.set_vehicle_speed(new_speed)
        elif action == "turn":
            direction = parameters.get('direction', 'left')
            self.execute_turn(direction)
        elif action == "park":
            self.execute_parking()
    
    def update_vehicle_position(self, speed, turn_rate):
        """Update vehicle position based on physics"""
        if speed != 0:
            # Convert speed to movement
            speed_ms = speed / 3.6  # km/h to m/s
            pixel_speed = speed_ms * 5  # Scale for visualization
            
            # Calculate new position
            heading_rad = math.radians(self.vehicle_heading)
            dx = pixel_speed * math.cos(heading_rad)
            dy = pixel_speed * math.sin(heading_rad)
            
            # Update position with bounds checking
            new_x = self.vehicle_x + dx
            new_y = self.vehicle_y + dy
            
            if 20 <= new_x <= 580:
                self.vehicle_x = new_x
            if 20 <= new_y <= 380:
                self.vehicle_y = new_y
    
    def update_simulation(self):
        """Update simulation state"""
        # Update vehicle position
        self.update_vehicle_position(self.vehicle_speed, 0)
        
        # Update map visualization
        self.map_widget.update_vehicle_state(
            self.vehicle_x, self.vehicle_y, self.vehicle_heading, self.vehicle_speed
        )
        
        # Update status display
        status = self.can_simulator.get_vehicle_state()
        self.status_labels["speed"].setText(f"Speed: {status.get('speed', 0):.1f} km/h")
        self.status_labels["position"].setText(f"Position: ({self.vehicle_x:.0f}, {self.vehicle_y:.0f})")
        self.status_labels["heading"].setText(f"Heading: {self.vehicle_heading:.0f}°")
        self.status_labels["gear"].setText(f"Gear: {status.get('gear', 'P')}")
        self.status_labels["fuel"].setText(f"Fuel: {status.get('fuel_level', 1.0)*100:.0f}%")
        self.status_labels["engine"].setText(f"Engine: {'On' if status.get('speed', 0) > 0 else 'Off'}")
        
        # Update CARLA vehicle if connected
        if self.vehicle and CARLA_AVAILABLE:
            try:
                control = carla.VehicleControl()
                control.throttle = min(self.vehicle_speed / 100.0, 1.0)
                control.brake = 0.0 if self.vehicle_speed > 0 else 1.0
                control.steer = 0.0  # Simplified for demo
                self.vehicle.apply_control(control)
            except Exception as e:
                pass  # Silent fail for demo
    
    def add_log(self, log_type, message):
        """Add entry to activity log"""
        timestamp = time.strftime("%H:%M:%S")
        color_map = {
            "info": "blue",
            "success": "green", 
            "warning": "orange",
            "error": "red",
            "command": "purple",
            "ai": "darkgreen",
            "nav": "brown"
        }
        
        color = color_map.get(log_type, "black")
        self.activity_log.append(f'<span style="color: {color};">[{timestamp}] {message}</span>')
        
        # Auto-scroll
        self.activity_log.verticalScrollBar().setValue(
            self.activity_log.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.camera_sensor:
            self.camera_sensor.destroy()
        if self.vehicle:
            self.vehicle.destroy()
        self.can_simulator.stop()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    print("🚗 Enhanced 3D CARLA Vehicle Simulation - Professional Edition")
    print("=" * 70)
    print(f"CARLA Status: {'✅ Available' if CARLA_AVAILABLE else '❌ Simulation Mode'}")
    print("Features:")
    print("- Enhanced 3D visualization with realistic graphics")
    print("- Advanced vehicle physics simulation") 
    print("- Professional control interface")
    print("- Real-time camera feed (when CARLA connected)")
    print("- AI command processing with Gemini")
    print("- Weather and environment controls")
    print("- Comprehensive vehicle diagnostics")
    print()
    
    if CARLA_AVAILABLE:
        print("💡 To enable full 3D mode:")
        print("1. Start CARLA: CarlaUE4.exe -windowed -ResX=1280 -ResY=720")
        print("2. This application will automatically connect")
        print()
    else:
        print("💡 Running in enhanced simulation mode")
        print("- All features available except live CARLA connection")
        print("- Install CARLA to enable full 3D mode")
        print()
    
    window = Enhanced3DSimulation()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
