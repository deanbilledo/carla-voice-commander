"""
Test script to verify Webots controller communication
"""

import time
import sys
import os

# Add project directory to path
sys.path.append(os.path.dirname(__file__))

from webots_overlay import WebotsControllerInterface

def test_controller_communication():
    """Test communication with Webots controller"""
    
    print("🧪 Testing Webots Controller Communication")
    print("=" * 50)
    
    # Initialize interface
    interface = WebotsControllerInterface()
    
    # Start Webots with our fixed world file
    print("🚀 Starting Webots with automobile_simple.wbt...")
    result = interface.start_webots("automobile_simple.wbt")
    
    if result:
        print("✅ Webots started successfully!")
        
        # Wait a moment for Webots to fully load
        print("⏳ Waiting for Webots to load...")
        time.sleep(3)
        
        # Test commands
        test_commands = [
            {"action": "forward", "speed": 20},
            {"action": "left"},
            {"action": "right"},
            {"action": "stop"}
        ]
        
        print("\n🎮 Testing vehicle commands:")
        for i, command in enumerate(test_commands):
            print(f"  {i+1}. Testing: {command}")
            interface.send_command(command)
            time.sleep(2)  # Wait between commands
        
        print("\n✅ Test commands sent successfully!")
        print("💡 Check Webots window to see if vehicle is moving")
        
    else:
        print("❌ Failed to start Webots")
        print("💡 Make sure Webots is installed and available in PATH")

if __name__ == "__main__":
    test_controller_communication()
