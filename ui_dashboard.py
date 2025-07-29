"""
PyQt5 Dashboard for CARLA Voice Commander
Interactive UI with vehicle status, map, and command log
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QTextEdit, QProgressBar,
                             QGroupBox, QGridLayout, QComboBox, QSlider, QCheckBox)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap, QPainter, QPen, QColor
import json
from config import Config
from utils.logger import Logger
from carla_interface import CarlaInterface
from gemini_agent import GeminiAgent
from voice.speech_recognition import SpeechRecognizer
from voice.text_to_speech import TextToSpeech

class VehicleStatusWidget(QGroupBox):
    """Widget for displaying vehicle status"""
    
    def __init__(self):
        super().__init__("Vehicle Status")
        self.init_ui()
    
    def init_ui(self):
        layout = QGridLayout()
        
        # Speed display
        self.speed_label = QLabel("Speed: 0.0 km/h")
        self.speed_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(QLabel("Speed:"), 0, 0)
        layout.addWidget(self.speed_label, 0, 1)
        
        # Location display
        self.location_label = QLabel("X: 0.0, Y: 0.0, Z: 0.0")
        layout.addWidget(QLabel("Location:"), 1, 0)
        layout.addWidget(self.location_label, 1, 1)
        
        # Control mode
        self.control_mode_label = QLabel("Manual")
        layout.addWidget(QLabel("Control Mode:"), 2, 0)
        layout.addWidget(self.control_mode_label, 2, 1)
        
        # Fuel level
        self.fuel_bar = QProgressBar()
        self.fuel_bar.setMaximum(100)
        self.fuel_bar.setValue(100)
        layout.addWidget(QLabel("Fuel:"), 3, 0)
        layout.addWidget(self.fuel_bar, 3, 1)
        
        # Health status
        self.health_bar = QProgressBar()
        self.health_bar.setMaximum(100)
        self.health_bar.setValue(100)
        layout.addWidget(QLabel("Health:"), 4, 0)
        layout.addWidget(self.health_bar, 4, 1)
        
        self.setLayout(layout)
    
    def update_status(self, status):
        """Update vehicle status display"""
        self.speed_label.setText(f"{status.get('speed', 0.0)} km/h")
        
        location = status.get('location', {})
        self.location_label.setText(
            f"X: {location.get('x', 0.0)}, "
            f"Y: {location.get('y', 0.0)}, "
            f"Z: {location.get('z', 0.0)}"
        )
        
        self.control_mode_label.setText(status.get('control_mode', 'Manual'))
        self.fuel_bar.setValue(int(status.get('fuel', 1.0) * 100))
        self.health_bar.setValue(int(status.get('health', 1.0) * 100))

class ControlWidget(QGroupBox):
    """Widget for manual vehicle control"""
    
    def __init__(self):
        super().__init__("Manual Control")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Control buttons
        button_layout = QGridLayout()
        
        self.forward_btn = QPushButton("Forward")
        self.backward_btn = QPushButton("Backward")
        self.left_btn = QPushButton("Turn Left")
        self.right_btn = QPushButton("Turn Right")
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        
        button_layout.addWidget(self.forward_btn, 0, 1)
        button_layout.addWidget(self.left_btn, 1, 0)
        button_layout.addWidget(self.stop_btn, 1, 1)
        button_layout.addWidget(self.right_btn, 1, 2)
        button_layout.addWidget(self.backward_btn, 2, 1)
        
        layout.addLayout(button_layout)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Max Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(100)
        self.speed_slider.setValue(50)
        self.speed_value_label = QLabel("50 km/h")
        
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        layout.addLayout(speed_layout)
        
        self.setLayout(layout)
        
        # Connect slider
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_value_label.setText(f"{v} km/h")
        )

class VoiceControlWidget(QGroupBox):
    """Widget for voice control interface"""
    
    def __init__(self):
        super().__init__("Voice Control")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Voice control toggle
        self.voice_enabled_cb = QCheckBox("Enable Voice Control")
        layout.addWidget(self.voice_enabled_cb)
        
        # Manual voice input
        voice_input_layout = QHBoxLayout()
        self.voice_input_btn = QPushButton("Speak Command")
        self.voice_status_label = QLabel("Ready")
        
        voice_input_layout.addWidget(self.voice_input_btn)
        voice_input_layout.addWidget(self.voice_status_label)
        layout.addLayout(voice_input_layout)
        
        # Last command display
        self.last_command_label = QLabel("Last Command: None")
        layout.addWidget(self.last_command_label)
        
        # AI response display
        self.ai_response_text = QTextEdit()
        self.ai_response_text.setMaximumHeight(100)
        self.ai_response_text.setPlaceholderText("AI responses will appear here...")
        layout.addWidget(QLabel("AI Response:"))
        layout.addWidget(self.ai_response_text)
        
        self.setLayout(layout)

class CommandLogWidget(QGroupBox):
    """Widget for displaying command history and logs"""
    
    def __init__(self):
        super().__init__("Command Log")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Command history
        self.command_log = QTextEdit()
        self.command_log.setReadOnly(True)
        layout.addWidget(self.command_log)
        
        # Clear button
        self.clear_btn = QPushButton("Clear Log")
        layout.addWidget(self.clear_btn)
        
        self.setLayout(layout)
        
        self.clear_btn.clicked.connect(self.clear_log)
    
    def add_log_entry(self, entry):
        """Add entry to command log"""
        self.command_log.append(entry)
    
    def clear_log(self):
        """Clear the command log"""
        self.command_log.clear()

class CarlaVoiceCommanderUI(QMainWindow):
    """Main UI for CARLA Voice Commander"""
    
    def __init__(self):
        super().__init__()
        self.logger = Logger.get_logger(__name__)
        
        # Initialize components
        self.carla_interface = CarlaInterface()
        self.gemini_agent = GeminiAgent()
        self.speech_recognizer = SpeechRecognizer()
        self.tts = TextToSpeech()
        
        # UI state
        self.voice_control_active = False
        
        self.init_ui()
        self.init_timers()
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("CARLA Voice Commander")
        self.setGeometry(100, 100, Config.DASHBOARD_WIDTH, Config.DASHBOARD_HEIGHT)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel
        left_panel = QVBoxLayout()
        
        # Vehicle status
        self.vehicle_status_widget = VehicleStatusWidget()
        left_panel.addWidget(self.vehicle_status_widget)
        
        # Control widget
        self.control_widget = ControlWidget()
        left_panel.addWidget(self.control_widget)
        
        # Voice control widget
        self.voice_control_widget = VoiceControlWidget()
        left_panel.addWidget(self.voice_control_widget)
        
        left_panel.addStretch()
        
        # Right panel - Command log
        self.command_log_widget = CommandLogWidget()
        
        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(400)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.command_log_widget)
    
    def init_timers(self):
        """Initialize update timers"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_vehicle_status)
        self.status_timer.start(1000 // Config.MAP_UPDATE_RATE)  # 30 FPS
    
    def connect_signals(self):
        """Connect UI signals"""
        # Control buttons
        self.control_widget.forward_btn.clicked.connect(
            lambda: self.send_control_command({"action": "forward", "throttle": 0.5})
        )
        self.control_widget.backward_btn.clicked.connect(
            lambda: self.send_control_command({"action": "forward", "throttle": -0.5})
        )
        self.control_widget.left_btn.clicked.connect(
            lambda: self.send_control_command({"action": "turn", "direction": "left"})
        )
        self.control_widget.right_btn.clicked.connect(
            lambda: self.send_control_command({"action": "turn", "direction": "right"})
        )
        self.control_widget.stop_btn.clicked.connect(
            lambda: self.send_control_command({"action": "stop"})
        )
        
        # Voice control
        self.voice_control_widget.voice_enabled_cb.toggled.connect(self.toggle_voice_control)
        self.voice_control_widget.voice_input_btn.clicked.connect(self.process_voice_command)
    
    def update_vehicle_status(self):
        """Update vehicle status display"""
        if self.carla_interface.vehicle:
            status = self.carla_interface.get_vehicle_status()
            self.vehicle_status_widget.update_status(status)
    
    def send_control_command(self, command):
        """Send control command to CARLA"""
        if self.carla_interface.apply_control(command):
            self.command_log_widget.add_log_entry(f"Manual Control: {command}")
    
    def toggle_voice_control(self, enabled):
        """Toggle voice control on/off"""
        self.voice_control_active = enabled
        
        if enabled:
            self.speech_recognizer.start_listening(self.on_voice_command)
            self.voice_control_widget.voice_status_label.setText("Listening...")
            self.command_log_widget.add_log_entry("Voice control enabled")
            self.tts.speak("Voice control activated")
        else:
            self.speech_recognizer.stop_listening()
            self.voice_control_widget.voice_status_label.setText("Ready")
            self.command_log_widget.add_log_entry("Voice control disabled")
            self.tts.speak("Voice control deactivated")
    
    def process_voice_command(self):
        """Process a single voice command"""
        self.voice_control_widget.voice_status_label.setText("Listening...")
        command = self.speech_recognizer.recognize_once()
        
        if command:
            self.on_voice_command(command)
        else:
            self.voice_control_widget.voice_status_label.setText("No command recognized")
            self.tts.speak("I didn't hear a command. Please try again.")
    
    def on_voice_command(self, command_text):
        """Handle voice command"""
        self.voice_control_widget.last_command_label.setText(f"Last Command: {command_text}")
        self.command_log_widget.add_log_entry(f"Voice Command: {command_text}")
        
        # Get current status for context
        vehicle_status = self.carla_interface.get_vehicle_status()
        environment_info = self.carla_interface.get_environment_info()
        
        # Process with Gemini
        response = self.gemini_agent.process_command(
            command_text, vehicle_status, environment_info
        )
        
        # Display AI response
        self.voice_control_widget.ai_response_text.setText(response['response'])
        self.command_log_widget.add_log_entry(f"AI Response: {response['response']}")
        
        # Speak response
        self.tts.speak(response['response'])
        
        # Execute action if not clarification
        if not response.get('clarification_needed', False):
            self.execute_ai_action(response)
        
        self.voice_control_widget.voice_status_label.setText("Ready" if self.voice_control_active else "Disabled")
    
    def execute_ai_action(self, ai_response):
        """Execute action based on AI response"""
        action = ai_response.get('action', '')
        parameters = ai_response.get('parameters', {})
        
        if action == "stop":
            self.send_control_command({"action": "stop"})
        elif action == "navigate":
            destination = ai_response.get('destination', '')
            self.command_log_widget.add_log_entry(f"Navigation to: {destination}")
            # TODO: Implement navigation logic
        elif action == "speed_change":
            # TODO: Implement speed control
            pass
        elif action == "turn":
            direction = parameters.get('direction', 'left')
            self.send_control_command({"action": "turn", "direction": direction})
        
        self.command_log_widget.add_log_entry(f"Executed action: {action}")
    
    def connect_to_carla(self):
        """Connect to CARLA simulator"""
        if self.carla_interface.connect():
            if self.carla_interface.spawn_vehicle():
                self.command_log_widget.add_log_entry("Connected to CARLA and spawned vehicle")
                return True
        
        self.command_log_widget.add_log_entry("Failed to connect to CARLA")
        return False
    
    def closeEvent(self, event):
        """Handle application close"""
        self.logger.info("Shutting down CARLA Voice Commander")
        
        # Cleanup components
        self.speech_recognizer.stop_listening()
        self.tts.cleanup()
        self.carla_interface.cleanup()
        
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = CarlaVoiceCommanderUI()
    window.show()
    
    # Try to connect to CARLA
    window.connect_to_carla()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
