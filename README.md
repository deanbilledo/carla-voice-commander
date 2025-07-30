# 🚗 Voice Commander - Webots Edition

AI-powered vehicle control system with 3D simulation using Webots.

## 🚀 Quick Start

1. **Install Webots**: Download from https://cyberbotics.com/
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Run Application**: `python test_overlay.py`
4. **Start Webots**: Click "Start Webots" in overlay
5. **Control Vehicle**: Use buttons or voice commands

## ✅ **FIXES APPLIED - WEBOTS SAMPLE VEHICLE**

### 🚗 **Using Webots Sample Car**
- ✅ **BmwX5 from Webots samples** - Professional vehicle model with realistic physics
- ✅ **Proper ground placement** - Vehicle positioned correctly on road surface
- ✅ **Working sensors** - GPS, compass, camera integrated properly
- ✅ **Vehicle library** - Uses Webots native vehicle controller library
- ✅ **Fixed JSON errors** - Robust command file parsing with error handling
- ✅ **Sensor optimization** - Removed undefined sensors to prevent warnings
- ✅ **Cleaned project** - Removed all non-working worlds and controllers

### 🎨 **UI/UX Improvements**
- ✅ **Better button layout** - No more overlapping buttons
- ✅ **Improved spacing** - Proper margins and padding throughout
- ✅ **Larger controls** - Easier to click and use
- ✅ **Organized sections** - Grouped controls with clear labels
- ✅ **Enhanced styling** - Professional appearance with better colors
- ✅ **Responsive design** - Proper sizing for all UI elements

### 🎨 **Rendering Issues Fixed**
- ✅ **Improved viewpoint** - Better camera angle and follow mode
- ✅ **Enhanced lighting** - Added proper directional light with shadows
- ✅ **Visual landmarks** - Added colored cubes for reference
- ✅ **Ground texture** - Green ground instead of gray

### 📊 **Vehicle Status Fixed**
- ✅ **Real-time updates** - Status updates every 100ms
- ✅ **File communication** - Status written to `commands/vehicle_status.json`
- ✅ **Live data** - Position, speed, gear, orientation tracking

### 🎮 **Vehicle Control Fixed**
- ✅ **Command communication** - Commands sent via `commands/current_command.json`
- ✅ **Motor control** - Proper differential steering
- ✅ **Responsive movement** - Forward/backward/turn/stop commands work

## 🎯 **Current Features**

### 🖥️ **Overlay Interface**
- **Clean white background** - Easy to read with improved contrast
- **Non-overlapping buttons** - Proper spacing and layout
- **Control sections** - Organized into logical groups
- **Better sizing** - Larger buttons and text for easier use
- **Status display** - Real-time vehicle information in dedicated window
- **Always on top** - Stays visible over Webots
- **Draggable windows** - Position overlays where you want them

### 🤖 **AI Integration**
- **Google Gemini AI** - Natural language command processing
- **Voice commands** - Speech-to-text integration
- **Smart responses** - Context-aware vehicle control

### 🌍 **Webots Simulation**
- **BmwX5 sample vehicle** - Professional grade vehicle model
- **Highway environment** - Clean road layout with proper physics
- **Sensor integration** - GPS, camera, compass, distance sensors
- **Real-time visualization** - Follow camera mode

## 🔧 **Troubleshooting**

### **Purple Background / No Rendering**
```bash
# 1. Check Webots installation
webots --version

# 2. Verify world file exists
ls worlds/highway_bmw.wbt

# 3. Restart with clean world
# Close Webots completely, then restart via overlay
```

### **Vehicle Not Moving**
```bash
# 1. Check command files are being created
ls commands/

# 2. Verify controller is running
# Look for "BmwX5 Vehicle Controller initialized" in Webots console

# 3. Check file permissions
# Ensure commands/ directory is writable

# 4. Test command system
python test_commands.py
```

### **Status Not Updating**
```bash
# 1. Check status file is being written
ls commands/vehicle_status.json

# 2. Verify timer is running
# Should see updates every 100ms in overlay

# 3. Restart overlay if frozen
python test_overlay.py
```

## 📁 **Project Structure**
```
carla-voice-commander/
├── webots_overlay.py           # Main overlay interface (improved UI)
├── test_overlay.py            # Application launcher
├── test_setup.py              # Setup verification script
├── test_commands.py           # Command system test script
├── worlds/
│   └── highway_bmw.wbt        # Main BmwX5 highway world (only working world)
├── controllers/
│   └── bmw_controller/        # BmwX5 vehicle controller (only working controller)
├── commands/                  # Communication files
│   ├── current_command.json   # Commands to vehicle
│   └── vehicle_status.json    # Status from vehicle
└── requirements.txt           # Dependencies
```

## 🎮 **Usage**

### **Manual Control**
1. Click "Start Webots" in overlay
2. Use arrow-like buttons to control vehicle
3. Watch Webots window for movement

### **Voice Control**
1. Click microphone button in overlay
2. Say commands like:
   - "Move forward"
   - "Turn left"
   - "Stop the car"
   - "Go faster"

### **AI Commands**
1. Type in command box: "Drive to the red landmark"
2. AI will interpret and execute appropriate actions

## 🔍 **Monitoring**

### **Vehicle Status Display**
- **Position**: (X, Y) coordinates
- **Speed**: Current speed in km/h
- **Heading**: Orientation in degrees
- **Gear**: Current gear (P/D/R)
- **Connection**: Webots connection status

### **Debug Output**
- Commands appear in terminal
- Vehicle status updates in real-time
- Error messages for troubleshooting

## 🌟 **Next Steps**

- **Add more vehicles** - Multi-vehicle simulation
- **Enhanced AI** - More complex commands
- **Better graphics** - Improved world environments
- **Autonomous features** - Path planning and obstacle avoidance

---
**Status**: ✅ Updated to use Webots sample BmwX5 vehicle - Professional grade simulation ready!
