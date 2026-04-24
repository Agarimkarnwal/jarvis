"""
JARVIS AI Assistant - Main Entry Point
Optimized for i3 12GB RAM systems
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import argparse
import signal
import threading
import time
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.voice_engine import VoiceEngine, VoiceConfig
from core.ai_core import AICore, AIConfig
from core.system_controller import SystemController, SystemConfig
from gui.app import JARVISInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class JARVIS:
    """Main JARVIS Application Controller"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize core components
        self.voice_config = VoiceConfig(**self.config.get('voice', {}))
        self.ai_config = AIConfig(**self.config.get('ai', {}))
        self.system_config = SystemConfig(**self.config.get('system', {}))
        
        # Initialize engines
        self.voice_engine = VoiceEngine(self.voice_config)
        self.ai_core = AICore(self.ai_config)
        self.system_controller = SystemController(self.system_config)
        
        # GUI interface
        self.gui = None
        self.running = False
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration from file"""
        default_config = {
            'voice': {
                'wake_word': 'Hey JARVIS',
                'sensitivity': 0.8,
                'voice_speed': 1.0,
                'voice_volume': 0.9,
                'language': 'en-US',
                'noise_reduction': True
            },
            'ai': {
                'primary_model': 'llama3:8b',
                'fallback_model': 'phi3:mini',
                'embedding_model': 'all-minilm:l6-v2',
                'temperature': 0.7,
                'max_tokens': 512,
                'context_window': 4096,
                'quantization': '4-bit',
                'cache_size': 1000
            },
            'system': {
                'max_cpu_usage': 80.0,
                'max_memory_usage': 85.0,
                'auto_cleanup': True,
                'security_mode': 'standard',
                'backup_enabled': True
            },
            'ui': {
                'theme': 'holographic',
                'animations': True,
                'transparency': 0.9,
                'window_opacity': 0.85,
                'particle_effects': True,
                'voice_visualizer': True,
                'system_monitor': True,
                'font_size': 14,
                'font_family': 'Segoe UI'
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge with defaults
                    for section in default_config:
                        if section in user_config:
                            default_config[section].update(user_config[section])
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}")
                
        return default_config
        
    def _setup_callbacks(self):
        """Setup voice engine callbacks"""
        self.voice_engine.set_callbacks(
            on_command=self._on_voice_command,
            on_wake_word=self._on_wake_word
        )
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        
    def _on_voice_command(self, command: str):
        """Handle voice command"""
        self.logger.info(f"Voice command received: {command}")
        
        # Process command asynchronously
        asyncio.create_task(self._process_command(command))
        
    def _on_wake_word(self):
        """Handle wake word detection"""
        self.logger.info("Wake word detected")
        if self.gui:
            # Update GUI state
            pass
            
    async def _process_command(self, command: str):
        """Process user command"""
        try:
            # Generate AI response
            response = await self.ai_core.generate_response(command)
            self.logger.info(f"AI Response: {response}")
            
            # Speak response
            self.voice_engine.speak(response)
            
            # Check if command requires system action
            await self._execute_system_command(command, response)
            
        except Exception as e:
            self.logger.error(f"Command processing failed: {e}")
            error_response = "I apologize, but I encountered an error processing your request."
            self.voice_engine.speak(error_response)
            
    async def _execute_system_command(self, command: str, ai_response: str):
        """Execute system commands based on AI response"""
        command_lower = command.lower()
        
        # System control commands
        if any(word in command_lower for word in ['shutdown', 'shut down']):
            result = await self.system_controller.execute_command('shutdown')
            if result['success']:
                self.logger.info("Shutdown command executed")
                
        elif any(word in command_lower for word in ['restart', 'reboot']):
            result = await self.system_controller.execute_command('restart')
            if result['success']:
                self.logger.info("Restart command executed")
                
        elif any(word in command_lower for word in ['sleep', 'hibernate']):
            result = await self.system_controller.execute_command('sleep')
            if result['success']:
                self.logger.info("Sleep command executed")
                
        elif 'open' in command_lower:
            # Extract application name
            apps = ['chrome', 'vscode', 'spotify', 'discord', 'steam']
            for app in apps:
                if app in command_lower:
                    result = await self.system_controller.execute_command(
                        'open_application', 
                        {'application': app}
                    )
                    if result['success']:
                        self.logger.info(f"Opened {app}")
                    break
                    
        elif 'find' in command_lower and 'file' in command_lower:
            # Extract filename
            words = command_lower.split()
            if 'file' in words:
                file_idx = words.index('file')
                if file_idx + 1 < len(words):
                    filename = words[file_idx + 1]
                    result = await self.system_controller.execute_command(
                        'find_file', 
                        {'pattern': filename}
                    )
                    if result['success'] and result['data']:
                        self.logger.info(f"Found {len(result['data'])} files")
                        
    def start_gui(self):
        """Start GUI interface"""
        try:
            self.logger.info("Starting GUI interface...")
            self.gui = JARVISInterface()
            self.gui.run()
        except Exception as e:
            self.logger.error(f"GUI startup failed: {e}")
            
    def start_voice_only(self):
        """Start voice-only interface"""
        try:
            self.logger.info("Starting voice-only interface...")
            self.voice_engine.start_listening()
            
            # Keep running
            self.running = True
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Voice interface stopped by user")
        except Exception as e:
            self.logger.error(f"Voice interface error: {e}")
        finally:
            self.voice_engine.stop_listening()
            
    def start_console(self):
        """Start console interface"""
        try:
            self.logger.info("Starting console interface...")
            print("🤖 JARVIS AI Assistant - Console Mode")
            print("Type 'help' for commands or 'quit' to exit")
            print("-" * 50)
            
            while True:
                try:
                    user_input = input("👤 You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("🤖 JARVIS: Goodbye!")
                        break
                        
                    elif user_input.lower() == 'help':
                        self._show_console_help()
                        
                    elif user_input.lower() == 'status':
                        self._show_system_status()
                        
                    elif user_input.lower() == 'clear':
                        os.system('cls' if os.name == 'nt' else 'clear')
                        
                    elif user_input:
                        # Process command
                        asyncio.run(self._process_command(user_input))
                        
                except KeyboardInterrupt:
                    print("\n🤖 JARVIS: Goodbye!")
                    break
                except EOFError:
                    print("\n🤖 JARVIS: Goodbye!")
                    break
                    
        except Exception as e:
            self.logger.error(f"Console interface error: {e}")
            
    def _show_console_help(self):
        """Show console help"""
        help_text = """
🤖 JARVIS Console Commands:
- help: Show this help message
- status: Show system status
- clear: Clear screen
- quit/exit/bye: Exit JARVIS

Voice Commands:
- "Hey JARVIS" + [command]: Activate voice assistant
- "Open [application]": Launch applications
- "Find file [name]": Search for files
- "System info": Show system information
- "Shutdown/Restart/Sleep": System control

Examples:
- "Hey JARVIS, open chrome"
- "Hey JARVIS, find file document.txt"
- "Hey JARVIS, what's the system status?"
        """
        print(help_text)
        
    def _show_system_status(self):
        """Show system status"""
        try:
            info = self.system_controller.get_system_info()
            metrics = info.get('current_metrics', {})
            
            print("\n📊 System Status:")
            print(f"CPU Usage: {metrics.get('cpu', {}).get('percent', 0):.1f}%")
            print(f"Memory Usage: {metrics.get('memory', {}).get('percent', 0):.1f}%")
            print(f"Disk Usage: {metrics.get('disk', {}).get('percent', 0):.1f}%")
            print(f"Uptime: {datetime.now() - info.get('boot_time', datetime.now())}")
            print(f"Running Processes: {len(info.get('processes', []))}")
            print("-" * 50)
            
        except Exception as e:
            print(f"Error getting system status: {e}")
            
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down JARVIS...")
        self.running = False
        
        if self.voice_engine:
            self.voice_engine.stop_listening()
            
        if self.system_controller:
            self.system_controller.monitor.stop_monitoring()
            
        self.logger.info("JARVIS shutdown complete")
        
    def run(self, mode: str = 'gui'):
        """Run JARVIS in specified mode"""
        self.logger.info(f"Starting JARVIS in {mode} mode")
        
        try:
            if mode == 'gui':
                self.start_gui()
            elif mode == 'voice':
                self.start_voice_only()
            elif mode == 'console':
                self.start_console()
            else:
                self.logger.error(f"Unknown mode: {mode}")
                print(f"Available modes: gui, voice, console")
                
        except Exception as e:
            self.logger.error(f"JARVIS startup failed: {e}")
        finally:
            self.shutdown()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='JARVIS AI Assistant')
    parser.add_argument('--mode', choices=['gui', 'voice', 'console'], 
                       default='gui', help='Interface mode')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Create and run JARVIS
    jarvis = JARVIS(args.config)
    jarvis.run(args.mode)

if __name__ == "__main__":
    main()
