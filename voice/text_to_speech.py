"""
Text-to-speech synthesis module
"""

import pyttsx3
import threading
import queue
from config import Config
from utils.logger import Logger

class TextToSpeech:
    """Text-to-speech handler"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.engine = None
        self.speech_queue = queue.Queue()
        self.is_running = False
        self.speech_thread = None
        
        self._initialize_engine()
        self._start_speech_thread()
    
    def _initialize_engine(self):
        """Initialize the TTS engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to find a female voice, fallback to first available
                female_voice = None
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        female_voice = voice
                        break
                
                if female_voice:
                    self.engine.setProperty('voice', female_voice.id)
                else:
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 200)  # Speed of speech
            self.engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)
            
            self.logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def _start_speech_thread(self):
        """Start the speech processing thread"""
        self.is_running = True
        self.speech_thread = threading.Thread(target=self._speech_loop)
        self.speech_thread.daemon = True
        self.speech_thread.start()
    
    def _speech_loop(self):
        """Main speech processing loop"""
        while self.is_running:
            try:
                # Get text from queue with timeout
                text = self.speech_queue.get(timeout=1)
                
                if text and self.engine:
                    self.logger.info(f"Speaking: {text}")
                    self.engine.say(text)
                    self.engine.runAndWait()
                
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in speech loop: {e}")
    
    def speak(self, text, priority=False):
        """
        Add text to speech queue
        
        Args:
            text (str): Text to speak
            priority (bool): If True, add to front of queue
        """
        if not text or not self.engine:
            return
        
        try:
            if priority:
                # Clear queue and add high priority message
                while not self.speech_queue.empty():
                    try:
                        self.speech_queue.get_nowait()
                        self.speech_queue.task_done()
                    except queue.Empty:
                        break
            
            self.speech_queue.put(text)
            self.logger.debug(f"Added to speech queue: {text}")
            
        except Exception as e:
            self.logger.error(f"Failed to queue speech: {e}")
    
    def speak_immediate(self, text):
        """Speak text immediately (blocking)"""
        if not text or not self.engine:
            return
        
        try:
            self.logger.info(f"Speaking immediately: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
            
        except Exception as e:
            self.logger.error(f"Failed to speak immediately: {e}")
    
    def stop_speaking(self):
        """Stop current speech and clear queue"""
        try:
            if self.engine:
                self.engine.stop()
            
            # Clear the queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
            
            self.logger.info("Stopped speaking and cleared queue")
            
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")
    
    def get_available_voices(self):
        """Get list of available voices"""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown')
                }
                voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            self.logger.error(f"Error getting voices: {e}")
            return []
    
    def set_voice(self, voice_id):
        """Set the voice by ID"""
        if not self.engine:
            return False
        
        try:
            self.engine.setProperty('voice', voice_id)
            self.logger.info(f"Voice changed to: {voice_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set voice: {e}")
            return False
    
    def cleanup(self):
        """Cleanup TTS resources"""
        try:
            self.is_running = False
            self.stop_speaking()
            
            if self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=2)
            
            if self.engine:
                self.engine.stop()
            
            self.logger.info("TTS cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during TTS cleanup: {e}")

# Example usage
if __name__ == "__main__":
    tts = TextToSpeech()
    
    # Test immediate speech
    tts.speak_immediate("Hello, I am your CARLA voice assistant.")
    
    # Test queued speech
    tts.speak("This is the first message.")
    tts.speak("This is the second message.")
    tts.speak("This is the third message.")
    
    # Wait for speech to complete
    import time
    time.sleep(10)
    
    # Test priority speech
    tts.speak("Emergency stop!", priority=True)
    
    time.sleep(3)
    tts.cleanup()
