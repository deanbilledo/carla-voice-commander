"""
Configuration module for CARLA Voice Commander
Loads environment variables and application settings
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    
    # CARLA Settings
    CARLA_HOST = os.getenv('CARLA_HOST', 'localhost')
    CARLA_PORT = int(os.getenv('CARLA_PORT', 2000))
    
    # Debug and Logging
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Voice Settings
    VOICE_LANGUAGE = os.getenv('VOICE_LANGUAGE', 'en-US')
    TTS_ENGINE = os.getenv('TTS_ENGINE', 'pyttsx3')
    SPEECH_RECOGNITION_TIMEOUT = int(os.getenv('SPEECH_RECOGNITION_TIMEOUT', 5))
    
    # AI Control Settings
    MAX_SPEED = float(os.getenv('MAX_SPEED', 50.0))
    SAFETY_DISTANCE = float(os.getenv('SAFETY_DISTANCE', 5.0))
    REACTION_TIME = float(os.getenv('REACTION_TIME', 0.5))
    
    # Dashboard Settings
    DASHBOARD_WIDTH = int(os.getenv('DASHBOARD_WIDTH', 1200))
    DASHBOARD_HEIGHT = int(os.getenv('DASHBOARD_HEIGHT', 800))
    MAP_UPDATE_RATE = int(os.getenv('MAP_UPDATE_RATE', 30))
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent
    LOGS_DIR = PROJECT_ROOT / 'logs'
    DATA_DIR = PROJECT_ROOT / 'data'
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration values"""
        if not cls.GOOGLE_API_KEY:
            print("WARNING: GOOGLE_API_KEY is not set. Please add it to your .env file.")
        
        # Create necessary directories
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        
        return True

# Validate configuration on import (with error handling)
try:
    Config.validate_config()
except Exception as e:
    print(f"Configuration warning: {e}")
