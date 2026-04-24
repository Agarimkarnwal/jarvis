"""
JARVIS Context Manager - Conversation memory and context tracking
Maintains conversation history, user preferences, and session state
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import pickle

logger = logging.getLogger(__name__)

@dataclass
class UserPreference:
    """User preference entry"""
    key: str
    value: Any
    category: str = "general"  # 'general', 'app', 'system', 'ai'
    confidence: float = 1.0  # How sure we are (0-1)
    last_updated: datetime = field(default_factory=datetime.now)
    
@dataclass
class SessionContext:
    """Current session context"""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    current_task: Optional[str] = None
    mood: str = "neutral"  # 'neutral', 'happy', 'frustrated', 'focused'
    recent_files: List[str] = field(default_factory=list)
    recent_apps: List[str] = field(default_factory=list)
    active_browser_tabs: List[str] = field(default_factory=list)
    
@dataclass
class ConversationTurn:
    """Single conversation turn"""
    user_message: str
    assistant_response: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[str] = None
    commands_executed: List[str] = field(default_factory=list)
    successful: bool = True

class ContextManager:
    """
    Manages conversation context, user preferences, and session state
    - Short-term memory: Current conversation (SQLite)
    - Long-term memory: User preferences (SQLite)
    - Session tracking: Current session state (in-memory)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            cache_dir = Path.home() / '.jarvis' / 'memory'
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / 'context.db')
            
        self.db_path = db_path
        self.session: Optional[SessionContext] = None
        
        # In-memory caches
        self._conversation_cache: List[ConversationTurn] = []
        self._preference_cache: Dict[str, UserPreference] = {}
        
        self._init_db()
        
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Conversation history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_message TEXT,
                    assistant_response TEXT,
                    timestamp REAL,
                    intent TEXT,
                    commands_executed TEXT,
                    successful INTEGER
                )
            """)
            
            # User preferences
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    category TEXT,
                    confidence REAL,
                    last_updated REAL
                )
            """)
            
            # Sessions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time REAL,
                    end_time REAL,
                    summary TEXT
                )
            """)
            
            conn.commit()
            
    def start_session(self, session_id: Optional[str] = None) -> SessionContext:
        """Start a new session"""
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        self.session = SessionContext(session_id=session_id)
        
        # Save to DB
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, start_time) VALUES (?, ?)",
                (session_id, datetime.now().timestamp())
            )
            conn.commit()
            
        logger.info(f"Started session: {session_id}")
        return self.session
        
    def end_session(self, summary: str = ""):
        """End current session"""
        if not self.session:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET end_time = ?, summary = ? WHERE session_id = ?",
                (datetime.now().timestamp(), summary, self.session.session_id)
            )
            conn.commit()
            
        logger.info(f"Ended session: {self.session.session_id}")
        self.session = None
        
    def add_conversation(self, turn: ConversationTurn):
        """Add conversation turn to history"""
        # Add to cache
        self._conversation_cache.append(turn)
        
        # Trim cache
        if len(self._conversation_cache) > 100:
            self._conversation_cache = self._conversation_cache[-50:]
            
        # Save to DB
        if self.session:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO conversations 
                       (session_id, user_message, assistant_response, timestamp, 
                        intent, commands_executed, successful)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        self.session.session_id,
                        turn.user_message,
                        turn.assistant_response,
                        turn.timestamp.timestamp(),
                        turn.intent,
                        json.dumps(turn.commands_executed),
                        1 if turn.successful else 0
                    )
                )
                conn.commit()
                
    def get_recent_conversation(self, n: int = 10) -> List[ConversationTurn]:
        """Get recent conversation turns"""
        # Try cache first
        if len(self._conversation_cache) >= n:
            return self._conversation_cache[-n:]
            
        # Load from DB
        if self.session:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT user_message, assistant_response, timestamp, intent, 
                              commands_executed, successful
                       FROM conversations 
                       WHERE session_id = ?
                       ORDER BY timestamp DESC
                       LIMIT ?""",
                    (self.session.session_id, n)
                )
                
                turns = []
                for row in cursor.fetchall():
                    turns.append(ConversationTurn(
                        user_message=row[0],
                        assistant_response=row[1],
                        timestamp=datetime.fromtimestamp(row[2]),
                        intent=row[3],
                        commands_executed=json.loads(row[4]) if row[4] else [],
                        successful=bool(row[5])
                    ))
                    
                return list(reversed(turns))
                
        return []
        
    def get_conversation_summary(self, n: int = 5) -> str:
        """Get text summary of recent conversation"""
        turns = self.get_recent_conversation(n)
        
        if not turns:
            return "No previous conversation"
            
        lines = []
        for turn in turns:
            user_msg = turn.user_message[:60] + "..." if len(turn.user_message) > 60 else turn.user_message
            assistant_msg = turn.assistant_response[:60] + "..." if len(turn.assistant_response) > 60 else turn.assistant_response
            lines.append(f"User: {user_msg}")
            lines.append(f"Assistant: {assistant_msg}")
            lines.append("")
            
        return "\n".join(lines)
        
    def set_preference(self, preference: UserPreference):
        """Set user preference"""
        # Update cache
        self._preference_cache[preference.key] = preference
        
        # Save to DB
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO preferences 
                   (key, value, category, confidence, last_updated)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    preference.key,
                    pickle.dumps(preference.value),
                    preference.category,
                    preference.confidence,
                    preference.last_updated.timestamp()
                )
            )
            conn.commit()
            
        logger.debug(f"Set preference: {preference.key} = {preference.value}")
        
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        # Try cache first
        if key in self._preference_cache:
            return self._preference_cache[key].value
            
        # Load from DB
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM preferences WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                return pickle.loads(row[0])
                
        return default
        
    def get_preferences_by_category(self, category: str) -> Dict[str, Any]:
        """Get all preferences in a category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT key, value FROM preferences WHERE category = ?",
                (category,)
            )
            return {row[0]: pickle.loads(row[1]) for row in cursor.fetchall()}
            
    def update_session(self, **kwargs):
        """Update current session context"""
        if not self.session:
            return
            
        for key, value in kwargs.items():
            if hasattr(self.session, key):
                setattr(self.session, key, value)
                
    def get_session_context(self) -> Optional[SessionContext]:
        """Get current session context"""
        return self.session
        
    def add_recent_file(self, file_path: str):
        """Add file to recent files list"""
        if self.session:
            self.session.recent_files.insert(0, file_path)
            self.session.recent_files = self.session.recent_files[:10]  # Keep last 10
            
    def add_recent_app(self, app_name: str):
        """Add app to recent apps list"""
        if self.session:
            self.session.recent_apps.insert(0, app_name)
            self.session.recent_apps = self.session.recent_apps[:10]
            
    def get_recent_files(self) -> List[str]:
        """Get recently accessed files"""
        return self.session.recent_files if self.session else []
        
    def get_recent_apps(self) -> List[str]:
        """Get recently opened apps"""
        return self.session.recent_apps if self.session else []
        
    def search_conversation_history(self, keyword: str, n: int = 10) -> List[ConversationTurn]:
        """Search conversation history for keyword"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT user_message, assistant_response, timestamp, intent
                   FROM conversations 
                   WHERE user_message LIKE ? OR assistant_response LIKE ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (f"%{keyword}%", f"%{keyword}%", n)
            )
            
            turns = []
            for row in cursor.fetchall():
                turns.append(ConversationTurn(
                    user_message=row[0],
                    assistant_response=row[1],
                    timestamp=datetime.fromtimestamp(row[2]),
                    intent=row[3]
                ))
                
            return turns
            
    def get_stats(self) -> Dict:
        """Get context manager statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Conversation count
            cursor = conn.execute("SELECT COUNT(*) FROM conversations")
            conv_count = cursor.fetchone()[0]
            
            # Preference count
            cursor = conn.execute("SELECT COUNT(*) FROM preferences")
            pref_count = cursor.fetchone()[0]
            
            # Session count
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            session_count = cursor.fetchone()[0]
            
            return {
                "total_conversations": conv_count,
                "total_preferences": pref_count,
                "total_sessions": session_count,
                "cached_conversations": len(self._conversation_cache),
                "cached_preferences": len(self._preference_cache),
                "current_session": self.session.session_id if self.session else None,
                "db_path": self.db_path
            }

# Global instance
_context_manager: Optional[ContextManager] = None

def get_context_manager() -> ContextManager:
    """Get or create global context manager"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
