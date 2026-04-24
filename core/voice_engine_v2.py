"""
JARVIS Voice Engine V2 - Non-blocking with Wake Word Detection
Handles missing PyAudio gracefully, uses threading for async operation
"""

import threading
import queue
import time
import logging
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import speech recognition
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    logger.warning("SpeechRecognition not available")

# Try to import PyAudio
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available - voice input disabled")

# Try to import TTS
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not available - speech output disabled")

class VoiceState(Enum):
    """Voice engine states"""
    IDLE = "idle"
    LISTENING_WAKE = "listening_wake"
    LISTENING_COMMAND = "listening_command"
    PROCESSING = "processing"
    SPEAKING = "speaking"

@dataclass
class VoiceCommand:
    """Voice command structure"""
    text: str
    timestamp: float
    confidence: float = 0.0
    is_wake_word: bool = False

class VoiceEngineV2:
    """Non-blocking voice engine with wake word detection"""
    
    def __init__(self, 
                 wake_word: str = "hey jarvis",
                 language: str = "en-US",
                 energy_threshold: int = 300,
                 pause_threshold: float = 0.8):
        
        self.wake_word = wake_word.lower()
        self.language = language
        self.energy_threshold = energy_threshold
        self.pause_threshold = pause_threshold
        
        # State management
        self.state = VoiceState.IDLE
        self.running = False
        
        # Audio components
        self.recognizer: Optional[sr.Recognizer] = None
        self.microphone: Optional[sr.Microphone] = None
        self.tts_engine: Optional[pyttsx3.Engine] = None
        
        # Threading
        self.audio_queue = queue.Queue(maxsize=10)
        self.command_queue = queue.Queue(maxsize=5)
        self.listen_thread: Optional[threading.Thread] = None
        self.process_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_wake_word: Optional[Callable] = None
        self.on_command: Optional[Callable[[str], None]] = None
        self.on_state_change: Optional[Callable[[VoiceState], None]] = None
        
        # Initialize
        self._init_components()
        
    def _init_components(self):
        """Initialize voice components with error handling"""
        # Initialize speech recognition
        if SPEECH_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = self.energy_threshold
                self.recognizer.pause_threshold = self.pause_threshold
                self.recognizer.dynamic_energy_threshold = True
                
                # Try to initialize microphone
                if PYAUDIO_AVAILABLE:
                    try:
                        self.microphone = sr.Microphone()
                        logger.info("Microphone initialized")
                    except Exception as e:
                        logger.error(f"Microphone init failed: {e}")
                        self.microphone = None
                else:
                    logger.warning("PyAudio not available - microphone disabled")
                    self.microphone = None
                    
                logger.info("Speech recognizer initialized")
            except Exception as e:
                logger.error(f"Speech recognition init failed: {e}")
                self.recognizer = None
        
        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 180)
                self.tts_engine.setProperty('volume', 0.9)
                
                # Get available voices
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Try to use a male voice (Jarvis style)
                    for voice in voices:
                        if 'male' in voice.name.lower() or 'david' in voice.id.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                
                logger.info("TTS engine initialized")
            except Exception as e:
                logger.error(f"TTS init failed: {e}")
                self.tts_engine = None
    
    def start(self):
        """Start voice engine in non-blocking mode"""
        if self.running:
            return
            
        self.running = True
        self._set_state(VoiceState.LISTENING_WAKE)
        
        # Start background threads
        if self.recognizer and self.microphone:
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        logger.info("Voice engine started")
    
    def stop(self):
        """Stop voice engine"""
        self.running = False
        self._set_state(VoiceState.IDLE)
        
        # Signal threads to stop
        self.audio_queue.put(None)
        
        # Wait for threads
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=2)
            
        logger.info("Voice engine stopped")
    
    def _set_state(self, state: VoiceState):
        """Update state and trigger callback"""
        self.state = state
        if self.on_state_change:
            try:
                self.on_state_change(state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def _listen_loop(self):
        """Background thread: Listen for audio continuously"""
        logger.info("Listen thread started")
        
        while self.running:
            try:
                if not self.microphone:
                    time.sleep(0.5)
                    continue
                    
                with self.microphone as source:
                    # Adjust for ambient noise periodically
                    if self.state == VoiceState.LISTENING_WAKE:
                        try:
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        except:
                            pass
                    
                    # Listen for audio
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        self.audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        # No audio detected, continue listening
                        pass
                        
            except Exception as e:
                logger.error(f"Listen error: {e}")
                time.sleep(0.5)
                
        logger.info("Listen thread stopped")
    
    def _process_loop(self):
        """Background thread: Process audio and recognize speech"""
        logger.info("Process thread started")
        
        while self.running:
            try:
                # Get audio from queue (blocking with timeout)
                try:
                    audio = self.audio_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if audio is None:  # Stop signal
                    break
                
                # Recognize speech
                self._set_state(VoiceState.PROCESSING)
                text = self._recognize_speech(audio)
                
                if text:
                    text_lower = text.lower()
                    
                    # Check for wake word
                    if self.wake_word in text_lower:
                        logger.info(f"Wake word detected: {text}")
                        self._set_state(VoiceState.LISTENING_COMMAND)
                        
                        if self.on_wake_word:
                            try:
                                self.on_wake_word()
                            except Exception as e:
                                logger.error(f"Wake word callback error: {e}")
                        
                        # Listen for command after wake word
                        self._listen_for_command()
                    
                    elif self.state == VoiceState.LISTENING_COMMAND:
                        # This is a command
                        logger.info(f"Command received: {text}")
                        
                        if self.on_command:
                            try:
                                self.on_command(text)
                            except Exception as e:
                                logger.error(f"Command callback error: {e}")
                        
                        self._set_state(VoiceState.LISTENING_WAKE)
                        
            except Exception as e:
                logger.error(f"Process error: {e}")
                time.sleep(0.5)
                
        logger.info("Process thread stopped")
    
    def _recognize_speech(self, audio) -> Optional[str]:
        """Recognize speech from audio data"""
        if not self.recognizer:
            return None
            
        try:
            # Use Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text
        except sr.UnknownValueError:
            # Speech not understood
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
    
    def _listen_for_command(self, timeout: float = 5.0):
        """Listen for command after wake word"""
        if not self.microphone or not self.recognizer:
            return
            
        try:
            with self.microphone as source:
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                    
                    # Process immediately
                    text = self._recognize_speech(audio)
                    if text:
                        logger.info(f"Command after wake: {text}")
                        if self.on_command:
                            self.on_command(text)
                            
                except sr.WaitTimeoutError:
                    logger.info("No command after wake word")
                    
        except Exception as e:
            logger.error(f"Command listen error: {e}")
    
    def speak(self, text: str, block: bool = False):
        """Speak text. If block=False, runs in background thread"""
        if not self.tts_engine:
            logger.info(f"[TTS disabled] {text}")
            return
            
        if block:
            self._speak_sync(text)
        else:
            # Run in background thread
            thread = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
            thread.start()
    
    def _speak_sync(self, text: str):
        """Synchronous speech - runs in separate thread"""
        try:
            self._set_state(VoiceState.SPEAKING)
            
            # Check if engine is busy - if so, create a new one
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except RuntimeError as e:
                if "run loop already started" in str(e):
                    # Engine is busy, create new one
                    logger.debug("Creating new TTS engine instance")
                    self.tts_engine = pyttsx3.init()
                    self.tts_engine.setProperty('rate', 180)
                    self.tts_engine.setProperty('volume', 0.9)
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                else:
                    raise
            
            # Return to listening state
            if self.running:
                self._set_state(VoiceState.LISTENING_WAKE)
                
        except Exception as e:
            logger.error(f"Speech error: {e}")
    
    def calibrate_microphone(self, duration: float = 2.0):
        """Calibrate microphone for ambient noise"""
        if not self.microphone or not self.recognizer:
            logger.error("Cannot calibrate - microphone not available")
            return False
            
        try:
            with self.microphone as source:
                logger.info(f"Calibrating microphone for {duration}s...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                logger.info(f"Calibration complete. Energy threshold: {self.recognizer.energy_threshold}")
                return True
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return False
    
    def test_microphone(self) -> Dict:
        """Test microphone functionality"""
        result = {
            "available": False,
            "speech_recognition": SPEECH_AVAILABLE,
            "pyaudio": PYAUDIO_AVAILABLE,
            "tts": TTS_AVAILABLE,
            "error": None
        }
        
        if not self.microphone:
            result["error"] = "Microphone not initialized"
            return result
            
        try:
            with self.microphone as source:
                result["available"] = True
                result["sample_rate"] = self.microphone.SAMPLE_RATE if hasattr(self.microphone, 'SAMPLE_RATE') else "unknown"
                result["chunk_size"] = self.microphone.CHUNK if hasattr(self.microphone, 'CHUNK') else "unknown"
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def get_status(self) -> Dict:
        """Get voice engine status"""
        return {
            "state": self.state.value,
            "running": self.running,
            "speech_available": SPEECH_AVAILABLE,
            "pyaudio_available": PYAUDIO_AVAILABLE,
            "tts_available": TTS_AVAILABLE,
            "microphone_initialized": self.microphone is not None,
            "recognizer_initialized": self.recognizer is not None,
            "tts_initialized": self.tts_engine is not None
        }
