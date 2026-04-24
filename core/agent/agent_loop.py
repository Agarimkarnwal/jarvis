"""
JARVIS Agent Loop - Perception-Planning-Execution (PPE)
The core orchestration loop that makes JARVIS agentic
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .planner import TaskPlanner, TaskAnalysis, TaskComplexity
from .orchestrator import SupervisorAgent, TaskPlan, WorkerType
from .memory import AgentMemory

logger = logging.getLogger(__name__)

class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    PERCEIVING = "perceiving"      # Understanding context
    PLANNING = "planning"          # Creating task plan
    EXECUTING = "executing"        # Running tasks
    OBSERVING = "observing"        # Checking results
    REFLECTING = "reflecting"      # Analyzing outcomes
    COMPLETE = "complete"          # Task done
    ERROR = "error"                # Failed

@dataclass
class AgentTask:
    """High-level task for the agent"""
    id: str
    query: str
    state: AgentState = AgentState.IDLE
    plan: Optional[TaskPlan] = None
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    iterations: int = 0
    max_iterations: int = 5

class AgentLoop:
    """
    JARVIS Agent Loop
    
    Perception → Planning → Execution → Observation → Reflection → [Loop]
    
    This is what makes JARVIS truly agentic - it can:
    1. Understand complex goals
    2. Plan multi-step solutions
    3. Execute with multiple workers
    4. Observe results
    5. Self-correct on errors
    6. Learn from outcomes
    """
    
    def __init__(self, llm_client=None, supervisor: Optional[SupervisorAgent] = None):
        self.llm = llm_client
        self.planner = TaskPlanner(llm_client)
        self.supervisor = supervisor or SupervisorAgent(llm_client)
        self.memory = AgentMemory()
        
        # State tracking
        self.current_task: Optional[AgentTask] = None
        self.state: AgentState = AgentState.IDLE
        self._state_callbacks: List[Callable] = []
        
        # Statistics
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_iterations': 0,
            'avg_task_duration': 0.0
        }
        
        logger.info("Agent Loop initialized (PPE architecture)")
        
    def register_state_callback(self, callback: Callable[[AgentState, AgentState], None]):
        """Register callback for state changes"""
        self._state_callbacks.append(callback)
        
    def _set_state(self, new_state: AgentState):
        """Update agent state with callbacks"""
        old_state = self.state
        self.state = new_state
        
        for callback in self._state_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"State callback error: {e}")
                
        logger.debug(f"Agent state: {old_state.value} → {new_state.value}")
        
    async def run(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main agent loop - Execute user request autonomously
        
        Args:
            query: User's natural language request
            context: Optional context (files, history, etc.)
            
        Returns:
            Execution results
        """
        start_time = datetime.now()
        
        # Create task
        task = AgentTask(
            id=f"task_{start_time.strftime('%Y%m%d_%H%M%S')}",
            query=query
        )
        self.current_task = task
        
        logger.info(f"=" * 60)
        logger.info(f"AGENT TASK: {query}")
        logger.info(f"=" * 60)
        
        try:
            # === PERCEPTION PHASE ===
            self._set_state(AgentState.PERCEIVING)
            await self._perceive(task, context)
            
            # Main execution loop
            while task.state != AgentState.COMPLETE and task.state != AgentState.ERROR:
                task.iterations += 1
                self.stats['total_iterations'] += 1
                
                if task.iterations > task.max_iterations:
                    task.error = "Max iterations exceeded"
                    self._set_state(AgentState.ERROR)
                    break
                    
                # === PLANNING PHASE ===
                self._set_state(AgentState.PLANNING)
                await self._plan(task)
                
                # === EXECUTION PHASE ===
                self._set_state(AgentState.EXECUTING)
                execution_result = await self._execute(task)
                
                # === OBSERVATION PHASE ===
                self._set_state(AgentState.OBSERVING)
                observation = await self._observe(task, execution_result)
                
                # === REFLECTION PHASE ===
                self._set_state(AgentState.REFLECTING)
                should_continue = await self._reflect(task, observation)
                
                if not should_continue:
                    if task.error:
                        self._set_state(AgentState.ERROR)
                    else:
                        self._set_state(AgentState.COMPLETE)
                        
            # Task complete
            task.completed_at = datetime.now()
            duration = (task.completed_at - task.created_at).total_seconds()
            
            # Update stats
            if task.state == AgentState.COMPLETE:
                self.stats['tasks_completed'] += 1
            else:
                self.stats['tasks_failed'] += 1
                
            # Update average duration
            n = self.stats['tasks_completed'] + self.stats['tasks_failed']
            self.stats['avg_task_duration'] = (
                (self.stats['avg_task_duration'] * (n - 1) + duration) / n
            )
            
            # Store in memory
            self.memory.add_to_conversation('user', query)
            self.memory.add_to_conversation(
                'assistant',
                self._format_result(task.results)
            )
            
            logger.info(f"=" * 60)
            logger.info(f"TASK COMPLETE in {duration:.1f}s ({task.iterations} iterations)")
            logger.info(f"=" * 60)
            
            return {
                'success': task.state == AgentState.COMPLETE,
                'query': query,
                'results': task.results,
                'error': task.error,
                'duration': duration,
                'iterations': task.iterations,
                'plan': task.plan
            }
            
        except Exception as e:
            logger.error(f"Agent loop error: {e}")
            return {
                'success': False,
                'query': query,
                'results': {},
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds(),
                'iterations': task.iterations if task else 0
            }
            
        finally:
            self.current_task = None
            self._set_state(AgentState.IDLE)
            
    async def _perceive(self, task: AgentTask, context: Optional[Dict]):
        """
        PERCEPTION: Gather context and understand the task
        
        - Analyze user intent
        - Load relevant memories
        - Identify required context
        """
        logger.info("[PERCEIVE] Analyzing intent and gathering context...")
        
        # Analyze intent
        analysis = self.planner.analyze_intent(task.query)
        
        # Load relevant memories
        memories = self.memory.get_context_summary()
        
        # Store in task
        task.results['_analysis'] = {
            'goal': analysis.goal,
            'complexity': analysis.complexity.value,
            'workers_needed': [w.value for w in analysis.required_workers],
            'memories': memories
        }
        
        logger.info(f"[PERCEIVE] Goal: {analysis.goal}")
        logger.info(f"[PERCEIVE] Complexity: {analysis.complexity.value}")
        logger.info(f"[PERCEIVE] Workers: {[w.value for w in analysis.required_workers]}")
        
    async def _plan(self, task: AgentTask):
        """
        PLANNING: Create execution plan
        
        - Break down into steps
        - Identify dependencies
        - Estimate duration
        """
        logger.info("[PLAN] Creating execution plan...")
        
        # Get analysis from perception
        analysis_data = task.results.get('_analysis', {})
        
        # Create plan
        plan = self.planner.create_plan(task.query)
        task.plan = plan
        
        logger.info(f"[PLAN] {len(plan.steps)} steps, ~{plan.estimated_duration}s estimated")
        for i, step in enumerate(plan.steps, 1):
            deps = f" (depends on: {step.depends_on})" if step.depends_on else ""
            logger.info(f"[PLAN] Step {i}: {step.worker_type.value} - {step.description[:50]}{deps}")
            
    async def _execute(self, task: AgentTask) -> Dict[str, Any]:
        """
        EXECUTION: Run the plan
        
        - Dispatch tasks to workers
        - Monitor progress
        - Collect results
        """
        logger.info("[EXECUTE] Running plan...")
        
        if not task.plan:
            return {'error': 'No plan to execute'}
            
        # Execute via supervisor
        result = await self.supervisor.execute_plan(task.plan)
        
        # Store results
        for step_id, step_result in result.get('results', {}).items():
            task.results[step_id] = step_result
            
        logger.info(f"[EXECUTE] Complete: {result.get('success', False)}")
        
        return result
        
    async def _observe(self, task: AgentTask, execution_result: Dict) -> Dict[str, Any]:
        """
        OBSERVATION: Analyze execution results
        
        - Check for errors
        - Validate outputs
        - Determine success/failure
        """
        logger.info("[OBSERVE] Analyzing results...")
        
        success = execution_result.get('success', False)
        failed_tasks = execution_result.get('failed_tasks', [])
        
        observation = {
            'success': success,
            'failed_tasks': failed_tasks,
            'total_results': len(execution_result.get('results', {})),
            'timestamp': datetime.now().isoformat()
        }
        
        if failed_tasks:
            # Collect error information
            errors = []
            for step in task.plan.steps if task.plan else []:
                if step.id in failed_tasks and step.error:
                    errors.append(f"{step.id}: {step.error}")
            observation['errors'] = errors
            
        logger.info(f"[OBSERVE] Success: {success}, Failed: {len(failed_tasks)}")
        
        return observation
        
    async def _reflect(self, task: AgentTask, observation: Dict) -> bool:
        """
        REFLECTION: Decide next action
        
        - If success: complete task
        - If failure: plan recovery or retry
        - Return False to stop, True to continue
        """
        logger.info("[REFLECT] Evaluating outcomes...")
        
        if observation.get('success', False):
            logger.info("[REFLECT] Task successful, completing...")
            return False  # Stop loop, we're done
            
        # Check if we should retry
        errors = observation.get('errors', [])
        if errors and task.iterations < task.max_iterations:
            logger.info(f"[REFLECT] Errors found, planning recovery...")
            
            # Refine plan with error feedback
            if task.plan:
                error_msg = '; '.join(errors)
                task.plan = self.planner.refine_plan(task.plan, error_msg)
                logger.info("[REFLECT] Plan refined for retry")
                return True  # Continue with refined plan
                
        # Max retries reached or unrecoverable
        task.error = f"Failed after {task.iterations} attempts: {'; '.join(errors)}"
        logger.info(f"[REFLECT] Task failed: {task.error}")
        return False  # Stop loop
        
    def _format_result(self, results: Dict) -> str:
        """Format results for user display"""
        # Remove internal keys
        display_results = {
            k: v for k, v in results.items()
            if not k.startswith('_')
        }
        
        if not display_results:
            return "Task completed successfully"
            
        # Format based on result type
        parts = []
        for key, value in display_results.items():
            if isinstance(value, dict):
                if 'error' in value:
                    parts.append(f"❌ {key}: {value['error']}")
                elif 'content' in value:
                    parts.append(f"✅ {key}: {value['content'][:100]}...")
                else:
                    parts.append(f"✅ {key}: {str(value)[:100]}")
            else:
                parts.append(f"✅ {key}: {str(value)[:100]}")
                
        return '\n'.join(parts) if parts else "Task completed"
        
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'state': self.state.value,
            'current_task': self.current_task.query if self.current_task else None,
            'memory_stats': self.memory.get_stats(),
            'agent_stats': self.stats,
            'supervisor_stats': self.supervisor.get_stats()
        }
