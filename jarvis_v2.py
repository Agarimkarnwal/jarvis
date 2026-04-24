"""
JARVIS AI Assistant V2 - Complete Implementation
Integrates: Voice Engine V2 + Command Processor + Non-blocking TTS
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from voice_engine_v2 import VoiceEngineV2, VoiceState, PYAUDIO_AVAILABLE
from command_processor import CommandProcessor, CommandResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JARVIS_V2:
    """Complete JARVIS AI Assistant"""
    
    def __init__(self):
        self.name = "JARVIS"
        self.version = "2.0"
        
        # Initialize components
        self.voice = VoiceEngineV2(wake_word="hey jarvis")
        self.commands = CommandProcessor()
        
        # Set callbacks
        self.voice.on_wake_word = self._on_wake_word
        self.voice.on_command = self._on_command
        self.voice.on_state_change = self._on_state_change
        
        # Track state
        self.awake = False
        self.running = False
        
    def _on_wake_word(self):
        """Called when wake word detected"""
        self.awake = True
        self.voice.speak("Yes? I'm listening.")
        print("\n🎤 Wake word detected! JARVIS is listening...")
        
    def _on_command(self, command_text: str):
        """Called when command received"""
        print(f"\n👤 Command: {command_text}")
        
        # Process the command
        result = self.commands.process_command(command_text)
        
        # Speak response
        print(f"🤖 JARVIS: {result.message}")
        self.voice.speak(result.message)
        
        # Reset wake state after command
        self.awake = False
        
    def _on_state_change(self, state: VoiceState):
        """Called when voice state changes"""
        state_icons = {
            VoiceState.IDLE: "⏸️",
            VoiceState.LISTENING_WAKE: "👂",
            VoiceState.LISTENING_COMMAND: "🎤",
            VoiceState.PROCESSING: "⚙️",
            VoiceState.SPEAKING: "🔊"
        }
        icon = state_icons.get(state, "❓")
        print(f"\r{icon} State: {state.value:20}", end="", flush=True)
        
    def start(self, mode: str = "voice"):
        """Start JARVIS"""
        print("=" * 60)
        print(f"🤖 {self.name} AI Assistant v{self.version}")
        print("=" * 60)
        
        # Show status
        status = self.voice.get_status()
        print(f"\n📊 Status:")
        print(f"   Voice Recognition: {'✅' if status['speech_available'] else '❌'}")
        print(f"   Microphone: {'✅' if status['microphone_initialized'] else '❌'}")
        print(f"   Text-to-Speech: {'✅' if status['tts_available'] else '❌'}")
        print(f"   PyAudio: {'✅' if PYAUDIO_AVAILABLE else '❌'}")
        
        if not status['microphone_initialized']:
            print("\n⚠️  Microphone not available - running in text mode only")
            mode = "text"
        
        print(f"\n🎯 Mode: {mode.upper()}")
        print("-" * 60)
        
        self.running = True
        
        if mode == "voice":
            self._run_voice_mode()
        else:
            self._run_text_mode()
            
    def _run_voice_mode(self):
        """Run with voice control"""
        print("🎤 Voice Mode Active")
        print("Say 'Hey JARVIS' to wake me up")
        print("Say 'quit' or press Ctrl+C to exit")
        print("-" * 60)
        
        # Start voice engine
        self.voice.start()
        
        # Welcome message
        self.voice.speak("JARVIS online. Say 'Hey JARVIS' to begin.")
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            
        self.voice.stop()
        self.voice.speak("Goodbye!")
        
    def _run_text_mode(self):
        """Run with text input"""
        print("⌨️  Text Mode Active")
        print("Type commands or 'help' for assistance")
        print("Type 'quit' to exit")
        print("-" * 60)
        
        # Welcome
        print("🤖 JARVIS: Hello! I'm ready to help. What would you like me to do?")
        
        while self.running:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("🤖 JARVIS: Goodbye!")
                    break
                    
                # Process command
                result = self.commands.process_command(user_input)
                print(f"🤖 JARVIS: {result.message}")
                
                # Speak if TTS available
                if self.voice.tts_engine:
                    self.voice.speak(result.message)
                    
            except KeyboardInterrupt:
                print("\n🤖 JARVIS: Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    def test_microphone(self):
        """Test microphone functionality"""
        print("\n🎤 Testing Microphone...")
        print("-" * 40)
        
        result = self.voice.test_microphone()
        
        print(f"Available: {result['available']}")
        print(f"Speech Recognition: {result['speech_recognition']}")
        print(f"PyAudio: {result['pyaudio']}")
        print(f"TTS: {result['tts']}")
        
        if result['error']:
            print(f"Error: {result['error']}")
            
        if result['available']:
            print("\n✅ Microphone is working!")
            
            # Calibrate
            print("\n🔧 Calibrating...")
            success = self.voice.calibrate_microphone(duration=2.0)
            if success:
                print("✅ Calibration complete!")
            else:
                print("❌ Calibration failed")
        else:
            print("\n⚠️  Microphone not available - voice mode disabled")
            
    def show_help(self):
        """Show help information"""
        result = self.commands._cmd_help()
        print(result)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS AI Assistant V2')
    parser.add_argument('--mode', choices=['voice', 'text'], default='text',
                       help='Interaction mode (default: text)')
    parser.add_argument('--test-mic', action='store_true',
                       help='Test microphone and exit')
    
    args = parser.parse_args()
    
    # Create JARVIS instance
    jarvis = JARVIS_V2()
    
    if args.test_mic:
        jarvis.test_microphone()
    else:
        jarvis.start(mode=args.mode)

if __name__ == "__main__":
    main()
