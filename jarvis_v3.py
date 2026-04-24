"""
JARVIS AI Assistant V3 - Performance Optimized
Async architecture, smart caching, lazy loading, <3s startup, <2GB memory
"""

import asyncio
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

# Lazy imports - only load when needed
_voice_engine = None
_command_processor = None
_async_manager = None
_cache_manager = None

class JARVIS_V3:
    """
    Performance-optimized JARVIS with:
    - <3 second startup
    - <2GB memory usage
    - Async command processing
    - Smart caching
    - Lazy component loading
    """
    
    VERSION = "3.0"
    NAME = "JARVIS"
    
    def __init__(self):
        self.start_time = time.time()
        self._init_stage = "created"
        
        # Performance tracking
        self._performance_stats = {
            'startup_time': 0,
            'init_stages': {},
            'commands_processed': 0,
            'cache_hits': 0
        }
        
        # Component references (lazy loaded)
        self._voice_engine = None
        self._command_processor = None
        self._async_manager = None
        
    async def initialize(self, fast_mode: bool = False):
        """
        Initialize JARVIS components
        
        Args:
            fast_mode: Skip non-essential initialization for faster startup
        """
        init_start = time.time()
        
        logger.info("🚀 JARVIS V3 Initializing...")
        
        # Stage 1: Core async manager (critical)
        await self._init_async_manager()
        self._performance_stats['init_stages']['async_manager'] = time.time() - init_start
        
        # Stage 2: Cache manager (critical)
        cache_start = time.time()
        from cache_manager import get_cache_manager
        global _cache_manager
        _cache_manager = get_cache_manager()
        self._performance_stats['init_stages']['cache_manager'] = time.time() - cache_start
        
        # Stage 3: Command processor (critical)
        cmd_start = time.time()
        from async_command_processor import get_async_command_processor
        global _command_processor
        _command_processor = get_async_command_processor()
        self._command_processor = _command_processor
        self._performance_stats['init_stages']['command_processor'] = time.time() - cmd_start
        
        if not fast_mode:
            # Stage 4: Voice engine (non-critical, deferred in fast mode)
            voice_start = time.time()
            await self._init_voice_engine()
            self._performance_stats['init_stages']['voice_engine'] = time.time() - voice_start
        else:
            logger.info("⚡ Fast mode: Voice engine deferred")
            self._performance_stats['init_stages']['voice_engine'] = 0
            
        # Calculate total startup time
        self._performance_stats['startup_time'] = time.time() - self.start_time
        self._init_stage = "ready"
        
        logger.info(f"✅ JARVIS V3 Ready! Startup: {self._performance_stats['startup_time']:.2f}s")
        
    async def _init_async_manager(self):
        """Initialize async manager"""
        from async_manager import init_async_manager
        global _async_manager
        _async_manager = await init_async_manager()
        self._async_manager = _async_manager
        
    async def _init_voice_engine(self):
        """Initialize voice engine (lazy)"""
        from voice_engine_v2 import VoiceEngineV2, PYAUDIO_AVAILABLE
        global _voice_engine
        
        if not PYAUDIO_AVAILABLE:
            logger.warning("Voice engine: PyAudio not available, skipping")
            return
            
        _voice_engine = VoiceEngineV2(wake_word="hey jarvis")
        self._voice_engine = _voice_engine
        logger.info("Voice engine initialized")
        
    async def process_command(self, text: str) -> str:
        """
        Process command with performance tracking
        
        Args:
            text: Command text
            
        Returns:
            Response message
        """
        start = time.time()
        
        if not self._command_processor:
            return "JARVIS not initialized"
            
        # Process command
        result = await self._command_processor.process_command_async(text)
        
        # Track performance
        self._performance_stats['commands_processed'] += 1
        duration = time.time() - start
        
        logger.debug(f"Command processed in {duration:.3f}s: {text[:30]}...")
        
        return result.message
        
    async def process_commands_batch(self, commands: List[str]) -> List[str]:
        """
        Process multiple commands in parallel
        
        Args:
            commands: List of command strings
            
        Returns:
            List of responses
        """
        if not self._command_processor:
            return ["JARVIS not initialized"] * len(commands)
            
        results = await self._command_processor.process_commands_batch(commands)
        return [r.message for r in results]
        
    def get_status(self) -> Dict:
        """Get JARVIS status and performance metrics"""
        # Memory usage
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Cache stats
        cache_stats = {}
        if self._command_processor:
            perf = self._command_processor.get_performance_stats()
            cache_stats = perf.get('cache', {})
            
        return {
            'version': self.VERSION,
            'status': self._init_stage,
            'uptime': time.time() - self.start_time,
            'startup_time': self._performance_stats['startup_time'],
            'commands_processed': self._performance_stats['commands_processed'],
            'memory': {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            },
            'cache': cache_stats,
            'init_stages': self._performance_stats['init_stages'],
            'voice_available': self._voice_engine is not None
        }
        
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down JARVIS V3...")
        
        # Stop voice engine
        if self._voice_engine:
            self._voice_engine.stop()
            
        # Stop async manager
        from async_manager import shutdown_async_manager
        await shutdown_async_manager()
        
        logger.info("✅ JARVIS V3 shutdown complete")

# Console interface
async def run_console_mode(jarvis: JARVIS_V3):
    """Run interactive console mode"""
    print("\n" + "="*60)
    print("JARVIS V3 - Performance Optimized")
    print("="*60)
    print("\n[CONSOLE] Console Mode - Type 'quit' to exit")
    print("Type 'stats' for performance metrics")
    print("-"*60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nJARVIS: Goodbye!")
                break
                
            if user_input.lower() == 'stats':
                status = jarvis.get_status()
                print(f"\n[STATS] Performance Stats:")
                print(f"   Startup: {status['startup_time']:.2f}s")
                print(f"   Memory: {status['memory']['rss_mb']:.1f} MB")
                print(f"   Commands: {status['commands_processed']}")
                print(f"   Cache Hit Rate: {status['cache'].get('combined_hit_rate', 0)}%")
                continue
                
            # Process command
            print("[...] Processing...", end="\r")
            start = time.time()
            
            response = await jarvis.process_command(user_input)
            
            duration = time.time() - start
            print(f"[JARVIS] {response}")
            print(f"   [{duration*1000:.1f}ms]")
            
        except KeyboardInterrupt:
            print("\n\nJARVIS: Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

# Performance test mode
async def run_performance_test(jarvis: JARVIS_V3):
    """Run performance benchmark"""
    print("\n" + "="*60)
    print("TEST: JARVIS V3 Performance Test")
    print("="*60)
    
    # Test 1: Startup time
    print(f"\n[1] Startup Time: {jarvis._performance_stats['startup_time']:.2f}s")
    print("   Target: <3s", "PASS" if jarvis._performance_stats['startup_time'] < 3 else "FAIL")
    
    # Test 2: Memory usage
    status = jarvis.get_status()
    print(f"\n[2] Memory Usage: {status['memory']['rss_mb']:.1f} MB")
    print("   Target: <2GB", "PASS" if status['memory']['rss_mb'] < 2000 else "FAIL")
    
    # Test 3: Command response times
    test_commands = ['hello', 'time', 'date', 'status', 'help']
    print(f"\n[3] Command Response Times:")
    
    total_time = 0
    for cmd in test_commands:
        start = time.time()
        response = await jarvis.process_command(cmd)
        duration = time.time() - start
        total_time += duration
        print(f"   {cmd:10} {duration*1000:6.1f}ms - {response[:40]}...")
        
    avg_time = total_time / len(test_commands)
    print(f"\n   Average: {avg_time*1000:.1f}ms")
    print("   Target: <500ms", "PASS" if avg_time < 0.5 else "FAIL")
    
    # Test 4: Batch processing
    print(f"\n[4] Batch Processing (5 commands parallel):")
    batch_start = time.time()
    responses = await jarvis.process_commands_batch(test_commands[:5])
    batch_duration = time.time() - batch_start
    print(f"   Time: {batch_duration*1000:.1f}ms")
    print(f"   Throughput: {len(responses)/batch_duration:.1f} cmd/sec")
    
    # Test 5: Cache performance
    print(f"\n[5] Cache Performance:")
    # Run same commands again (should hit cache)
    cached_start = time.time()
    for cmd in test_commands[:3]:
        await jarvis.process_command(cmd)
    cached_duration = time.time() - cached_start
    print(f"   Cached commands: {cached_duration*1000:.1f}ms")
    print(f"   Speedup: {(total_time/3)/cached_duration:.1f}x")
    
    # Final stats
    final_status = jarvis.get_status()
    print(f"\n" + "="*60)
    print("📊 Final Statistics:")
    print(f"   Commands Processed: {final_status['commands_processed']}")
    print(f"   Cache Hit Rate: {final_status['cache'].get('combined_hit_rate', 0)}%")
    print(f"   Memory: {final_status['memory']['rss_mb']:.1f} MB")
    print("="*60)

# Main entry point
async def main():
    """Main async entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS V3 - Performance Optimized')
    parser.add_argument('--fast', action='store_true', help='Fast startup mode')
    parser.add_argument('--test', action='store_true', help='Run performance tests')
    parser.add_argument('--command', type=str, help='Single command to execute')
    
    args = parser.parse_args()
    
    # Create and initialize JARVIS
    jarvis = JARVIS_V3()
    
    try:
        await jarvis.initialize(fast_mode=args.fast)
        
        if args.test:
            await run_performance_test(jarvis)
        elif args.command:
            response = await jarvis.process_command(args.command)
            print(response)
        else:
            await run_console_mode(jarvis)
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await jarvis.shutdown()

if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
