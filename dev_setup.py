"""
Development utilities and scripts for CARLA Voice Commander
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")

def check_environment():
    """Check if environment is properly configured"""
    print("Checking environment configuration...")
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Copy .env.example to .env and configure it.")
        return False
    
    # Check for required environment variables
    from config import Config
    
    checks = [
        ("GOOGLE_API_KEY", Config.GOOGLE_API_KEY, "Get API key from Google AI Studio"),
        ("CARLA_HOST", Config.CARLA_HOST, "CARLA simulator host"),
        ("CARLA_PORT", Config.CARLA_PORT, "CARLA simulator port")
    ]
    
    all_good = True
    for name, value, description in checks:
        if value:
            print(f"✅ {name}: {value}")
        else:
            print(f"❌ {name}: Not set ({description})")
            all_good = False
    
    return all_good

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    modules = [
        ("PyQt5", "GUI framework"),
        ("speech_recognition", "Speech recognition"),
        ("pyttsx3", "Text-to-speech"),
        ("google.generativeai", "Gemini AI"),
        ("carla", "CARLA simulator (optional for development)"),
    ]
    
    for module, description in modules:
        try:
            __import__(module)
            print(f"✅ {module}: Available")
        except ImportError:
            if module == "carla":
                print(f"⚠️  {module}: Not available ({description}) - Install CARLA simulator")
            else:
                print(f"❌ {module}: Not available ({description}) - Run: pip install {module}")

def run_tests():
    """Run unit tests"""
    print("Running tests...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-v"])
        print("All tests passed!")
    except subprocess.CalledProcessError as e:
        print(f"Some tests failed: {e}")
    except FileNotFoundError:
        print("pytest not found. Install with: pip install pytest")

def create_shortcuts():
    """Create convenient run shortcuts"""
    print("Creating run shortcuts...")
    
    # Dashboard shortcut
    dashboard_script = """@echo off
cd /d "%~dp0"
python main.py --mode dashboard
pause
"""
    
    # Headless shortcut  
    headless_script = """@echo off
cd /d "%~dp0"
python main.py --mode headless
pause
"""
    
    with open("run_dashboard.bat", "w") as f:
        f.write(dashboard_script)
    
    with open("run_headless.bat", "w") as f:
        f.write(headless_script)
    
    print("Created run_dashboard.bat and run_headless.bat")

def main():
    """Main development setup function"""
    print("🚗 CARLA Voice Commander - Development Setup")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("\n1. Checking environment...")
    env_ok = check_environment()
    
    print("\n2. Testing imports...")
    test_imports()
    
    print("\n3. Installing dependencies...")
    install_dependencies()
    
    print("\n4. Creating shortcuts...")
    create_shortcuts()
    
    print("\n5. Running tests...")
    run_tests()
    
    print("\n" + "=" * 50)
    if env_ok:
        print("✅ Setup complete! You can now run:")
        print("   - python main.py --mode dashboard  (or run_dashboard.bat)")
        print("   - python main.py --mode headless   (or run_headless.bat)")
    else:
        print("⚠️  Setup needs attention. Please fix the environment issues above.")
    
    print("\nMake sure CARLA simulator is running before starting the application!")

if __name__ == "__main__":
    main()
