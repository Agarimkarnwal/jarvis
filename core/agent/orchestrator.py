"""
JARVIS Supervisor Agent - Multi-Agent System Orchestrator
Coordinates specialized worker agents for complex tasks
Pattern: Supervisor-Worker (hierarchical)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class WorkerType(Enum):
    """Types of specialized workers"""
    RESEARCH = "research"        # Web search, information gathering
    CODE = "code"                # Code generation, editing
    FILE = "file"                # File operations, analysis
    SYSTEM = "system"            # System commands, diagnostics
    VERIFY = "verify"            # Testing, validation
    EXECUTE = "execute"          # Execution, deployment

@dataclass
class WorkerTask:
    """Task assigned to a worker"""
    id: str
    worker_type: WorkerType
    description: str
    parameters: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class TaskPlan:
    """Multi-step task plan"""
    goal: str
    steps: List[WorkerTask]
    parallel_groups: List[List[str]]  # Task IDs that can run in parallel
    estimated_duration: int  # seconds

class WorkerAgent:
    """Base class for specialized workers"""
    
    def __init__(self, worker_type: WorkerType, tools: Dict[str, Callable]):
        self.type = worker_type
        self.tools = tools
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_duration': 0.0
        }
        
    async def execute(self, task: WorkerTask) -> Any:
        """Execute a task - override in subclasses"""
        raise NotImplementedError()
        
    def _update_stats(self, duration: float, success: bool):
        """Update worker statistics"""
        if success:
            self.stats['tasks_completed'] += 1
        else:
            self.stats['tasks_failed'] += 1
            
        # Update average duration
        n = self.stats['tasks_completed'] + self.stats['tasks_failed']
        self.stats['avg_duration'] = (
            (self.stats['avg_duration'] * (n - 1) + duration) / n
        )

class ResearchWorker(WorkerAgent):
    """Worker for research and information gathering"""
    
    def __init__(self, tools: Dict[str, Callable]):
        super().__init__(WorkerType.RESEARCH, tools)
        
    async def execute(self, task: WorkerTask) -> Any:
        """Execute research task"""
        start = datetime.now()
        
        try:
            operation = task.parameters.get('operation')
            
            if operation == 'web_search':
                query = task.parameters.get('query')
                result = await self.tools['web_search'](query)
                
            elif operation == 'fetch_url':
                url = task.parameters.get('url')
                result = await self.tools['fetch_url'](url)
                
            elif operation == 'summarize':
                text = task.parameters.get('text')
                result = await self.tools['summarize'](text)
                
            else:
                result = {"error": f"Unknown operation: {operation}"}
                
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=True)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=False)
            return {"error": str(e)}

class CodeWorker(WorkerAgent):
    """Worker for code generation and editing"""
    
    def __init__(self, tools: Dict[str, Callable]):
        super().__init__(WorkerType.CODE, tools)
        
    async def execute(self, task: WorkerTask) -> Any:
        """Execute code task"""
        start = datetime.now()
        
        try:
            operation = task.parameters.get('operation')
            
            if operation == 'generate':
                prompt = task.parameters.get('prompt')
                language = task.parameters.get('language', 'python')
                result = await self.tools['generate_code'](prompt, language)
                
            elif operation == 'edit':
                file_path = task.parameters.get('file_path')
                changes = task.parameters.get('changes')
                result = await self.tools['edit_file'](file_path, changes)
                
            elif operation == 'analyze':
                code = task.parameters.get('code')
                result = await self.tools['analyze_code'](code)
                
            else:
                result = {"error": f"Unknown operation: {operation}"}
                
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=True)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=False)
            return {"error": str(e)}

class FileWorker(WorkerAgent):
    """Worker for file operations"""
    
    def __init__(self, tools: Dict[str, Callable]):
        super().__init__(WorkerType.FILE, tools)
        
    async def execute(self, task: WorkerTask) -> Any:
        """Execute file task"""
        start = datetime.now()
        
        try:
            operation = task.parameters.get('operation')
            
            if operation == 'read':
                path = task.parameters.get('path')
                result = await self.tools['read_file'](path)
                
            elif operation == 'write':
                path = task.parameters.get('path')
                content = task.parameters.get('content')
                result = await self.tools['write_file'](path, content)
                
            elif operation == 'search':
                pattern = task.parameters.get('pattern')
                path = task.parameters.get('path', '.')
                result = await self.tools['search_files'](pattern, path)
                
            elif operation == 'list':
                path = task.parameters.get('path', '.')
                result = await self.tools['list_directory'](path)
                
            else:
                result = {"error": f"Unknown operation: {operation}"}
                
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=True)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=False)
            return {"error": str(e)}

class SystemWorker(WorkerAgent):
    """Worker for system operations"""
    
    def __init__(self, tools: Dict[str, Callable]):
        super().__init__(WorkerType.SYSTEM, tools)
        
    async def execute(self, task: WorkerTask) -> Any:
        """Execute system task"""
        start = datetime.now()
        
        try:
            operation = task.parameters.get('operation')
            
            if operation == 'info':
                result = await self.tools['system_info']()
                
            elif operation == 'command':
                cmd = task.parameters.get('command')
                result = await self.tools['execute_command'](cmd)
                
            elif operation == 'manage_process':
                action = task.parameters.get('action')
                pid = task.parameters.get('pid')
                result = await self.tools['manage_process'](action, pid)
                
            else:
                result = {"error": f"Unknown operation: {operation}"}
                
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=True)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self._update_stats(duration, success=False)
            return {"error": str(e)}

class SupervisorAgent:
    """
    Supervisor Agent - Coordinates worker agents
    Manages task planning, dispatch, and result synthesis
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.workers: Dict[WorkerType, WorkerAgent] = {}
        self.active_tasks: Dict[str, WorkerTask] = {}
        self.task_history: List[WorkerTask] = []
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'parallel_executions': 0
        }
        
    def register_worker(self, worker: WorkerAgent):
        """Register a worker agent"""
        self.workers[worker.type] = worker
        logger.info(f"Registered worker: {worker.type.value}")
        
    async def execute_plan(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        Execute a task plan with parallelization
        
        Args:
            plan: TaskPlan with steps and parallel groups
            
        Returns:
            Results from all tasks
        """
        logger.info(f"Executing plan: {plan.goal}")
        logger.info(f"Total steps: {len(plan.steps)}")
        
        results = {}
        completed_tasks = set()
        
        # Execute each parallel group
        for group in plan.parallel_groups:
            # Get tasks in this group
            group_tasks = [
                t for t in plan.steps
                if t.id in group and t.status == 'pending'
            ]
            
            # Check dependencies
            ready_tasks = [
                t for t in group_tasks
                if all(d in completed_tasks for d in t.depends_on)
            ]
            
            if ready_tasks:
                logger.info(f"Executing {len(ready_tasks)} tasks in parallel")
                
                # Execute in parallel
                tasks_coros = [
                    self._execute_single_task(t)
                    for t in ready_tasks
                ]
                
                group_results = await asyncio.gather(*tasks_coros, return_exceptions=True)
                
                # Process results
                for task, result in zip(ready_tasks, group_results):
                    if isinstance(result, Exception):
                        task.status = 'failed'
                        task.error = str(result)
                        results[task.id] = {"error": str(result)}
                    else:
                        task.status = 'completed'
                        task.result = result
                        completed_tasks.add(task.id)
                        results[task.id] = result
                        
                self.stats['parallel_executions'] += 1
                
        # Check for failed tasks
        failed = [t for t in plan.steps if t.status == 'failed']
        if failed:
            logger.warning(f"{len(failed)} tasks failed")
            
        return {
            'success': len(failed) == 0,
            'results': results,
            'failed_tasks': [t.id for t in failed],
            'stats': self.get_stats()
        }
        
    async def _execute_single_task(self, task: WorkerTask) -> Any:
        """Execute a single task"""
        worker = self.workers.get(task.worker_type)
        
        if not worker:
            raise ValueError(f"No worker registered for type: {task.worker_type}")
            
        task.status = 'running'
        task.started_at = datetime.now()
        
        self.active_tasks[task.id] = task
        self.stats['total_tasks'] += 1
        
        try:
            result = await worker.execute(task)
            self.stats['successful_tasks'] += 1
            return result
            
        except Exception as e:
            self.stats['failed_tasks'] += 1
            raise e
            
        finally:
            task.completed_at = datetime.now()
            self.task_history.append(task)
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
                
    def get_stats(self) -> Dict:
        """Get supervisor statistics"""
        return {
            **self.stats,
            'active_tasks': len(self.active_tasks),
            'workers': {wt.value: w.stats for wt, w in self.workers.items()}
        }
        
    def get_worker_status(self) -> Dict[str, str]:
        """Get status of all workers"""
        return {
            wt.value: 'ready' if w else 'not_registered'
            for wt, w in self.workers.items()
        }
