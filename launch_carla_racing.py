"""
🎮 CARLA Connection Test and Launcher
Simple script to test CARLA connection and launch the main simulation
"""

import socket
import subprocess
import sys
import time
import os

def check_carla_server():
    """Check if CARLA server is running on localhost:2000"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 2000))
        sock.close()
        return result == 0
    except Exception:
        return False

def start_carla():
    """Start CARLA server"""
    carla_path = r"C:\Carla-0.10.0-Win64-Shipping\CarlaUnreal.exe"
    if os.path.exists(carla_path):
        print("🚀 Starting CARLA simulator...")
        subprocess.Popen([carla_path, "-windowed", "-ResX=1920", "-ResY=1080"])
        return True
    else:
        print("❌ CARLA not found at expected path")
        return False

def main():
    print("🎮 CARLA Racing Commander - Launcher")
    print("=" * 50)
    
    # Check if CARLA is running
    if check_carla_server():
        print("✅ CARLA server is already running on localhost:2000")
    else:
        print("⚠️ CARLA server not detected")
        print("Starting CARLA simulator...")
        
        if start_carla():
            print("🔄 Waiting for CARLA to start...")
            # Wait up to 30 seconds for CARLA to start
            for i in range(30):
                time.sleep(1)
                if check_carla_server():
                    print("✅ CARLA server is now running!")
                    break
                print(f"⏳ Waiting... ({i+1}/30)")
            else:
                print("❌ CARLA server did not start in time")
                print("💡 Try starting CARLA manually:")
                print("1. Navigate to C:\\Carla-0.10.0-Win64-Shipping")
                print("2. Run: CarlaUnreal.exe -windowed -ResX=1920 -ResY=1080")
                print("3. Wait for the 3D world to load")
                print("4. Then run this script again")
                return
        else:
            print("❌ Could not start CARLA")
            return
    
    # Now start the main simulation
    print("🎮 Starting CARLA Racing Commander...")
    try:
        import carla_3d_simulation
        carla_3d_simulation.main()
    except Exception as e:
        print(f"❌ Error starting simulation: {e}")
        print("💡 You can still run the simulation manually:")
        print("python carla_3d_simulation.py")

if __name__ == "__main__":
    main()
