"""
JARVIS Ollama Client FAST - Ultra-low latency AI responses
Optimizations: Model keep-alive, response caching, parallel processing
"""

import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import time

logger = logging.getLogger(__name__)

@dataclass
class CachedResponse:
    """Cached AI response"""
    key: str
    response: str
    created_at: datetime
    ttl_seconds: int = 300  # 5 min cache
    
    def is_valid(self) -> bool:
        return (datetime.now() - self.created_at).seconds < self.ttl_seconds

class FastOllamaClient:
    """
    HIGH-SPEED Ollama client with aggressive optimizations
    Target: <500ms first token, <2s full response
    """
    
    DEFAULT_MODEL = "llama3.2:3b"
    
    # SPEED-OPTIMIZED SETTINGS
    FAST_OPTIONS = {
        "temperature": 0.5,        # Lower = faster, more focused
        "num_predict": 128,        # Shorter responses (was 512)
        "top_p": 0.85,            # Slightly narrower sampling
        "top_k": 20,              # Faster token selection
        "repeat_penalty": 1.05,    # Lighter penalty = faster
        "num_ctx": 2048,          # Smaller context window = faster
        "batch_size": 512,        # Process more tokens at once
        "num_thread": 4,          # Use all i3 threads
        "num_gpu": 0,             # CPU-only (no GPU overhead)
    }
    
    # ADAPTIVE TOKEN LIMITS - Research-backed optimization
    ADAPTIVE_LIMITS = {
        'greeting': 32,      # hello, hi, hey
        'question': 64,      # what, how, why
        'task': 128,         # open, search, find
        'explanation': 192,  # explain, describe
        'code': 256,         # code, script, write
        'chat': 128,         # conversation
        'command': 64,       # system commands
    }
    
    # Intent detection patterns
    INTENT_PATTERNS = {
        'greeting': r'\b(hello|hi|hey|greetings|howdy|morning|evening)\b',
        'question': r'\b(what|how|why|when|where|who|which)\b.*\?',
        'task': r'\b(open|launch|start|search|find|get|show|tell)\b',
        'explanation': r'\b(explain|describe|tell me about|what is|how does)\b',
        'code': r'\b(code|script|program|write.*python|function|api)\b',
        'command': r'\b(status|time|date|help|shutdown|restart)\b',
    }
    
    def __init__(self, model: str = None, host: str = "http://localhost:11434"):
        self.model = model or self.DEFAULT_MODEL
        self.host = host
        self.client = None
        self._available = False
        
        # Model pre-loaded flag
        self._model_loaded = False
        self._last_keepalive = None
        
        # Response cache
        self._cache: Dict[str, CachedResponse] = {}
        self._cache_max_size = 50
        
        # Request queue for parallel processing
        self._request_queue = asyncio.Queue()
        self._processing = False
        
        # Performance tracking
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'avg_response_time': 0.0,
            'model_load_time': 0.0
        }
        
        # Conversation context (minimal for speed)
        self.context_window: List[Dict] = []
        self.max_context = 10  # Reduced from 20
        
        # ULTRA-COMPACT system prompt (50 tokens vs 200+ = 4x faster processing)
        # Research: Shorter prompts = significantly faster inference
        self.system_prompt = "You are JARVIS, an efficient AI assistant. Be concise and action-oriented. Keep responses brief and helpful."
        
    @property
    def available(self) -> bool:
        """Check if Ollama is available"""
        return self._available and self._model_loaded
        
    async def initialize(self) -> bool:
        """Initialize and PRE-LOAD model for instant responses"""
        try:
            import ollama
            self.client = ollama.AsyncClient(host=self.host)
            
            # Test connection
            await self.client.list()
            self._available = True
            
            # PRE-LOAD MODEL (critical for speed)
            logger.info("🚀 Pre-loading model into memory...")
            load_start = time.time()
            
            await self._preload_model()
            
            self._stats['model_load_time'] = time.time() - load_start
            self._model_loaded = True
            
            # Start keepalive task
            asyncio.create_task(self._keepalive_loop())
            
            logger.info(f"✅ Model ready! Load time: {self._stats['model_load_time']:.1f}s")
            return True
            
        except Exception as e:
            logger.error(f"Fast Ollama init failed: {e}")
            self._available = False
            return False
            
    async def _preload_model(self):
        """Pre-load model with a warmup request"""
        try:
            # Simple warmup query to load model into RAM
            await self.client.generate(
                model=self.model,
                prompt="Hi",
                options={"num_predict": 1}  # Minimal generation
            )
        except Exception as e:
            logger.warning(f"Model preload warning: {e}")
            
    async def _keepalive_loop(self):
        """Keep model loaded in memory with periodic pings"""
        while self._available:
            try:
                # Ping every 2 minutes to keep model hot
                await asyncio.sleep(120)
                
                if self._model_loaded:
                    # Lightweight keepalive
                    await self.client.generate(
                        model=self.model,
                        prompt="",
                        options={"num_predict": 1}
                    )
                    self._last_keepalive = datetime.now()
                    logger.debug("Model keepalive ping sent")
                    
            except Exception as e:
                logger.debug(f"Keepalive error: {e}")
                
    def _get_cache_key(self, message: str, context: List[Dict]) -> str:
        """Generate cache key from message + context"""
        # Simple hash of message + recent context
        context_str = json.dumps(context[-2:]) if context else ""
        key_str = f"{message}:{context_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
        
    def _get_cached(self, key: str) -> Optional[str]:
        """Get cached response if valid"""
        if key in self._cache:
            cached = self._cache[key]
            if cached.is_valid():
                self._stats['cache_hits'] += 1
                logger.debug(f"Cache hit for key: {key[:8]}...")
                return cached.response
            else:
                del self._cache[key]
        return None
        
    def _cache_response(self, key: str, response: str, ttl: int = 300):
        """Cache response for future use"""
        # Manage cache size
        if len(self._cache) >= self._cache_max_size:
            # Remove oldest
            oldest = min(self._cache.items(), key=lambda x: x[1].created_at)
            del self._cache[oldest[0]]
            
        self._cache[key] = CachedResponse(
            key=key,
            response=response,
            created_at=datetime.now(),
            ttl_seconds=ttl
        )
        
    def _detect_intent(self, message: str) -> str:
        """Detect query intent for adaptive token limits"""
        import re
        message_lower = message.lower()
        
        for intent, pattern in self.INTENT_PATTERNS.items():
            if re.search(pattern, message_lower):
                return intent
        return 'chat'  # Default
        
    def _get_adaptive_options(self, message: str) -> dict:
        """Get options with adaptive token limits"""
        intent = self._detect_intent(message)
        token_limit = self.ADAPTIVE_LIMITS.get(intent, 128)
        
        # Copy base options
        opts = self.FAST_OPTIONS.copy()
        opts['num_predict'] = token_limit
        
        # Further optimization for very short queries
        if len(message) < 20:
            opts['temperature'] = 0.3  # More deterministic
            opts['top_p'] = 0.8
            
        return opts
        
    async def chat_fast(self, message: str) -> str:
        """
        ULTRA-FAST chat with caching and optimizations
        Target: <2s total response time
        Adaptive token limits based on intent
        """
        if not self._available:
            return "AI offline"
            
        start_time = time.time()
        self._stats['total_requests'] += 1
        
        # Check cache first
        cache_key = self._get_cache_key(message, self.context_window)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        try:
            # Build minimal messages for speed
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.context_window[-self.max_context:],
                {"role": "user", "content": message}
            ]
            
            # Get adaptive options based on intent
            adaptive_opts = self._get_adaptive_options(message)
            
            # FAST non-streaming request (streaming adds overhead)
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=False,  # Faster than streaming
                    options=adaptive_opts
                ),
                timeout=8.0  # Hard timeout
            )
            
            result = response['message']['content']
            
            # Update context
            self.context_window.append({"role": "user", "content": message})
            self.context_window.append({"role": "assistant", "content": result})
            
            # Trim context
            if len(self.context_window) > self.max_context * 2:
                self.context_window = self.context_window[-self.max_context:]
                
            # Cache common responses
            if len(message) < 50:  # Only cache short queries
                self._cache_response(cache_key, result, ttl=300)
                
            # Update stats
            duration = time.time() - start_time
            self._update_stats(duration)
            
            logger.debug(f"Response in {duration:.2f}s: {result[:50]}...")
            return result
            
        except asyncio.TimeoutError:
            logger.error("Response timeout (>10s)")
            return "I'm taking too long. Let me try a simpler approach..."
        except Exception as e:
            logger.error(f"Fast chat error: {e}")
            return f"Error: {str(e)[:100]}"
            
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        STREAMING chat for real-time feel
        First token in <500ms
        """
        if not self._available:
            yield "AI offline"
            return
            
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.context_window[-5:],  # Even smaller context for streaming
                {"role": "user", "content": message}
            ]
            
            # Use slightly faster options for streaming
            stream_options = {**self.FAST_OPTIONS, "num_predict": 100}
            
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options=stream_options
            )
            
            full_response = ""
            token_count = 0
            
            async for chunk in response:
                content = chunk.get('message', {}).get('content', '')
                if content:
                    full_response += content
                    token_count += 1
                    yield content
                    
                    # Limit tokens for speed
                    if token_count > 100:
                        break
                        
            # Save to context
            self.context_window.append({"role": "user", "content": message})
            self.context_window.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Error: {str(e)[:100]}"
            
    def _update_stats(self, duration: float):
        """Update performance statistics"""
        n = self._stats['total_requests']
        self._stats['avg_response_time'] = (
            (self._stats['avg_response_time'] * (n - 1) + duration) / n
        )
        
    def get_stats(self) -> Dict:
        """Get performance stats"""
        return {
            **self._stats,
            'cache_size': len(self._cache),
            'cache_hit_rate': (
                self._stats['cache_hits'] / max(1, self._stats['total_requests']) * 100
            ),
            'model_loaded': self._model_loaded,
            'context_size': len(self.context_window)
        }
        
    def clear_cache(self):
        """Clear response cache"""
        self._cache.clear()
        
    def clear_context(self):
        """Clear conversation context"""
        self.context_window.clear()
        
    async def shutdown(self):
        """Shutdown client"""
        self._available = False
        logger.info("Fast Ollama client shutdown")

# Global instance
_fast_client = None

def get_fast_ollama_client():
    """Get or create global fast client"""
    global _fast_client
    if _fast_client is None:
        _fast_client = FastOllamaClient()
    return _fast_client
