"""
Quick setup script for CARLA Voice Commander
"""

import os
import subprocess
import sys
from pathlib import Path

def run_setup():
    """Run quick setup for CARLA Voice Commander"""
    print("🚗 CARLA Voice Commander - Quick Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the carla-voice-commander directory")
        return False
    
    # Install core dependencies
    print("\n📦 Installing core dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "PyQt5", "google-generativeai", "speech_recognition", 
            "pyttsx3", "numpy", "python-dotenv", "requests", "pytest"
        ])
        print("✅ Core dependencies installed!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    
    # Check .env file
    print("\n🔧 Checking configuration...")
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from template")
        else:
            with open(".env", "w") as f:
                f.write("GOOGLE_API_KEY=your_gemini_api_key_here\n")
                f.write("CARLA_HOST=localhost\n")
                f.write("CARLA_PORT=2000\n")
                f.write("DEBUG_MODE=True\n")
                f.write("LOG_LEVEL=INFO\n")
            print("✅ Created basic .env file")
    
    print("⚠️  Please edit .env and add your Google Gemini API key!")
    
    # Run tests
    print("\n🧪 Running tests...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-v"])
        print("✅ All tests passed!")
    except subprocess.CalledProcessError:
        print("⚠️  Some tests failed, but that's okay for now")
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Get a Google Gemini API key from: https://makersuite.google.com/app/apikey")
    print("2. Edit .env file and add your API key")
    print("3. Run the application:")
    print("   - python main.py --mode dashboard   (GUI mode)")
    print("   - python main.py --mode headless    (command line)")
    print("   - python integration_example.py     (demo mode)")
    
    return True

if __name__ == "__main__":
    run_setup()
