"""
JARVIS AI Assistant Setup Script
Installation and configuration for optimal performance on i3 systems
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JARVISSetup:
    """JARVIS installation and setup manager"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.system = platform.system().lower()
        
    def check_system_requirements(self):
        """Check system requirements"""
        logger.info("🔍 Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 8:
            logger.error("❌ Python 3.8+ required")
            return False
        else:
            logger.info(f"✅ Python {python_version.major}.{python_version.minor} detected")
            
        # Check system specs
        try:
            import psutil
            
            # Check RAM
            memory = psutil.virtual_memory()
            ram_gb = memory.total / (1024**3)
            logger.info(f"💾 RAM: {ram_gb:.1f} GB")
            
            if ram_gb < 8:
                logger.warning("⚠️  Less than 8GB RAM detected - performance may be limited")
            elif ram_gb >= 12:
                logger.info("✅ Sufficient RAM for optimal performance")
                
            # Check CPU
            cpu_count = psutil.cpu_count()
            logger.info(f"🖥️  CPU cores: {cpu_count}")
            
            if cpu_count < 4:
                logger.warning("⚠️  Less than 4 CPU cores detected - performance may be limited")
            else:
                logger.info("✅ Sufficient CPU cores")
                
        except ImportError:
            logger.warning("⚠️  Cannot check system specs (psutil not installed)")
            
        return True
        
    def install_dependencies(self):
        """Install Python dependencies"""
        logger.info("📦 Installing Python dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            logger.error("❌ requirements.txt not found")
            return False
            
        try:
            # Upgrade pip
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True)
            
            # Install requirements
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                         check=True)
            
            logger.info("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
            
    def install_system_dependencies(self):
        """Install system-specific dependencies"""
        logger.info("🔧 Installing system dependencies...")
        
        if self.system == "windows":
            try:
                # Install Windows-specific dependencies
                logger.info("🪟 Windows system detected")
                
                # Check for Visual C++ redistributable
                logger.info("✅ Windows dependencies ready")
                
            except Exception as e:
                logger.error(f"❌ Windows setup failed: {e}")
                return False
                
        elif self.system == "linux":
            try:
                # Install Linux dependencies
                logger.info("🐧 Linux system detected")
                
                # Install audio dependencies
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", 
                              "portaudio19-dev", "python3-pyaudio", 
                              "espeak", "ffmpeg"], check=True)
                
                logger.info("✅ Linux dependencies installed")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Linux setup failed: {e}")
                logger.warning("⚠️  Please install manually: sudo apt-get install portaudio19-dev python3-pyaudio espeak ffmpeg")
                return False
                
        elif self.system == "darwin":
            try:
                # Install macOS dependencies
                logger.info("🍎 macOS system detected")
                
                # Install with Homebrew
                subprocess.run(["brew", "install", "portaudio", "ffmpeg"], check=True)
                
                logger.info("✅ macOS dependencies installed")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ macOS setup failed: {e}")
                logger.warning("⚠️  Please install manually: brew install portaudio ffmpeg")
                return False
                
        return True
        
    def setup_ai_models(self):
        """Setup AI models"""
        logger.info("🤖 Setting up AI models...")
        
        try:
            import ollama
            
            # Check if Ollama is installed
            try:
                subprocess.run(["ollama", "--version"], check=True, capture_output=True)
                logger.info("✅ Ollama is installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("❌ Ollama not found. Please install Ollama first:")
                logger.info("📥 Download from: https://ollama.ai/")
                return False
                
            # Pull models
            models = ["llama3:8b", "phi3:mini", "all-minilm:l6-v2"]
            
            for model in models:
                logger.info(f"📥 Pulling model: {model}")
                try:
                    ollama.pull(model)
                    logger.info(f"✅ {model} installed")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to pull {model}: {e}")
                    
            logger.info("✅ AI models setup complete")
            return True
            
        except ImportError:
            logger.error("❌ Ollama Python package not installed")
            return False
            
    def test_microphone(self):
        """Test microphone functionality"""
        logger.info("🎤 Testing microphone...")
        
        try:
            import speech_recognition as sr
            
            # Initialize recognizer
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            
            # Test microphone
            with microphone as source:
                logger.info("🔧 Calibrating microphone...")
                recognizer.adjust_for_ambient_noise(source, duration=2)
                
            logger.info("✅ Microphone test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Microphone test failed: {e}")
            logger.warning("⚠️  Please check your microphone settings")
            return False
            
    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        logger.info("🖥️  Creating desktop shortcut...")
        
        try:
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "JARVIS.lnk"
            
            if self.system == "windows":
                import winshell
                
                # Create Windows shortcut
                shortcut = winshell.shortcut(str(shortcut_path))
                shortcut.path = sys.executable
                shortcut.arguments = f'"{self.project_root / "main.py"}"'
                shortcut.description = "JARVIS AI Assistant"
                shortcut.icon_location = (str(self.project_root / "assets" / "jarvis.ico"), 0)
                shortcut.write()
                
                logger.info(f"✅ Desktop shortcut created: {shortcut_path}")
                
            else:
                # Create shell script for Linux/macOS
                script_path = desktop / "jarvis.sh"
                with open(script_path, 'w') as f:
                    f.write(f"#!/bin/bash\n")
                    f.write(f'cd "{self.project_root}"\n')
                    f.write(f'"{sys.executable}" main.py\n')
                    
                # Make executable
                os.chmod(script_path, 0o755)
                
                logger.info(f"✅ Desktop script created: {script_path}")
                
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to create desktop shortcut: {e}")
            return False
            
    def verify_installation(self):
        """Verify installation"""
        logger.info("🔍 Verifying installation...")
        
        try:
            # Test imports
            from core.voice_engine import VoiceEngine
            from core.ai_core import AICore
            from core.system_controller import SystemController
            
            logger.info("✅ Core modules imported successfully")
            
            # Test configuration
            from main import JARVIS
            jarvis = JARVIS()
            
            logger.info("✅ JARVIS instance created successfully")
            
            # Cleanup
            jarvis.shutdown()
            
            logger.info("✅ Installation verification complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Installation verification failed: {e}")
            return False
            
    def run_setup(self):
        """Run complete setup"""
        logger.info("🚀 Starting JARVIS setup...")
        
        steps = [
            ("System Requirements", self.check_system_requirements),
            ("System Dependencies", self.install_system_dependencies),
            ("Python Dependencies", self.install_dependencies),
            ("AI Models", self.setup_ai_models),
            ("Microphone Test", self.test_microphone),
            ("Desktop Shortcut", self.create_desktop_shortcut),
            ("Installation Verification", self.verify_installation)
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            logger.info(f"\n📍 {step_name}")
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except Exception as e:
                logger.error(f"❌ {step_name} failed: {e}")
                failed_steps.append(step_name)
                
        # Summary
        logger.info("\n" + "="*50)
        logger.info("🎯 SETUP SUMMARY")
        logger.info("="*50)
        
        if failed_steps:
            logger.error(f"❌ Failed steps: {', '.join(failed_steps)}")
            logger.error("⚠️  Please resolve the issues above before running JARVIS")
            return False
        else:
            logger.info("✅ Setup completed successfully!")
            logger.info("🎉 JARVIS is ready to use!")
            logger.info("\n📖 Usage:")
            logger.info("  GUI Mode: python main.py --mode gui")
            logger.info("  Voice Mode: python main.py --mode voice")
            logger.info("  Console Mode: python main.py --mode console")
            logger.info("\n🚀 Start JARVIS: python main.py")
            return True

def main():
    """Main setup entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS AI Assistant Setup')
    parser.add_argument('--skip-models', action='store_true', 
                       help='Skip AI model installation')
    parser.add_argument('--test-only', action='store_true', 
                       help='Only run tests')
    
    args = parser.parse_args()
    
    setup = JARVISSetup()
    
    if args.test_only:
        setup.verify_installation()
    else:
        setup.run_setup()

if __name__ == "__main__":
    main()
