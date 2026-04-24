"""
JARVIS Voice Engine - Advanced Voice Recognition and Synthesis
Optimized for i3 12GB RAM systems with efficient processing
"""

import speech_recognition as sr
import pyttsx3
import numpy as np
import threading
import queue
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json
import time

@dataclass
class VoiceConfig:
    """Voice engine configuration"""
    wake_word: str = "Hey JARVIS"
    sensitivity: float = 0.8
    voice_speed: float = 1.0
    voice_volume: float = 0.9
    language: str = "en-US"
    noise_reduction: bool = True

class VoiceEngine:
    """Advanced voice recognition and synthesis engine"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self._configure_tts()
        
        # Audio processing queues
        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Wake word detection
        self.wake_word_detected = False
        self.listening_active = False
        
        # Background threads
        self.listening_thread = None
        self.processing_thread = None
        
        # Callbacks
        self.on_command_received: Optional[Callable] = None
        self.on_wake_word_detected: Optional[Callable] = None
        
        # Performance optimization
        self.audio_buffer = np.zeros(1024, dtype=np.float32)
        self.noise_floor = 0.0
        
    def _configure_tts(self):
        """Configure text-to-speech engine"""
        voices = self.tts_engine.getProperty('voices')
        
        # Select best voice (prefer male, professional)
        for voice in voices:
            if 'male' in voice.gender.lower() or 'david' in voice.id.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Set voice properties
        self.tts_engine.setProperty('rate', int(200 * self.config.voice_speed))
        self.tts_engine.setProperty('volume', self.config.voice_volume)
        
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        self.logger.info("Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        self.logger.info("Microphone calibration complete")
        
    def start_listening(self):
        """Start continuous listening for wake word and commands"""
        if self.listening_active:
            return
            
        self.listening_active = True
        self.calibrate_microphone()
        
        # Start background threads
        self.listening_thread = threading.Thread(
            target=self._listening_loop, 
            daemon=True
        )
        self.processing_thread = threading.Thread(
            target=self._processing_loop, 
            daemon=True
        )
        
        self.listening_thread.start()
        self.processing_thread.start()
        
        self.logger.info("Voice engine started listening")
        
    def stop_listening(self):
        """Stop voice listening"""
        self.listening_active = False
        if self.listening_thread:
            self.listening_thread.join(timeout=1)
        if self.processing_thread:
            self.processing_thread.join(timeout=1)
        self.logger.info("Voice engine stopped listening")
        
    def _listening_loop(self):
        """Background loop for audio capture"""
        while self.listening_active:
            try:
                with self.microphone as source:
                    # Capture audio with timeout
                    audio = self.recognizer.listen(
                        source, 
                        timeout=1, 
                        phrase_time_limit=5
                    )
                    
                # Put audio in processing queue
                self.audio_queue.put(audio)
                
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Audio capture error: {e}")
                continue
                
    def _processing_loop(self):
        """Background loop for audio processing"""
        while self.listening_active:
            try:
                # Get audio from queue
                audio = self.audio_queue.get(timeout=1)
                
                # Process audio
                self._process_audio(audio)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Audio processing error: {e}")
                continue
                
    def _process_audio(self, audio: sr.AudioData):
        """Process captured audio"""
        try:
            # Convert to raw audio data
            raw_audio = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
            
            # Apply noise reduction if enabled
            if self.config.noise_reduction:
                raw_audio = self._reduce_noise(raw_audio)
                
            # Convert back to AudioData
            processed_audio = sr.AudioData(
                raw_audio.tobytes(), 
                audio.sample_rate, 
                audio.sample_width
            )
            
            # Recognize speech
            text = self.recognizer.recognize_google(
                processed_audio, 
                language=self.config.language
            )
            
            # Check for wake word
            if self.config.wake_word.lower() in text.lower():
                self.wake_word_detected = True
                if self.on_wake_word_detected:
                    self.on_wake_word_detected()
                self.logger.info(f"Wake word detected: {text}")
                
                # Listen for command after wake word
                command = self._listen_for_command()
                if command and self.on_command_received:
                    self.on_command_received(command)
                    
            elif self.wake_word_detected:
                # Process as command if wake word was detected
                if self.on_command_received:
                    self.on_command_received(text)
                self.wake_word_detected = False
                
        except sr.UnknownValueError:
            # Speech not understood
            pass
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition error: {e}")
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
            
    def _listen_for_command(self) -> Optional[str]:
        """Listen for command after wake word detection"""
        try:
            with self.microphone as source:
                # Listen for command with shorter timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=3, 
                    phrase_time_limit=10
                )
                
            # Recognize command
            command = self.recognizer.recognize_google(
                audio, 
                language=self.config.language
            )
            
            self.logger.info(f"Command received: {command}")
            return command
            
        except sr.WaitTimeoutError:
            self.logger.info("No command received after wake word")
            return None
        except sr.UnknownValueError:
            self.logger.info("Command not understood")
            return None
        except Exception as e:
            self.logger.error(f"Command listening error: {e}")
            return None
            
    def _reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Simple noise reduction using spectral subtraction"""
        # Calculate noise floor from first few samples
        if self.noise_floor == 0:
            self.noise_floor = np.mean(np.abs(audio[:100]))
            
        # Apply simple noise gate
        threshold = self.noise_floor * 3
        audio[np.abs(audio) < threshold] = 0
        
        return audio
        
    def speak(self, text: str) -> None:
        """Convert text to speech"""
        try:
            # Run TTS in separate thread to avoid blocking
            threading.Thread(
                target=self._speak_sync, 
                args=(text,), 
                daemon=True
            ).start()
            
        except Exception as e:
            self.logger.error(f"Speech synthesis error: {e}")
            
    def _speak_sync(self, text: str) -> None:
        """Synchronous speech synthesis"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Speech synthesis error: {e}")
            
    def set_callbacks(self, 
                     on_command: Callable[[str], None],
                     on_wake_word: Callable[[], None]):
        """Set event callbacks"""
        self.on_command_received = on_command
        self.on_wake_word_detected = on_wake_word
        
    def get_voices(self) -> list:
        """Get available TTS voices"""
        return self.tts_engine.getProperty('voices')
        
    def set_voice(self, voice_id: str) -> bool:
        """Set TTS voice by ID"""
        try:
            self.tts_engine.setProperty('voice', voice_id)
            return True
        except Exception as e:
            self.logger.error(f"Voice setting error: {e}")
            return False
            
    def test_microphone(self) -> Dict[str, Any]:
        """Test microphone functionality"""
        test_results = {
            'working': False,
            'noise_level': 0,
            'sample_rate': 0,
            'error': None
        }
        
        try:
            with self.microphone as source:
                # Test audio capture
                audio = self.recognizer.listen(source, timeout=2)
                test_results['working'] = True
                test_results['sample_rate'] = audio.sample_rate
                
                # Calculate noise level
                raw_audio = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                test_results['noise_level'] = np.mean(np.abs(raw_audio))
                
        except Exception as e:
            test_results['error'] = str(e)
            
        return test_results
        
    def __del__(self):
        """Cleanup on deletion"""
        self.stop_listening()
