"""
Simple vehicle movement test
Run this after Webots is started with the automobile_simple.wbt world
"""

import time
from PyQt5.QtWidgets import QApplication
import sys
import os

sys.path.append(os.path.dirname(__file__))

from webots_overlay import WebotsOverlayApp

def test_vehicle_movement():
    """Test vehicle movement through overlay"""
    
    print("🎮 Testing Vehicle Movement Through Overlay")
    print("=" * 50)
    print("💡 Make sure Webots is running with automobile_simple.wbt")
    print("💡 You should see a red car in the Webots window")
    print()
    
    app = QApplication(sys.argv)
    
    # Create overlay app
    overlay_app = WebotsOverlayApp()
    overlay_app.show()
    
    print("✅ Overlay started - try these actions:")
    print("  1. Click 'Start Webots' if not already started")
    print("  2. Use the Forward/Backward/Turn buttons")
    print("  3. Try voice commands")
    print("  4. Watch the Webots window for vehicle movement")
    print()
    print("🔍 Vehicle should automatically move forward for 3 seconds as a test")
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_vehicle_movement()
