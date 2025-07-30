"""
Setup CARLA for Voice Commander
Automated CARLA installation and configuration for enhanced 3D simulation
"""

import sys
import os
import subprocess
import glob
from pathlib import Path

def find_carla_installation():
    """Find CARLA installation directory"""
    possible_paths = [
        r"C:\Carla-0.10.0-Win64-Shipping",
        r"C:\CARLA_0.9.15",
        r"C:\UnrealEngine\CARLA",
        r"D:\Carla-0.10.0-Win64-Shipping",
        r"D:\CARLA",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def setup_carla_python_path():
    """Setup CARLA Python path"""
    carla_path = find_carla_installation()
    
    if not carla_path:
        print("❌ CARLA installation not found!")
        print("Please install CARLA from: https://github.com/carla-simulator/carla/releases")
        return False
    
    print(f"✅ Found CARLA at: {carla_path}")
    
    # Add to Python path
    python_api_path = os.path.join(carla_path, "PythonAPI", "carla")
    
    if python_api_path not in sys.path:
        sys.path.insert(0, python_api_path)
    
    # Try to find and install wheel
    dist_path = os.path.join(python_api_path, "dist")
    if os.path.exists(dist_path):
        wheel_files = glob.glob(os.path.join(dist_path, "*.whl"))
        
        if wheel_files:
            print(f"📦 Found {len(wheel_files)} wheel file(s)")
            
            # Try to install the most compatible wheel
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            print(f"🐍 Current Python version: {python_version}")
            
            # Find best wheel match
            best_wheel = None
            for wheel in wheel_files:
                if "cp38" in wheel or "cp39" in wheel or "cp310" in wheel or "cp311" in wheel:
                    best_wheel = wheel
                    break
            
            if best_wheel:
                try:
                    print(f"🔧 Installing CARLA wheel: {os.path.basename(best_wheel)}")
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", best_wheel, 
                        "--force-reinstall", "--no-deps"
                    ], check=True)
                    print("✅ CARLA wheel installed successfully!")
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ Wheel installation failed: {e}")
                    print("🔄 Adding CARLA path directly...")
                    return add_carla_to_path(python_api_path)
            else:
                print("⚠️ No compatible wheel found for current Python version")
                return add_carla_to_path(python_api_path)
        else:
            print("⚠️ No wheel files found")
            return add_carla_to_path(python_api_path)
    else:
        print("⚠️ CARLA dist directory not found")
        return add_carla_to_path(python_api_path)

def add_carla_to_path(carla_path):
    """Add CARLA directly to Python path"""
    if os.path.exists(carla_path):
        sys.path.insert(0, carla_path)
        print(f"✅ Added CARLA path: {carla_path}")
        return True
    return False

def test_carla_import():
    """Test CARLA import"""
    try:
        import carla
        print("✅ CARLA imported successfully!")
        print(f"📦 CARLA version: {carla.version}")
        return True
    except ImportError as e:
        print(f"❌ CARLA import failed: {e}")
        return False

def check_carla_server():
    """Check if CARLA server is running"""
    try:
        import carla
        client = carla.Client('localhost', 2000)
        client.set_timeout(5.0)
        world = client.get_world()
        print("✅ CARLA server is running!")
        return True
    except Exception as e:
        print(f"⚠️ CARLA server not accessible: {e}")
        print("💡 Start CARLA server with: CarlaUE4.exe")
        return False

def create_carla_startup_script():
    """Create CARLA startup script"""
    carla_path = find_carla_installation()
    if not carla_path:
        return
    
    carla_exe = os.path.join(carla_path, "CarlaUE4.exe")
    if not os.path.exists(carla_exe):
        carla_exe = os.path.join(carla_path, "CarlaUE4", "Binaries", "Win64", "CarlaUE4.exe")
    
    if os.path.exists(carla_exe):
        script_content = f'''@echo off
echo Starting CARLA Server...
echo CARLA will start in windowed mode with optimal settings
echo Close this window to stop CARLA
cd /d "{carla_path}"
"{carla_exe}" -windowed -ResX=1280 -ResY=720 -quality-level=Low
pause
'''
        script_path = os.path.join(os.getcwd(), "start_carla.bat")
        with open(script_path, 'w') as f:
            f.write(script_content)
        print(f"✅ Created CARLA startup script: {script_path}")
        print("💡 Run 'start_carla.bat' to start CARLA server")

def main():
    """Main setup function"""
    print("🚗 CARLA Voice Commander Setup")
    print("=" * 40)
    
    print("\n1. Searching for CARLA installation...")
    if not setup_carla_python_path():
        print("❌ CARLA setup failed!")
        return False
    
    print("\n2. Testing CARLA import...")
    if not test_carla_import():
        print("❌ CARLA import test failed!")
        print("🔄 Trying alternative setup...")
        
        # Try direct path setup
        carla_path = find_carla_installation()
        if carla_path:
            python_api = os.path.join(carla_path, "PythonAPI", "carla")
            if add_carla_to_path(python_api):
                if test_carla_import():
                    print("✅ Alternative setup successful!")
                else:
                    print("❌ Alternative setup failed!")
                    return False
    
    print("\n3. Checking CARLA server...")
    check_carla_server()
    
    print("\n4. Creating startup script...")
    create_carla_startup_script()
    
    print("\n🎉 CARLA setup complete!")
    print("\nNext steps:")
    print("1. Run 'start_carla.bat' to start CARLA server")
    print("2. Run 'python carla_3d_simulation.py' for full 3D simulation")
    print("3. Enjoy the enhanced CARLA experience!")
    
    return True

if __name__ == "__main__":
    main()
    
    def get_download_info(self):
        """Get CARLA download information based on system"""
        base_url = f"https://github.com/carla-simulator/carla/releases/download/{self.carla_version}"
        
        if self.system == "windows":
            simulator_file = f"CARLA_{self.carla_version}.zip"
            if "38" in self.python_version:
                wheel_file = f"carla-{self.carla_version}-py3.8-win-amd64.whl"
            elif "39" in self.python_version:
                wheel_file = f"carla-{self.carla_version}-py3.9-win-amd64.whl"
            elif "310" in self.python_version or "3.10" in self.python_version:
                wheel_file = f"carla-{self.carla_version}-py3.10-win-amd64.whl"
            elif "311" in self.python_version or "3.11" in self.python_version:
                wheel_file = f"carla-{self.carla_version}-py3.11-win-amd64.whl"
            else:
                wheel_file = f"carla-{self.carla_version}-py3.8-win-amd64.whl"  # fallback
        elif self.system == "linux":
            simulator_file = f"CARLA_{self.carla_version}.tar.gz"
            wheel_file = f"carla-{self.carla_version}-py3.7-linux-x86_64.whl"
        else:
            print(f"❌ Unsupported system: {self.system}")
            return None, None
        
        return f"{base_url}/{wheel_file}", f"{base_url}/{simulator_file}"
    
    def install_carla_wheel(self):
        """Install CARLA Python API"""
        wheel_url, _ = self.get_download_info()
        if not wheel_url:
            return False
        
        print(f"📥 Installing CARLA Python API from: {wheel_url}")
        
        try:
            # Install directly from URL
            subprocess.run([
                sys.executable, "-m", "pip", "install", wheel_url
            ], check=True)
            
            print("✅ CARLA Python API installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install CARLA wheel: {e}")
            return False
    
    def download_carla_simulator(self, install_dir="C:\\CARLA"):
        """Download and extract CARLA simulator"""
        _, simulator_url = self.get_download_info()
        if not simulator_url:
            return False
        
        print(f"📥 Downloading CARLA simulator from: {simulator_url}")
        print(f"📂 Install directory: {install_dir}")
        
        # Create install directory
        Path(install_dir).mkdir(parents=True, exist_ok=True)
        
        # Download file
        filename = simulator_url.split("/")[-1]
        filepath = os.path.join(install_dir, filename)
        
        try:
            response = requests.get(simulator_url, stream=True)
            response.raise_for_status()
            
            file_size = int(response.headers.get('content-length', 0))
            print(f"📊 File size: {file_size / (1024*1024*1024):.1f} GB")
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if file_size > 0:
                            percent = (downloaded / file_size) * 100
                            print(f"\\r📊 Progress: {percent:.1f}%", end="", flush=True)
            
            print("\\n✅ Download complete")
            
            # Extract archive
            print("📦 Extracting CARLA simulator...")
            if filename.endswith('.zip'):
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(install_dir)
            else:
                # For tar.gz files
                import tarfile
                with tarfile.open(filepath, 'r:gz') as tar_ref:
                    tar_ref.extractall(install_dir)
            
            # Remove archive file
            os.remove(filepath)
            
            print(f"✅ CARLA simulator extracted to: {install_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download/extract CARLA: {e}")
            return False
    
    def create_start_script(self, carla_dir="C:\\CARLA"):
        """Create a script to start CARLA easily"""
        if self.system == "windows":
            script_content = f'''@echo off
echo Starting CARLA Simulator...
cd /d "{carla_dir}"
CarlaUE4.exe -windowed -ResX=1280 -ResY=720 -quality-level=Low
pause
'''
            script_path = os.path.join(os.getcwd(), "start_carla.bat")
        else:
            script_content = f'''#!/bin/bash
echo "Starting CARLA Simulator..."
cd "{carla_dir}"
./CarlaUE4.sh -windowed -ResX=1280 -ResY=720 -quality-level=Low
'''
            script_path = os.path.join(os.getcwd(), "start_carla.sh")
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        if self.system != "windows":
            os.chmod(script_path, 0o755)
        
        print(f"✅ Start script created: {script_path}")
        return script_path
    
    def run_installation(self, full_install=True):
        """Run the complete installation process"""
        print("🚗 CARLA Installation Helper")
        print("=" * 50)
        
        # Check current installation
        if self.check_carla_installation():
            print("✅ CARLA Python API already installed")
        else:
            print("📦 Installing CARLA Python API...")
            if not self.install_carla_wheel():
                print("❌ Failed to install CARLA Python API")
                return False
        
        if full_install:
            print("\\n📥 Installing CARLA Simulator...")
            install_dir = input("📂 Install directory (default: C:\\CARLA): ").strip()
            if not install_dir:
                install_dir = "C:\\CARLA"
            
            if not self.download_carla_simulator(install_dir):
                print("❌ Failed to install CARLA simulator")
                return False
            
            # Create start script
            self.create_start_script(install_dir)
        
        print("\\n✅ Installation complete!")
        print("\\n📋 Next steps:")
        print("1. Start CARLA simulator using start_carla.bat")
        print("2. Run the demo: python carla_demo.py")
        print("3. Enjoy controlling vehicles with voice commands!")
        
        return True

def quick_setup():
    """Quick setup function"""
    installer = CarlaInstaller()
    
    print("🚗 CARLA Voice Commander Setup")
    print("=" * 40)
    print("This will install CARLA for vehicle simulation.")
    print("\\nOptions:")
    print("1. Install CARLA Python API only (for development)")
    print("2. Full installation (API + Simulator ~4GB)")
    print("3. Check current installation")
    
    choice = input("\\nChoose option (1-3): ").strip()
    
    if choice == "1":
        installer.install_carla_wheel()
    elif choice == "2":
        installer.run_installation(full_install=True)
    elif choice == "3":
        installer.check_carla_installation()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    quick_setup()
