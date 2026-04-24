"""
JARVIS Intent Classifier - Natural language understanding
Classifies user intent and extracts entities for smart routing
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Intent types for classification"""
    COMMAND = "command"           # System command (open, close, search)
    CONVERSATION = "conversation"   # General chat (greeting, question)
    TASK = "task"                 # Multi-step task
    INFORMATION = "information"   # Information request
    ENTERTAINMENT = "entertainment" # Fun/entertainment
    PRODUCTIVITY = "productivity"   # Work-related
    SYSTEM = "system"             # System control
    UNKNOWN = "unknown"

class ConfidenceLevel(Enum):
    """Confidence levels for intent classification"""
    HIGH = 0.9      # >90% sure
    MEDIUM = 0.7    # 70-90% sure
    LOW = 0.5       # 50-70% sure
    UNCERTAIN = 0.3 # <50% sure

@dataclass
class Intent:
    """Classified intent with metadata"""
    type: IntentType
    confidence: float
    action: Optional[str] = None  # Specific action (e.g., "open_chrome")
    entities: Dict[str, str] = None  # Extracted entities
    raw_text: str = ""
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}

@dataclass
class Entity:
    """Extracted entity"""
    type: str       # 'app', 'file', 'time', 'person', etc.
    value: str      # The actual value
    start: int      # Start position in text
    end: int        # End position

class IntentClassifier:
    """
    Classifies user intent from natural language
    Uses pattern matching + keyword analysis
    """
    
    def __init__(self):
        # Command patterns (high priority)
        self.command_patterns = {
            # System commands
            r'\b(status|system info|how\s+(is|are)\s+(system|computer|pc))\b': 
                (IntentType.COMMAND, 'system_status', 0.95),
            r'\b(open|launch|start)\s+(chrome|browser|internet)\b': 
                (IntentType.COMMAND, 'open_chrome', 0.95),
            r'\b(open|launch|start)\s+(notepad|text editor)\b': 
                (IntentType.COMMAND, 'open_notepad', 0.95),
            r'\b(open|launch|start)\s+(calculator|calc)\b': 
                (IntentType.COMMAND, 'open_calculator', 0.95),
            r'\b(open|launch|start)\s+(explorer|file manager|files?)\b': 
                (IntentType.COMMAND, 'open_explorer', 0.95),
            r'\b(open|launch|start)\s+(vs\s*code|code|vscode)\b': 
                (IntentType.COMMAND, 'open_vscode', 0.95),
            r'\b(open|launch|start)\s+(spotify|music)\b': 
                (IntentType.COMMAND, 'open_spotify', 0.95),
            r'\b(open|launch|start)\s+(discord|chat)\b': 
                (IntentType.COMMAND, 'open_discord', 0.95),
            
            # File commands
            r'\b(find|search|locate)\s+(file|document)\b': 
                (IntentType.COMMAND, 'find_file', 0.9),
            r'\b(open|show)\s+(downloads|documents|desktop|pictures)\b': 
                (IntentType.COMMAND, 'open_folder', 0.9),
            r'\b(create|make)\s+(folder|directory)\b': 
                (IntentType.COMMAND, 'create_folder', 0.9),
            
            # Web commands
            r'\b(search|google|look\s+up)\s+(for\s+)?(.+)\b': 
                (IntentType.COMMAND, 'web_search', 0.9),
            r'\b(open|go\s+to)\s+(youtube|github|gmail|reddit)\b': 
                (IntentType.COMMAND, 'open_website', 0.9),
            
            # Time commands
            r'\b(what\s+)?time\s+(is\s+it|now)\??\b': 
                (IntentType.COMMAND, 'get_time', 0.98),
            r'\b(what\s+)?date\s+(is\s+it|today)\??\b': 
                (IntentType.COMMAND, 'get_date', 0.98),
            r'\bwhat\s+day\s+(is\s+it|today)\??\b': 
                (IntentType.COMMAND, 'get_day', 0.98),
            
            # System control
            r'\b(shutdown|turn\s+off|power\s+off)\s+(computer|pc|system)\b': 
                (IntentType.COMMAND, 'system_shutdown', 0.95),
            r'\b(restart|reboot)\s+(computer|pc|system)\b': 
                (IntentType.COMMAND, 'system_restart', 0.95),
            r'\b(sleep|hibernate)\b': 
                (IntentType.COMMAND, 'system_sleep', 0.95),
            r'\b(lock)\s+(computer|screen|pc)\b': 
                (IntentType.COMMAND, 'system_lock', 0.95),
            r'\b(volume\s+(up|down|mute|unmute)|mute|unmute)\b': 
                (IntentType.COMMAND, 'volume_control', 0.9),
        }
        
        # Conversation patterns (low priority, fallback)
        self.conversation_patterns = {
            r'\b(hello|hi|hey|greetings|howdy)\b': 
                (IntentType.CONVERSATION, 'greeting', 0.8),
            r'\b(goodbye|bye|see\s+you|later|night)\b': 
                (IntentType.CONVERSATION, 'farewell', 0.8),
            r'\b(thank\s*(you|s)|thanks|appreciate)\b': 
                (IntentType.CONVERSATION, 'gratitude', 0.8),
            r'\b(how\s+are\s+you|how\s+you\s+doing)\b': 
                (IntentType.CONVERSATION, 'wellbeing', 0.8),
            r'\b(what\s+can\s+you\s+do|what\s+are\s+your\s+features|help)\b': 
                (IntentType.INFORMATION, 'capabilities', 0.85),
        }
        
        # Task patterns (multi-step)
        self.task_patterns = {
            r'\b(help\s+me|prepare|set\s+up|get\s+ready)\b': 
                (IntentType.TASK, 'assistance', 0.85),
            r'\b(organize|clean\s+up|tidy)\b': 
                (IntentType.TASK, 'organization', 0.8),
        }
        
        # Entertainment patterns
        self.entertainment_patterns = {
            r'\b(joke|funny|humor|laugh)\b': 
                (IntentType.ENTERTAINMENT, 'joke', 0.85),
            r'\b(story|tell\s+me\s+about|narrative)\b': 
                (IntentType.ENTERTAINMENT, 'story', 0.8),
            r'\b(bored|entertain|something\s+fun)\b': 
                (IntentType.ENTERTAINMENT, 'entertainment', 0.85),
        }
        
        # Productivity patterns
        self.productivity_patterns = {
            r'\b(remind\s+me|set\s+reminder|alarm)\b': 
                (IntentType.PRODUCTIVITY, 'reminder', 0.85),
            r'\b(note|write\s+down|remember\s+this)\b': 
                (IntentType.PRODUCTIVITY, 'note', 0.85),
            r'\b(schedule|calendar|meeting|appointment)\b': 
                (IntentType.PRODUCTIVITY, 'scheduling', 0.85),
        }
        
        # Entity extractors
        self.entity_patterns = {
            'app': r'\b(open|launch|start)\s+([a-zA-Z\s]+?)(?:\s+(?:and|then|please|now)\b|$)',
            'file': r'\b(file|document|pdf|word|excel)\s+(?:called|named)?\s+[\'"]?([^\'"]+?)[\'"]?\b',
            'time': r'\b(at|for|in)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\b',
            'date': r'\b(tomorrow|today|next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            'person': r'\b(from|to|with|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            'search_query': r'\b(search|google|look\s+up|find)\s+(?:for\s+)?["\']?([^"\']+)["\']?',
        }
        
    def classify(self, text: str) -> Intent:
        """
        Classify user intent from text
        
        Args:
            text: User input text
            
        Returns:
            Intent with type, confidence, action, and entities
        """
        text_lower = text.lower().strip()
        
        # Try command patterns first (highest priority)
        for pattern, (intent_type, action, confidence) in self.command_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                entities = self._extract_entities(text_lower, match)
                return Intent(
                    type=intent_type,
                    confidence=confidence,
                    action=action,
                    entities=entities,
                    raw_text=text
                )
        
        # Try task patterns
        for pattern, (intent_type, action, confidence) in self.task_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                entities = self._extract_entities(text_lower, match)
                return Intent(
                    type=intent_type,
                    confidence=confidence,
                    action=action,
                    entities=entities,
                    raw_text=text
                )
                
        # Try entertainment patterns
        for pattern, (intent_type, action, confidence) in self.entertainment_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                return Intent(
                    type=intent_type,
                    confidence=confidence,
                    action=action,
                    raw_text=text
                )
                
        # Try productivity patterns
        for pattern, (intent_type, action, confidence) in self.productivity_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                return Intent(
                    type=intent_type,
                    confidence=confidence,
                    action=action,
                    raw_text=text
                )
        
        # Try conversation patterns (lowest priority)
        for pattern, (intent_type, action, confidence) in self.conversation_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                return Intent(
                    type=intent_type,
                    confidence=confidence,
                    action=action,
                    raw_text=text
                )
        
        # No pattern matched - return unknown
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.0,
            raw_text=text
        )
        
    def _extract_entities(self, text: str, match: re.Match) -> Dict[str, str]:
        """Extract entities from matched text"""
        entities = {}
        
        # Extract app names
        app_match = re.search(self.entity_patterns['app'], text)
        if app_match:
            entities['app'] = app_match.group(2).strip()
            
        # Extract file names
        file_match = re.search(self.entity_patterns['file'], text)
        if file_match:
            entities['file'] = file_match.group(2).strip()
            
        # Extract search queries
        search_match = re.search(self.entity_patterns['search_query'], text)
        if search_match:
            entities['query'] = search_match.group(1).strip()
            
        # Extract times
        time_match = re.search(self.entity_patterns['time'], text)
        if time_match:
            entities['time'] = time_match.group(2).strip()
            
        # Extract dates
        date_match = re.search(self.entity_patterns['date'], text)
        if date_match:
            entities['date'] = date_match.group(1).strip()
            
        return entities
        
    def should_use_ai(self, intent: Intent) -> bool:
        """
        Determine if AI (LLM) should handle this intent
        vs direct command execution
        
        Args:
            intent: Classified intent
            
        Returns:
            True if AI should handle, False for direct command
        """
        # High confidence commands should be executed directly
        if intent.type == IntentType.COMMAND and intent.confidence > 0.85:
            return False
            
        # Medium confidence - let AI decide
        if intent.confidence > 0.6:
            return True
            
        # Low confidence or unknown - definitely use AI
        return True
        
    def get_suggested_commands(self, text: str) -> List[str]:
        """
        Suggest possible commands for ambiguous input
        
        Args:
            text: User input
            
        Returns:
            List of suggested command strings
        """
        suggestions = []
        text_lower = text.lower()
        
        # Check for partial matches
        if 'open' in text_lower:
            suggestions.extend([
                "open chrome",
                "open notepad",
                "open calculator",
                "open file explorer"
            ])
            
        if 'search' in text_lower or 'find' in text_lower:
            suggestions.extend([
                "search web for [topic]",
                "find file [filename]",
                "search downloads folder"
            ])
            
        if 'time' in text_lower or 'date' in text_lower:
            suggestions.extend([
                "what time is it?",
                "what is today's date?"
            ])
            
        return suggestions[:5]  # Limit to 5 suggestions
        
    def batch_classify(self, texts: List[str]) -> List[Intent]:
        """Classify multiple texts"""
        return [self.classify(text) for text in texts]

# Global instance
_classifier: Optional[IntentClassifier] = None

def get_intent_classifier() -> IntentClassifier:
    """Get or create global intent classifier"""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier
