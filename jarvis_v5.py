#!/usr/bin/env python3
"""
JARVIS v5.0 - AGENTIC AI ASSISTANT
Perception-Planning-Execution (PPE) Architecture
Multi-Agent System (MAS) with Claude Code-level capabilities
Optimized for i3 + 12GB RAM

"Make it EPIC" - Phase 3 Implementation
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import AgentLoop, SupervisorAgent, WorkerType
from core.agent.orchestrator import (
    ResearchWorker, CodeWorker, FileWorker, SystemWorker
)
from core.agent.executor import ToolExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JARVISAgentV5:
    """
    JARVIS v5.0 - The EPIC Agent
    Autonomous AI with multi-agent orchestration
    """
    
    def __init__(self):
        self.tool_executor = ToolExecutor()
        self.supervisor = SupervisorAgent()
        self.agent = AgentLoop(supervisor=self.supervisor)
        self._init_workers()
        
        logger.info("=" * 70)
        logger.info("   JARVIS v5.0 - AGENTIC AI SYSTEM")
        logger.info("   Perception-Planning-Execution Architecture")
        logger.info("   Multi-Agent System with 20+ Tools")
        logger.info("=" * 70)
        
    def _init_workers(self):
        """Initialize all worker agents"""
        tools = self.tool_executor.tools
        
        # Register workers with supervisor
        self.supervisor.register_worker(ResearchWorker(tools))
        self.supervisor.register_worker(CodeWorker(tools))
        self.supervisor.register_worker(FileWorker(tools))
        self.supervisor.register_worker(SystemWorker(tools))
        
        logger.info("Workers initialized: Research, Code, File, System")
        
    async def run_task(self, query: str) -> dict:
        """
        Execute a task through the agent loop
        
        Args:
            query: Natural language task description
            
        Returns:
            Task results
        """
        logger.info(f"\n🎯 TASK: {query}")
        logger.info("-" * 70)
        
        start = datetime.now()
        
        # Run through agent loop
        result = await self.agent.run(query)
        
        duration = (datetime.now() - start).total_seconds()
        
        # Display results
        if result['success']:
            logger.info(f"\n✅ COMPLETE in {duration:.1f}s ({result.get('iterations', 1)} iterations)")
            
            # Show key results
            for key, value in result.get('results', {}).items():
                if not key.startswith('_') and key != 'plan':
                    if isinstance(value, dict):
                        if 'error' in value:
                            logger.info(f"   {key}: ❌ {value['error']}")
                        elif 'content' in value:
                            content = value['content'][:100].replace('\n', ' ')
                            logger.info(f"   {key}: {content}...")
                        else:
                            logger.info(f"   {key}: ✅ {list(value.keys())}")
        else:
            logger.info(f"\n❌ FAILED in {duration:.1f}s")
            if result.get('error'):
                logger.info(f"   Error: {result['error']}")
                
        return result
        
    async def interactive_mode(self):
        """Interactive agent mode"""
        print("\n" + "=" * 70)
        print("   🤖 JARVIS AGENT v5.0 - Interactive Mode")
        print("   Type 'quit' to exit, 'help' for examples")
        print("=" * 70 + "\n")
        
        examples = [
            "Read file: example.txt",
            "Search for Python files",
            "Analyze my system status",
            "Write a Python hello world script",
            "Find and analyze code files",
        ]
        
        while True:
            try:
                query = input("\n📝 You: ").strip()
                
                if not query:
                    continue
                    
                if query.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Goodbye!")
                    break
                    
                if query.lower() == 'help':
                    print("\n📚 Example tasks:")
                    for ex in examples:
                        print(f"   • {ex}")
                    print("\n💡 Try: 'Search for Python files and analyze them'")
                    continue
                    
                # Execute task
                result = await self.run_task(query)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                
    async def demo_mode(self):
        """Demo mode with example tasks"""
        print("\n" + "=" * 70)
        print("   🎬 JARVIS AGENT v5.0 - Demo Mode")
        print("=" * 70)
        
        demo_tasks = [
            "List current directory",
            "Search for Python files",
            "Read file: core/agent/__init__.py",
            "Analyze my system status",
            "Execute command: echo 'Hello from JARVIS!'",
        ]
        
        for i, task in enumerate(demo_tasks, 1):
            print(f"\n{'='*70}")
            print(f"   Demo {i}/{len(demo_tasks)}")
            print(f"{'='*70}")
            
            try:
                await self.run_task(task)
                await asyncio.sleep(1)  # Pause between demos
            except Exception as e:
                logger.error(f"Demo task failed: {e}")
                
        print("\n" + "=" * 70)
        print("   ✅ Demo Complete!")
        print("=" * 70)

def print_status(jarvis: JARVISAgentV5):
    """Print system status"""
    status = jarvis.agent.get_status()
    
    print("\n" + "=" * 70)
    print("   📊 SYSTEM STATUS")
    print("=" * 70)
    print(f"   State: {status['state']}")
    print(f"   Memory: {status['memory_stats']['total_entries']}/{status['memory_stats']['max_entries']} entries")
    print(f"   Tasks: {status['agent_stats']['tasks_completed']} completed, {status['agent_stats']['tasks_failed']} failed")
    print(f"   Iterations: {status['agent_stats']['total_iterations']}")
    print(f"   Workers: {list(status['supervisor_stats']['workers'].keys())}")
    print("=" * 70 + "\n")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS Agent v5.0')
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    parser.add_argument('--task', type=str, help='Run single task and exit')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    
    args = parser.parse_args()
    
    # Initialize JARVIS
    jarvis = JARVISAgentV5()
    
    if args.status:
        print_status(jarvis)
        return
        
    if args.task:
        result = await jarvis.run_task(args.task)
        print("\n📊 Full Result:")
        print(f"   Success: {result['success']}")
        print(f"   Duration: {result['duration']:.1f}s")
        print(f"   Iterations: {result.get('iterations', 1)}")
        
        if result.get('results'):
            print(f"\n   Results:")
            for key, value in result['results'].items():
                if not key.startswith('_'):
                    print(f"      {key}: {type(value).__name__}")
        return
        
    if args.demo:
        await jarvis.demo_mode()
    else:
        await jarvis.interactive_mode()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
