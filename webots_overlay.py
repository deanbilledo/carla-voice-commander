"""
🎮 Webots Vehicle Control Overlay
Transparent overlay GUI for controlling Webots vehicle simulation
"""

import sys
import os
import time
import math
import threading
import subprocess
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QTextEdit, QLineEdit,
                             QGroupBox, QGridLayout, QFrame, QSlider, QComboBox,
                             QTabWidget, QProgressBar, QCheckBox, QMessageBox)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QThread, QObject
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QBrush, QPixmap

# Import project modules
from config import Config
from utils.logger import Logger

# Try to import GeminiAgent, but make it optional
try:
    from gemini_agent import GeminiAgent
    GEMINI_AVAILABLE = True
except ImportError:
    print("⚠️ GeminiAgent not available - AI features disabled")
    GeminiAgent = None
    GEMINI_AVAILABLE = False

class WebotsControllerInterface(QObject):
    """Interface to communicate with Webots controller"""
    
    status_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.logger = Logger.get_logger(__name__)
        self.webots_process = None
        self.controller_active = False
        
        # Vehicle state from controller
        self.vehicle_state = {
            'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'orientation': {'yaw': 0.0},
            'speed_kmh': 0.0,
            'gear': 'P',
            'engine_rpm': 0,
            'connected': False
        }
        
        # Initialize AI
        if GEMINI_AVAILABLE:
            self.gemini_agent = GeminiAgent()
        else:
            self.gemini_agent = None
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(100)  # 10 FPS
    
    def start_webots(self, world_file: str = "highway_bmw.wbt"):
        """Start Webots with specified world file"""
        try:
            webots_path = self._find_webots_executable()
            if not webots_path:
                self.logger.error("Webots executable not found")
                # Show installation dialog
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Webots Not Found")
                msg.setText("Webots simulator not found!\n\n"
                           "📥 Installation Instructions:\n"
                           "1. Download Webots from: https://cyberbotics.com/\n"
                           "2. Install with default settings\n"
                           "3. Restart this application\n\n"
                           "🔍 Searched locations:\n"
                           "• C:\\Program Files\\Webots\\\n"
                           "• C:\\Program Files (x86)\\Webots\\\n"
                           "• System PATH\n\n"
                           "💡 Alternative: Run Webots manually and load:\n"
                           f"   {os.path.abspath('worlds/city_bmw.wbt')}")
                msg.exec_()
                return False
            
            # Check if world file exists
            world_path = os.path.join(os.path.dirname(__file__), "worlds", world_file)
            if not os.path.exists(world_path):
                self.logger.warning(f"World file not found: {world_path}, using default")
                # Try to start Webots without world file
                cmd = [webots_path]
            else:
                cmd = [webots_path, world_path]
            
            self.logger.info(f"Starting Webots: {' '.join(cmd)}")
            self.webots_process = subprocess.Popen(cmd, shell=False)
            
            # Give Webots time to start
            time.sleep(2)
            
            # Check if process started successfully
            if self.webots_process.poll() is None:
                self.controller_active = True
                self.vehicle_state['connected'] = True
                self.logger.info(f"✅ Webots started successfully with world: {world_file}")
                return True
            else:
                self.logger.error("Webots failed to start")
                return False
            
        except FileNotFoundError:
            self.logger.error("Webots executable not found in PATH")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start Webots: {e}")
            return False
    
    def _find_webots_executable(self) -> Optional[str]:
        """Find Webots executable on system"""
        possible_paths = [
            # Webots R2023b and newer
            r"C:\Program Files\Webots\msys64\mingw64\bin\webots.exe",
            r"C:\Program Files (x86)\Webots\msys64\mingw64\bin\webots.exe", 
            # Older versions
            r"C:\Program Files\Webots\webots.exe",
            r"C:\Program Files (x86)\Webots\webots.exe",
            # Custom installations
            r"C:\Webots\msys64\mingw64\bin\webots.exe",
            r"C:\Webots\webots.exe",
            # Alternative locations
            r"D:\Program Files\Webots\msys64\mingw64\bin\webots.exe",
            r"D:\Webots\msys64\mingw64\bin\webots.exe",
            # Try PATH
            "webots.exe",
            "webots"
        ]
        
        for path in possible_paths:
            if path.endswith('.exe'):
                if os.path.exists(path):
                    self.logger.info(f"Found Webots at: {path}")
                    return path
            else:
                # Check if in PATH
                try:
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        self.logger.info(f"Found Webots in PATH: {path}")
                        return path
                except:
                    continue
        
        # If not found, show installation message
        self.logger.error("Webots executable not found")
        return None
    
    def send_command(self, command: Dict[str, Any]):
        """Send command to Webots controller via file communication"""
        if not self.controller_active:
            self.logger.warning("Webots controller not active")
            return
        
        try:
            # Create commands directory if it doesn't exist
            commands_dir = os.path.join(os.path.dirname(__file__), "commands")
            os.makedirs(commands_dir, exist_ok=True)
            
            # Write command to file that Webots controller can read
            command_file = os.path.join(commands_dir, "current_command.json")
            
            import json
            with open(command_file, 'w') as f:
                json.dump(command, f)
            
            # Also update our local state for the overlay
            action = command.get('action', '')
            
            if action == 'forward':
                speed = command.get('speed', 20.0)
                self.vehicle_state['speed_kmh'] = speed
                self.vehicle_state['gear'] = 'D'
                self.logger.info(f"Command sent: Move forward at {speed} km/h")
                
            elif action == 'backward':
                speed = command.get('speed', 10.0)
                self.vehicle_state['speed_kmh'] = -speed
                self.vehicle_state['gear'] = 'R'
                self.logger.info(f"Command sent: Move backward at {speed} km/h")
                
            elif action == 'left':
                self.vehicle_state['orientation']['yaw'] += 5.0
                self.logger.info("Command sent: Turn left")
                
            elif action == 'right':
                self.vehicle_state['orientation']['yaw'] -= 5.0
                self.logger.info("Command sent: Turn right")
                
            elif action == 'stop':
                self.vehicle_state['speed_kmh'] = 0.0
                self.vehicle_state['gear'] = 'P'
                self.logger.info("Command sent: Emergency stop")
                
            elif action == 'park':
                self.vehicle_state['speed_kmh'] = 0.0
                self.vehicle_state['gear'] = 'P'
                self.logger.info("Command sent: Park vehicle")
                
            elif action == 'ai_command':
                self.process_ai_command(command.get('text', ''))
            
            # Emit status update
            self.status_updated.emit(self.vehicle_state)
            
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
    
    def process_ai_command(self, command_text: str):
        """Process AI command"""
        self.logger.info(f"Processing AI command: {command_text}")
        
        if not self.gemini_agent:
            self.logger.warning("Gemini AI not available - using simple command parsing")
            # Simple fallback command processing
            command_text = command_text.lower()
            if 'forward' in command_text or 'ahead' in command_text:
                command = {'action': 'move_forward', 'speed': 25}
            elif 'back' in command_text or 'reverse' in command_text:
                command = {'action': 'move_backward', 'speed': 15}
            elif 'left' in command_text:
                command = {'action': 'turn_left'}
            elif 'right' in command_text:
                command = {'action': 'turn_right'}
            elif 'stop' in command_text:
                command = {'action': 'stop'}
            else:
                self.logger.warning(f"Unknown command: {command_text}")
                return
            
            self.send_command(command)
            return
        
        # Get AI response
        response = self.gemini_agent.process_command(command_text, {}, self.vehicle_state)
        
        if response and not response.get('clarification_needed', False):
            # Execute AI action
            action = response.get('action', '')
            parameters = response.get('parameters', {})
            
            if action:
                command = {'action': action}
                command.update(parameters)
                self.send_command(command)
    
    def update_status(self):
        """Update vehicle status"""
        # Simulate position updates based on speed
        if self.vehicle_state['speed_kmh'] != 0:
            speed_ms = self.vehicle_state['speed_kmh'] / 3.6
            dt = 0.1  # 100ms update
            
            # Simple position update
            yaw_rad = math.radians(self.vehicle_state['orientation']['yaw'])
            dx = speed_ms * dt * math.cos(yaw_rad)
            dy = speed_ms * dt * math.sin(yaw_rad)
            
            self.vehicle_state['position']['x'] += dx
            self.vehicle_state['position']['y'] += dy
            
            # Update engine RPM based on speed
            self.vehicle_state['engine_rpm'] = int(abs(self.vehicle_state['speed_kmh']) * 50)
        
        self.status_updated.emit(self.vehicle_state.copy())
    
    def stop_webots(self):
        """Stop Webots simulation"""
        try:
            if self.webots_process:
                self.webots_process.terminate()
                self.webots_process = None
            
            self.controller_active = False
            self.vehicle_state['connected'] = False
            self.logger.info("Webots simulation stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop Webots: {e}")

class ControlOverlay(QFrame):
    """Main control overlay window"""
    
    command_signal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 650)  # Made wider and taller
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 230);
                border: 2px solid rgba(100, 100, 100, 150);
                border-radius: 15px;
            }
            QPushButton {
                background: rgba(240, 240, 240, 200);
                color: black;
                border: 1px solid gray;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
                min-height: 45px;
                margin: 3px;
            }
            QPushButton:hover {
                background: rgba(220, 220, 220, 200);
                border: 2px solid darkgray;
            }
            QPushButton:pressed {
                background: rgba(200, 200, 200, 200);
            }
            QLabel {
                color: black;
                font-weight: bold;
                font-size: 11px;
                margin: 2px;
            }
            QLineEdit {
                background: rgba(250, 250, 250, 200);
                border: 1px solid gray;
                border-radius: 5px;
                color: black;
                padding: 8px;
                font-size: 11px;
                margin: 2px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid gray;
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 100);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ffff;
                width: 20px;
                border-radius: 10px;
            }
            QComboBox {
                background: rgba(0, 0, 0, 150);
                border: 1px solid #00ffff;
                border-radius: 5px;
                color: #ffffff;
                padding: 5px;
                margin: 2px;
            }
        """)
        self.init_ui()
        self.make_draggable()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🚗 WEBOTS VEHICLE CONTROL")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: black; font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Webots status
        self.webots_status = QLabel("🔴 Webots: Disconnected")
        self.webots_status.setAlignment(Qt.AlignCenter)
        self.webots_status.setStyleSheet("font-size: 12px; margin: 5px;")
        layout.addWidget(self.webots_status)
        
        # Start/Stop Webots
        webots_group = QGroupBox("🚀 Webots Control")
        webots_layout = QHBoxLayout()
        webots_layout.setSpacing(10)
        
        self.start_btn = QPushButton("🚀 Start Webots")
        self.start_btn.clicked.connect(self.start_webots)
        self.stop_btn = QPushButton("🛑 Stop Webots")
        self.stop_btn.clicked.connect(self.stop_webots)
        webots_layout.addWidget(self.start_btn)
        webots_layout.addWidget(self.stop_btn)
        
        webots_group.setLayout(webots_layout)
        layout.addWidget(webots_group)
        
        # AI Command input
        ai_group = QGroupBox("🤖 AI Commands")
        ai_layout = QVBoxLayout()
        ai_layout.setSpacing(8)
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("'drive forward', 'turn left', 'park'...")
        self.command_input.returnPressed.connect(self.send_ai_command)
        self.command_input.setMinimumHeight(35)
        ai_layout.addWidget(self.command_input)
        
        ai_btn = QPushButton("🧠 Send AI Command")
        ai_btn.clicked.connect(self.send_ai_command)
        ai_btn.setMinimumHeight(45)
        ai_layout.addWidget(ai_btn)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # Manual controls
        manual_group = QGroupBox("🎮 Manual Controls")
        manual_layout = QVBoxLayout()
        manual_layout.setSpacing(8)
        
        # Movement controls in rows to prevent overlap
        movement_controls = [
            ("⬆️ Forward", {"action": "move_forward", "speed": 25}),
            ("⬇️ Reverse", {"action": "move_backward", "speed": 15}),
        ]
        
        # First row - Forward/Reverse
        movement_row1 = QHBoxLayout()
        movement_row1.setSpacing(10)
        for label, cmd in movement_controls:
            btn = QPushButton(label)
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda checked, command=cmd: self.command_signal.emit(command))
            movement_row1.addWidget(btn)
        manual_layout.addLayout(movement_row1)
        
        # Second row - Left/Right
        turning_controls = [
            ("⬅️ Left", {"action": "turn_left"}),
            ("➡️ Right", {"action": "turn_right"}),
        ]
        
        movement_row2 = QHBoxLayout()
        movement_row2.setSpacing(10)
        for label, cmd in turning_controls:
            btn = QPushButton(label)
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda checked, command=cmd: self.command_signal.emit(command))
            movement_row2.addWidget(btn)
        manual_layout.addLayout(movement_row2)
        
        # Third row - Stop/Park
        action_controls = [
            ("🛑 Stop", {"action": "stop"}),
            ("🅿️ Park", {"action": "park"}),
        ]
        
        movement_row3 = QHBoxLayout()
        movement_row3.setSpacing(10)
        for label, cmd in action_controls:
            btn = QPushButton(label)
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda checked, command=cmd: self.command_signal.emit(command))
            movement_row3.addWidget(btn)
        manual_layout.addLayout(movement_row3)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        # Speed control
        speed_group = QGroupBox("⚡ Speed Control")
        speed_layout = QVBoxLayout()
        speed_layout.setSpacing(8)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 60)
        self.speed_slider.setValue(0)
        self.speed_slider.valueChanged.connect(self.speed_changed)
        self.speed_slider.setMinimumHeight(30)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("Speed: 0 km/h")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet("font-size: 12px; margin: 5px;")
        speed_layout.addWidget(self.speed_label)
        
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # World selection
        world_group = QGroupBox("🌍 World Selection")
        world_layout = QVBoxLayout()
        world_layout.setSpacing(8)
        
        world_label = QLabel("Current World:")
        world_label.setStyleSheet("font-size: 11px;")
        world_layout.addWidget(world_label)
        
        self.world_combo = QComboBox()
        self.world_combo.addItems([
            "highway_bmw.wbt"
        ])
        self.world_combo.setMinimumHeight(35)
        world_layout.addWidget(self.world_combo)
        
        world_group.setLayout(world_layout)
        layout.addWidget(world_group)
        
        # Close button
        close_btn = QPushButton("✖️ Close Overlay")
        close_btn.clicked.connect(self.close)
        close_btn.setMinimumHeight(45)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 80, 80, 200);
                color: white;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 80, 80, 255);
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
    
    def start_webots(self):
        """Start Webots simulation"""
        world_file = self.world_combo.currentText()
        self.command_signal.emit({"action": "start_webots", "world": world_file})
    
    def stop_webots(self):
        """Stop Webots simulation"""
        self.command_signal.emit({"action": "stop_webots"})
    
    def send_ai_command(self):
        """Send AI command"""
        text = self.command_input.text().strip()
        if text:
            self.command_signal.emit({"action": "ai_command", "text": text})
            self.command_input.clear()
    
    def speed_changed(self, value):
        """Handle speed slider change"""
        self.speed_label.setText(f"Speed: {value} km/h")
        if value > 0:
            self.command_signal.emit({"action": "move_forward", "speed": value})
        elif value < 0:
            self.command_signal.emit({"action": "move_backward", "speed": abs(value)})
        else:
            self.command_signal.emit({"action": "stop"})
    
    def update_webots_status(self, connected: bool):
        """Update Webots connection status"""
        if connected:
            self.webots_status.setText("🟢 Webots: Connected")
            self.webots_status.setStyleSheet("color: green;")
        else:
            self.webots_status.setText("🔴 Webots: Disconnected")
            self.webots_status.setStyleSheet("color: red;")

class StatusOverlay(QFrame):
    """Vehicle status display overlay"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(350, 300)  # Made slightly larger
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 230);
                border: 2px solid rgba(100, 100, 100, 150);
                border-radius: 15px;
            }
            QLabel {
                color: black;
                font-weight: bold;
                font-size: 12px;
                margin: 3px;
                padding: 5px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid gray;
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        self.init_ui()
        self.make_draggable()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("📊 VEHICLE STATUS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: black; font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Status group
        status_group = QGroupBox("🚗 Live Vehicle Data")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(5)
        
        # Status labels
        self.status_labels = {}
        status_items = [
            ("speed", "⚡ Speed: 0 km/h"),
            ("position", "📍 Position: (0.0, 0.0)"),
            ("orientation", "🧭 Heading: 0°"),
            ("gear", "⚙️ Gear: P"),
            ("connection", "🔗 Status: Disconnected")
        ]
        
        for key, initial in status_items:
            label = QLabel(initial)
            label.setStyleSheet("background: rgba(245, 245, 245, 150); border-radius: 5px; padding: 8px;")
            self.status_labels[key] = label
            status_layout.addWidget(label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
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
    
    def update_status(self, vehicle_state: Dict[str, Any]):
        """Update status display"""
        pos = vehicle_state.get('position', {})
        orientation = vehicle_state.get('orientation', {})
        
        self.status_labels["speed"].setText(f"⚡ Speed: {vehicle_state.get('speed_kmh', 0):.1f} km/h")
        self.status_labels["position"].setText(f"📍 Position: ({pos.get('x', 0):.1f}, {pos.get('y', 0):.1f})")
        self.status_labels["orientation"].setText(f"🧭 Heading: {orientation.get('yaw', 0):.0f}°")
        self.status_labels["gear"].setText(f"⚙️ Gear: {vehicle_state.get('gear', 'P')}")
        self.status_labels["rpm"].setText(f"🔧 RPM: {vehicle_state.get('engine_rpm', 0)}")
        
        if vehicle_state.get('connected', False):
            self.status_labels["connection"].setText("🟢 Status: Connected")
            self.status_labels["connection"].setStyleSheet("color: green;")
        else:
            self.status_labels["connection"].setText("🔴 Status: Disconnected")
            self.status_labels["connection"].setStyleSheet("color: red;")

class WebotsOverlayApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = Logger.get_logger(__name__)
        
        # Hide main window (we only use overlays)
        self.hide()
        
        # Initialize Webots interface
        self.webots_interface = WebotsControllerInterface()
        self.webots_interface.status_updated.connect(self.update_status)
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.read_vehicle_status)
        self.status_timer.start(100)  # Update every 100ms
        
        # Create overlay windows
        self.control_overlay = ControlOverlay()
        self.status_overlay = StatusOverlay()
        
        # Connect signals
        self.control_overlay.command_signal.connect(self.handle_command)
        
        # Position overlays
        screen = QApplication.primaryScreen().geometry()
        self.control_overlay.move(screen.width() - 370, 50)  # Top right
        self.status_overlay.move(20, screen.height() - 300)  # Bottom left
        
        # Show overlays
        self.control_overlay.show()
        self.status_overlay.show()
        
        self.logger.info("Webots overlay application started")
    
    def read_vehicle_status(self):
        """Read vehicle status from file"""
        try:
            status_file = os.path.join(os.path.dirname(__file__), "commands", "vehicle_status.json")
            if os.path.exists(status_file):
                import json
                with open(status_file, 'r') as f:
                    status = json.load(f)
                
                # Update status overlay
                self.status_overlay.update_status(status)
                
        except Exception as e:
            pass  # Silently handle file read errors
    
    def handle_command(self, command: Dict[str, Any]):
        """Handle commands from overlay"""
        action = command.get('action', '')
        
        print(f"🎮 Overlay received command: {command}")  # Debug output
        
        if action == 'start_webots':
            world = command.get('world', 'highway_bmw.wbt')
            success = self.webots_interface.start_webots(world)
            self.control_overlay.update_webots_status(success)
        elif action == 'stop_webots':
            self.webots_interface.stop_webots()
            self.control_overlay.update_webots_status(False)
        else:
            print(f"🚗 Sending command to Webots: {command}")  # Debug output
            self.webots_interface.send_command(command)
    
    def update_status(self, vehicle_state: Dict[str, Any]):
        """Update status overlay"""
        self.status_overlay.update_status(vehicle_state)
    
    def closeEvent(self, event):
        """Handle application close"""
        self.webots_interface.stop_webots()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    print("🚗 Webots Vehicle Control Overlay")
    print("=" * 40)
    print("🎮 Features:")
    print("- Transparent overlay controls")
    print("- AI command processing with Gemini")
    print("- Real-time vehicle status")
    print("- Multiple world environments")
    print("- Direct Webots integration")
    print()
    print("📋 Instructions:")
    print("1. Click 'Start Webots' to launch simulation")
    print("2. Use manual controls or AI commands")
    print("3. Drag overlays to reposition")
    print("4. Monitor vehicle status in real-time")
    print()
    
    # Create main application
    webots_app = WebotsOverlayApp()
    
    # Run application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted")
        webots_app.close()

if __name__ == "__main__":
    main()
