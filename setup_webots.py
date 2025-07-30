"""
🔧 Webots Installation Checker and Setup
Helps users install and configure Webots for the Voice Commander project
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def check_webots_installation():
    """Check if Webots is installed and return installation status"""
    
    print("🔍 Checking Webots Installation...")
    print("=" * 50)
    
    # Possible Webots installation paths
    webots_paths = [
        r"C:\Program Files\Webots\msys64\mingw64\bin\webots.exe",
        r"C:\Program Files (x86)\Webots\msys64\mingw64\bin\webots.exe",
        r"C:\Program Files\Webots\webots.exe",
        r"C:\Program Files (x86)\Webots\webots.exe",
        r"C:\Webots\msys64\mingw64\bin\webots.exe",
        r"C:\Webots\webots.exe",
        r"D:\Program Files\Webots\msys64\mingw64\bin\webots.exe",
        r"D:\Webots\msys64\mingw64\bin\webots.exe"
    ]
    
    found_installations = []
    
    # Check each path
    for path in webots_paths:
        if os.path.exists(path):
            found_installations.append(path)
            print(f"✅ Found Webots at: {path}")
    
    # Check if webots is in PATH
    try:
        result = subprocess.run(['webots', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ Webots found in system PATH")
            found_installations.append("webots (in PATH)")
    except:
        pass
    
    if found_installations:
        print(f"\n🎉 Webots installation found! ({len(found_installations)} location(s))")
        print("\n📋 Installation Details:")
        for i, installation in enumerate(found_installations, 1):
            print(f"  {i}. {installation}")
        return True
    else:
        print("❌ No Webots installation found")
        return False

def show_installation_guide():
    """Show Webots installation guide"""
    
    print("\n📥 Webots Installation Guide")
    print("=" * 50)
    print("🌐 Webots Official Website: https://cyberbotics.com/")
    print()
    print("📋 Installation Steps:")
    print("1. Visit: https://cyberbotics.com/doc/guide/installation")
    print("2. Download Webots for Windows")
    print("3. Run the installer with administrator privileges")
    print("4. Follow the installation wizard")
    print("5. Restart this script to verify installation")
    print()
    print("💻 System Requirements:")
    print("• Windows 10/11 (64-bit)")
    print("• 4GB RAM minimum (8GB recommended)")
    print("• DirectX 11 compatible graphics card")
    print("• 2GB free disk space")
    print()
    print("🔧 Recommended Settings:")
    print("• Install to default location: C:\\Program Files\\Webots")
    print("• Add Webots to system PATH (checkbox during installation)")
    print("• Install all components (C++/Python/Java/MATLAB)")

def check_python_dependencies():
    """Check if required Python packages are installed"""
    
    print("\n🐍 Checking Python Dependencies...")
    print("=" * 50)
    
    required_packages = {
        'PyQt5': 'PyQt5>=5.15.0',
        'google-generativeai': 'google-generativeai>=0.3.0',
        'speech_recognition': 'speech_recognition>=3.10.0',
        'pyttsx3': 'pyttsx3>=2.90',
        'numpy': 'numpy>=1.24.0',
        'python-dotenv': 'python-dotenv>=1.0.0',
        'requests': 'requests>=2.31.0'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - installed")
        except ImportError:
            print(f"❌ {package} - missing")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\n⚠️  Missing {len(missing_packages)} package(s)")
        print("\n📦 To install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("\n🎉 All Python dependencies are installed!")
        return True

def setup_project_environment():
    """Set up the project environment"""
    
    print("\n🔧 Setting up Project Environment...")
    print("=" * 50)
    
    project_dir = Path(__file__).parent
    
    # Check .env file
    env_file = project_dir / '.env'
    env_example = project_dir / '.env.example'
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created")
            print("⚠️  Please edit .env and add your GEMINI_API_KEY")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    elif env_file.exists():
        print("✅ .env file exists")
    
    # Check worlds directory
    worlds_dir = project_dir / 'worlds'
    if worlds_dir.exists():
        print("✅ Webots worlds directory exists")
        
        automobile_world = worlds_dir / 'automobile.wbt'
        if automobile_world.exists():
            print("✅ automobile.wbt world file exists")
        else:
            print("⚠️  automobile.wbt world file missing")
    else:
        print("❌ Webots worlds directory missing")
    
    # Check controllers directory
    controllers_dir = project_dir / 'controllers'
    if controllers_dir.exists():
        print("✅ Webots controllers directory exists")
    else:
        print("❌ Webots controllers directory missing")

def run_setup_wizard():
    """Run the complete setup wizard"""
    
    print("🚗 Voice Commander - Webots Setup Wizard")
    print("=" * 60)
    print("This wizard will help you set up Webots for the Voice Commander project")
    print()
    
    # Step 1: Check Webots
    webots_installed = check_webots_installation()
    
    if not webots_installed:
        show_installation_guide()
        
        print("\n❓ Would you like to:")
        print("1. Open Webots download page")
        print("2. Continue without Webots (limited functionality)")
        print("3. Exit and install manually")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print("🌐 Opening Webots download page...")
            webbrowser.open('https://cyberbotics.com/doc/guide/installation')
            print("Please install Webots and run this script again.")
            return False
        elif choice == '2':
            print("⚠️  Continuing without Webots - overlay will work but simulation won't start")
        else:
            print("👋 Please install Webots and run this script again")
            return False
    
    # Step 2: Check Python dependencies
    print()
    deps_ok = check_python_dependencies()
    
    if not deps_ok:
        print("\n❓ Would you like to install missing dependencies now? (y/n): ", end="")
        install_deps = input().strip().lower()
        
        if install_deps in ['y', 'yes']:
            print("📦 Installing dependencies...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                             check=True)
                print("✅ Dependencies installed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
                return False
        else:
            print("⚠️  Please install dependencies manually before running the application")
    
    # Step 3: Set up project environment
    print()
    setup_project_environment()
    
    # Final summary
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("📋 Next Steps:")
    print("1. Edit .env file and add your GEMINI_API_KEY")
    print("2. Run the application: python test_overlay.py")
    print("3. Click 'Start Webots' in the overlay interface")
    print("4. Control the vehicle using AI commands or manual controls")
    print()
    print("🆘 Need help? Check the README.md file for detailed instructions")
    
    return True

def main():
    """Main setup function"""
    
    try:
        success = run_setup_wizard()
        
        if success:
            print("\n❓ Would you like to start the Voice Commander application now? (y/n): ", end="")
            start_app = input().strip().lower()
            
            if start_app in ['y', 'yes']:
                print("🚀 Starting Voice Commander...")
                try:
                    subprocess.run([sys.executable, 'test_overlay.py'])
                except KeyboardInterrupt:
                    print("\n👋 Application closed")
                except Exception as e:
                    print(f"❌ Failed to start application: {e}")
    
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
