"""
JARVIS AI Brain - Main orchestrator combining LLM + Commands + Context
The central intelligence that makes JARVIS truly smart
"""

import asyncio
import logging
from typing import Optional, Dict, List, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from ollama_client import OllamaClient, get_ollama_client
from context_manager import ContextManager, get_context_manager, ConversationTurn
from intent_classifier import IntentClassifier, get_intent_classifier, IntentType
from async_command_processor import AsyncCommandProcessor, get_async_command_processor

logger = logging.getLogger(__name__)

class ResponseType(Enum):
    """Types of responses"""
    COMMAND = "command"         # Direct command execution
    AI = "ai"                   # AI-generated response
    HYBRID = "hybrid"           # AI explanation + command execution
    ERROR = "error"             # Error response

@dataclass
class AIResponse:
    """Structured AI response"""
    text: str
    response_type: ResponseType
    commands_executed: List[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.commands_executed is None:
            self.commands_executed = []

class AIBrain:
    """
    JARVIS AI Brain - Central intelligence orchestrator
    
    Combines:
    - Ollama LLM for natural conversations
    - Intent classifier for command routing
    - Command processor for system actions
    - Context manager for memory
    """
    
    def __init__(self):
        self.ollama: Optional[OllamaClient] = None
        self.context: Optional[ContextManager] = None
        self.intent_classifier: Optional[IntentClassifier] = None
        self.command_processor: Optional[AsyncCommandProcessor] = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize all AI brain components"""
        try:
            logger.info("🧠 Initializing JARVIS AI Brain...")
            
            # Initialize Ollama (AI core)
            self.ollama = get_ollama_client()
            if not await self.ollama.initialize():
                logger.warning("Ollama not available - running in command-only mode")
                
            # Initialize context manager (memory)
            self.context = get_context_manager()
            self.context.start_session()
            
            # Initialize intent classifier (NLU)
            self.intent_classifier = get_intent_classifier()
            
            # Initialize command processor (actions)
            self.command_processor = get_async_command_processor()
            
            self._initialized = True
            logger.info("✅ AI Brain initialized")
            return True
            
        except Exception as e:
            logger.error(f"AI Brain initialization failed: {e}")
            return False
            
    @property
    def available(self) -> bool:
        """Check if AI brain is available (Ollama running)"""
        return self._initialized and self.ollama and self.ollama.available
        
    async def process(self, user_input: str) -> AIResponse:
        """
        Process user input through AI brain
        
        Args:
            user_input: What the user said/typed
            
        Returns:
            AIResponse with text and metadata
        """
        if not self._initialized:
            return AIResponse(
                text="AI Brain not initialized. Please restart JARVIS.",
                response_type=ResponseType.ERROR,
                confidence=0.0
            )
            
        try:
            # Step 1: Classify intent
            intent = self.intent_classifier.classify(user_input)
            logger.debug(f"Intent: {intent.type.value} ({intent.confidence:.2f}) - {intent.action}")
            
            # Step 2: Route based on intent type and confidence
            if intent.type == IntentType.COMMAND and intent.confidence > 0.85:
                # High confidence command - execute directly
                return await self._handle_command(user_input, intent)
                
            elif intent.type == IntentType.UNKNOWN:
                # Unknown intent - use AI
                if self.available:
                    return await self._handle_ai_conversation(user_input)
                else:
                    return AIResponse(
                        text="I'm not sure how to do that. Try saying 'help' to see what I can do.",
                        response_type=ResponseType.AI,
                        confidence=0.5
                    )
                    
            else:
                # Medium confidence - use AI with context
                if self.available:
                    return await self._handle_hybrid(user_input, intent)
                else:
                    # Fallback to direct command
                    return await self._handle_command(user_input, intent)
                    
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return AIResponse(
                text=f"I encountered an error: {str(e)}",
                response_type=ResponseType.ERROR,
                confidence=0.0
            )
            
    async def process_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        Process user input with streaming response
        
        Yields:
            Response chunks for real-time display
        """
        response = await self.process(user_input)
        
        # Stream the response text word by word
        words = response.text.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
            await asyncio.sleep(0.01)  # Small delay for natural feel
            
    async def _handle_command(self, user_input: str, intent) -> AIResponse:
        """Handle direct command execution"""
        logger.info(f"Executing command: {intent.action}")
        
        # Execute through command processor
        result = await self.command_processor.process_command_async(user_input)
        
        # Record in context
        turn = ConversationTurn(
            user_message=user_input,
            assistant_response=result.message,
            intent=intent.action,
            commands_executed=[intent.action],
            successful=result.success
        )
        self.context.add_conversation(turn)
        
        return AIResponse(
            text=result.message,
            response_type=ResponseType.COMMAND,
            commands_executed=[intent.action],
            confidence=intent.confidence
        )
        
    async def _handle_ai_conversation(self, user_input: str) -> AIResponse:
        """Handle pure AI conversation"""
        logger.info("Using AI for conversation")
        
        # Get conversation context
        conversation_history = self.context.get_conversation_summary(5)
        
        # Build enhanced prompt with context
        enhanced_prompt = f"""Previous conversation:
{conversation_history}

User: {user_input}

Respond naturally as JARVIS:"""
        
        # Get AI response
        response_text = await self.ollama.chat_sync(enhanced_prompt)
        
        # Record in context
        turn = ConversationTurn(
            user_message=user_input,
            assistant_response=response_text,
            intent="conversation",
            successful=True
        )
        self.context.add_conversation(turn)
        
        return AIResponse(
            text=response_text,
            response_type=ResponseType.AI,
            confidence=0.8
        )
        
    async def _handle_hybrid(self, user_input: str, intent) -> AIResponse:
        """Handle hybrid AI + Command"""
        logger.info(f"Hybrid handling: {intent.action}")
        
        # Execute command first
        command_result = await self.command_processor.process_command_async(user_input)
        
        # Get AI explanation/refinement
        prompt = f"""The user asked: "{user_input}"
I executed: {intent.action}
Result: {command_result.message}

Provide a brief, natural response acknowledging what was done:"""
        
        if self.available:
            ai_text = await self.ollama.chat_sync(prompt)
        else:
            ai_text = command_result.message
            
        # Record in context
        turn = ConversationTurn(
            user_message=user_input,
            assistant_response=ai_text,
            intent=intent.action,
            commands_executed=[intent.action],
            successful=command_result.success
        )
        self.context.add_conversation(turn)
        
        return AIResponse(
            text=ai_text,
            response_type=ResponseType.HYBRID,
            commands_executed=[intent.action],
            confidence=intent.confidence
        )
        
    async def handle_task(self, user_input: str) -> AIResponse:
        """
        Handle complex multi-step tasks
        
        Example: "Help me prepare for my meeting"
        -> AI plans steps -> Executes each step -> Summarizes
        """
        if not self.available:
            return AIResponse(
                text="Complex task planning requires AI brain. Please ensure Ollama is running.",
                response_type=ResponseType.ERROR
            )
            
        # Ask AI to break down the task
        planning_prompt = f"""The user wants me to help with: "{user_input}"

Break this down into 3-5 specific, actionable steps that I can execute.
Format: numbered list with clear actions.

Steps:"""
        
        plan = await self.ollama.chat_sync(planning_prompt)
        
        # Parse steps and execute
        executed_commands = []
        results = []
        
        # Simple parsing (in production, use structured output)
        lines = plan.strip().split('\n')
        for line in lines:
            if line.strip() and (line[0].isdigit() or line.strip().startswith('-')):
                step = line.strip().lstrip('0123456789.- ')
                
                # Try to execute each step
                try:
                    result = await self.process(step)
                    executed_commands.extend(result.commands_executed)
                    results.append(result.text)
                except Exception as e:
                    results.append(f"Could not complete: {step}")
                    
        # Generate summary
        summary_prompt = f"""I completed these tasks:
{chr(10).join(f"- {r}" for r in results)}

Provide a brief, natural summary of what was accomplished:"""
        
        summary = await self.ollama.chat_sync(summary_prompt)
        
        return AIResponse(
            text=summary,
            response_type=ResponseType.HYBRID,
            commands_executed=executed_commands,
            confidence=0.85
        )
        
    def get_status(self) -> Dict:
        """Get AI brain status"""
        return {
            "initialized": self._initialized,
            "ai_available": self.available,
            "ollama_status": "connected" if (self.ollama and self.ollama.available) else "disconnected",
            "model": self.ollama.model if self.ollama else None,
            "context_stats": self.context.get_stats() if self.context else None,
            "conversation_turns": len(self.context._conversation_cache) if self.context else 0
        }
        
    def clear_memory(self):
        """Clear conversation memory"""
        if self.context:
            self.context.clear_context()
        if self.ollama:
            self.ollama.clear_context()
            
    async def shutdown(self):
        """Shutdown AI brain"""
        logger.info("🛑 Shutting down AI Brain...")
        
        if self.context:
            self.context.end_session("AI Brain shutdown")
            
        self._initialized = False
        logger.info("✅ AI Brain shutdown complete")

# Global instance
_ai_brain: Optional[AIBrain] = None

def get_ai_brain() -> AIBrain:
    """Get or create global AI brain"""
    global _ai_brain
    if _ai_brain is None:
        _ai_brain = AIBrain()
    return _ai_brain

async def init_ai_brain() -> bool:
    """Initialize global AI brain"""
    brain = get_ai_brain()
    return await brain.initialize()

async def test_ai_brain():
    """Quick test of AI brain"""
    brain = get_ai_brain()
    
    if not await brain.initialize():
        print("❌ AI Brain initialization failed")
        return
        
    print("✅ AI Brain initialized")
    print(f"Status: {brain.get_status()}")
    
    # Test conversations
    test_inputs = [
        "Hello",
        "What time is it?",
        "Open Chrome",
        "I'm feeling bored today"
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 You: {user_input}")
        response = await brain.process(user_input)
        print(f"🤖 JARVIS: {response.text}")
        print(f"   Type: {response.response_type.value}, Confidence: {response.confidence:.2f}")
        
if __name__ == "__main__":
    asyncio.run(test_ai_brain())
