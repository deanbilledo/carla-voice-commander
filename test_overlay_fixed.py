"""
🚗 Webots Overlay Test Launcher
Test the overlay interface with error handling and debugging
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
        print("📋 Importing overlay modules...")
        
        # Import and test the overlay
        from webots_overlay import WebotsOverlayApp
        
        print("✅ Overlay modules loaded successfully")
        print("🎮 Starting overlay interface...")
        
        # Create main application
        webots_app = WebotsOverlayApp()
        
        print("✅ Application created successfully")
        print("📱 Overlay windows should be visible on screen")
        
        # Show info message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Voice Commander - Webots")
        msg.setText("🎮 Webots Overlay Interface Started!\n\n"
                   "📋 Features available:\n"
                   "• Transparent control overlay\n"
                   "• Manual vehicle controls\n"
                   "• Vehicle status monitoring\n"
                   "• Basic AI command processing\n\n"
                   "📌 To use with Webots:\n"
                   "1. Install Webots from cyberbotics.com\n"
                   "2. Click 'Start Webots' in the control panel\n"
                   "3. Use the overlay controls\n\n"
                   "⚠️ Note: If Gemini AI is not available,\n"
                   "basic fallback commands will be used.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        print("💡 Overlay interface is now running...")
        print("   - Control overlay should be at top-right")
        print("   - Status overlay should be at bottom-left")
        print("   - Both windows can be dragged to reposition")
        print("   - Close any overlay window to exit")
        
        # Run the application
        print("🚀 Starting Qt event loop...")
        sys.exit(app.exec_())
        
    except ImportError as e:
        error_msg = f"❌ Import error: {e}"
        print(error_msg)
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
        
        return 1
        
    except Exception as e:
        error_msg = f"❌ Application error: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        
        # Show error dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical) 
        msg.setWindowTitle("Application Error")
        msg.setText(f"Application failed to start:\n{e}\n\n"
                   "Check the terminal for detailed error information.")
        msg.exec_()
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code else 0)
