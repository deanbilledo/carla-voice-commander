#!/usr/bin/env python3
"""
Test script for Webots BmwX5 setup
"""

import os
import sys

def main():
    print("🚗 Webots BmwX5 Setup Test")
    print("=" * 50)
    
    # Check world file
    highway_world = "worlds/highway_bmw.wbt"
    if os.path.exists(highway_world):
        print(f"✅ Highway world file exists: {highway_world}")
    else:
        print(f"❌ Highway world file missing: {highway_world}")
    
    # Check controller
    bmw_controller = "controllers/bmw_controller/bmw_controller.py"
    if os.path.exists(bmw_controller):
        print(f"✅ BMW controller exists: {bmw_controller}")
    else:
        print(f"❌ BMW controller missing: {bmw_controller}")
    
    # Check overlay
    overlay_file = "webots_overlay.py"
    if os.path.exists(overlay_file):
        print(f"✅ Overlay file exists: {overlay_file}")
    else:
        print(f"❌ Overlay file missing: {overlay_file}")
    
    # Check commands directory
    commands_dir = "commands"
    if not os.path.exists(commands_dir):
        os.makedirs(commands_dir)
        print(f"✅ Created commands directory: {commands_dir}")
    else:
        print(f"✅ Commands directory exists: {commands_dir}")
    
    print("\n🎯 Next Steps:")
    print("1. Run: python test_overlay.py")
    print("2. Click 'Start Webots' in the overlay")
    print("3. You should see a BmwX5 on a highway road")
    print("4. Use the control buttons to move the vehicle")
    
    print("\n✅ Setup verification complete!")

if __name__ == "__main__":
    main()
