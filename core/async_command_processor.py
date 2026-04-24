"""
JARVIS Async Command Processor - Non-blocking command execution with caching
Optimizes performance through async I/O and intelligent caching
"""

import asyncio
import psutil
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from command_processor import CommandProcessor, CommandResult, CommandType
from cache_manager import get_cache_manager, cache_result
from async_manager import get_async_manager, TaskPriority

logger = logging.getLogger(__name__)

class AsyncCommandProcessor(CommandProcessor):
    """
    Async version of command processor with performance optimizations
    - Async subprocess execution
    - Cached system metrics
    - Parallel command execution
    - Non-blocking I/O
    """
    
    def __init__(self):
        super().__init__()
        self.cache = get_cache_manager()
        self.async_manager = get_async_manager()
        
        # Metric cache keys
        self._metric_keys = {
            'cpu': 'system:cpu_percent',
            'memory': 'system:memory_percent',
            'disk': 'system:disk_percent',
            'network': 'system:network_io'
        }
        
        # Last metric update times
        self._last_metric_update = {}
        
    # ============== ASYNC SYSTEM COMMANDS ==============
    
    async def _async_cmd_status(self) -> str:
        """Async system status with caching"""
        cache_key = 'command:status'
        
        # Try cache first (500ms TTL for status)
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        # Get fresh data
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            cpu = await loop.run_in_executor(None, lambda: psutil.cpu_percent(interval=0.1))
            mem = psutil.virtual_memory()
            
            result = f"System Status: CPU {cpu}%, Memory {mem.percent}% ({round(mem.used/1e9,1)}/{round(mem.total/1e9,1)} GB)"
            
            # Cache for 500ms
            self.cache.set(cache_key, result, memory_ttl=0.5, disk_ttl=0)
            
            return result
        except Exception as e:
            return f"System status unavailable: {e}"
    
    async def _async_cmd_time(self) -> str:
        """Async time command with 1s caching"""
        cache_key = 'command:time'
        
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        result = f"The current time is {datetime.now().strftime('%I:%M %p')}"
        self.cache.set(cache_key, result, memory_ttl=1, disk_ttl=0)
        return result
    
    async def _async_cmd_date(self) -> str:
        """Async date command with 1s caching"""
        cache_key = 'command:date'
        
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        result = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
        self.cache.set(cache_key, result, memory_ttl=1, disk_ttl=0)
        return result
    
    async def _async_open_app(self, app_name: str, paths: List[str]) -> str:
        """Async application opener using subprocess"""
        import subprocess
        import os
        
        try:
            for path in paths:
                if os.path.exists(path):
                    # Non-blocking subprocess
                    proc = await asyncio.create_subprocess_exec(
                        path,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    # Don't wait, let it run in background
                    return f"{app_name} opened"
                    
            # If not found by path, try shell command
            app_lower = app_name.lower()
            cmd_map = {
                'chrome': 'start chrome',
                'notepad': 'notepad',
                'calculator': 'calc',
                'file explorer': 'explorer'
            }
            
            if app_lower in cmd_map:
                proc = await asyncio.create_subprocess_shell(
                    cmd_map[app_lower],
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                return f"{app_name} opened"
                
            return f"{app_name} not found"
            
        except Exception as e:
            return f"Failed to open {app_name}: {e}"
    
    async def _async_cmd_open_chrome(self) -> str:
        """Async Chrome opener"""
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        return await self._async_open_app("Chrome", paths)
    
    async def _async_cmd_open_notepad(self) -> str:
        """Async Notepad opener"""
        return await self._async_open_app("Notepad", [])
    
    async def _async_cmd_open_calculator(self) -> str:
        """Async Calculator opener"""
        return await self._async_open_app("Calculator", [])
    
    async def _async_cmd_open_explorer(self) -> str:
        """Async File Explorer opener"""
        return await self._async_open_app("File Explorer", [])
    
    # ============== CACHED HELP COMMANDS ==============
    
    @cache_result(ttl=3600)  # Cache help for 1 hour
    def _cached_cmd_help(self) -> str:
        """Cached help command"""
        return super()._cmd_help()
    
    @cache_result(ttl=86400)  # Cache intro for 1 day
    def _cached_cmd_introduce(self) -> str:
        """Cached introduction"""
        return super()._cmd_introduce()
    
    # ============== ASYNC PROCESS COMMAND ==============
    
    async def process_command_async(self, text: str) -> CommandResult:
        """
        Async command processing with optimizations
        
        Args:
            text: Command text to process
            
        Returns:
            CommandResult with execution status and response
        """
        import re
        
        text_lower = text.lower().strip()
        
        # Quick cache lookup for exact matches
        quick_cache_key = f"cmd:{hash(text_lower)}"
        cached = self.cache.get(quick_cache_key)
        if cached and cached.get('expires', 0) > datetime.now().timestamp():
            return CommandResult(
                success=cached['success'],
                message=cached['message'],
                command_type=CommandType(cached.get('type', 'unknown'))
            )
        
        # Try to match against all command patterns
        for cmd_type, commands in self.commands.items():
            for cmd in commands:
                for pattern in cmd["patterns"]:
                    match = re.search(pattern, text_lower)
                    if match:
                        params = match.groups()
                        
                        try:
                            # Check for async version first
                            action_name = cmd["action"].__name__
                            async_action_name = f"_async{action_name}"
                            
                            if hasattr(self, async_action_name):
                                # Use async version
                                async_action = getattr(self, async_action_name)
                                result = await async_action(*params) if params else await async_action()
                            else:
                                # Fall back to sync version in thread pool
                                loop = asyncio.get_running_loop()
                                result = await loop.run_in_executor(
                                    None, 
                                    lambda: cmd["action"](*params) if params else cmd["action"]()
                                )
                            
                            # Ensure we return a CommandResult
                            if isinstance(result, CommandResult):
                                self._log_command(text, cmd_type, result.success)
                                
                                # Cache successful results
                                if result.success and cmd_type in [CommandType.TIME, CommandType.HELP]:
                                    self.cache.set(quick_cache_key, {
                                        'success': result.success,
                                        'message': result.message,
                                        'type': cmd_type.value,
                                        'expires': datetime.now().timestamp() + 60
                                    }, memory_ttl=60, disk_ttl=300)
                                
                                return result
                            else:
                                # Convert to CommandResult
                                message = str(result) if result else "Command executed"
                                success = not message.startswith(("Failed", "Error", "not found"))
                                self._log_command(text, cmd_type, success)
                                
                                return CommandResult(
                                    success=success,
                                    message=message,
                                    command_type=cmd_type
                                )
                                
                        except Exception as e:
                            logger.error(f"Command execution error: {e}")
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
    
    def process_command(self, text: str) -> CommandResult:
        """
        Synchronous wrapper for async command processing
        For use in non-async contexts
        """
        try:
            # Check if we're in an async context
            loop = asyncio.get_running_loop()
            # If we are, create task and wait for it
            future = asyncio.run_coroutine_threadsafe(
                self.process_command_async(text), loop
            )
            return future.result(timeout=5)
        except RuntimeError:
            # No event loop, run our own
            return asyncio.run(self.process_command_async(text))
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return CommandResult(
                success=False,
                message=f"Error: {str(e)}",
                command_type=CommandType.UNKNOWN
            )
    
    # ============== BATCH COMMAND PROCESSING ==============
    
    async def process_commands_batch(self, commands: List[str]) -> List[CommandResult]:
        """
        Process multiple commands in parallel
        
        Args:
            commands: List of command strings
            
        Returns:
            List of CommandResults in same order
        """
        # Create tasks for all commands
        tasks = [
            self.process_command_async(cmd)
            for cmd in commands
        ]
        
        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(CommandResult(
                    success=False,
                    message=f"Error: {str(result)}",
                    command_type=CommandType.UNKNOWN
                ))
            else:
                final_results.append(result)
                
        return final_results
    
    # ============== PERFORMANCE METRICS ==============
    
    def get_performance_stats(self) -> Dict:
        """Get command processor performance statistics"""
        cache_stats = self.cache.get_stats()
        command_stats = self.get_command_stats()
        
        return {
            'cache': cache_stats,
            'commands': command_stats,
            'performance': {
                'cache_hit_rate': cache_stats.get('combined_hit_rate', 0),
                'memory_entries': cache_stats.get('memory', {}).get('entries', 0),
                'disk_entries': cache_stats.get('disk', {}).get('entries', 0),
                'total_cached_size': cache_stats.get('total_size_bytes', 0)
            }
        }

# Global instance for convenience
_async_processor: Optional[AsyncCommandProcessor] = None

def get_async_command_processor() -> AsyncCommandProcessor:
    """Get or create global async command processor"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncCommandProcessor()
    return _async_processor
