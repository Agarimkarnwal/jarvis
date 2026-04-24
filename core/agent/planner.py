"""
JARVIS Task Planner - Perception-Planning-Execution (PPE)
Breaks complex tasks into executable steps with dependency management
"""

import re
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .orchestrator import WorkerType, WorkerTask, TaskPlan

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"        # 1-2 steps, single worker
    MODERATE = "moderate"    # 3-5 steps, possible parallel
    COMPLEX = "complex"      # 6+ steps, requires planning

@dataclass
class PlanStep:
    """Single step in a plan"""
    id: str
    description: str
    worker_type: WorkerType
    operation: str
    parameters: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    estimated_time: int = 5  # seconds
    
@dataclass
class TaskAnalysis:
    """Analysis of user intent"""
    original_query: str
    goal: str
    complexity: TaskComplexity
    required_workers: List[WorkerType]
    context_needed: List[str]

class TaskPlanner:
    """
    Intelligent Task Planner
    Converts natural language into executable task plans
    """
    
    # Intent patterns for quick classification
    INTENT_PATTERNS = {
        'file_read': r'\b(read|show|display|open|view|get|find)\b.*\b(file|content|text)\b',
        'file_write': r'\b(write|create|save|update|modify|edit)\b.*\b(file|document)\b',
        'file_search': r'\b(search|find|locate|look for)\b.*\b(file|files|pattern)\b',
        'code_generate': r'\b(write|create|generate|make)\b.*\b(code|script|program|function)\b',
        'code_analyze': r'\b(analyze|review|check|examine|debug)\b.*\b(code|script)\b',
        'web_search': r'\b(search|look up|find|google|research)\b.*\b(web|online|internet)\b',
        'web_fetch': r'\b(fetch|get|download|read)\b.*\b(url|website|page|web)\b',
        'system_info': r'\b(status|info|check|monitor|diagnose)\b.*\b(system|computer|cpu|memory)\b',
        'system_exec': r'\b(run|execute|launch|start|open)\b.*\b(program|app|command|script)\b',
        'data_analyze': r'\b(analyze|process|parse|extract)\b.*\b(data|csv|json|excel)\b',
        'multi_step': r'\b(and then|after that|next|finally|step|process)\b',
    }
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self._plan_cache: Dict[str, TaskPlan] = {}
        
    def analyze_intent(self, query: str) -> TaskAnalysis:
        """
        Analyze user intent and classify task complexity
        
        Args:
            query: User's natural language request
            
        Returns:
            TaskAnalysis with goal, complexity, and requirements
        """
        query_lower = query.lower()
        
        # Detect required workers from patterns
        required_workers = []
        
        if re.search(self.INTENT_PATTERNS['file_read'], query_lower) or \
           re.search(self.INTENT_PATTERNS['file_write'], query_lower) or \
           re.search(self.INTENT_PATTERNS['file_search'], query_lower):
            required_workers.append(WorkerType.FILE)
            
        if re.search(self.INTENT_PATTERNS['code_generate'], query_lower) or \
           re.search(self.INTENT_PATTERNS['code_analyze'], query_lower):
            required_workers.append(WorkerType.CODE)
            
        if re.search(self.INTENT_PATTERNS['web_search'], query_lower) or \
           re.search(self.INTENT_PATTERNS['web_fetch'], query_lower):
            required_workers.append(WorkerType.RESEARCH)
            
        if re.search(self.INTENT_PATTERNS['system_info'], query_lower) or \
           re.search(self.INTENT_PATTERNS['system_exec'], query_lower):
            required_workers.append(WorkerType.SYSTEM)
            
        if re.search(self.INTENT_PATTERNS['data_analyze'], query_lower):
            required_workers.append(WorkerType.FILE)
            required_workers.append(WorkerType.CODE)
            
        # Determine complexity
        complexity = TaskComplexity.SIMPLE
        if re.search(self.INTENT_PATTERNS['multi_step'], query_lower):
            complexity = TaskComplexity.COMPLEX
        elif len(required_workers) > 1:
            complexity = TaskComplexity.MODERATE
        elif len(query.split()) > 15:
            complexity = TaskComplexity.MODERATE
            
        # Extract goal (simplified)
        goal = query
        
        return TaskAnalysis(
            original_query=query,
            goal=goal,
            complexity=complexity,
            required_workers=list(set(required_workers)),
            context_needed=[]
        )
        
    def create_plan(self, query: str, analysis: Optional[TaskAnalysis] = None) -> TaskPlan:
        """
        Create execution plan from query
        
        Args:
            query: User request
            analysis: Optional pre-computed analysis
            
        Returns:
            TaskPlan with steps and parallel groups
        """
        if analysis is None:
            analysis = self.analyze_intent(query)
            
        # Check cache for similar queries
        cache_key = self._get_cache_key(query)
        if cache_key in self._plan_cache:
            logger.debug(f"Using cached plan for: {query[:50]}...")
            return self._plan_cache[cache_key]
            
        # Generate plan based on complexity
        if analysis.complexity == TaskComplexity.SIMPLE:
            plan = self._create_simple_plan(query, analysis)
        elif analysis.complexity == TaskComplexity.MODERATE:
            plan = self._create_moderate_plan(query, analysis)
        else:
            plan = self._create_complex_plan(query, analysis)
            
        # Cache plan
        self._plan_cache[cache_key] = plan
        
        # Limit cache size
        if len(self._plan_cache) > 50:
            oldest = list(self._plan_cache.keys())[0]
            del self._plan_cache[oldest]
            
        return plan
        
    def _create_simple_plan(self, query: str, analysis: TaskAnalysis) -> TaskPlan:
        """Create plan for simple tasks (1-2 steps)"""
        steps = []
        
        # Single worker task
        if WorkerType.FILE in analysis.required_workers:
            if 'read' in query.lower() or 'show' in query.lower():
                steps.append(WorkerTask(
                    id='step_1',
                    worker_type=WorkerType.FILE,
                    description=f"Read file for: {query[:50]}...",
                    parameters={'operation': 'read', 'path': self._extract_path(query)}
                ))
            elif 'search' in query.lower() or 'find' in query.lower():
                steps.append(WorkerTask(
                    id='step_1',
                    worker_type=WorkerType.FILE,
                    description=f"Search files for: {query[:50]}...",
                    parameters={'operation': 'search', 'pattern': self._extract_pattern(query)}
                ))
                
        elif WorkerType.SYSTEM in analysis.required_workers:
            steps.append(WorkerTask(
                id='step_1',
                worker_type=WorkerType.SYSTEM,
                description=f"System operation: {query[:50]}...",
                parameters={'operation': 'info'}
            ))
            
        elif WorkerType.RESEARCH in analysis.required_workers:
            steps.append(WorkerTask(
                id='step_1',
                worker_type=WorkerType.RESEARCH,
                description=f"Web search: {query[:50]}...",
                parameters={'operation': 'web_search', 'query': query}
            ))
            
        else:
            # Default to code worker for unknown
            steps.append(WorkerTask(
                id='step_1',
                worker_type=WorkerType.CODE,
                description=f"Process: {query[:50]}...",
                parameters={'operation': 'analyze', 'code': query}
            ))
            
        return TaskPlan(
            goal=analysis.goal,
            steps=steps,
            parallel_groups=[['step_1']],
            estimated_duration=5
        )
        
    def _create_moderate_plan(self, query: str, analysis: TaskAnalysis) -> TaskPlan:
        """Create plan for moderate tasks (3-5 steps, some parallel)"""
        steps = []
        step_id = 0
        
        # Example: "Search for Python files and analyze them"
        if WorkerType.FILE in analysis.required_workers:
            step_id += 1
            search_step = WorkerTask(
                id=f'step_{step_id}',
                worker_type=WorkerType.FILE,
                description='Search for relevant files',
                parameters={'operation': 'search', 'pattern': '*.py'}
            )
            steps.append(search_step)
            
        if WorkerType.CODE in analysis.required_workers:
            step_id += 1
            code_step = WorkerTask(
                id=f'step_{step_id}',
                worker_type=WorkerType.CODE,
                description='Analyze found code',
                parameters={'operation': 'analyze'},
                depends_on=['step_1'] if step_id > 1 else []
            )
            steps.append(code_step)
            
        if WorkerType.RESEARCH in analysis.required_workers:
            step_id += 1
            research_step = WorkerTask(
                id=f'step_{step_id}',
                worker_type=WorkerType.RESEARCH,
                description='Research context',
                parameters={'operation': 'web_search', 'query': analysis.goal}
            )
            steps.append(research_step)
            
        # Determine parallel groups
        parallel_groups = []
        independent = [s.id for s in steps if not s.depends_on]
        if independent:
            parallel_groups.append(independent)
            
        dependent = [s.id for s in steps if s.depends_on]
        for dep_id in dependent:
            parallel_groups.append([dep_id])
            
        return TaskPlan(
            goal=analysis.goal,
            steps=steps,
            parallel_groups=parallel_groups,
            estimated_duration=sum(s.estimated_time for s in steps)
        )
        
    def _create_complex_plan(self, query: str, analysis: TaskAnalysis) -> TaskPlan:
        """
        Create plan for complex tasks (6+ steps)
        Uses LLM for sophisticated planning if available
        """
        # For now, use moderate plan as base and extend
        base_plan = self._create_moderate_plan(query, analysis)
        
        # Add verification step
        verify_step = WorkerTask(
            id=f'step_{len(base_plan.steps) + 1}',
            worker_type=WorkerType.VERIFY,
            description='Verify results',
            parameters={'operation': 'validate'},
            depends_on=[s.id for s in base_plan.steps]
        )
        base_plan.steps.append(verify_step)
        base_plan.parallel_groups.append([verify_step.id])
        
        base_plan.estimated_duration = sum(s.estimated_time for s in base_plan.steps)
        
        return base_plan
        
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        # Normalize query
        normalized = re.sub(r'[^\w]', '', query.lower())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
        
    def _extract_path(self, query: str) -> str:
        """Extract file path from query (simplified)"""
        # Look for common path patterns
        patterns = [
            r'\b(\w+\.(?:py|txt|json|csv|md|js|html))\b',
            r'\b(\./[\w/]+\.\w+)\b',
            r'\b(~?/[\w/]+\.\w+)\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
                
        return '.'
        
    def _extract_pattern(self, query: str) -> str:
        """Extract search pattern from query"""
        # Common patterns
        if 'python' in query.lower() or '.py' in query:
            return '*.py'
        if 'text' in query.lower() or '.txt' in query:
            return '*.txt'
        if 'json' in query.lower():
            return '*.json'
            
        return '*'
        
    def refine_plan(self, plan: TaskPlan, feedback: str) -> TaskPlan:
        """
        Refine plan based on execution feedback
        
        Args:
            plan: Original plan
            feedback: Error message or feedback
            
        Returns:
            Refined plan
        """
        logger.info(f"Refining plan based on feedback: {feedback[:100]}...")
        
        # Add recovery steps
        recovery_step = WorkerTask(
            id=f'recovery_{len(plan.steps)}',
            worker_type=WorkerType.CODE,
            description=f'Recover from: {feedback[:50]}',
            parameters={'operation': 'analyze', 'code': feedback}
        )
        
        plan.steps.append(recovery_step)
        plan.parallel_groups.append([recovery_step.id])
        
        return plan
