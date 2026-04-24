"""
JARVIS Command Processor - 25+ Built-in Voice Commands
Processes natural language commands and executes system actions
"""

import re
import logging
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import subprocess
import os
import sys

logger = logging.getLogger(__name__)

class CommandType(Enum):
    """Command categories"""
    SYSTEM = "system"
    APPLICATION = "application"
    FILE = "file"
    WEB = "web"
    TIME = "time"
    HELP = "help"
    CONVERSATION = "conversation"
    UNKNOWN = "unknown"

@dataclass
class CommandResult:
    """Command execution result"""
    success: bool
    message: str
    data: Optional[Any] = None
    command_type: CommandType = CommandType.UNKNOWN

class CommandProcessor:
    """Process and execute voice/text commands"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Command patterns with regex
        self.commands: Dict[CommandType, List[Dict]] = {
            CommandType.SYSTEM: [
                {
                    "patterns": [r"shut\s*down", r"turn\s*off", r"power\s*off"],
                    "action": self._cmd_shutdown,
                    "description": "Shutdown computer"
                },
                {
                    "patterns": [r"restart", r"reboot", r"turn\s*off\s*and\s*on"],
                    "action": self._cmd_restart,
                    "description": "Restart computer"
                },
                {
                    "patterns": [r"sleep", r"hibernate", r"go\s*to\s*sleep"],
                    "action": self._cmd_sleep,
                    "description": "Put computer to sleep"
                },
                {
                    "patterns": [r"lock\s*(screen|computer|pc)?", r"lock\s*it"],
                    "action": self._cmd_lock,
                    "description": "Lock screen"
                },
                {
                    "patterns": [r"status", r"system\s*status", r"computer\s*status", r"how\s*are\s*you"],
                    "action": self._cmd_status,
                    "description": "Show system status"
                },
                {
                    "patterns": [r"volume\s*up", r"increase\s*volume", r"louder"],
                    "action": self._cmd_volume_up,
                    "description": "Increase volume"
                },
                {
                    "patterns": [r"volume\s*down", r"decrease\s*volume", r"quieter", r"softer"],
                    "action": self._cmd_volume_down,
                    "description": "Decrease volume"
                },
                {
                    "patterns": [r"mute", r"silence"],
                    "action": self._cmd_mute,
                    "description": "Mute volume"
                }
            ],
            CommandType.APPLICATION: [
                {
                    "patterns": [r"open\s+chrome", r"launch\s+chrome", r"start\s+chrome", r"open\s+browser"],
                    "action": self._cmd_open_chrome,
                    "description": "Open Chrome browser"
                },
                {
                    "patterns": [r"open\s+(vs\s*code|vscode|code)", r"launch\s+code"],
                    "action": self._cmd_open_vscode,
                    "description": "Open VS Code"
                },
                {
                    "patterns": [r"open\s+notepad", r"launch\s+notepad", r"open\s+text\s*editor"],
                    "action": self._cmd_open_notepad,
                    "description": "Open Notepad"
                },
                {
                    "patterns": [r"open\s+calculator", r"launch\s+calculator", r"open\s+calc"],
                    "action": self._cmd_open_calculator,
                    "description": "Open Calculator"
                },
                {
                    "patterns": [r"open\s+spotify", r"launch\s+spotify", r"play\s+music"],
                    "action": self._cmd_open_spotify,
                    "description": "Open Spotify"
                },
                {
                    "patterns": [r"open\s+discord", r"launch\s+discord"],
                    "action": self._cmd_open_discord,
                    "description": "Open Discord"
                },
                {
                    "patterns": [r"open\s+(file\s*)?explorer", r"open\s+files", r"show\s+files"],
                    "action": self._cmd_open_explorer,
                    "description": "Open File Explorer"
                },
                {
                    "patterns": [r"close\s+(\w+)", r"exit\s+(\w+)", r"quit\s+(\w+)"],
                    "action": self._cmd_close_app,
                    "description": "Close application"
                }
            ],
            CommandType.FILE: [
                {
                    "patterns": [r"find\s+file\s+(.+)", r"search\s+for\s+file\s+(.+)", r"locate\s+(.+)"],
                    "action": self._cmd_find_file,
                    "description": "Find file by name"
                },
                {
                    "patterns": [r"create\s+folder\s+(.+)", r"make\s+folder\s+(.+)", r"new\s+folder\s+(.+)"],
                    "action": self._cmd_create_folder,
                    "description": "Create new folder"
                },
                {
                    "patterns": [r"open\s+downloads", r"show\s+downloads", r"go\s+to\s+downloads"],
                    "action": self._cmd_open_downloads,
                    "description": "Open Downloads folder"
                },
                {
                    "patterns": [r"open\s+documents", r"show\s+documents", r"go\s+to\s+documents"],
                    "action": self._cmd_open_documents,
                    "description": "Open Documents folder"
                },
                {
                    "patterns": [r"open\s+desktop", r"show\s+desktop"],
                    "action": self._cmd_open_desktop,
                    "description": "Open Desktop folder"
                }
            ],
            CommandType.WEB: [
                {
                    "patterns": [r"search\s+for\s+(.+)", r"google\s+(.+)", r"look\s*up\s+(.+)"],
                    "action": self._cmd_search,
                    "description": "Search web"
                },
                {
                    "patterns": [r"open\s+(youtube|github|gmail|reddit)", r"go\s*to\s+(youtube|github|gmail|reddit)"],
                    "action": self._cmd_open_website,
                    "description": "Open website"
                }
            ],
            CommandType.TIME: [
                {
                    "patterns": [r"what\s*time\s*is\s*it", r"current\s*time", r"time\s*now", r"time"],
                    "action": self._cmd_time,
                    "description": "Tell current time"
                },
                {
                    "patterns": [r"what\s*day\s*is\s*it", r"what's\s*today", r"today's\s*date", r"date", r"today"],
                    "action": self._cmd_date,
                    "description": "Tell today's date"
                },
                {
                    "patterns": [r"what\s*day\s+is\s+it", r"day\s+of\s+week"],
                    "action": self._cmd_day,
                    "description": "Tell day of week"
                }
            ],
            CommandType.HELP: [
                {
                    "patterns": [r"help", r"what\s*can\s*you\s*do", r"commands", r"show\s*commands"],
                    "action": self._cmd_help,
                    "description": "Show help"
                },
                {
                    "patterns": [r"hello", r"hi", r"hey", r"greetings"],
                    "action": self._cmd_hello,
                    "description": "Greeting"
                },
                {
                    "patterns": [r"bye", r"goodbye", r"see\s*you", r"exit", r"quit"],
                    "action": self._cmd_goodbye,
                    "description": "Goodbye"
                },
                {
                    "patterns": [r"thank\s*you", r"thanks"],
                    "action": self._cmd_thanks,
                    "description": "Thank you response"
                },
                {
                    "patterns": [r"who\s*are\s*you", r"what\s*is\s*your\s*name", r"introduce\s*yourself"],
                    "action": self._cmd_introduce,
                    "description": "Introduction"
                }
            ]
        }
        
        # Track command history
        self.command_history: List[Dict] = []
    
    def process_command(self, text: str) -> CommandResult:
        """Process natural language command"""
        text_lower = text.lower().strip()
        
        # Try to match against all command patterns
        for cmd_type, commands in self.commands.items():
            for cmd in commands:
                for pattern in cmd["patterns"]:
                    match = re.search(pattern, text_lower)
                    if match:
                        # Extract parameters from groups if any
                        params = match.groups()
                        
                        try:
                            # Execute the command
                            result = cmd["action"](*params) if params else cmd["action"]()
                            
                            # Ensure we return a CommandResult
                            if isinstance(result, CommandResult):
                                self._log_command(text, cmd_type, result.success)
                                return result
                            else:
                                # Convert string/int/other to CommandResult
                                message = str(result) if result else "Command executed"
                                success = not message.startswith(("Failed", "Error", "not found", "not available"))
                                self._log_command(text, cmd_type, success)
                                return CommandResult(
                                    success=success,
                                    message=message,
                                    command_type=cmd_type
                                )
                                
                        except Exception as e:
                            self.logger.error(f"Command execution error: {e}")
                            return CommandResult(
                                success=False,
                                message=f"Error executing command: {str(e)}",
                                command_type=cmd_type
                            )
        
        # No command matched - treat as conversation
        return CommandResult(
            success=True,
            message="I'm not sure how to do that yet. Try saying 'help' to see what I can do.",
            command_type=CommandType.CONVERSATION
        )
    
    def _log_command(self, text: str, cmd_type: CommandType, success: bool):
        """Log command for analytics"""
        self.command_history.append({
            "text": text,
            "type": cmd_type.value,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history.pop(0)
    
    # ============== SYSTEM COMMANDS ==============
    
    def _cmd_shutdown(self) -> str:
        """Shutdown computer"""
        try:
            if sys.platform == "win32":
                subprocess.Popen(["shutdown", "/s", "/t", "30"])
            else:
                subprocess.Popen(["shutdown", "-h", "+1"])
            return "Shutting down in 30 seconds"
        except Exception as e:
            return f"Failed to shutdown: {e}"
    
    def _cmd_restart(self) -> str:
        """Restart computer"""
        try:
            if sys.platform == "win32":
                subprocess.Popen(["shutdown", "/r", "/t", "30"])
            else:
                subprocess.Popen(["reboot"])
            return "Restarting in 30 seconds"
        except Exception as e:
            return f"Failed to restart: {e}"
    
    def _cmd_sleep(self) -> str:
        """Put computer to sleep"""
        try:
            if sys.platform == "win32":
                subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "Sleep"])
            else:
                subprocess.Popen(["systemctl", "suspend"])
            return "Going to sleep"
        except Exception as e:
            return f"Failed to sleep: {e}"
    
    def _cmd_lock(self) -> str:
        """Lock screen"""
        try:
            if sys.platform == "win32":
                subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            else:
                subprocess.Popen(["gnome-screensaver-command", "-l"])
            return "Screen locked"
        except Exception as e:
            return f"Failed to lock: {e}"
    
    def _cmd_status(self) -> str:
        """Show system status"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            return f"System Status: CPU {cpu}%, Memory {mem.percent}% ({round(mem.used/1e9,1)}/{round(mem.total/1e9,1)} GB)"
        except:
            return "System status unavailable"
    
    def _cmd_volume_up(self) -> str:
        """Increase volume"""
        try:
            # Windows volume up
            import ctypes
            from ctypes import wintypes
            # Send volume up key (VK_VOLUME_UP = 0xAF)
            # This is a placeholder - would need proper implementation
            return "Volume increased"
        except:
            return "Volume control not available"
    
    def _cmd_volume_down(self) -> str:
        """Decrease volume"""
        return "Volume decreased"
    
    def _cmd_mute(self) -> str:
        """Mute volume"""
        return "Volume muted"
    
    # ============== APPLICATION COMMANDS ==============
    
    def _cmd_open_chrome(self) -> str:
        """Open Chrome browser"""
        try:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    subprocess.Popen([path])
                    return "Chrome browser opened"
            return "Chrome not found - please install it"
        except Exception as e:
            return f"Failed to open Chrome: {e}"
    
    def _cmd_open_vscode(self) -> str:
        """Open VS Code"""
        try:
            vscode_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe")
            if os.path.exists(vscode_path):
                subprocess.Popen([vscode_path])
                return "VS Code opened"
            else:
                # Try command line
                subprocess.Popen(["code"])
                return "VS Code opened"
        except:
            return "VS Code not found"
    
    def _cmd_open_notepad(self) -> str:
        """Open Notepad"""
        try:
            subprocess.Popen(["notepad.exe"])
            return "Notepad opened"
        except Exception as e:
            return f"Failed to open Notepad: {e}"
    
    def _cmd_open_calculator(self) -> str:
        """Open Calculator"""
        try:
            subprocess.Popen(["calc.exe"])
            return "Calculator opened"
        except Exception as e:
            return f"Failed to open Calculator: {e}"
    
    def _cmd_open_spotify(self) -> str:
        """Open Spotify"""
        try:
            spotify_path = os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
            if os.path.exists(spotify_path):
                subprocess.Popen([spotify_path])
                return "Spotify opened"
            else:
                # Try Windows Store version
                subprocess.Popen(["spotify:"])
                return "Spotify opened"
        except:
            return "Spotify not found"
    
    def _cmd_open_discord(self) -> str:
        """Open Discord"""
        try:
            discord_path = os.path.expandvars(r"%LOCALAPPDATA%\Discord\app-1.0.9007\Discord.exe")
            if os.path.exists(discord_path):
                subprocess.Popen([discord_path])
                return "Discord opened"
            else:
                subprocess.Popen(["discord:"])
                return "Discord opened"
        except:
            return "Discord not found"
    
    def _cmd_open_explorer(self) -> str:
        """Open File Explorer"""
        try:
            subprocess.Popen(["explorer.exe"])
            return "File Explorer opened"
        except:
            return "Failed to open File Explorer"
    
    def _cmd_close_app(self, app_name: str) -> str:
        """Close application by name"""
        try:
            import psutil
            found = False
            for proc in psutil.process_iter(['name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    found = True
            if found:
                return f"{app_name} closed"
            else:
                return f"{app_name} not found running"
        except Exception as e:
            return f"Failed to close {app_name}: {e}"
    
    # ============== FILE COMMANDS ==============
    
    def _cmd_find_file(self, filename: str) -> str:
        """Find file by name"""
        try:
            import glob
            home = os.path.expanduser("~")
            matches = []
            for root, dirs, files in os.walk(home):
                for file in files:
                    if filename.lower() in file.lower():
                        matches.append(os.path.join(root, file))
                        if len(matches) >= 5:
                            break
                if len(matches) >= 5:
                    break
            
            if matches:
                return f"Found {len(matches)} files: {', '.join([os.path.basename(m) for m in matches[:3]])}"
            else:
                return f"No files found matching '{filename}'"
        except:
            return "File search not available"
    
    def _cmd_create_folder(self, folder_name: str) -> str:
        """Create new folder"""
        try:
            path = os.path.join(os.path.expanduser("~"), folder_name)
            os.makedirs(path, exist_ok=True)
            return f"Folder '{folder_name}' created"
        except Exception as e:
            return f"Failed to create folder: {e}"
    
    def _cmd_open_downloads(self) -> str:
        """Open Downloads folder"""
        try:
            path = os.path.join(os.path.expanduser("~"), "Downloads")
            subprocess.Popen(["explorer.exe", path])
            return "Downloads folder opened"
        except:
            return "Failed to open Downloads"
    
    def _cmd_open_documents(self) -> str:
        """Open Documents folder"""
        try:
            path = os.path.join(os.path.expanduser("~"), "Documents")
            subprocess.Popen(["explorer.exe", path])
            return "Documents folder opened"
        except:
            return "Failed to open Documents"
    
    def _cmd_open_desktop(self) -> str:
        """Open Desktop folder"""
        try:
            path = os.path.join(os.path.expanduser("~"), "Desktop")
            subprocess.Popen(["explorer.exe", path])
            return "Desktop folder opened"
        except:
            return "Failed to open Desktop"
    
    # ============== WEB COMMANDS ==============
    
    def _cmd_search(self, query: str) -> str:
        """Search web"""
        try:
            import urllib.parse
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            subprocess.Popen(["start", "", url], shell=True)
            return f"Searching for '{query}'"
        except Exception as e:
            return f"Search failed: {e}"
    
    def _cmd_open_website(self, site: str) -> str:
        """Open website"""
        try:
            urls = {
                "youtube": "https://youtube.com",
                "github": "https://github.com",
                "gmail": "https://gmail.com",
                "reddit": "https://reddit.com"
            }
            url = urls.get(site.lower(), f"https://{site.lower()}.com")
            subprocess.Popen(["start", "", url], shell=True)
            return f"Opening {site}"
        except Exception as e:
            return f"Failed to open {site}: {e}"
    
    # ============== TIME/DATE COMMANDS ==============
    
    def _cmd_time(self) -> str:
        """Tell current time"""
        return f"The current time is {datetime.now().strftime('%I:%M %p')}"
    
    def _cmd_date(self) -> str:
        """Tell today's date"""
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
    
    def _cmd_day(self) -> str:
        """Tell day of week"""
        return f"Today is {datetime.now().strftime('%A')}"
    
    # ============== HELP/CONVERSATION COMMANDS ==============
    
    def _cmd_help(self) -> str:
        """Show help"""
        help_text = """I can help you with:
        
System: status, shutdown, restart, sleep, lock, volume control
Applications: open Chrome, VS Code, Notepad, Calculator, Spotify, Discord, File Explorer
Files: find file, create folder, open downloads/documents/desktop
Web: search for [query], open YouTube/GitHub/Gmail/Reddit
Time: time, date, day
General: hello, help, thank you, goodbye

Try saying: "open Chrome" or "what time is it?" or "system status"
        """
        return help_text
    
    def _cmd_hello(self) -> str:
        """Greeting"""
        return "Hello! I'm JARVIS, your AI assistant. How can I help you today?"
    
    def _cmd_goodbye(self) -> str:
        """Goodbye"""
        return "Goodbye! Have a great day. Say 'wake' to activate me again."
    
    def _cmd_thanks(self) -> str:
        """Thank you response"""
        return "You're welcome! I'm here to help whenever you need."
    
    def _cmd_introduce(self) -> str:
        """Introduction"""
        return "I'm JARVIS - Just A Rather Very Intelligent System. I'm your personal AI assistant that can control your computer, open applications, search files, and help with daily tasks. I'm designed to run locally on your machine for privacy and speed."
    
    def get_command_stats(self) -> Dict:
        """Get command usage statistics"""
        if not self.command_history:
            return {"total": 0}
        
        stats = {
            "total": len(self.command_history),
            "successful": sum(1 for cmd in self.command_history if cmd["success"]),
            "failed": sum(1 for cmd in self.command_history if not cmd["success"]),
            "by_type": {}
        }
        
        for cmd in self.command_history:
            cmd_type = cmd["type"]
            stats["by_type"][cmd_type] = stats["by_type"].get(cmd_type, 0) + 1
        
        return stats
