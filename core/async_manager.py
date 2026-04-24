"""
JARVIS Async Manager - Central async event loop and task management
Handles concurrent operations with priority queuing and timeout handling
"""

import asyncio
import logging
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import time
import weakref

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4

@dataclass
class AsyncTask:
    """Async task definition"""
    id: str
    coro: Any
    priority: TaskPriority
    timeout: Optional[float] = None
    callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    
@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0

class AsyncManager:
    """
    Central async task manager for JARVIS
    - Priority-based task queuing
    - Timeout handling
    - Thread pool for CPU-bound tasks
    - Automatic cleanup
    """
    
    def __init__(self, max_workers: int = 4):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="jarvis_worker")
        self._tasks: Dict[str, asyncio.Task] = {}
        self._priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running = False
        self._main_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'avg_duration': 0.0
        }
        
    async def start(self):
        """Start the async manager"""
        if self._running:
            return
            
        self._running = True
        self.loop = asyncio.get_running_loop()
        
        # Start main processing loop
        self._main_task = asyncio.create_task(self._process_queue())
        
        logger.info("Async manager started")
        
    async def stop(self):
        """Stop the async manager gracefully"""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel all pending tasks
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
                
        # Cancel main processing loop
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
                
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("Async manager stopped")
        
    async def _process_queue(self):
        """Main task processing loop"""
        while self._running:
            try:
                # Get task from priority queue (with timeout)
                priority, task = await asyncio.wait_for(
                    self._priority_queue.get(), 
                    timeout=1.0
                )
                
                # Execute task
                asyncio.create_task(self._execute_task(task))
                
            except asyncio.TimeoutError:
                # No tasks available, continue loop
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                
    async def _execute_task(self, task: AsyncTask):
        """Execute a single async task with timeout and callbacks"""
        start_time = time.time()
        
        try:
            # Execute with timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(task.coro, timeout=task.timeout)
            else:
                result = await task.coro
                
            duration = time.time() - start_time
            task_result = TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                duration=duration
            )
            
            self._stats['completed_tasks'] += 1
            
            # Call success callback
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(task_result)
                    else:
                        task.callback(task_result)
                except Exception as e:
                    logger.error(f"Callback error for task {task.id}: {e}")
                    
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            task_result = TaskResult(
                task_id=task.id,
                success=False,
                error=asyncio.TimeoutError(f"Task timed out after {task.timeout}s"),
                duration=duration
            )
            self._stats['failed_tasks'] += 1
            
            if task.error_callback:
                try:
                    if asyncio.iscoroutinefunction(task.error_callback):
                        await task.error_callback(task_result)
                    else:
                        task.error_callback(task_result)
                except Exception as e:
                    logger.error(f"Error callback error for task {task.id}: {e}")
                    
        except asyncio.CancelledError:
            self._stats['cancelled_tasks'] += 1
            raise
            
        except Exception as e:
            duration = time.time() - start_time
            task_result = TaskResult(
                task_id=task.id,
                success=False,
                error=e,
                duration=duration
            )
            self._stats['failed_tasks'] += 1
            
            if task.error_callback:
                try:
                    if asyncio.iscoroutinefunction(task.error_callback):
                        await task.error_callback(task_result)
                    else:
                        task.error_callback(task_result)
                except Exception as cb_e:
                    logger.error(f"Error callback error for task {task.id}: {cb_e}")
                    
        finally:
            self._stats['total_tasks'] += 1
            # Update average duration
            self._stats['avg_duration'] = (
                (self._stats['avg_duration'] * (self._stats['total_tasks'] - 1) + duration) 
                / self._stats['total_tasks']
            )
            
    async def submit(self, coro, task_id: Optional[str] = None,
                     priority: TaskPriority = TaskPriority.MEDIUM,
                     timeout: Optional[float] = None,
                     callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None) -> str:
        """
        Submit an async task for execution
        
        Args:
            coro: Coroutine to execute
            task_id: Optional task identifier (auto-generated if not provided)
            priority: Task priority level
            timeout: Optional timeout in seconds
            callback: Success callback function
            error_callback: Error callback function
            
        Returns:
            Task ID string
        """
        if not self._running:
            raise RuntimeError("Async manager not started")
            
        task_id = task_id or f"task_{time.time()}_{id(coro)}"
        
        task = AsyncTask(
            id=task_id,
            coro=coro,
            priority=priority,
            timeout=timeout,
            callback=callback,
            error_callback=error_callback
        )
        
        # Add to priority queue
        await self._priority_queue.put((priority.value, task))
        
        logger.debug(f"Task {task_id} submitted with priority {priority.name}")
        
        return task_id
        
    def submit_sync(self, func, *args, 
                    priority: TaskPriority = TaskPriority.MEDIUM,
                    timeout: Optional[float] = None,
                    callback: Optional[Callable] = None,
                    error_callback: Optional[Callable] = None) -> str:
        """
        Submit a synchronous function to run in thread pool
        
        Args:
            func: Function to execute
            args: Function arguments
            priority: Task priority level
            timeout: Optional timeout in seconds
            callback: Success callback function
            error_callback: Error callback function
            
        Returns:
            Task ID string
        """
        async def wrapper():
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self._executor, func, *args)
            
        # Need to handle this differently since we're in async context
        # For now, return a coroutine that caller should await or submit
        return self.submit(wrapper(), priority=priority, timeout=timeout,
                          callback=callback, error_callback=error_callback)
        
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cancelled, False if not found or already done
        """
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False
        
    def get_stats(self) -> Dict:
        """Get task execution statistics"""
        return {
            **self._stats,
            'pending_tasks': len(self._tasks),
            'queue_size': self._priority_queue.qsize() if hasattr(self._priority_queue, 'qsize') else 0
        }
        
    async def wait_for_all(self, timeout: Optional[float] = None):
        """Wait for all pending tasks to complete"""
        if not self._tasks:
            return
            
        pending = [task for task in self._tasks.values() if not task.done()]
        if pending:
            await asyncio.wait(pending, timeout=timeout)

# Global async manager instance
_async_manager: Optional[AsyncManager] = None

def get_async_manager() -> AsyncManager:
    """Get or create global async manager instance"""
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncManager()
    return _async_manager

async def init_async_manager():
    """Initialize global async manager"""
    manager = get_async_manager()
    await manager.start()
    return manager

async def shutdown_async_manager():
    """Shutdown global async manager"""
    global _async_manager
    if _async_manager:
        await _async_manager.stop()
        _async_manager = None

# Convenience functions for common operations
async def run_async(coro, timeout: Optional[float] = None) -> Any:
    """Run a coroutine with optional timeout"""
    manager = get_async_manager()
    task_id = await manager.submit(coro, timeout=timeout)
    # Wait for completion (simplified - in practice, use callback)
    return task_id

async def run_in_thread(func, *args, timeout: Optional[float] = None) -> Any:
    """Run a synchronous function in thread pool"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_async_manager()._executor, func, *args)
