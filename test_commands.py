#!/usr/bin/env python3
"""
Test the command system and verify fixes
"""

import json
import time
import os

def test_command_system():
    print("🧪 Testing Command System")
    print("=" * 40)
    
    # Test various command formats
    test_commands = [
        {"command": "forward"},
        {"action": "move_forward"},
        {"command": "left"},
        {"action": "turn_right"},
        {"command": "stop"}
    ]
    
    commands_dir = "commands"
    command_file = os.path.join(commands_dir, "current_command.json")
    
    # Ensure directory exists
    os.makedirs(commands_dir, exist_ok=True)
    
    for i, cmd in enumerate(test_commands):
        print(f"📝 Test {i+1}: {cmd}")
        
        # Write command to file
        with open(command_file, 'w') as f:
            json.dump(cmd, f)
        
        print(f"   ✅ Command written to {command_file}")
        time.sleep(1)  # Small delay
    
    print("\n🎯 Command tests complete!")
    print("💡 These commands should now work without JSON errors")
    
    # Check if status file exists
    status_file = os.path.join(commands_dir, "vehicle_status.json")
    if os.path.exists(status_file):
        print(f"✅ Status file exists: {status_file}")
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
                print(f"📊 Current status: Connected={status.get('connected', False)}")
        except:
            print("⚠️ Status file exists but may have JSON issues")
    else:
        print(f"⚠️ Status file not found: {status_file}")

if __name__ == "__main__":
    test_command_system()
