"""
JARVIS AI Core - Advanced AI Processing and Response Generation
Optimized for local processing on i3 12GB RAM systems
"""

import asyncio
import logging
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama not available, using fallback AI")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence transformers not available")

@dataclass
class AIConfig:
    """AI engine configuration"""
    primary_model: str = "llama3:8b"
    fallback_model: str = "phi3:mini"
    embedding_model: str = "all-minilm:l6-v2"
    temperature: float = 0.7
    max_tokens: int = 512
    context_window: int = 4096
    quantization: str = "4-bit"
    cache_size: int = 1000

@dataclass
class ConversationMessage:
    """Conversation message structure"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    embedding: Optional[np.ndarray] = None

class ConversationMemory:
    """Advanced conversation memory management"""
    
    def __init__(self, max_messages: int = 100):
        self.max_messages = max_messages
        self.messages: List[ConversationMessage] = []
        self.context_keywords: Dict[str, float] = {}
        self.user_preferences: Dict[str, Any] = {}
        
    def add_message(self, role: str, content: str, embedding: Optional[np.ndarray] = None):
        """Add message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            embedding=embedding
        )
        
        self.messages.append(message)
        
        # Maintain message limit
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
            
        # Extract and update context keywords
        self._update_context_keywords(content)
        
    def get_context(self, window_size: int = 10) -> List[ConversationMessage]:
        """Get recent conversation context"""
        return self.messages[-window_size:] if self.messages else []
        
    def _update_context_keywords(self, content: str):
        """Extract and weight context keywords"""
        # Simple keyword extraction (can be enhanced with NLP libraries)
        words = content.lower().split()
        for word in words:
            if len(word) > 3:  # Filter short words
                self.context_keywords[word] = self.context_keywords.get(word, 0) + 1
                
    def get_relevant_context(self, query: str, top_k: int = 5) -> List[ConversationMessage]:
        """Get context relevant to current query"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return self.get_context()
            
        # Simple relevance based on keyword matching
        query_words = set(query.lower().split())
        scored_messages = []
        
        for msg in self.messages:
            msg_words = set(msg.content.lower().split())
            overlap = len(query_words.intersection(msg_words))
            scored_messages.append((overlap, msg))
            
        # Sort by relevance and return top_k
        scored_messages.sort(reverse=True, key=lambda x: x[0])
        return [msg for _, msg in scored_messages[:top_k]]

class AICore:
    """Advanced AI processing engine"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize conversation memory
        self.memory = ConversationMemory()
        
        # Initialize AI models
        self.primary_model = None
        self.fallback_model = None
        self.embedding_model = None
        
        # Response cache for performance
        self.response_cache: Dict[str, Tuple[str, datetime]] = {}
        
        # Task planning
        self.current_tasks: List[Dict[str, Any]] = []
        
        # Initialize models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize AI models"""
        if OLLAMA_AVAILABLE:
            try:
                # Pull models if not available
                self._ensure_model_available(self.config.primary_model)
                self._ensure_model_available(self.config.fallback_model)
                self.logger.info("AI models initialized successfully")
            except Exception as e:
                self.logger.error(f"Model initialization failed: {e}")
                
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(self.config.embedding_model)
                self.logger.info("Embedding model initialized")
            except Exception as e:
                self.logger.error(f"Embedding model initialization failed: {e}")
                
    def _ensure_model_available(self, model_name: str):
        """Ensure model is available locally"""
        try:
            models = ollama.list()
            if not any(model['name'].startswith(model_name.split(':')[0]) for model in models['models']):
                self.logger.info(f"Pulling model: {model_name}")
                ollama.pull(model_name)
        except Exception as e:
            self.logger.error(f"Model availability check failed: {e}")
            
    async def generate_response(self, 
                              user_input: str, 
                              context: Optional[List[ConversationMessage]] = None) -> str:
        """Generate AI response to user input"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(user_input)
            if cache_key in self.response_cache:
                cached_response, timestamp = self.response_cache[cache_key]
                if datetime.now() - timestamp < timedelta(hours=1):
                    self.logger.info("Returning cached response")
                    return cached_response
                    
            # Build conversation context
            conversation_context = self._build_context(user_input, context)
            
            # Generate response
            response = await self._generate_with_model(user_input, conversation_context)
            
            # Cache response
            self.response_cache[cache_key] = (response, datetime.now())
            
            # Update memory
            embedding = self._get_embedding(user_input) if self.embedding_model else None
            self.memory.add_message("user", user_input, embedding)
            
            response_embedding = self._get_embedding(response) if self.embedding_model else None
            self.memory.add_message("assistant", response, response_embedding)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return "I apologize, but I'm having trouble processing that right now. Please try again."
            
    def _build_context(self, user_input: str, context: Optional[List[ConversationMessage]]) -> str:
        """Build conversation context for AI model"""
        context_parts = []
        
        # System prompt
        system_prompt = self._get_system_prompt()
        context_parts.append(f"System: {system_prompt}")
        
        # Recent conversation history
        if context:
            for msg in context[-5:]:  # Last 5 messages
                context_parts.append(f"{msg.role.capitalize()}: {msg.content}")
        else:
            # Use memory context
            recent_messages = self.memory.get_context(5)
            for msg in recent_messages:
                context_parts.append(f"{msg.role.capitalize()}: {msg.content}")
                
        return "\n".join(context_parts)
        
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI model"""
        return """You are JARVIS (Just A Rather Very Intelligent System), a sophisticated AI assistant designed to help users with various tasks on their computer. You are:

- Professional and helpful
- Context-aware and proactive  
- Efficient and concise
- Knowledgeable about system operations
- Friendly but formal in tone

Provide clear, actionable responses. If you need to perform system operations, explain what you're going to do first. Always prioritize user privacy and system security."""
        
    async def _generate_with_model(self, user_input: str, context: str) -> str:
        """Generate response using AI model"""
        if not OLLAMA_AVAILABLE:
            return self._fallback_response(user_input)
            
        try:
            # Use primary model first
            response = ollama.generate(
                model=self.config.primary_model,
                prompt=f"{context}\n\nUser: {user_input}\nAssistant:",
                options={
                    'temperature': self.config.temperature,
                    'num_predict': self.config.max_tokens,
                    'top_k': 40,
                    'top_p': 0.9,
                    'repeat_penalty': 1.1
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            self.logger.error(f"Primary model failed: {e}")
            
            # Try fallback model
            try:
                response = ollama.generate(
                    model=self.config.fallback_model,
                    prompt=f"{context}\n\nUser: {user_input}\nAssistant:",
                    options={
                        'temperature': self.config.temperature,
                        'num_predict': min(self.config.max_tokens, 256)  # Smaller for fallback
                    }
                )
                return response['response'].strip()
                
            except Exception as e2:
                self.logger.error(f"Fallback model failed: {e2}")
                return self._fallback_response(user_input)
                
    def _fallback_response(self, user_input: str) -> str:
        """Fallback response when AI models are unavailable"""
        # Simple rule-based responses
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm JARVIS, your AI assistant. How can I help you today?"
            
        elif any(word in input_lower for word in ['help', 'assist']):
            return "I can help you with system control, file management, web searches, and more. What would you like to do?"
            
        elif any(word in input_lower for word in ['thank', 'thanks']):
            return "You're welcome! I'm here to help."
            
        elif 'time' in input_lower:
            return f"The current time is {datetime.now().strftime('%I:%M %p')}."
            
        else:
            return "I understand you're asking about something, but I'm currently operating in limited mode. Please ensure the AI models are properly configured."
            
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
        
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get text embedding for semantic search"""
        if not self.embedding_model:
            return None
            
        try:
            return self.embedding_model.encode(text)
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return None
            
    async def plan_task(self, task_description: str) -> List[Dict[str, Any]]:
        """Break down complex task into steps"""
        task_steps = []
        
        # Simple task planning (can be enhanced with AI)
        if 'open' in task_description.lower():
            app_name = self._extract_app_name(task_description)
            if app_name:
                task_steps.append({
                    'action': 'open_application',
                    'target': app_name,
                    'description': f'Open {app_name}'
                })
                
        elif 'search' in task_description.lower():
            query = self._extract_search_query(task_description)
            if query:
                task_steps.append({
                    'action': 'web_search',
                    'target': query,
                    'description': f'Search for {query}'
                })
                
        elif 'file' in task_description.lower():
            if 'find' in task_description.lower():
                filename = self._extract_filename(task_description)
                if filename:
                    task_steps.append({
                        'action': 'find_file',
                        'target': filename,
                        'description': f'Find file {filename}'
                    })
                    
        return task_steps
        
    def _extract_app_name(self, text: str) -> Optional[str]:
        """Extract application name from text"""
        apps = ['chrome', 'firefox', 'vscode', 'spotify', 'discord', 'steam']
        text_lower = text.lower()
        
        for app in apps:
            if app in text_lower:
                return app
                
        return None
        
    def _extract_search_query(self, text: str) -> Optional[str]:
        """Extract search query from text"""
        # Simple extraction - can be enhanced with NLP
        if 'search for' in text.lower():
            return text.lower().split('search for')[-1].strip()
        elif 'search' in text.lower():
            return text.lower().split('search')[-1].strip()
            
        return None
        
    def _extract_filename(self, text: str) -> Optional[str]:
        """Extract filename from text"""
        # Simple extraction - can be enhanced with NLP
        if 'file' in text.lower():
            words = text.lower().split()
            file_idx = words.index('file')
            if file_idx + 1 < len(words):
                return words[file_idx + 1]
                
        return None
        
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation statistics and summary"""
        return {
            'total_messages': len(self.memory.messages),
            'user_messages': len([m for m in self.memory.messages if m.role == 'user']),
            'assistant_messages': len([m for m in self.memory.messages if m.role == 'assistant']),
            'top_keywords': sorted(self.memory.context_keywords.items(), 
                                 key=lambda x: x[1], reverse=True)[:10],
            'cache_size': len(self.response_cache),
            'active_tasks': len(self.current_tasks)
        }
        
    def clear_cache(self):
        """Clear response cache"""
        self.response_cache.clear()
        self.logger.info("Response cache cleared")
        
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.messages.clear()
        self.memory.context_keywords.clear()
        self.logger.info("Conversation memory cleared")
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        info = {
            'primary_model': self.config.primary_model,
            'fallback_model': self.config.fallback_model,
            'embedding_model': self.config.embedding_model,
            'ollama_available': OLLAMA_AVAILABLE,
            'sentence_transformers_available': SENTENCE_TRANSFORMERS_AVAILABLE
        }
        
        if OLLAMA_AVAILABLE:
            try:
                models = ollama.list()
                info['available_models'] = [model['name'] for model in models['models']]
            except:
                info['available_models'] = []
                
        return info
