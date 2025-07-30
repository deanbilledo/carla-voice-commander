"""
🎮 CARLA Racing Game - 3D Vehicle Simulation
Professional gaming-style vehicle simulation with spectacular 3D graphics
"""

import sys
import os
import time
import math
import numpy as np
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

# Add CARLA path - multiple potential locations
carla_paths = [
    r"C:\Carla-0.10.0-Win64-Shipping\PythonAPI\carla",
    r"C:\Carla-0.10.0-Win64-Shipping\PythonAPI\carla\dist",
    r"C:\CARLA_0.9.13\PythonAPI\carla",
    r"C:\CARLA_0.9.13\PythonAPI\carla\dist"
]

for carla_path in carla_paths:
    if os.path.exists(carla_path) and carla_path not in sys.path:
        sys.path.append(carla_path)
        print(f"Added CARLA path: {carla_path}")

# Try to import CARLA with better error handling
try:
    # First try direct import
    import carla
    CARLA_AVAILABLE = True
    print("✅ CARLA imported successfully!")
except ImportError as e:
    print(f"❌ Direct CARLA import failed: {e}")
    
    # Try importing from wheel files
    try:
        wheel_files = glob.glob(r"C:\Carla-0.10.0-Win64-Shipping\PythonAPI\carla\dist\*.whl")
        print(f"Found CARLA wheel files: {wheel_files}")
        
        # Try adding the actual carla module from the directory
        carla_module_path = r"C:\Carla-0.10.0-Win64-Shipping\PythonAPI\carla"
        if carla_module_path not in sys.path:
            sys.path.insert(0, carla_module_path)
        
        # Try importing again
        import carla
        CARLA_AVAILABLE = True
        print("✅ CARLA imported from wheel directory!")
        
    except Exception as e2:
        print(f"❌ CARLA wheel import failed: {e2}")
        print("💡 To use CARLA 3D graphics:")
        print("1. Start CARLA server: CarlaUnreal.exe (not CarlaUE4.exe)")
        print("2. Wait for server to start on localhost:2000")
        print("3. Restart this application")
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
        if image_data is not None:
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
    
    def paintEvent(self, event):
        """Paint the camera image"""
        painter = QPainter(self)
        
        if self.image:
            painter.drawPixmap(self.rect(), self.image, self.image.rect())
        else:
            # Draw placeholder
            painter.fillRect(self.rect(), QColor(50, 50, 50))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawText(self.rect(), Qt.AlignCenter, "Camera Feed\n(Connect to CARLA)")

class GameStyle3DMapWidget(QFrame):
    """Gaming-style 3D map visualization with spectacular effects"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(600, 400)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("border: 2px solid #00ff00; background-color: #001100;")
        
        # Vehicle state
        self.vehicle_x = 300
        self.vehicle_y = 200
        self.vehicle_heading = 0
        self.vehicle_speed = 0
        self.trail_points = []
        
        # Game effects
        self.particles = []
        self.explosions = []
        self.boost_effect = False
        self.racing_line = []
        
        # Environment
        self.buildings = self._generate_3d_buildings()
        self.roads = self._generate_road_network()
        self.traffic_lights = self._generate_traffic_system()
        self.weather = {"time": 12.0, "clouds": 0.3, "rain": 0.0}
        self.neon_buildings = self._generate_neon_buildings()
        
        # Gaming animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_game_effects)
        self.animation_timer.start(16)  # 60 FPS for smooth gaming feel
        
    def _generate_3d_buildings(self):
        """Generate futuristic gaming-style buildings"""
        import random
        buildings = []
        for _ in range(30):
            x = random.randint(50, 550)
            y = random.randint(50, 350)
            w = random.randint(30, 90)
            h = random.randint(30, 90)
            height = random.randint(4, 12)
            glow_color = random.choice([
                QColor(0, 255, 255), QColor(255, 0, 255), QColor(255, 255, 0),
                QColor(0, 255, 0), QColor(255, 100, 0), QColor(100, 100, 255)
            ])
            buildings.append({
                "x": x, "y": y, "width": w, "height": h,
                "building_height": height, 
                "color": QColor(40, 40, 60),
                "glow_color": glow_color,
                "neon_intensity": random.randint(50, 255)
            })
        return buildings
    
    def _generate_neon_buildings(self):
        """Generate neon-lit gaming buildings"""
        import random
        neon_buildings = []
        for _ in range(10):
            x = random.randint(100, 500)
            y = random.randint(100, 300)
            neon_buildings.append({
                "x": x, "y": y, "width": 60, "height": 80,
                "neon_color": random.choice([
                    QColor(0, 255, 255), QColor(255, 0, 255), QColor(255, 255, 0)
                ]),
                "pulse_speed": random.uniform(0.02, 0.05)
            })
        return neon_buildings
    
    def _generate_road_network(self):
        """Generate futuristic gaming road network with neon effects"""
        return [
            # Main racing circuits
            {"type": "horizontal", "y": 200, "x1": 0, "x2": 600, "width": 80, "lanes": 6, "neon": True},
            {"type": "horizontal", "y": 120, "x1": 0, "x2": 600, "width": 60, "lanes": 4, "neon": True},
            {"type": "horizontal", "y": 280, "x1": 0, "x2": 600, "width": 60, "lanes": 4, "neon": True},
            {"type": "vertical", "x": 300, "y1": 0, "y2": 400, "width": 80, "lanes": 6, "neon": True},
            {"type": "vertical", "x": 180, "y1": 0, "y2": 400, "width": 50, "lanes": 3, "neon": False},
            {"type": "vertical", "x": 420, "y1": 0, "y2": 400, "width": 50, "lanes": 3, "neon": False},
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
    
    def update_game_effects(self):
        """Update gaming effects and animations"""
        # Update traffic lights with gaming colors
        for light in self.traffic_lights:
            light["timer"] += 1
            if light["timer"] >= light["cycle"]:
                light["timer"] = 0
                # Cycle through states with gaming effects
                if light["state"] == "green":
                    light["state"] = "yellow"
                elif light["state"] == "yellow":
                    light["state"] = "red"
                else:
                    light["state"] = "green"
        
        # Update particles and effects
        self._update_particles()
        
        # Update weather with gaming atmosphere
        self.weather["time"] += 0.02
        if self.weather["time"] >= 24:
            self.weather["time"] = 0
        
        # Add speed particles when moving fast
        if self.vehicle_speed > 50:
            self._add_speed_particles()
            
        self.update()
    
    def _update_particles(self):
        """Update particle effects"""
        # Remove old particles
        self.particles = [p for p in self.particles if p["life"] > 0]
        
        # Update existing particles
        for particle in self.particles:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["life"] -= 1
            particle["alpha"] = max(0, particle["alpha"] - 5)
    
    def _add_speed_particles(self):
        """Add speed boost particles"""
        import random
        import math
        
        if len(self.particles) < 50:  # Limit particles
            # Create particles behind the vehicle
            angle = math.radians(self.vehicle_heading + 180)
            for _ in range(3):
                particle = {
                    "x": self.vehicle_x + random.randint(-5, 5),
                    "y": self.vehicle_y + random.randint(-5, 5),
                    "dx": math.cos(angle) * random.randint(2, 5),
                    "dy": math.sin(angle) * random.randint(2, 5),
                    "life": 30,
                    "alpha": 255,
                    "color": random.choice([
                        QColor(255, 255, 0), QColor(255, 100, 0), QColor(255, 0, 0)
                    ])
                }
                self.particles.append(particle)
    
    def paintEvent(self, event):
        """Paint spectacular gaming-style 3D visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Gaming-style sky with gradient
        sky_color = self._get_gaming_sky_color()
        painter.fillRect(self.rect(), sky_color)
        
        # Draw futuristic roads with neon effects
        self._draw_gaming_roads(painter)
        
        # Draw neon buildings with glow effects
        self._draw_gaming_buildings(painter)
        
        # Draw gaming-style traffic lights
        self._draw_gaming_traffic_lights(painter)
        
        # Draw speed particles
        self._draw_particles(painter)
        
        # Draw racing trail with neon glow
        self._draw_gaming_trail(painter)
        
        # Draw vehicle with gaming effects
        self._draw_gaming_vehicle(painter)
        
        # Draw gaming HUD
        self._draw_gaming_hud(painter)
    
    def _get_gaming_sky_color(self):
        """Get cyberpunk-style sky color"""
        time_norm = (self.weather["time"] % 24) / 24
        if 0.25 <= time_norm <= 0.75:  # Day - Cyberpunk blue
            return QColor(0, 50, 100)
        elif 0.75 < time_norm <= 0.9 or 0.1 <= time_norm < 0.25:  # Sunset - Neon purple
            return QColor(80, 0, 80)
        else:  # Night - Dark with neon hints
            return QColor(10, 0, 30)
    
    def _draw_gaming_roads(self, painter):
        """Draw futuristic racing roads with neon effects"""
        for road in self.roads:
            if road["type"] == "horizontal":
                # Road base - dark
                painter.fillRect(0, road["y"] - road["width"]//2, 600, road["width"], QColor(20, 20, 30))
                
                # Neon edges if enabled
                if road.get("neon", False):
                    painter.setPen(QPen(QColor(0, 255, 255), 4))
                    painter.drawLine(0, road["y"] - road["width"]//2, 600, road["y"] - road["width"]//2)
                    painter.drawLine(0, road["y"] + road["width"]//2, 600, road["y"] + road["width"]//2)
                
                # Racing lane markings - neon style
                painter.setPen(QPen(QColor(255, 255, 0), 3, Qt.DashLine))
                for i in range(1, road["lanes"]):
                    y = road["y"] - road["width"]//2 + (road["width"] * i // road["lanes"])
                    painter.drawLine(0, y, 600, y)
                
            else:  # vertical
                painter.fillRect(road["x"] - road["width"]//2, 0, road["width"], 400, QColor(20, 20, 30))
                
                if road.get("neon", False):
                    painter.setPen(QPen(QColor(0, 255, 255), 4))
                    painter.drawLine(road["x"] - road["width"]//2, 0, road["x"] - road["width"]//2, 400)
                    painter.drawLine(road["x"] + road["width"]//2, 0, road["x"] + road["width"]//2, 400)
                
                painter.setPen(QPen(QColor(255, 255, 0), 3, Qt.DashLine))
                for i in range(1, road["lanes"]):
                    x = road["x"] - road["width"]//2 + (road["width"] * i // road["lanes"])
                    painter.drawLine(x, 0, x, 400)
    
    def _draw_gaming_buildings(self, painter):
        """Draw cyberpunk-style buildings with neon effects"""
        for building in self.buildings:
            # Building shadow with neon glow
            shadow_offset = building["building_height"] * 3
            painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
            painter.drawRect(
                building["x"] + shadow_offset, building["y"] + shadow_offset,
                building["width"], building["height"]
            )
            
            # Main building - dark base
            painter.setBrush(QBrush(building["color"]))
            painter.setPen(QPen(building["glow_color"], 2))
            painter.drawRect(building["x"], building["y"], building["width"], building["height"])
            
            # Neon window grid
            painter.setBrush(QBrush(building["glow_color"]))
            for i in range(5, building["width"] - 5, 12):
                for j in range(8, building["height"] - 8, 15):
                    if (i + j) % 3 == 0:  # Random pattern
                        painter.drawRect(building["x"] + i, building["y"] + j, 6, 8)
            
            # Neon outline glow effect
            painter.setPen(QPen(building["glow_color"], 3))
            painter.setBrush(QBrush())
            painter.drawRect(building["x"]-1, building["y"]-1, building["width"]+2, building["height"]+2)
    
    def _draw_gaming_traffic_lights(self, painter):
        """Draw futuristic gaming traffic lights"""
        for light in self.traffic_lights:
            # Holographic pole
            painter.setBrush(QBrush(QColor(100, 100, 150)))
            painter.setPen(QPen(QColor(0, 255, 255), 2))
            painter.drawRect(light["x"]-3, light["y"]-20, 6, 40)
            
            # Futuristic housing with glow
            painter.setBrush(QBrush(QColor(30, 30, 50)))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawRect(light["x"]-12, light["y"]-15, 24, 30)
            
            # Gaming-style lights with intense glow
            colors = {
                "red": QColor(255, 0, 0), 
                "yellow": QColor(255, 255, 0), 
                "green": QColor(0, 255, 0)
            }
            
            for i, state in enumerate(["red", "yellow", "green"]):
                y_offset = light["y"] - 10 + i * 10
                if light["state"] == state:
                    # Active light with glow effect
                    painter.setBrush(QBrush(colors[state]))
                    painter.setPen(QPen(colors[state], 4))
                    painter.drawEllipse(light["x"]-6, y_offset, 12, 8)
                    # Extra glow
                    painter.setPen(QPen(colors[state], 2))
                    painter.drawEllipse(light["x"]-8, y_offset-1, 16, 10)
                else:
                    painter.setBrush(QBrush(QColor(50, 50, 50)))
                    painter.setPen(QPen(QColor(100, 100, 100), 1))
                    painter.drawEllipse(light["x"]-4, y_offset+1, 8, 6)
    
    def _draw_particles(self, painter):
        """Draw speed and effect particles"""
        for particle in self.particles:
            if particle["life"] > 0:
                color = particle["color"]
                color.setAlpha(particle["alpha"])
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(color, 2))
                painter.drawEllipse(int(particle["x"]-2), int(particle["y"]-2), 4, 4)
    
    def _draw_gaming_trail(self, painter):
        """Draw neon racing trail"""
        if len(self.trail_points) > 1:
            # Main trail
            painter.setPen(QPen(QColor(0, 255, 255), 4))
            for i in range(1, len(self.trail_points)):
                x1, y1 = self.trail_points[i-1]
                x2, y2 = self.trail_points[i]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Glow effect
            painter.setPen(QPen(QColor(0, 255, 255, 100), 8))
            for i in range(1, len(self.trail_points)):
                x1, y1 = self.trail_points[i-1]
                x2, y2 = self.trail_points[i]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_gaming_vehicle(self, painter):
        """Draw futuristic racing vehicle"""
        painter.save()
        painter.translate(self.vehicle_x, self.vehicle_y)
        painter.rotate(self.vehicle_heading)
        
        # Vehicle shadow with neon underglow
        painter.setBrush(QBrush(QColor(0, 255, 255, 50)))
        painter.drawRect(-20, -12, 40, 24)
        
        # Main vehicle body - sleek design
        painter.setBrush(QBrush(QColor(255, 50, 50)))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(-18, -10, 36, 20)
        
        # Racing stripes
        painter.setBrush(QBrush(QColor(255, 255, 0)))
        painter.drawRect(-15, -2, 30, 4)
        
        # Futuristic windows
        painter.setBrush(QBrush(QColor(100, 200, 255, 200)))
        painter.drawRect(-12, -7, 24, 14)
        
        # Neon headlights
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 255, 255), 3))
        painter.drawEllipse(15, -7, 6, 6)
        painter.drawEllipse(15, 1, 6, 6)
        
        # Speed boost effect
        if self.vehicle_speed > 70:
            painter.setPen(QPen(QColor(255, 255, 0), 3))
            for i in range(5):
                painter.drawLine(-25 - i*3, 0, -30 - i*3, 0)
        
        # Racing exhaust
        if self.vehicle_speed > 0:
            painter.setBrush(QBrush(QColor(255, 100, 0, 150)))
            painter.drawEllipse(-22, -3, 4, 6)
        
        painter.restore()
    
    def _draw_gaming_hud(self, painter):
        """Draw gaming-style HUD with neon effects"""
        # HUD background
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRect(5, 5, 200, 130)
        
        # Neon border
        painter.setPen(QPen(QColor(0, 255, 255), 2))
        painter.drawRect(5, 5, 200, 130)
        
        # Gaming-style text
        painter.setPen(QPen(QColor(0, 255, 255), 1))
        painter.drawText(10, 25, f"🎮 RACING SIMULATION")
        
        painter.setPen(QPen(QColor(255, 255, 0), 1))
        painter.drawText(10, 45, f"⚡ SPEED: {self.vehicle_speed:.0f} KM/H")
        
        painter.setPen(QPen(QColor(255, 100, 255), 1))
        painter.drawText(10, 65, f"📍 POS: ({self.vehicle_x:.0f}, {self.vehicle_y:.0f})")
        
        painter.setPen(QPen(QColor(100, 255, 100), 1))
        painter.drawText(10, 85, f"🧭 HEADING: {self.vehicle_heading:.0f}°")
        
        painter.setPen(QPen(QColor(255, 150, 0), 1))
        painter.drawText(10, 105, f"⏰ TIME: {self.weather['time']:.1f}:00")
        
        # Speed meter
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawText(10, 125, f"BOOST: {'ACTIVE' if self.vehicle_speed > 50 else 'READY'}")
        
        # Status indicator
        if CARLA_AVAILABLE:
            painter.setPen(QPen(QColor(0, 255, 0), 1))
            painter.drawText(10, 390, "✅ CARLA RACING MODE")
        else:
            painter.setPen(QPen(QColor(255, 255, 0), 1))
            painter.drawText(10, 390, "🎮 ARCADE MODE")

class VehicleControlPanel(QGroupBox):
    """Advanced vehicle control panel"""
    
    vehicle_command = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__("🎮 Advanced Vehicle Control")
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

class CARLA3DSimulation(QMainWindow):
    """Main 3D CARLA simulation window"""
    
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
        self.setWindowTitle("🎮 CARLA RACING COMMANDER - Gaming Edition")
        self.setGeometry(100, 100, 1400, 900)
        
        # Gaming-style cyberpunk theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1a1a2e, stop:1 #16213e);
                color: #00ffff;
                font-family: 'Courier New', monospace;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ff006e, stop:1 #8338ec);
                color: white;
                border: 2px solid #00ffff;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ff1744, stop:1 #651fff);
                border: 2px solid #ffff00;
            }
            QLabel {
                color: #00ffff;
                font-weight: bold;
                font-size: 11px;
            }
            QGroupBox {
                color: #00ffff;
                border: 2px solid #ff006e;
                border-radius: 8px;
                margin: 8px;
                padding-top: 15px;
                font-weight: bold;
                font-size: 13px;
            }
            QGroupBox::title {
                color: #ffff00;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextEdit {
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid #00ffff;
                border-radius: 8px;
                color: #00ffff;
                font-family: 'Courier New', monospace;
            }
            QLineEdit {
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid #ff006e;
                border-radius: 6px;
                color: #ffff00;
                padding: 6px;
                font-weight: bold;
            }
        """)
        
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
        self.map_widget = GameStyle3DMapWidget()
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
            self.add_log("info", "✅ CARLA 0.10.0 ready for connection")
        else:
            self.add_log("warning", "⚠️ CARLA not available - running in enhanced simulation mode")
    
    def init_carla(self):
        """Initialize CARLA connection with full 3D graphics"""
        if not CARLA_AVAILABLE:
            self.add_log("warning", "❌ CARLA not available - install CARLA 0.10.0 for full 3D graphics")
            return
        
        try:
            # Connect to CARLA server
            self.carla_client = carla.Client('localhost', 2000)
            self.carla_client.set_timeout(20.0)
            
            # Load CARLA world
            self.carla_world = self.carla_client.get_world()
            self.add_log("success", "✅ Connected to CARLA 3D simulator")
            
            # Set up spectator camera for main 3D view
            spectator = self.carla_world.get_spectator()
            spectator_transform = carla.Transform(
                carla.Location(x=0, y=0, z=50),
                carla.Rotation(pitch=-45, yaw=0, roll=0)
            )
            spectator.set_transform(spectator_transform)
            
            # Configure world settings for better performance
            settings = self.carla_world.get_settings()
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = 0.05  # 20 FPS
            settings.no_rendering_mode = False  # Enable full 3D rendering
            self.carla_world.apply_settings(settings)
            
            # Set weather for gaming atmosphere
            weather = carla.WeatherParameters(
                cloudiness=30.0,
                precipitation=0.0,
                sun_altitude_angle=45.0,
                sun_azimuth_angle=0.0,
                precipitation_deposits=0.0,
                wind_intensity=10.0,
                fog_density=0.0,
                fog_distance=100.0,
                wetness=0.0
            )
            self.carla_world.set_weather(weather)
            
            # Spawn gaming-style vehicle
            blueprint_library = self.carla_world.get_blueprint_library()
            
            # Try to get a sports car for gaming feel
            vehicle_blueprints = [
                'vehicle.dodge.charger_2020',
                'vehicle.ford.mustang',
                'vehicle.chevrolet.camaro',
                'vehicle.tesla.model3',
                'vehicle.audi.tt'
            ]
            
            vehicle_bp = None
            for bp_name in vehicle_blueprints:
                try:
                    vehicle_bp = blueprint_library.find(bp_name)
                    if vehicle_bp:
                        break
                except:
                    continue
            
            if not vehicle_bp:
                vehicle_bp = blueprint_library.filter('vehicle.*')[0]
            
            # Set vehicle color for gaming style
            if vehicle_bp.has_attribute('color'):
                color = '255,50,50'  # Red for racing
                vehicle_bp.set_attribute('color', color)
            
            # Spawn vehicle at a good location
            spawn_points = self.carla_world.get_map().get_spawn_points()
            if spawn_points:
                # Choose a spawn point
                spawn_point = spawn_points[0]
                self.vehicle = self.carla_world.spawn_actor(vehicle_bp, spawn_point)
                
                # Set up multiple cameras for full 3D experience
                self._setup_carla_cameras()
                
                # Set spectator to follow vehicle for 3D view
                self._setup_spectator_follow()
                
                self.add_log("success", f"🏎️ Gaming vehicle spawned: {vehicle_bp.id}")
                self.add_log("info", "🎮 CARLA 3D graphics active - switch to CARLA window for full experience")
            
        except Exception as e:
            self.add_log("error", f"❌ CARLA connection failed: {e}")
            self.add_log("info", "💡 To use CARLA 3D graphics:")
            self.add_log("info", "1. Start CARLA: CarlaUE4.exe")
            self.add_log("info", "2. Restart this application")
    
    def _setup_carla_cameras(self):
        """Set up multiple cameras for full 3D experience"""
        if not self.vehicle:
            return
            
        blueprint_library = self.carla_world.get_blueprint_library()
        
        # Main dashboard camera
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '1280')
        camera_bp.set_attribute('image_size_y', '720')
        camera_bp.set_attribute('fov', '90')
        
        # Camera attached to vehicle for dashboard view
        camera_transform = carla.Transform(
            carla.Location(x=1.5, z=2.4),
            carla.Rotation(pitch=0, yaw=0, roll=0)
        )
        self.camera_sensor = self.carla_world.spawn_actor(
            camera_bp, camera_transform, attach_to=self.vehicle
        )
        self.camera_sensor.listen(self.camera_widget.update_image)
        
        # Third-person camera for cinematic view
        third_person_transform = carla.Transform(
            carla.Location(x=-8.0, z=3.0),
            carla.Rotation(pitch=-10, yaw=0, roll=0)
        )
        self.third_person_camera = self.carla_world.spawn_actor(
            camera_bp, third_person_transform, attach_to=self.vehicle
        )
        
    def _setup_spectator_follow(self):
        """Set up spectator camera to follow vehicle in 3D"""
        if not self.vehicle:
            return
            
        def update_spectator():
            if self.vehicle:
                vehicle_transform = self.vehicle.get_transform()
                spectator = self.carla_world.get_spectator()
                
                # Position camera above and behind vehicle for cinematic view
                spectator_location = carla.Location(
                    x=vehicle_transform.location.x - 15,
                    y=vehicle_transform.location.y,
                    z=vehicle_transform.location.z + 8
                )
                
                spectator_rotation = carla.Rotation(
                    pitch=-20,
                    yaw=vehicle_transform.rotation.yaw,
                    roll=0
                )
                
                spectator_transform = carla.Transform(spectator_location, spectator_rotation)
                spectator.set_transform(spectator_transform)
        
        # Timer to update spectator camera
        self.spectator_timer = QTimer()
        self.spectator_timer.timeout.connect(update_spectator)
        self.spectator_timer.start(50)  # Update at 20 FPS
    
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
        """Execute vehicle movement in CARLA 3D"""
        if self.vehicle and CARLA_AVAILABLE:
            # Use real CARLA physics
            control = carla.VehicleControl()
            
            if direction == "forward":
                control.throttle = min(speed / 100.0, 1.0)
                control.brake = 0.0
                control.reverse = False
                self.vehicle_speed = speed
            elif direction == "reverse":
                control.throttle = 0.0
                control.brake = 0.0
                control.reverse = True
                control.throttle = min(speed / 100.0, 1.0)
                self.vehicle_speed = -speed
            
            control.steer = 0.0
            control.hand_brake = False
            
            self.vehicle.apply_control(control)
            self.add_log("info", f"🎮 CARLA 3D: {direction} at {speed} km/h")
        else:
            # Fallback to simulation mode
            if direction == "forward":
                self.vehicle_speed = speed
                self.update_vehicle_position(speed, 0)
            elif direction == "reverse":
                self.vehicle_speed = -speed
                self.update_vehicle_position(-speed, 0)
            
            self.add_log("info", f"🎮 Simulation: {direction} at {speed} km/h")
        
        self.can_simulator.update_vehicle_state(speed=abs(self.vehicle_speed), gear='D' if speed > 0 else 'R')
    
    def execute_turn(self, direction):
        """Execute vehicle turn in CARLA 3D"""
        if self.vehicle and CARLA_AVAILABLE:
            # Use real CARLA steering
            control = carla.VehicleControl()
            control.throttle = 0.3  # Gentle acceleration during turn
            control.brake = 0.0
            
            if direction == "left":
                control.steer = -0.5
                turn_angle = -30
            else:  # right
                control.steer = 0.5
                turn_angle = 30
            
            control.reverse = False
            control.hand_brake = False
            
            self.vehicle.apply_control(control)
            self.add_log("info", f"🎮 CARLA 3D: Turning {direction}")
            
            # Reset steering after delay
            def reset_steering():
                if self.vehicle:
                    reset_control = carla.VehicleControl()
                    reset_control.throttle = 0.0
                    reset_control.steer = 0.0
                    reset_control.brake = 0.0
                    self.vehicle.apply_control(reset_control)
            
            QTimer.singleShot(1000, reset_steering)
        else:
            # Fallback simulation
            turn_angle = -30 if direction == "left" else 30
            self.vehicle_heading = (self.vehicle_heading + turn_angle) % 360
            self.add_log("info", f"🎮 Simulation: Turning {direction}")
        
        self.can_simulator.update_vehicle_state(steering_angle=turn_angle)
    
    def execute_emergency_stop(self):
        """Execute emergency stop in CARLA 3D"""
        if self.vehicle and CARLA_AVAILABLE:
            # Real CARLA emergency stop
            control = carla.VehicleControl()
            control.throttle = 0.0
            control.brake = 1.0
            control.steer = 0.0
            control.hand_brake = True
            control.reverse = False
            
            self.vehicle.apply_control(control)
            self.add_log("warning", "🚨 CARLA 3D: EMERGENCY STOP ACTIVATED")
        else:
            # Fallback simulation
            self.vehicle_speed = 0
            self.add_log("warning", "🚨 Simulation: EMERGENCY STOP ACTIVATED")
        
        self.can_simulator.update_vehicle_state(speed=0, brake_pressure=1.0, gear='P')
    
    def set_vehicle_speed(self, speed):
        """Set vehicle speed in CARLA 3D"""
        if self.vehicle and CARLA_AVAILABLE:
            # Use CARLA physics for speed control
            control = carla.VehicleControl()
            
            if speed > 0:
                control.throttle = min(speed / 100.0, 1.0)
                control.brake = 0.0
                control.reverse = False
            elif speed < 0:
                control.throttle = min(abs(speed) / 100.0, 1.0)
                control.brake = 0.0
                control.reverse = True
            else:
                control.throttle = 0.0
                control.brake = 1.0
                control.reverse = False
            
            control.steer = 0.0
            control.hand_brake = False
            
            self.vehicle.apply_control(control)
            self.add_log("info", f"🎮 CARLA 3D: Speed set to {speed} km/h")
        else:
            # Fallback simulation
            self.vehicle_speed = speed
            self.update_vehicle_position(speed, 0)
            self.add_log("info", f"🎮 Simulation: Speed set to {speed} km/h")
        
        self.can_simulator.update_vehicle_state(speed=abs(speed))
    
    def execute_parking(self):
        """Execute parking maneuver in CARLA 3D"""
        if self.vehicle and CARLA_AVAILABLE:
            # Real CARLA parking
            control = carla.VehicleControl()
            control.throttle = 0.0
            control.brake = 1.0
            control.steer = 0.0
            control.hand_brake = True
            control.reverse = False
            
            self.vehicle.apply_control(control)
            self.add_log("info", "🅿️ CARLA 3D: Vehicle parked successfully")
        else:
            # Fallback simulation
            self.vehicle_speed = 0
            self.add_log("info", "🅿️ Simulation: Vehicle parked successfully")
        
        self.can_simulator.update_vehicle_state(speed=0, gear='P')
    
    def set_vehicle_steering(self, angle):
        """Set vehicle steering angle in CARLA 3D"""
        if self.vehicle and CARLA_AVAILABLE:
            # Use real CARLA steering
            control = carla.VehicleControl()
            control.throttle = 0.1  # Gentle movement
            control.brake = 0.0
            control.steer = angle / 100.0  # Normalize to -1.0 to 1.0
            control.reverse = False
            control.hand_brake = False
            
            self.vehicle.apply_control(control)
            self.add_log("info", f"🎮 CARLA 3D: Steering set to {angle}°")
        else:
            # Fallback simulation
            self.vehicle_heading = (self.vehicle_heading + angle * 0.1) % 360
            self.add_log("info", f"🎮 Simulation: Steering set to {angle}°")
        
        self.can_simulator.update_vehicle_state(steering_angle=angle)
    
    def set_weather(self, weather):
        """Set weather conditions in CARLA 3D"""
        self.add_log("info", f"🌤️ Weather changed to: {weather}")
        
        if self.carla_world and CARLA_AVAILABLE:
            # Set real CARLA weather
            weather_presets = {
                "clear": carla.WeatherParameters(
                    cloudiness=10.0, precipitation=0.0, sun_altitude_angle=60.0,
                    fog_density=0.0, wetness=0.0
                ),
                "cloudy": carla.WeatherParameters(
                    cloudiness=80.0, precipitation=0.0, sun_altitude_angle=45.0,
                    fog_density=0.0, wetness=0.0
                ),
                "rainy": carla.WeatherParameters(
                    cloudiness=90.0, precipitation=70.0, sun_altitude_angle=30.0,
                    fog_density=0.0, wetness=50.0
                ),
                "foggy": carla.WeatherParameters(
                    cloudiness=60.0, precipitation=0.0, sun_altitude_angle=30.0,
                    fog_density=80.0, wetness=0.0
                ),
                "night": carla.WeatherParameters(
                    cloudiness=30.0, precipitation=0.0, sun_altitude_angle=-30.0,
                    fog_density=0.0, wetness=0.0
                )
            }
            
            if weather in weather_presets:
                self.carla_world.set_weather(weather_presets[weather])
                self.add_log("success", f"✅ CARLA 3D weather updated to {weather}")
        
        # Update map widget weather for 2D fallback
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
        """Update simulation state with real CARLA 3D physics"""
        # Update CARLA vehicle with real physics
        if self.vehicle and CARLA_AVAILABLE:
            try:
                # Apply vehicle control based on current speed and steering
                control = carla.VehicleControl()
                
                # Convert our speed to throttle/brake
                if self.vehicle_speed > 0:
                    control.throttle = min(self.vehicle_speed / 100.0, 1.0)
                    control.brake = 0.0
                elif self.vehicle_speed < 0:
                    control.throttle = 0.0
                    control.brake = min(abs(self.vehicle_speed) / 100.0, 1.0)
                else:
                    control.throttle = 0.0
                    control.brake = 0.0
                
                control.steer = 0.0  # Will be updated by steering commands
                control.hand_brake = False
                control.reverse = self.vehicle_speed < 0
                
                self.vehicle.apply_control(control)
                
                # Get real vehicle state from CARLA
                vehicle_transform = self.vehicle.get_transform()
                vehicle_velocity = self.vehicle.get_velocity()
                
                # Update our display with real CARLA data
                self.vehicle_x = vehicle_transform.location.x
                self.vehicle_y = vehicle_transform.location.y
                self.vehicle_heading = vehicle_transform.rotation.yaw
                
                # Calculate real speed from CARLA physics
                real_speed = 3.6 * (vehicle_velocity.x**2 + vehicle_velocity.y**2 + vehicle_velocity.z**2)**0.5
                
                # Update map visualization with real CARLA data
                self.map_widget.update_vehicle_state(
                    self.vehicle_x, self.vehicle_y, self.vehicle_heading, real_speed
                )
                
                # Update status display with real CARLA data
                status = self.can_simulator.get_vehicle_state()
                self.status_labels["speed"].setText(f"⚡ Speed: {real_speed:.1f} km/h")
                self.status_labels["position"].setText(f"📍 Position: ({self.vehicle_x:.0f}, {self.vehicle_y:.0f})")
                self.status_labels["heading"].setText(f"🧭 Heading: {self.vehicle_heading:.0f}°")
                self.status_labels["gear"].setText(f"⚙️ Gear: {status.get('gear', 'D')}")
                self.status_labels["fuel"].setText(f"⛽ Fuel: {status.get('fuel_level', 1.0)*100:.0f}%")
                self.status_labels["engine"].setText(f"🔥 Engine: {'RACING' if real_speed > 50 else 'CRUISING' if real_speed > 0 else 'IDLE'}")
                
                # Tick CARLA world for physics simulation
                self.carla_world.tick()
                
            except Exception as e:
                self.add_log("error", f"CARLA update error: {e}")
                self._fallback_simulation()
        else:
            # Fallback simulation when CARLA not available
            self._fallback_simulation()
    
    def _fallback_simulation(self):
        """Fallback simulation when CARLA 3D is not available"""
        # Update vehicle position
        self.update_vehicle_position(self.vehicle_speed, 0)
        
        # Update gaming effects for our 2D fallback
        self._update_gaming_effects()
        
        # Update map visualization
        self.map_widget.update_vehicle_state(
            self.vehicle_x, self.vehicle_y, self.vehicle_heading, self.vehicle_speed
        )
        
        # Update status display
        status = self.can_simulator.get_vehicle_state()
        self.status_labels["speed"].setText(f"⚡ Speed: {status.get('speed', 0):.1f} km/h")
        self.status_labels["position"].setText(f"📍 Position: ({self.vehicle_x:.0f}, {self.vehicle_y:.0f})")
        self.status_labels["heading"].setText(f"🧭 Heading: {self.vehicle_heading:.0f}°")
        self.status_labels["gear"].setText(f"⚙️ Gear: {status.get('gear', 'P')}")
        self.status_labels["fuel"].setText(f"⛽ Fuel: {status.get('fuel_level', 1.0)*100:.0f}%")
        self.status_labels["engine"].setText(f"🔥 Engine: {'RACING' if status.get('speed', 0) > 50 else 'CRUISING' if status.get('speed', 0) > 0 else 'IDLE'}")
    
    def _update_gaming_effects(self):
        """Update gaming visual effects (fallback mode only)"""
        # Update map effects
        self.map_widget.update_game_effects()
        
        # Simulate dynamic vehicle movement for demo (only in fallback mode)
        if not (self.vehicle and CARLA_AVAILABLE):
            time_factor = time.time() * 0.3
            radius = 150
            center_x, center_y = 300, 200
            
            self.vehicle_x = center_x + radius * np.cos(time_factor)
            self.vehicle_y = center_y + radius * np.sin(time_factor)
            self.vehicle_heading = np.degrees(time_factor + np.pi/2)
            self.vehicle_speed = 60 + 30 * np.sin(time_factor * 3)  # Racing speeds
    
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
        """Clean up CARLA 3D resources on close"""
        try:
            if hasattr(self, 'spectator_timer'):
                self.spectator_timer.stop()
            
            if hasattr(self, 'third_person_camera') and self.third_person_camera:
                self.third_person_camera.destroy()
            
            if self.camera_sensor:
                self.camera_sensor.destroy()
            
            if self.vehicle:
                self.vehicle.destroy()
            
            if self.carla_world and CARLA_AVAILABLE:
                # Reset CARLA world settings
                settings = self.carla_world.get_settings()
                settings.synchronous_mode = False
                self.carla_world.apply_settings(settings)
            
            self.can_simulator.stop()
            self.add_log("info", "🔄 CARLA 3D resources cleaned up")
            
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    print("🎮 CARLA Racing Commander - Gaming Edition with 3D Graphics")
    print("=" * 70)
    print(f"CARLA Status: {'✅ Available' if CARLA_AVAILABLE else '❌ Not Available'}")
    print()
    print("🎮 GAMING FEATURES:")
    print("- Real CARLA 3D graphics and physics simulation")
    print("- Cinematic third-person camera following")
    print("- Real-time weather and environment control")
    print("- Sports car with racing physics")
    print("- AI command processing with Gemini")
    print("- Professional CAN bus simulation")
    print("- Gaming-style HUD and controls")
    print()
    
    if CARLA_AVAILABLE:
        print("🚀 FULL 3D MODE AVAILABLE!")
        print("📋 Setup Instructions:")
        print("1. Start CARLA simulator:")
        print("   CarlaUE4.exe -windowed -ResX=1920 -ResY=1080")
        print("2. Run this application - it will connect automatically")
        print("3. Use the CARLA window for full 3D experience")
        print("4. Use this interface for AI control and monitoring")
        print()
        print("🎮 Controls:")
        print("- Use buttons for vehicle control")
        print("- Type AI commands: 'drive forward', 'turn left', etc.")
        print("- Weather controls affect real CARLA 3D environment")
    else:
        print("⚠️  CARLA 3D NOT AVAILABLE")
        print("� To enable full 3D graphics:")
        print("1. Download CARLA 0.10.0 from: https://github.com/carla-simulator/carla/releases")
        print("2. Extract to C:\\Carla-0.10.0-Win64-Shipping")
        print("3. Start CarlaUE4.exe")
        print("4. Restart this application")
        print()
        print("🎮 Current mode: 2D Gaming Simulation with enhanced graphics")
    print()
    
    window = CARLA3DSimulation()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
