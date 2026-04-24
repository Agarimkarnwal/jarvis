"""
JARVIS Ollama Client - Async LLM wrapper with streaming support
Optimized for i3 + 12GB RAM with lightweight Llama 3.2 model
"""

import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
@dataclass
class ChatResponse:
    """Complete chat response"""
    content: str
    done: bool = False
    total_duration: float = 0.0
    load_duration: float = 0.0
    prompt_eval_count: int = 0
    eval_count: int = 0

class OllamaClient:
    """
    Async Ollama client for JARVIS AI brain
    - Streaming support for real-time responses
    - Context management
    - Performance optimized for i3/12GB
    """
    
    DEFAULT_MODEL = "llama3.2:3b"
    DEFAULT_OPTIONS = {
        "temperature": 0.7,
        "num_predict": 512,  # Limit tokens for speed
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
    }
    
    def __init__(self, model: str = None, host: str = "http://localhost:11434"):
        self.model = model or self.DEFAULT_MODEL
        self.host = host
        self.client = None
        self._available = False
        
        # Conversation context
        self.context_window: List[ChatMessage] = []
        self.max_context = 20  # Keep last 20 exchanges
        
        # System prompt (JARVIS personality)
        self.system_prompt = """You are JARVIS (Just A Rather Very Intelligent System), an advanced AI assistant running locally on a laptop.

Your characteristics:
- Professional yet friendly tone
- Efficient and concise responses
- Technically knowledgeable
- Proactive in offering help
- You can control the computer (open apps, search files, system commands)
- You remember context from previous messages

When responding:
- Keep answers under 3 sentences when possible
- Be helpful and action-oriented
- If you don't know something, say so honestly
- Use technical terms appropriately for the user's level"""
        
    async def initialize(self) -> bool:
        """Initialize Ollama connection"""
        try:
            import ollama
            self.client = ollama.AsyncClient(host=self.host)
            
            # Test connection
            await self.client.list()
            self._available = True
            
            logger.info(f"Ollama client initialized with model: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Ollama initialization failed: {e}")
            self._available = False
            return False
            
    @property
    def available(self) -> bool:
        """Check if Ollama is available"""
        return self._available
        
    async def chat(self, 
                   message: str, 
                   stream: bool = True,
                   system: str = None,
                   options: Dict = None) -> AsyncGenerator[str, None]:
        """
        Send chat message and get streaming response
        
        Args:
            message: User message
            stream: Whether to stream response
            system: Optional system prompt override
            options: Generation options override
            
        Yields:
            Response text chunks
        """
        if not self._available:
            yield "AI brain not available. Is Ollama running?"
            return
            
        try:
            # Build messages array
            messages = [{"role": "system", "content": system or self.system_prompt}]
            
            # Add context (recent conversation)
            for msg in self.context_window[-self.max_context:]:
                messages.append({"role": msg.role, "content": msg.content})
                
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Prepare options
            opts = {**self.DEFAULT_OPTIONS, **(options or {})}
            
            logger.debug(f"Sending chat to Ollama: {message[:50]}...")
            
            # Stream response
            full_response = ""
            
            if stream:
                # Streaming mode
                response = await self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    options=opts
                )
                
                async for chunk in response:
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        full_response += content
                        yield content
            else:
                # Non-streaming mode
                response = await self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    options=opts
                )
                full_response = response['message']['content']
                yield full_response
                    
            # Save to context
            self.add_to_context("user", message)
            self.add_to_context("assistant", full_response)
            
            logger.debug(f"Response complete: {full_response[:50]}...")
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"Error: {str(e)}"
            
    async def chat_sync(self, 
                       message: str,
                       system: str = None,
                       options: Dict = None) -> str:
        """
        Non-streaming chat (returns full response)
        
        Args:
            message: User message
            system: Optional system prompt
            options: Generation options
            
        Returns:
            Full response text
        """
        full_response = ""
        async for chunk in self.chat(message, stream=True, system=system, options=options):
            full_response += chunk
        return full_response
        
    def add_to_context(self, role: str, content: str):
        """Add message to conversation context"""
        msg = ChatMessage(role=role, content=content)
        self.context_window.append(msg)
        
        # Trim if too long
        if len(self.context_window) > self.max_context:
            self.context_window = self.context_window[-self.max_context:]
            
    def clear_context(self):
        """Clear conversation context"""
        self.context_window.clear()
        logger.info("Context cleared")
        
    def get_context_summary(self) -> str:
        """Get summary of current context"""
        if not self.context_window:
            return "No conversation history"
            
        lines = []
        for msg in self.context_window[-5:]:  # Last 5 messages
            prefix = "You: " if msg.role == "user" else "JARVIS: "
            content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            lines.append(f"{prefix}{content}")
            
        return "\n".join(lines)
        
    async def generate(self, 
                      prompt: str,
                      options: Dict = None) -> str:
        """
        Raw generation without conversation context
        
        Args:
            prompt: Raw prompt text
            options: Generation options
            
        Returns:
            Generated text
        """
        if not self._available:
            return "AI brain not available"
            
        try:
            opts = {**self.DEFAULT_OPTIONS, **(options or {})}
            
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options=opts
            )
            
            return response.get('response', '')
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error: {str(e)}"
            
    async def check_model(self) -> Dict:
        """Check if model is available and get info"""
        if not self._available:
            return {"available": False, "error": "Ollama not connected"}
            
        try:
            # List models
            models = await self.client.list()
            
            # Find our model
            for model in models.get('models', []):
                if model['name'] == self.model:
                    return {
                        "available": True,
                        "name": model['name'],
                        "size": model.get('size', 0),
                        "parameter_size": model.get('details', {}).get('parameter_size', 'unknown'),
                        "quantization": model.get('details', {}).get('quantization_level', 'unknown')
                    }
                    
            return {
                "available": False,
                "error": f"Model {self.model} not found",
                "installed_models": [m['name'] for m in models.get('models', [])]
            }
            
        except Exception as e:
            return {"available": False, "error": str(e)}

# Global client instance
_ollama_client: Optional[OllamaClient] = None

def get_ollama_client() -> OllamaClient:
    """Get or create global Ollama client"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

async def init_ollama() -> bool:
    """Initialize Ollama globally"""
    client = get_ollama_client()
    return await client.initialize()

async def test_ollama():
    """Quick test of Ollama"""
    client = get_ollama_client()
    
    if not await client.initialize():
        print("❌ Ollama not available")
        return
        
    # Check model
    model_info = await client.check_model()
    print(f"Model info: {model_info}")
    
    # Test chat
    print("\n🧪 Testing chat...")
    response = await client.chat_sync("Hello! Say 'JARVIS AI ready' if you can hear me.")
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
