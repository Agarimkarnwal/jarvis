"""
JARVIS AI Assistant V4 - With AI Brain
Combines performance optimizations with natural language AI
Runs on i3 + 12GB RAM using local Llama 3.2
"""

import asyncio
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

# Lazy imports
_ai_brain = None

class JARVIS_V4:
    """
    JARVIS V4 - AI-Powered Assistant
    
    Features:
    - Natural language conversations with Llama 3.2
    - Context-aware responses
    - Smart command routing (AI vs Direct)
    - Conversation memory
    - All V3 performance optimizations
    """
    
    VERSION = "4.0"
    NAME = "JARVIS AI"
    
    def __init__(self):
        self.start_time = time.time()
        self._init_stage = "created"
        self._ai_brain = None
        
        # Performance tracking
        self._performance_stats = {
            'startup_time': 0,
            'init_stages': {},
            'commands_processed': 0,
            'ai_responses': 0,
            'cache_hits': 0
        }
        
    async def initialize(self, fast_mode: bool = False):
        """Initialize JARVIS V4 with AI brain"""
        init_start = time.time()
        
        print("="*60)
        print(f"🤖 {self.NAME} v{self.VERSION} Initializing...")
        print("="*60)
        
        # Initialize AI Brain (includes async manager, cache, commands)
        ai_start = time.time()
        from ai_brain import init_ai_brain, get_ai_brain
        
        ai_initialized = await init_ai_brain()
        self._ai_brain = get_ai_brain()
        
        self._performance_stats['init_stages']['ai_brain'] = time.time() - ai_start
        
        # Calculate total startup time
        self._performance_stats['startup_time'] = time.time() - self.start_time
        self._init_stage = "ready"
        
        # Print status
        status = self._ai_brain.get_status()
        print(f"\n✅ JARVIS V4 Ready!")
        print(f"   Startup: {self._performance_stats['startup_time']:.2f}s")
        print(f"   AI Brain: {'Active' if status['ai_available'] else 'Offline (Command Mode)'}")
        
        if status['ai_available']:
            print(f"   Model: {status['model']}")
            print(f"   Context: Ready")
        else:
            print(f"   Note: Install Ollama + Llama 3.2 for AI features")
            
        print("="*60 + "\n")
        
    async def process(self, user_input: str) -> str:
        """
        Process user input through AI brain
        
        Args:
            user_input: What the user said/typed
            
        Returns:
            Response text
        """
        if not self._ai_brain:
            return "JARVIS not initialized"
            
        start = time.time()
        
        # Process through AI brain
        response = await self._ai_brain.process(user_input)
        
        # Track performance
        duration = time.time() - start
        self._performance_stats['commands_processed'] += 1
        if response.response_type.value in ['ai', 'hybrid']:
            self._performance_stats['ai_responses'] += 1
            
        logger.debug(f"Processed in {duration:.3f}s: {user_input[:30]}...")
        
        return response.text
        
    async def process_stream(self, user_input: str):
        """Process with streaming response"""
        if not self._ai_brain:
            yield "JARVIS not initialized"
            return
            
        async for chunk in self._ai_brain.process_stream(user_input):
            yield chunk
            
    def get_status(self) -> Dict:
        """Get JARVIS status"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        ai_status = self._ai_brain.get_status() if self._ai_brain else {}
        
        return {
            'version': self.VERSION,
            'status': self._init_stage,
            'uptime': time.time() - self.start_time,
            'startup_time': self._performance_stats['startup_time'],
            'commands_processed': self._performance_stats['commands_processed'],
            'ai_responses': self._performance_stats['ai_responses'],
            'memory': {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
            },
            'ai_status': ai_status
        }
        
    def clear_memory(self):
        """Clear conversation memory"""
        if self._ai_brain:
            self._ai_brain.clear_memory()
            print("🧠 Conversation memory cleared")
            
    async def shutdown(self):
        """Graceful shutdown"""
        print("\n🛑 Shutting down JARVIS V4...")
        
        if self._ai_brain:
            await self._ai_brain.shutdown()
            
        print("✅ Shutdown complete")

# Console interface
async def run_console_mode(jarvis: JARVIS_V4):
    """Run interactive console mode"""
    print("[CONSOLE] Natural Language Mode - Type 'quit' to exit")
    print("Type 'clear' to reset memory | 'stats' for metrics")
    print("-"*60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nJARVIS: Goodbye!")
                break
                
            if user_input.lower() == 'clear':
                jarvis.clear_memory()
                continue
                
            if user_input.lower() == 'stats':
                status = jarvis.get_status()
                print(f"\n[STATS]")
                print(f"   Version: {status['version']}")
                print(f"   Startup: {status['startup_time']:.2f}s")
                print(f"   Memory: {status['memory']['rss_mb']:.1f} MB")
                print(f"   Commands: {status['commands_processed']}")
                print(f"   AI Responses: {status['ai_responses']}")
                if status['ai_status']:
                    print(f"   AI: {status['ai_status'].get('ai_available', False)}")
                continue
                
            # Process input
            print("[...]", end="\r")
            start = time.time()
            
            response = await jarvis.process(user_input)
            
            duration = time.time() - start
            print(f"JARVIS: {response}")
            print(f"   [{duration*1000:.1f}ms]")
            
        except KeyboardInterrupt:
            print("\n\nJARVIS: Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

# Performance test
async def run_performance_test(jarvis: JARVIS_V4):
    """Run performance benchmark"""
    print("\n" + "="*60)
    print("TEST: JARVIS V4 Performance & AI Test")
    print("="*60)
    
    status = jarvis.get_status()
    
    # Test 1: Startup
    print(f"\n[1] Startup: {status['startup_time']:.2f}s")
    print("   Target: <5s", "PASS" if status['startup_time'] < 5 else "FAIL")
    
    # Test 2: Memory
    print(f"\n[2] Memory: {status['memory']['rss_mb']:.1f} MB")
    print("   Target: <2GB", "PASS" if status['memory']['rss_mb'] < 2000 else "FAIL")
    
    # Test 3: Command responses
    print(f"\n[3] Command Responses:")
    commands = ['hello', 'time', 'date', 'status', 'open chrome']
    for cmd in commands:
        start = time.time()
        response = await jarvis.process(cmd)
        duration = time.time() - start
        print(f"   {cmd:15} {duration*1000:6.1f}ms - {response[:40]}...")
        
    # Test 4: AI responses (if available)
    if status['ai_status'].get('ai_available'):
        print(f"\n[4] AI Responses:")
        ai_prompts = [
            "How are you today?",
            "What can you help me with?",
            "Tell me about yourself"
        ]
        for prompt in ai_prompts:
            start = time.time()
            response = await jarvis.process(prompt)
            duration = time.time() - start
            print(f"   {prompt[:20]:20} {duration*1000:6.1f}ms - {response[:40]}...")
    else:
        print(f"\n[4] AI: Not available (Ollama offline)")
        
    # Test 5: Context memory
    print(f"\n[5] Context Memory:")
    print("   Testing conversation continuity...")
    await jarvis.process("My name is Boss")
    response = await jarvis.process("What is my name?")
    print(f"   Response: {response[:60]}...")
    
    print("\n" + "="*60)

# Main entry
async def main():
    """Main async entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS V4 - AI Powered')
    parser.add_argument('--fast', action='store_true', help='Fast startup')
    parser.add_argument('--test', action='store_true', help='Run tests')
    parser.add_argument('--command', type=str, help='Single command')
    
    args = parser.parse_args()
    
    # Create and initialize
    jarvis = JARVIS_V4()
    
    try:
        await jarvis.initialize(fast_mode=args.fast)
        
        if args.test:
            await run_performance_test(jarvis)
        elif args.command:
            response = await jarvis.process(args.command)
            print(response)
        else:
            await run_console_mode(jarvis)
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await jarvis.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
