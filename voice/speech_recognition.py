"""
Speech recognition module for converting speech to text
"""

import speech_recognition as sr
import threading
import time
from config import Config
from utils.logger import Logger

class SpeechRecognizer:
    """Speech recognition handler"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.listen_thread = None
        self.callback = None
        
        # Calibrate microphone
        self._calibrate_microphone()
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                self.logger.info("Microphone calibration complete")
        except Exception as e:
            self.logger.error(f"Failed to calibrate microphone: {e}")
    
    def start_listening(self, callback):
        """Start continuous speech recognition"""
        if self.is_listening:
            self.logger.warning("Already listening")
            return
        
        self.callback = callback
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        self.logger.info("Started listening for speech")
    
    def stop_listening(self):
        """Stop continuous speech recognition"""
        self.is_listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        
        self.logger.info("Stopped listening for speech")
    
    def _listen_loop(self):
        """Main listening loop"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Recognize speech
                text = self._recognize_speech(audio)
                
                if text and self.callback:
                    self.callback(text)
                    
            except sr.WaitTimeoutError:
                # Timeout is normal, continue listening
                continue
            except Exception as e:
                self.logger.error(f"Error in listen loop: {e}")
                time.sleep(1)  # Brief pause before retrying
    
    def _recognize_speech(self, audio):
        """Recognize speech from audio data"""
        try:
            # Use Google Web Speech API
            text = self.recognizer.recognize_google(
                audio, 
                language=Config.VOICE_LANGUAGE
            )
            self.logger.info(f"Recognized speech: {text}")
            return text
            
        except sr.UnknownValueError:
            self.logger.debug("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return None
    
    def recognize_once(self):
        """Recognize speech once (blocking)"""
        try:
            with self.microphone as source:
                self.logger.info("Listening for command...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=Config.SPEECH_RECOGNITION_TIMEOUT,
                    phrase_time_limit=5
                )
            
            text = self._recognize_speech(audio)
            return text
            
        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timeout")
            return None
        except Exception as e:
            self.logger.error(f"Error in single recognition: {e}")
            return None

# Example usage
if __name__ == "__main__":
    def on_speech(text):
        print(f"Heard: {text}")
    
    recognizer = SpeechRecognizer()
    
    # Test single recognition
    print("Say something...")
    result = recognizer.recognize_once()
    print(f"Recognized: {result}")
    
    # Test continuous recognition
    recognizer.start_listening(on_speech)
    
    try:
        time.sleep(10)  # Listen for 10 seconds
    except KeyboardInterrupt:
        pass
    
    recognizer.stop_listening()
