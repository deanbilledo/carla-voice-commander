# 🚗 Voice Commander - Webots Setup Guide

## Quick Installation Status ✅

**Python Dependencies:** ✅ All installed
- google-generativeai: ✅ v0.8.5
- PyQt5: ✅ Installed
- Other dependencies: ✅ Available

**Webots Simulator:** ❌ Not installed

## 📥 Install Webots (Required for 3D Simulation)

### Option 1: Direct Download (Recommended)
1. **Visit:** https://cyberbotics.com/doc/guide/installation
2. **Download:** Webots R2023b for Windows (64-bit)
3. **Install:** Run installer as Administrator
4. **Important:** Check "Add to PATH" during installation

### Option 2: Package Manager
```powershell
# Using Chocolatey (if you have it)
choco install webots

# Using Winget (Windows 11)
winget install Cyberbotics.Webots
```

### Installation Verification
After installation, run:
```powershell
python setup_webots.py
```

## 🚀 Quick Start (Current Status)

### What Works Now:
✅ **Overlay Interface** - Transparent control panels  
✅ **AI Integration** - Gemini AI command processing  
✅ **Voice Recognition** - Speech-to-text commands  

### After Installing Webots:
✅ **3D Simulation** - Realistic vehicle physics  
✅ **Sensor Data** - GPS, camera, distance sensors  
✅ **World Environments** - Pre-built driving scenarios  

## 🎮 Usage Instructions

### 1. Start the Application
```powershell
python test_overlay.py
```

### 2. Control Options
- **AI Commands:** "drive forward", "turn left", "stop"
- **Manual Controls:** WASD keys or GUI buttons
- **Voice Commands:** Click microphone button and speak

### 3. Webots Integration
- Click "Start Webots" button (after installation)
- Select automobile.wbt world file
- Control vehicle through overlay interface

## 🔧 Configuration

### API Keys (.env file)
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Webots Settings
- **Default World:** `worlds/automobile.wbt`
- **Controller:** `controllers/webots_controller/`
- **Installation Path:** Auto-detected from multiple locations

## 📁 Project Structure
```
carla-voice-commander/
├── webots_overlay.py          # Main overlay interface
├── webots_controller.py       # Vehicle controller
├── test_overlay.py           # Test runner
├── setup_webots.py          # Installation wizard
├── worlds/
│   └── automobile.wbt       # Webots world file
├── controllers/
│   └── webots_controller/   # Controller files
└── requirements.txt         # Dependencies
```

## 🆘 Troubleshooting

### "Webots not found" Error
1. Ensure Webots is installed in standard location
2. Add Webots to system PATH
3. Restart terminal/application

### Voice Recognition Issues
1. Check microphone permissions
2. Install speech_recognition: `pip install speech_recognition`
3. Test with: `python -c "import speech_recognition; print('OK')"`

### GUI Display Issues
1. Update graphics drivers
2. Install PyQt5: `pip install PyQt5>=5.15.0`
3. Run as Administrator if needed

## 🎯 Next Steps

1. **Install Webots** for full 3D simulation
2. **Configure API key** in .env file  
3. **Test with voice commands** using microphone
4. **Explore world files** and create custom scenarios

---
**Status:** Ready to use with overlay interface! Install Webots for full 3D simulation.
