# 🚗 CARLA Voice Commander

A real-time, voice-controlled autonomous vehicle simulation system built on the CARLA Simulator and integrated with Google Gemini AI.

## 🛠️ Project Overview

CARLA Voice Commander is an intelligent driving assistant that uses natural language understanding to control a simulated vehicle. The system toggles between manual, AI, and voice control modes while simulating automotive realism via a RAMN CAN protocol.

## 📦 Features & Capabilities

- **Control Modes**: Manual → AI → Voice (via speech recognition and Gemini)
- **Gemini AI Integration**: Natural language understanding for driving commands
- **CARLA Simulator**: High-fidelity driving environment with vehicle physics and sensors
- **CAN Bus Support**: Simulated RAMN CAN protocol with ECUs and CAN message types
- **PyQt5 Dashboard**: Interactive UI with vehicle status, map, and command log
- **Speech Interface**: Convert voice to text and respond using TTS
- **AI Planning**: A* pathfinding, behavior control, and traffic interaction

## 🧩 File Structure

```
carla-voice-commander/
├── main.py                 # Entry point for the app
├── config.py               # Loads environment + settings
├── gemini_agent.py         # Gemini API interface
├── carla_interface.py      # Connects to CARLA + vehicle control
├── ui_dashboard.py         # PyQt5 UI dashboard
├── .env                    # API keys and runtime settings
├── requirements.txt        # Dependencies
├── voice/                  # Voice recognition and synthesis
├── ai_control/             # AI driving logic
├── navigation/             # Route and location planning
├── nlp/                    # Intent classification and command parsing
├── ramn/                   # CAN bus simulation (RAMN protocol)
├── utils/                  # Logging and helpers
└── tests/                  # Unit tests
```

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables**
   Copy `.env.example` to `.env` and add your API keys:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   CARLA_HOST=localhost
   CARLA_PORT=2000
   DEBUG_MODE=True
   LOG_LEVEL=INFO
   ```

3. **Start CARLA Simulator**
   ```bash
   # Run CARLA simulator (assuming CARLA is installed)
   CarlaUE4.exe -windowed -ResX=800 -ResY=600
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

## 🎯 Voice Commands Examples

- "Drive to the nearest gas station"
- "Park the car"
- "Follow that blue car"
- "Stop at the next traffic light"
- "Turn left at the intersection"

## 🧠 AI Agent Behavior

The Gemini agent operates as a helpful and safe driving assistant that:

- Interprets voice commands and translates them into control instructions
- Asks clarifying questions for ambiguous commands
- Maintains awareness of vehicle status, environment, and traffic
- Provides clear, informative responses with a polite tone

## 📋 Requirements

- Python 3.8+
- CARLA Simulator 0.9.13+
- Google API Key for Gemini
- PyQt5 for UI
- Speech recognition libraries

## 🛡️ Safety Features

- Emergency stop commands
- Speed limit enforcement
- Traffic rule compliance
- Collision avoidance

## 📝 License

MIT License - see LICENSE file for details.
