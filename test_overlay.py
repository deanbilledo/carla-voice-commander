"""
🚗 Webots Overlay Test Launcher
Test the overlay interface without requiring Webots installation
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox

def main():
    """Test launcher for overlay interface"""
    print("🚗 Voice Commander - Webots Edition Test")
    print("=" * 50)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    try:
        # Import and test the overlay
        from webots_overlay import WebotsOverlayApp
        
        print("✅ Overlay modules loaded successfully")
        print("🎮 Starting overlay interface...")
        
        # Create main application
        webots_app = WebotsOverlayApp()
        
        # Show info message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Voice Commander - Webots")
        msg.setText("🎮 Webots Overlay Interface Started!\n\n"
                   "📋 Features available:\n"
                   "• Transparent control overlay\n"
                   "• AI command processing\n"
                   "• Vehicle status monitoring\n"
                   "• Manual controls\n\n"
                   "📌 To use with Webots:\n"
                   "1. Install Webots from cyberbotics.com\n"
                   "2. Click 'Start Webots' in the control panel\n"
                   "3. Use the overlay controls")
        msg.exec_()
        
        # Run the application
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        
        # Show error dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Import Error")
        msg.setText(f"Failed to import modules:\n{e}\n\n"
                   "Please install dependencies:\n"
                   "pip install -r requirements.txt")
        msg.exec_()
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        
        # Show error dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical) 
        msg.setWindowTitle("Application Error")
        msg.setText(f"Application failed to start:\n{e}")
        msg.exec_()

if __name__ == "__main__":
    main()
