"""
🎮 CARLA Racing Overlay Launcher
Starts CARLA and the transparent overlay GUI
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def main():
    print("🎮 CARLA Racing Overlay Launcher")
    print("=" * 40)
    
    # Check if CARLA is already running
    print("🔍 Checking if CARLA is running...")
    
    # Give CARLA time to start if it's not running
    carla_running = False
    try:
        import carla
        client = carla.Client('localhost', 2000)
        client.set_timeout(5.0)
        world = client.get_world()
        carla_running = True
        print("✅ CARLA is already running!")
    except:
        print("❌ CARLA not detected")
    
    if not carla_running:
        print("🚀 Starting CARLA...")
        carla_path = r"C:\CARLA_0.10.0\CarlaUnreal.exe"
        
        if os.path.exists(carla_path):
            try:
                # Start CARLA in background
                subprocess.Popen([carla_path], shell=True)
                print("✅ CARLA started!")
                print("⏳ Waiting for CARLA to initialize...")
                time.sleep(10)  # Give CARLA time to start
            except Exception as e:
                print(f"❌ Failed to start CARLA: {e}")
                print("Please start CARLA manually and run this again")
                return
        else:
            print(f"❌ CARLA not found at: {carla_path}")
            print("Please start CARLA manually and run this again")
            return
    
    # Start the overlay GUI
    print("🖥️ Starting overlay interface...")
    try:
        subprocess.run([sys.executable, "carla_overlay_gui.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Overlay closed by user")
    except Exception as e:
        print(f"❌ Overlay failed: {e}")

if __name__ == "__main__":
    main()
