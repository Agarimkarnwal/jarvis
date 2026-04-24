# 🤖 JARVIS AI Assistant

**Just A Rather Very Intelligent System** - Your personal AI assistant optimized for i3 12GB RAM laptops

![JARVIS](https://img.shields.io/badge/JARVIS-AI_Assistant-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![License](https://img.shields.io/badge/License-MIT-yellow) ![Platform](https://img.shields.io/badge/Platform-Windows_Linux_macOS-lightgrey)

## 🚀 Overview

JARVIS is a sophisticated, voice-controlled AI assistant that transforms your laptop into a futuristic command center. Built specifically for optimal performance on i3 systems with 12GB RAM, JARVIS combines cutting-edge AI, voice recognition, system automation, and a stunning holographic visual interface.

### ✨ Key Features

- **🎤 Voice Control**: Natural language interaction with "Hey JARVIS" wake word
- **🧠 Local AI**: Privacy-first processing with Llama 3 and Phi-3 models
- **💻 System Control**: Complete automation of applications, files, and system functions
- **🎨 Holographic UI**: Modern, animated interface with real-time visualizations
- **⚡ Optimized Performance**: Efficient resource management for i3 processors
- **🔒 Privacy-Focused**: All processing happens locally on your machine

## 🎯 System Requirements

### Minimum Requirements
- **CPU**: Intel i3 or equivalent
- **RAM**: 8GB (12GB+ recommended for optimal performance)
- **Storage**: 10GB free space
- **OS**: Windows 10+, Ubuntu 20.04+, macOS 10.15+
- **Python**: 3.8 or higher

### Recommended Requirements
- **CPU**: Intel i5 or higher
- **RAM**: 16GB
- **Storage**: SSD with 20GB free space
- **Microphone**: For voice interaction

## 📦 Installation

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/jarvis-ai-assistant.git
cd jarvis-ai-assistant

# Run automated setup
python setup.py
```

### Manual Install

1. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

2. **Install System Dependencies**

**Windows:**
```bash
# Install Visual C++ Redistributable (if not present)
# Download from Microsoft website
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio espeak ffmpeg
```

**macOS:**
```bash
brew install portaudio ffmpeg
```

3. **Install Ollama**
```bash
# Download and install Ollama
# Visit: https://ollama.ai/

# Pull AI models
ollama pull llama3:8b
ollama pull phi3:mini
ollama pull all-minilm:l6-v2
```

4. **Verify Installation**
```bash
python main.py --test
```

## 🚀 Getting Started

### Launch JARVIS

```bash
# GUI Mode (Recommended)
python main.py --mode gui

# Voice-Only Mode
python main.py --mode voice

# Console Mode
python main.py --mode console
```

### First Time Setup

1. **Calibrate Microphone**
   - JARVIS will automatically calibrate your microphone on first run
   - Speak clearly when prompted

2. **Wake Word Activation**
   - Say "Hey JARVIS" to activate voice assistant
   - Wait for the confirmation tone

3. **Basic Commands**
   - "Hey JARVIS, open Chrome"
   - "Hey JARVIS, what time is it?"
   - "Hey JARVIS, find file document.txt"

## 🎮 Usage Guide

### Voice Commands

#### System Control
- **"Hey JARVIS, shutdown"** - Shutdown computer
- **"Hey JARVIS, restart"** - Restart computer  
- **"Hey JARVIS, sleep"** - Put computer to sleep
- **"Hey JARVIS, lock screen"** - Lock the screen

#### Application Management
- **"Hey JARVIS, open Chrome"** - Launch Chrome
- **"Hey JARVIS, open VS Code"** - Launch Visual Studio Code
- **"Hey JARVIS, close Spotify"** - Close application

#### File Operations
- **"Hey JARVIS, find file report.pdf"** - Search for files
- **"Hey JARVIS, create folder Projects"** - Create folders
- **"Hey JARVIS, open folder Downloads"** - Open folders

#### Web & Search
- **"Hey JARVIS, search for Python tutorials"** - Web search
- **"Hey JARVIS, open github.com"** - Open websites

#### Productivity
- **"Hey JARVIS, remind me to call Mom at 5pm"** - Set reminders
- **"Hey JARVIS, take a note: meeting tomorrow at 10am"** - Take notes
- **"Hey JARVIS, start timer for 25 minutes"** - Set timers

### GUI Interface

The JARVIS GUI features a modern holographic design with:

- **📊 Real-time System Monitor**: CPU, memory, disk usage visualization
- **💬 Conversation History**: Interactive chat interface
- **🎤 Voice Waveform**: Live audio visualization
- **⚡ Quick Actions**: One-click system commands
- **⚙️ Settings Panel**: Customize voice, AI, and system preferences

### Console Mode

For terminal users, JARVIS provides a full console interface:

```bash
👤 You: help
🤖 JARVIS: Available commands...
👤 You: status  
🤖 JARVIS: CPU: 45%, Memory: 3.2GB, Uptime: 2h 15m
```

## 🛠️ Configuration

### Voice Settings

Edit `config/config.yaml`:

```yaml
voice:
  wake_word: "Hey JARVIS"
  sensitivity: 0.8
  voice_speed: 1.0
  voice_volume: 0.9
  language: "en-US"
  noise_reduction: true
```

### AI Model Settings

```yaml
ai:
  primary_model: "llama3:8b"
  fallback_model: "phi3:mini"
  temperature: 0.7
  max_tokens: 512
  context_window: 4096
```

### System Paths

Configure application paths for your system:

```yaml
applications:
  chrome: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  vscode: "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
```

## 🔧 Advanced Features

### Custom Commands

Create custom voice commands in `config/custom_commands.yaml`:

```yaml
custom_commands:
  - trigger: "start work session"
    actions:
      - open: "chrome"
      - open: "vscode"
      - open: "spotify"
      - speak: "Work session started. Good luck!"
```

### Automation Routines

Set up automated routines:

```python
# Morning routine
def morning_routine():
    jarvis.open_application("chrome")
    jarvis.open_application("vscode")
    jarvis.speak("Good morning! Your workspace is ready.")
```

### Integration Hub

Connect with third-party services:

- **Calendar Integration**: Google Calendar, Outlook
- **Home Automation**: Smart home devices
- **Communication**: Discord, Slack, Email
- **Development**: Git, Docker, IDE plugins

## 📊 Performance Optimization

### Memory Management

JARVIS automatically manages memory usage:

- **Dynamic Allocation**: 2-4GB base usage
- **Smart Caching**: LRU eviction for efficiency
- **Memory Pooling**: Reuse frequent operations
- **Garbage Collection**: Optimized cleanup

### CPU Optimization

- **Multi-threading**: Parallel task processing
- **Load Balancing**: Distribute across CPU cores
- **Background Processing**: Non-blocking operations
- **Idle Scheduling**: Heavy tasks during idle time

### Storage Optimization

- **SSD Caching**: Fast model loading
- **Log Rotation**: Automatic cleanup
- **Compression**: Efficient data storage
- **Indexing**: Fast file searches

## 🐛 Troubleshooting

### Common Issues

**Voice Recognition Not Working**
```bash
# Test microphone
python -c "import speech_recognition as sr; print('Microphone OK')"

# Check audio drivers
# Windows: Update audio drivers in Device Manager
# Linux: sudo apt-get install pulseaudio
```

**AI Models Not Responding**
```bash
# Check Ollama status
ollama list

# Reinstall models
ollama pull llama3:8b
```

**High Memory Usage**
```bash
# Clear AI cache
python main.py --clear-cache

# Reduce model size
# Edit config.yaml: use phi3:mini instead of llama3:8b
```

**GUI Not Starting**
```bash
# Check display drivers
# Install/update graphics drivers

# Try console mode
python main.py --mode console
```

### Debug Mode

Enable debug logging:

```bash
python main.py --debug --mode console
```

Check log files:

```bash
tail -f jarvis.log
```

### Performance Monitoring

Monitor system resources:

```python
# In Python console
from jarvis.core.system_controller import SystemController
controller = SystemController()
print(controller.get_system_info())
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the Repository**
2. **Create Feature Branch**
```bash
git checkout -b feature/amazing-feature
```

3. **Make Changes**
   - Follow PEP 8 style guidelines
   - Add tests for new features
   - Update documentation

4. **Submit Pull Request**
   - Describe your changes
   - Include test results
   - Update README if needed

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black jarvis/
flake8 jarvis/
```

## 📝 Changelog

### Version 1.0.0 (Current)
- ✅ Voice recognition with wake word detection
- ✅ Local AI processing with Llama 3 and Phi-3
- ✅ System control and automation
- ✅ Holographic GUI interface
- ✅ Real-time system monitoring
- ✅ Cross-platform compatibility

### Upcoming Features (Version 2.0)
- 🚧 Mobile app companion
- 🚧 Cloud sync options
- 🚧 Advanced AI integrations
- 🚧 Home automation control
- 🚧 Multi-user profiles
- 🚧 Plugin system

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama Team** - For the amazing local AI platform
- **OpenAI** - Whisper speech recognition model
- **Streamlit** - For the beautiful GUI framework
- **Plotly** - For stunning data visualizations
- **Python Community** - For the incredible ecosystem

## 📞 Support

- **Documentation**: [Wiki](https://github.com/your-username/jarvis-ai-assistant/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/jarvis-ai-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/jarvis-ai-assistant/discussions)
- **Email**: jarvis-support@example.com

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/jarvis-ai-assistant&type=Date)](https://star-history.com/#your-username/jarvis-ai-assistant&Date)

---

**🎉 Thank you for choosing JARVIS AI Assistant!**

*Transform your laptop into a futuristic command center with the power of AI.*
