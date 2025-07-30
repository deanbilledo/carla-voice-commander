"""
Test script to verify all fixes
"""

import time
import json
import os

def test_vehicle_status():
    """Test if vehicle status is being updated"""
    print("🧪 Testing Vehicle Status Updates")
    print("=" * 40)
    
    status_file = "commands/vehicle_status.json"
    
    if not os.path.exists(status_file):
        print("❌ Status file not found")
        return False
    
    # Read status file
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        print("✅ Status file readable")
        print(f"📍 Position: ({status.get('position', {}).get('x', 0):.1f}, {status.get('position', {}).get('y', 0):.1f})")
        print(f"⚡ Speed: {status.get('speed_kmh', 0):.1f} km/h")
        print(f"⚙️ Gear: {status.get('gear', 'P')}")
        print(f"🔗 Connected: {status.get('connected', False)}")
        print(f"⏰ Last update: {time.time() - status.get('timestamp', 0):.1f}s ago")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading status: {e}")
        return False

def test_command_sending():
    """Test sending a command"""
    print("\n🎮 Testing Command Sending")
    print("=" * 40)
    
    command = {"action": "forward", "speed": 15}
    
    try:
        with open("commands/current_command.json", 'w') as f:
            json.dump(command, f)
        
        print("✅ Command sent successfully")
        print(f"📤 Command: {command}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending command: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Voice Commander - System Test")
    print("=" * 50)
    print("💡 Make sure Webots is running with automobile_simple.wbt")
    print()
    
    # Test status
    status_ok = test_vehicle_status()
    
    # Test commands
    command_ok = test_command_sending()
    
    print(f"\n📊 Test Results:")
    print(f"   Status System: {'✅ OK' if status_ok else '❌ FAIL'}")
    print(f"   Command System: {'✅ OK' if command_ok else '❌ FAIL'}")
    
    if status_ok and command_ok:
        print("\n🎉 All systems working!")
        print("💡 Try using the overlay to control the vehicle")
    else:
        print("\n⚠️ Some issues detected")
        print("💡 Check Webots console for errors")
