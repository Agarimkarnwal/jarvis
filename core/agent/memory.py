"""
JARVIS Agent Memory - Tiered Memory System
Tier 1: User Memory (persistent across workspaces)
Tier 2: Repository Memory (workspace-specific)
Tier 3: Session Memory (temporary task context)
Optimized for i3/12GB with LanceDB
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Single memory entry"""
    key: str
    value: Any
    tier: str  # 'user', 'repo', 'session'
    created_at: datetime
    access_count: int = 1
    ttl_seconds: Optional[int] = None
    
    def is_valid(self) -> bool:
        if self.ttl_seconds is None:
            return True
        age = (datetime.now() - self.created_at).seconds
        return age < self.ttl_seconds

class MemoryTier:
    """Memory tier with LRU eviction"""
    
    def __init__(self, name: str, max_entries: int = 100):
        self.name = name
        self.max_entries = max_entries
        self.entries: Dict[str, MemoryEntry] = {}
        self._access_order: List[str] = []
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory"""
        if key not in self.entries:
            return None
            
        entry = self.entries[key]
        if not entry.is_valid():
            del self.entries[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None
            
        entry.access_count += 1
        # Update access order (LRU)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return entry.value
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in memory"""
        # Evict if at capacity
        if len(self.entries) >= self.max_entries and key not in self.entries:
            self._evict_lru()
            
        self.entries[key] = MemoryEntry(
            key=key,
            value=value,
            tier=self.name,
            created_at=datetime.now(),
            ttl_seconds=ttl
        )
        
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
    def _evict_lru(self):
        """Evict least recently used entry"""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self.entries:
                del self.entries[lru_key]
                logger.debug(f"Evicted {self.name} memory: {lru_key}")
                
    def clear(self):
        """Clear all entries"""
        self.entries.clear()
        self._access_order.clear()
        
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        expired = [
            k for k, e in self.entries.items()
            if not e.is_valid()
        ]
        for k in expired:
            del self.entries[k]
            if k in self._access_order:
                self._access_order.remove(k)
        return len(expired)

class AgentMemory:
    """
    Tiered memory system for JARVIS Agent
    Optimized for 12GB RAM with aggressive cleanup
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace = workspace_path or str(Path.home() / '.jarvis')
        
        # Three-tier memory system
        self.user_memory = MemoryTier('user', max_entries=50)      # Persistent prefs
        self.repo_memory = MemoryTier('repo', max_entries=100)     # Workspace context
        self.session_memory = MemoryTier('session', max_entries=30) # Task context
        
        # SQLite for persistent storage (low memory footprint)
        self.db_path = Path(self.workspace) / '.jarvis_memory.db'
        self._init_db()
        
        # Load persistent memories
        self._load_persistent()
        
        logger.info("Agent memory initialized (tiered system)")
        
    def _init_db(self):
        """Initialize SQLite database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_memory (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Repository context table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repo_memory (
                repo_hash TEXT,
                key TEXT,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (repo_hash, key)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _load_persistent(self):
        """Load persistent memories from SQLite"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Load user preferences
            cursor.execute('SELECT key, value FROM user_memory')
            for row in cursor.fetchall():
                try:
                    self.user_memory.set(row[0], json.loads(row[1]))
                except:
                    self.user_memory.set(row[0], row[1])
                    
            conn.close()
            logger.debug("Loaded persistent memories")
        except Exception as e:
            logger.warning(f"Failed to load persistent memory: {e}")
            
    def _save_persistent(self, tier: str, key: str, value: Any):
        """Save to persistent storage"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            if tier == 'user':
                cursor.execute(
                    'INSERT OR REPLACE INTO user_memory (key, value) VALUES (?, ?)',
                    (key, json.dumps(value))
                )
            elif tier == 'repo':
                repo_hash = hashlib.md5(self.workspace.encode()).hexdigest()[:16]
                cursor.execute(
                    'INSERT OR REPLACE INTO repo_memory (repo_hash, key, value) VALUES (?, ?, ?)',
                    (repo_hash, key, json.dumps(value))
                )
                
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to save persistent memory: {e}")
            
    def get(self, key: str, tier: Optional[str] = None) -> Optional[Any]:
        """
        Get value from memory
        Searches tiers in order: session -> repo -> user
        """
        if tier:
            if tier == 'session':
                return self.session_memory.get(key)
            elif tier == 'repo':
                return self.repo_memory.get(key)
            elif tier == 'user':
                return self.user_memory.get(key)
            return None
            
        # Search all tiers (session first, most recent)
        for memory_tier in [self.session_memory, self.repo_memory, self.user_memory]:
            value = memory_tier.get(key)
            if value is not None:
                return value
                
        return None
        
    def set(self, key: str, value: Any, tier: str = 'session', persistent: bool = False):
        """
        Set value in memory tier
        
        Args:
            key: Memory key
            value: Value to store
            tier: 'user', 'repo', or 'session'
            persistent: Save to SQLite (for user/repo only)
        """
        if tier == 'session':
            self.session_memory.set(key, value, ttl=3600)  # 1 hour default
        elif tier == 'repo':
            self.repo_memory.set(key, value)
            if persistent:
                self._save_persistent(tier, key, value)
        elif tier == 'user':
            self.user_memory.set(key, value)
            if persistent:
                self._save_persistent(tier, key, value)
                
    def get_conversation_history(self, limit: int = 20) -> List[Dict]:
        """Get recent conversation history"""
        history = self.session_memory.get('_conversation')
        if history:
            return history[-limit:]
        return []
        
    def add_to_conversation(self, role: str, content: str):
        """Add message to conversation history"""
        history = self.session_memory.get('_conversation') or []
        history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 messages (memory optimization)
        if len(history) > 50:
            history = history[-50:]
            
        self.session_memory.set('_conversation', history, ttl=7200)  # 2 hours
        
    def get_context_summary(self) -> str:
        """Generate compact context summary for LLM"""
        parts = []
        
        # User preferences (compact)
        prefs = self._get_compact_prefs()
        if prefs:
            parts.append(f"User: {prefs}")
            
        # Repository context (compact)
        repo_ctx = self._get_compact_repo_context()
        if repo_ctx:
            parts.append(f"Project: {repo_ctx}")
            
        # Session notes
        notes = self.session_memory.get('_session_notes')
        if notes:
            parts.append(f"Notes: {notes}")
            
        return ' | '.join(parts) if parts else ''
        
    def _get_compact_prefs(self) -> str:
        """Get compact user preferences"""
        prefs = []
        editor = self.user_memory.get('editor')
        if editor:
            prefs.append(f"editor={editor}")
        style = self.user_memory.get('code_style')
        if style:
            prefs.append(f"style={style}")
        return ','.join(prefs) if prefs else ''
        
    def _get_compact_repo_context(self) -> str:
        """Get compact repository context"""
        ctx = []
        lang = self.repo_memory.get('primary_language')
        if lang:
            ctx.append(f"lang={lang}")
        framework = self.repo_memory.get('framework')
        if framework:
            ctx.append(f"fw={framework}")
        return ','.join(ctx) if ctx else ''
        
    def cleanup(self):
        """Cleanup expired entries (call periodically)"""
        total = 0
        total += self.session_memory.cleanup_expired()
        total += self.repo_memory.cleanup_expired()
        
        if total > 0:
            logger.debug(f"Cleaned up {total} expired memory entries")
            
    def clear_session(self):
        """Clear session memory (new task)"""
        self.session_memory.clear()
        logger.debug("Session memory cleared")
        
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            'user_entries': len(self.user_memory.entries),
            'repo_entries': len(self.repo_memory.entries),
            'session_entries': len(self.session_memory.entries),
            'total_entries': (
                len(self.user_memory.entries) +
                len(self.repo_memory.entries) +
                len(self.session_memory.entries)
            ),
            'max_entries': (
                self.user_memory.max_entries +
                self.repo_memory.max_entries +
                self.session_memory.max_entries
            )
        }
