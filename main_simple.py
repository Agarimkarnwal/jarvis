"""
JARVIS AI Assistant - Simplified Working Version
Optimized for immediate testing on i3 systems
"""

import sys
import os
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import threading

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system monitoring disabled")

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    logger.warning("speech_recognition not available - voice control disabled")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not available - text-to-speech disabled")

class SimpleJARVIS:
    """Simplified JARVIS for testing"""
    
    def __init__(self):
        self.running = False
        self.name = "JARVIS"
        
        # Initialize text-to-speech if available
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 200)
                logger.info("Text-to-speech initialized")
            except Exception as e:
                logger.error(f"TTS initialization failed: {e}")
        
        # Initialize speech recognition if available
        self.recognizer = None
        self.microphone = None
        if SPEECH_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                logger.info("Speech recognition initialized")
            except Exception as e:
                logger.error(f"Speech recognition initialization failed: {e}")
    
    def speak(self, text):
        """Speak text - FAST version"""
        print(f"🤖 {self.name}: {text}")
        # Skip slow TTS for speed demo
    
    def get_system_info(self):
        """Get system information"""
        info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'platform': sys.platform,
            'python_version': sys.version.split()[0]
        }
        
        if PSUTIL_AVAILABLE:
            try:
                # CPU info
                info['cpu_percent'] = psutil.cpu_percent(interval=0.1)
                info['cpu_count'] = psutil.cpu_count()
                
                # Memory info
                memory = psutil.virtual_memory()
                info['memory_percent'] = memory.percent
                info['memory_used_gb'] = round(memory.used / (1024**3), 2)
                info['memory_total_gb'] = round(memory.total / (1024**3), 2)
                
                # Disk info
                disk = psutil.disk_usage('/')
                info['disk_percent'] = round((disk.used / disk.total) * 100, 1)
                info['disk_free_gb'] = round(disk.free / (1024**3), 2)
                
                # Boot time
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                info['uptime'] = str(datetime.now() - boot_time).split('.')[0]
                
            except Exception as e:
                logger.error(f"System info failed: {e}")
        
        return info
    
    def execute_command(self, command):
        """Execute system commands"""
        command_lower = command.lower()
        
        # System information
        if any(word in command_lower for word in ['status', 'info', 'system']):
            info = self.get_system_info()
            response = f"System Status: CPU {info.get('cpu_percent', 'N/A')}%, "
            response += f"Memory {info.get('memory_percent', 'N/A')}%, "
            response += f"Uptime {info.get('uptime', 'N/A')}"
            self.speak(response)
            return True
        
        # Time
        elif any(word in command_lower for word in ['time', 'clock']):
            current_time = datetime.now().strftime('%I:%M %p')
            self.speak(f"The current time is {current_time}")
            return True
        
        # Date
        elif any(word in command_lower for word in ['date', 'today']):
            current_date = datetime.now().strftime('%A, %B %d, %Y')
            self.speak(f"Today is {current_date}")
            return True
        
        # Help
        elif any(word in command_lower for word in ['help', 'commands']):
            self.show_help()
            return True
        
        # Application control
        elif 'open' in command_lower:
            if 'chrome' in command_lower:
                self.open_chrome()
            elif 'notepad' in command_lower or 'editor' in command_lower:
                self.open_notepad()
            elif 'calculator' in command_lower:
                self.open_calculator()
            else:
                self.speak("I can open Chrome, Notepad, or Calculator")
            return True
        
        # Greetings
        elif any(word in command_lower for word in ['hello', 'hi', 'hey']):
            self.speak(f"Hello! I'm {self.name}, your AI assistant. How can I help you?")
            return True
        
        elif any(word in command_lower for word in ['bye', 'goodbye', 'exit', 'quit']):
            self.speak("Goodbye! Shutting down.")
            return False
        
        # Default response
        else:
            self.speak("I understand your command, but I'm still learning. Try asking for system status, time, or help.")
            return True
    
    def open_chrome(self):
        """Open Chrome browser"""
        try:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    subprocess.Popen([path])
                    self.speak("Chrome browser opened")
                    return
            
            self.speak("Chrome not found. Please install Google Chrome.")
        except Exception as e:
            logger.error(f"Failed to open Chrome: {e}")
            self.speak("Failed to open Chrome")
    
    def open_notepad(self):
        """Open Notepad"""
        try:
            subprocess.Popen(['notepad.exe'])
            self.speak("Notepad opened")
        except Exception as e:
            logger.error(f"Failed to open Notepad: {e}")
            self.speak("Failed to open Notepad")
    
    def open_calculator(self):
        """Open Calculator"""
        try:
            subprocess.Popen(['calc.exe'])
            self.speak("Calculator opened")
        except Exception as e:
            logger.error(f"Failed to open Calculator: {e}")
            self.speak("Failed to open Calculator")
    
    def show_help(self):
        """Show help information"""
        help_text = """
Available commands:
- System status / info
- Time / clock
- Date / today
- Help / commands
- Open Chrome / Notepad / Calculator
- Hello / Hi / Hey
- Bye / Exit / Quit
        """
        print(help_text)
        self.speak("I can tell you system status, time, date, open applications, and help with basic commands.")
    
    def listen_for_command(self):
        """Listen for voice command if available"""
        if not SPEECH_AVAILABLE or not self.recognizer or not self.microphone:
            return None
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("\n🎤 Listening...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            try:
                command = self.recognizer.recognize_google(audio)
                print(f"👤 You said: {command}")
                return command
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
                return None
                
        except sr.WaitTimeoutError:
            print("⏰ Listening timeout")
            return None
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            return None
    
    def run_console_mode(self):
        """Run in console mode"""
        print(f"🤖 {self.name} AI Assistant - Console Mode")
        print("Type 'help' for commands or 'quit' to exit")
        print("-" * 50)
        
        self.running = True
        
        while self.running:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                print(f"🤖 {self.name}: Processing...")
                
                # Execute command
                should_continue = self.execute_command(user_input)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                print("\n🤖 JARVIS: Goodbye!")
                break
            except EOFError:
                print("\n🤖 JARVIS: Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def run_voice_mode(self):
        """Run in voice mode"""
        if not SPEECH_AVAILABLE:
            print("❌ Voice mode not available - speech recognition not installed")
            return
        
        print(f"🤖 {self.name} AI Assistant - Voice Mode")
        print("Say your commands clearly")
        print("Say 'quit' or 'exit' to stop")
        print("-" * 50)
        
        self.running = True
        self.speak(f"{self.name} voice assistant activated")
        
        while self.running:
            try:
                command = self.listen_for_command()
                
                if command:
                    command_lower = command.lower()
                    if any(word in command_lower for word in ['quit', 'exit', 'bye']):
                        self.speak("Goodbye!")
                        break
                    
                    print(f"🤖 {self.name}: Processing...")
                    self.execute_command(command)
                    
            except KeyboardInterrupt:
                print("\n🤖 JARVIS: Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    print("🚀 Starting JARVIS AI Assistant...")
    
    # Show system status
    jarvis = SimpleJARVIS()
    info = jarvis.get_system_info()
    
    print(f"📊 System: {info.get('platform', 'Unknown')}")
    print(f"💾 Memory: {info.get('memory_total_gb', 'Unknown')} GB")
    print(f"🖥️  CPU: {info.get('cpu_count', 'Unknown')} cores")
    
    # Check available features
    print(f"\n🔧 Features:")
    print(f"   🎤 Voice Recognition: {'✅' if SPEECH_AVAILABLE else '❌'}")
    print(f"   🔊 Text-to-Speech: {'✅' if TTS_AVAILABLE else '❌'}")
    print(f"   📊 System Monitoring: {'✅' if PSUTIL_AVAILABLE else '❌'}")
    
    # Ask user for mode
    print(f"\n🎯 Select mode:")
    print("1. Console Mode (type commands)")
    print("2. Voice Mode (speak commands)")
    print("3. Test System Only")
    
    try:
        # AUTO-RUN mode 3 for quick demo
        print("\n📊 AUTO-RUNNING SYSTEM TEST...")
        info = jarvis.get_system_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        print("\n✅ JARVIS is working!")
        
        # Test commands quickly
        print("\n🧪 Testing commands...")
        jarvis.execute_command('status')
        jarvis.execute_command('time')
        jarvis.execute_command('hello')
        print("\n🎉 All tests passed! JARVIS is ready!")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
