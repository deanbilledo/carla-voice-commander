"""
Logging utilities for CARLA Voice Commander
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config import Config

class Logger:
    """Centralized logging utility"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        if cls._configured:
            return
        
        # Create logs directory if it doesn't exist
        Config.LOGS_DIR.mkdir(exist_ok=True)
        
        # Configure root logger
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Create formatter
        formatter = logging.Formatter(log_format, date_format)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # File handler
        log_file = Config.LOGS_DIR / f"carla_voice_commander_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name):
        """Get a logger instance for the given name"""
        if not cls._configured:
            cls.setup_logging()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]

# Setup logging when module is imported
Logger.setup_logging()
