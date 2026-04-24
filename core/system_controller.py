"""
JARVIS System Controller - Advanced System Management and Automation
Optimized for Windows systems with efficient resource management
"""

import os
import sys
import subprocess
import psutil
import pyautogui
import time
import logging
import json
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading
import asyncio
from datetime import datetime
import winreg
import ctypes
from ctypes import wintypes

@dataclass
class SystemConfig:
    """System controller configuration"""
    max_cpu_usage: float = 80.0
    max_memory_usage: float = 85.0
    auto_cleanup: bool = True
    security_mode: str = "standard"
    backup_enabled: bool = True

class ProcessManager:
    """Advanced process management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running processes with details"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent'],
                    'status': proc.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return processes
        
    def kill_process(self, pid: int) -> bool:
        """Safely terminate a process"""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
            self.logger.info(f"Process {pid} terminated successfully")
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
            self.logger.error(f"Failed to kill process {pid}: {e}")
            return False
            
    def start_process(self, command: str, shell: bool = True) -> Optional[subprocess.Popen]:
        """Start a new process"""
        try:
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.logger.info(f"Process started: {command}")
            return process
        except Exception as e:
            self.logger.error(f"Failed to start process: {e}")
            return None
            
    def get_process_by_name(self, name: str) -> Optional[psutil.Process]:
        """Find process by name"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == name.lower():
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

class FileManager:
    """Advanced file system operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def find_files(self, pattern: str, search_path: str = None) -> List[str]:
        """Find files matching pattern"""
        if search_path is None:
            search_path = os.path.expanduser("~")
            
        found_files = []
        
        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if pattern.lower() in file.lower():
                        found_files.append(os.path.join(root, file))
                        
                # Limit search depth for performance
                if len(found_files) > 100:
                    break
                    
        except Exception as e:
            self.logger.error(f"File search failed: {e}")
            
        return found_files[:50]  # Return max 50 results
        
    def create_folder(self, path: str) -> bool:
        """Create folder with error handling"""
        try:
            os.makedirs(path, exist_ok=True)
            self.logger.info(f"Folder created: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create folder {path}: {e}")
            return False
            
    def move_file(self, source: str, destination: str) -> bool:
        """Move file safely"""
        try:
            shutil.move(source, destination)
            self.logger.info(f"File moved: {source} -> {destination}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move file: {e}")
            return False
            
    def copy_file(self, source: str, destination: str) -> bool:
        """Copy file safely"""
        try:
            shutil.copy2(source, destination)
            self.logger.info(f"File copied: {source} -> {destination}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy file: {e}")
            return False
            
    def delete_file(self, path: str) -> bool:
        """Delete file safely"""
        try:
            os.remove(path)
            self.logger.info(f"File deleted: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {path}: {e}")
            return False
            
    def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get detailed file information"""
        try:
            stat = os.stat(path)
            return {
                'path': path,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'is_file': os.path.isfile(path),
                'is_directory': os.path.isdir(path)
            }
        except Exception as e:
            self.logger.error(f"Failed to get file info for {path}: {e}")
            return None

class SystemMonitor:
    """Real-time system monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history = []
        
    def start_monitoring(self, interval: float = 1.0):
        """Start system monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("System monitoring started")
        
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("System monitoring stopped")
        
    def _monitoring_loop(self, interval: float):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 entries
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)
                    
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(interval)
                
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Temperature (if available)
            temps = {}
            try:
                temps = psutil.sensors_temperatures()
            except:
                pass
                
            # Battery (if available)
            battery = {}
            try:
                battery = psutil.sensors_battery()._asdict()
            except:
                pass
                
            return {
                'timestamp': datetime.now(),
                'cpu': {
                    'percent': cpu_percent,
                    'frequency': cpu_freq.current if cpu_freq else None,
                    'count': cpu_count
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'temperature': temps,
                'battery': battery
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return {}
            
    def get_average_metrics(self, minutes: int = 5) -> Dict[str, Any]:
        """Get average metrics over time period"""
        if not self.metrics_history:
            return {}
            
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history 
            if m['timestamp'] > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
            
        # Calculate averages
        avg_cpu = sum(m['cpu']['percent'] for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m['memory']['percent'] for m in recent_metrics) / len(recent_metrics)
        
        return {
            'period_minutes': minutes,
            'sample_count': len(recent_metrics),
            'avg_cpu_percent': avg_cpu,
            'avg_memory_percent': avg_memory,
            'max_cpu_percent': max(m['cpu']['percent'] for m in recent_metrics),
            'max_memory_percent': max(m['memory']['percent'] for m in recent_metrics)
        }

class SystemController:
    """Main system controller orchestrating all system operations"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize subsystems
        self.process_manager = ProcessManager()
        self.file_manager = FileManager()
        self.monitor = SystemMonitor()
        
        # Application paths (configurable)
        self.app_paths = {
            'chrome': r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            'vscode': r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            'spotify': r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
            'discord': r"C:\Users\%USERNAME%\AppData\Local\Discord\app-1.0.9007\Discord.exe",
            'steam': r"C:\Program Files (x86)\Steam\steam.exe"
        }
        
        # Start monitoring
        self.monitor.start_monitoring()
        
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute system command with validation"""
        params = params or {}
        result = {
            'success': False,
            'message': '',
            'data': None
        }
        
        try:
            if command == 'open_application':
                app_name = params.get('application', '').lower()
                success = await self._open_application(app_name)
                result['success'] = success
                result['message'] = f"Opened {app_name}" if success else f"Failed to open {app_name}"
                
            elif command == 'close_application':
                app_name = params.get('application', '').lower()
                success = await self._close_application(app_name)
                result['success'] = success
                result['message'] = f"Closed {app_name}" if success else f"Failed to close {app_name}"
                
            elif command == 'find_file':
                pattern = params.get('pattern', '')
                files = self.file_manager.find_files(pattern)
                result['success'] = True
                result['message'] = f"Found {len(files)} files"
                result['data'] = files
                
            elif command == 'create_folder':
                path = params.get('path', '')
                success = self.file_manager.create_folder(path)
                result['success'] = success
                result['message'] = f"Created folder {path}" if success else f"Failed to create folder {path}"
                
            elif command == 'system_info':
                info = self.get_system_info()
                result['success'] = True
                result['message'] = "System information retrieved"
                result['data'] = info
                
            elif command == 'shutdown':
                success = await self._shutdown_system()
                result['success'] = success
                result['message'] = "Shutdown initiated" if success else "Failed to shutdown"
                
            elif command == 'restart':
                success = await self._restart_system()
                result['success'] = success
                result['message'] = "Restart initiated" if success else "Failed to restart"
                
            elif command == 'sleep':
                success = await self._sleep_system()
                result['success'] = success
                result['message'] = "Sleep initiated" if success else "Failed to sleep"
                
            elif command == 'lock_screen':
                success = await self._lock_screen()
                result['success'] = success
                result['message'] = "Screen locked" if success else "Failed to lock screen"
                
            else:
                result['message'] = f"Unknown command: {command}"
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            result['message'] = f"Error: {str(e)}"
            
        return result
        
    async def _open_application(self, app_name: str) -> bool:
        """Open application by name"""
        app_path = self.app_paths.get(app_name)
        if not app_path:
            self.logger.error(f"Unknown application: {app_name}")
            return False
            
        # Expand environment variables
        app_path = os.path.expandvars(app_path)
        
        # Check if application exists
        if not os.path.exists(app_path):
            self.logger.error(f"Application not found: {app_path}")
            return False
            
        # Check if already running
        existing_proc = self.process_manager.get_process_by_name(
            os.path.basename(app_path).replace('.exe', '')
        )
        if existing_proc:
            self.logger.info(f"Application {app_name} already running")
            return True
            
        # Start application
        process = self.process_manager.start_process(f'"{app_path}"')
        return process is not None
        
    async def _close_application(self, app_name: str) -> bool:
        """Close application by name"""
        app_path = self.app_paths.get(app_name)
        if not app_path:
            self.logger.error(f"Unknown application: {app_name}")
            return False
            
        app_exe = os.path.basename(app_path).replace('.exe', '')
        proc = self.process_manager.get_process_by_name(app_exe)
        
        if proc:
            return self.process_manager.kill_process(proc.pid)
        else:
            self.logger.info(f"Application {app_name} not running")
            return True
            
    async def _shutdown_system(self) -> bool:
        """Shutdown the system"""
        try:
            # Use Windows shutdown command
            subprocess.run(['shutdown', '/s', '/t', '30'], check=True)
            return True
        except Exception as e:
            self.logger.error(f"Shutdown failed: {e}")
            return False
            
    async def _restart_system(self) -> bool:
        """Restart the system"""
        try:
            subprocess.run(['shutdown', '/r', '/t', '30'], check=True)
            return True
        except Exception as e:
            self.logger.error(f"Restart failed: {e}")
            return False
            
    async def _sleep_system(self) -> bool:
        """Put system to sleep"""
        try:
            # Windows sleep command
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', 'Sleep'], check=True)
            return True
        except Exception as e:
            self.logger.error(f"Sleep failed: {e}")
            return False
            
    async def _lock_screen(self) -> bool:
        """Lock the screen"""
        try:
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=True)
            return True
        except Exception as e:
            self.logger.error(f"Screen lock failed: {e}")
            return False
            
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # Current metrics
            current = self.monitor.get_current_metrics()
            
            # Process information
            processes = self.process_manager.get_running_processes()
            
            # Disk information
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    }
                except:
                    continue
                    
            return {
                'timestamp': datetime.now(),
                'current_metrics': current,
                'processes': processes[:20],  # Top 20 processes
                'disk_usage': disk_usage,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()),
                'python_version': sys.version,
                'platform': sys.platform
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
            
    def cleanup_system(self) -> Dict[str, Any]:
        """Perform system cleanup operations"""
        cleanup_results = {
            'temp_files_cleaned': 0,
            'processes_terminated': 0,
            'memory_freed': 0
        }
        
        try:
            # Clean temporary files
            temp_paths = [
                os.environ.get('TEMP', ''),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
            ]
            
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    for item in os.listdir(temp_path):
                        try:
                            item_path = os.path.join(temp_path, item)
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                                cleanup_results['temp_files_cleaned'] += 1
                        except:
                            continue
                            
            # Terminate high-memory processes (with caution)
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    if proc.info['memory_percent'] > 50:  # High memory usage
                        # Only terminate non-essential processes
                        essential_processes = ['explorer.exe', 'winlogon.exe', 'csrss.exe', 'svchost.exe']
                        if proc.info['name'].lower() not in essential_processes:
                            self.process_manager.kill_process(proc.info['pid'])
                            cleanup_results['processes_terminated'] += 1
                except:
                    continue
                    
            self.logger.info(f"System cleanup completed: {cleanup_results}")
            
        except Exception as e:
            self.logger.error(f"System cleanup failed: {e}")
            
        return cleanup_results
        
    def set_app_path(self, app_name: str, path: str):
        """Set custom application path"""
        self.app_paths[app_name.lower()] = path
        self.logger.info(f"Set {app_name} path to: {path}")
        
    def __del__(self):
        """Cleanup on deletion"""
        if self.monitor:
            self.monitor.stop_monitoring()
