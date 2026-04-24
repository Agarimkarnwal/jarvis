"""
JARVIS Cache Manager - Multi-tier caching system
In-memory LRU cache + disk cache with SQLite for persistent storage
"""

import sqlite3
import pickle
import hashlib
import json
import time
import logging
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0

class MemoryCache:
    """
    In-memory LRU cache with TTL support
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._current_size = 0
        self._max_size_bytes = 50 * 1024 * 1024  # 50MB default
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
                
            # Check if expired
            if entry.expires_at and time.time() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                return None
                
            # Update access stats
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._hits += 1
            return entry.value
            
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache"""
        with self._lock:
            # Calculate size
            try:
                size = len(pickle.dumps(value))
            except:
                size = 1024  # Estimate
                
            # Check if we need to evict
            while (len(self._cache) >= self.max_size or 
                   self._current_size + size > self._max_size_bytes):
                if not self._evict_lru():
                    break
                    
            # Create entry
            now = time.time()
            expires = now + (ttl or self.default_ttl) if (ttl or self.default_ttl) else None
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=expires,
                size_bytes=size
            )
            
            # Check if updating existing key
            if key in self._cache:
                self._current_size -= self._cache[key].size_bytes
                
            self._cache[key] = entry
            self._current_size += size
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            return True
            
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                self._current_size -= self._cache[key].size_bytes
                del self._cache[key]
                return True
            return False
            
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._current_size = 0
            
    def _evict_lru(self) -> bool:
        """Evict least recently used entry"""
        if not self._cache:
            return False
            
        # Get first item (least recently used)
        key, entry = self._cache.popitem(last=False)
        self._current_size -= entry.size_bytes
        self._evictions += 1
        
        logger.debug(f"Evicted key {key} from memory cache")
        return True
        
    def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed"""
        with self._lock:
            now = time.time()
            expired = [
                key for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]
            
            for key in expired:
                self._current_size -= self._cache[key].size_bytes
                del self._cache[key]
                
            return len(expired)
            
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'entries': len(self._cache),
            'size_bytes': self._current_size,
            'max_size_bytes': self._max_size_bytes,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': round(hit_rate, 2),
            'evictions': self._evictions
        }

class DiskCache:
    """
    Persistent disk cache using SQLite
    """
    
    def __init__(self, db_path: Optional[str] = None, max_size_mb: int = 100):
        if db_path is None:
            cache_dir = Path.home() / '.jarvis' / 'cache'
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / 'disk_cache.db')
            
        self.db_path = db_path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        self._init_db()
        
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at REAL,
                    expires_at REAL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL,
                    size_bytes INTEGER
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed ON cache_entries(last_accessed)
            """)
            
            conn.commit()
            
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, expires_at FROM cache_entries WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                
                if row is None:
                    return None
                    
                value_blob, expires_at = row
                
                # Check if expired
                if expires_at and time.time() > expires_at:
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    conn.commit()
                    return None
                    
                # Update access stats
                conn.execute(
                    """UPDATE cache_entries 
                       SET access_count = access_count + 1, last_accessed = ?
                       WHERE key = ?""",
                    (time.time(), key)
                )
                conn.commit()
                
                return pickle.loads(value_blob)
                
        except Exception as e:
            logger.error(f"Disk cache get error: {e}")
            return None
            
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in disk cache"""
        try:
            # Serialize value
            value_blob = pickle.dumps(value)
            size = len(value_blob)
            
            # Check if we need to make space
            self._ensure_space(size)
            
            now = time.time()
            expires = now + ttl if ttl else None
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache_entries 
                        (key, value, created_at, expires_at, access_count, last_accessed, size_bytes)
                        VALUES (?, ?, ?, ?, 0, ?, ?)""",
                    (key, value_blob, now, expires, now, size)
                )
                conn.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Disk cache set error: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """Delete key from disk cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Disk cache delete error: {e}")
            return False
            
    def clear(self):
        """Clear all disk cache entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries")
                conn.commit()
        except Exception as e:
            logger.error(f"Disk cache clear error: {e}")
            
    def _ensure_space(self, required_bytes: int):
        """Ensure there's enough space, evict if needed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current size
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                total_size = cursor.fetchone()[0] or 0
                
                # Evict oldest entries if needed
                while total_size + required_bytes > self.max_size_bytes:
                    cursor = conn.execute(
                        """SELECT key, size_bytes FROM cache_entries 
                           ORDER BY last_accessed ASC LIMIT 1"""
                    )
                    row = cursor.fetchone()
                    
                    if row is None:
                        break
                        
                    key, size = row
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    total_size -= size
                    
                conn.commit()
                
        except Exception as e:
            logger.error(f"Disk cache space management error: {e}")
            
    def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM cache_entries WHERE expires_at < ?",
                    (time.time(),)
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Disk cache cleanup error: {e}")
            return 0
            
    def get_stats(self) -> Dict:
        """Get disk cache statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache_entries")
                count, size = cursor.fetchone()
                
                return {
                    'entries': count or 0,
                    'size_bytes': size or 0,
                    'max_size_bytes': self.max_size_bytes,
                    'db_path': self.db_path
                }
        except Exception as e:
            logger.error(f"Disk cache stats error: {e}")
            return {'entries': 0, 'size_bytes': 0, 'error': str(e)}

class CacheManager:
    """
    Multi-tier cache manager combining memory and disk cache
    """
    
    def __init__(self, 
                 memory_max_size: int = 1000,
                 memory_ttl: Optional[float] = 300,
                 disk_max_size_mb: int = 100,
                 disk_ttl: Optional[float] = 3600):
        """
        Initialize cache manager
        
        Args:
            memory_max_size: Max entries in memory cache
            memory_ttl: Default TTL for memory cache (seconds)
            disk_max_size_mb: Max size for disk cache (MB)
            disk_ttl: Default TTL for disk cache (seconds)
        """
        self.memory = MemoryCache(max_size=memory_max_size, default_ttl=memory_ttl)
        self.disk = DiskCache(max_size_mb=disk_max_size_mb)
        self.default_memory_ttl = memory_ttl
        self.default_disk_ttl = disk_ttl
        
    def get(self, key: str, use_disk: bool = True) -> Optional[Any]:
        """
        Get value from cache (memory first, then disk)
        
        Args:
            key: Cache key
            use_disk: Whether to check disk cache if not in memory
            
        Returns:
            Cached value or None
        """
        # Try memory first
        value = self.memory.get(key)
        if value is not None:
            return value
            
        # Try disk if enabled
        if use_disk:
            value = self.disk.get(key)
            if value is not None:
                # Promote to memory cache
                self.memory.set(key, value, ttl=self.default_memory_ttl)
                return value
                
        return None
        
    def set(self, key: str, value: Any, 
            memory_ttl: Optional[float] = None,
            disk_ttl: Optional[float] = None,
            use_disk: bool = True) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            memory_ttl: TTL for memory cache (None = use default)
            disk_ttl: TTL for disk cache (None = use default, 0 = don't cache to disk)
            use_disk: Whether to also cache to disk
            
        Returns:
            True if successfully cached
        """
        # Always cache to memory
        self.memory.set(key, value, ttl=memory_ttl or self.default_memory_ttl)
        
        # Optionally cache to disk
        if use_disk and disk_ttl != 0:
            self.disk.set(key, value, ttl=disk_ttl or self.default_disk_ttl)
            
        return True
        
    def delete(self, key: str) -> bool:
        """Delete from both memory and disk cache"""
        memory_deleted = self.memory.delete(key)
        disk_deleted = self.disk.delete(key)
        return memory_deleted or disk_deleted
        
    def clear(self, clear_disk: bool = False):
        """Clear cache"""
        self.memory.clear()
        if clear_disk:
            self.disk.clear()
            
    def cleanup_expired(self) -> Dict[str, int]:
        """Cleanup expired entries from both caches"""
        return {
            'memory': self.memory.cleanup_expired(),
            'disk': self.disk.cleanup_expired()
        }
        
    def get_stats(self) -> Dict:
        """Get combined cache statistics"""
        memory_stats = self.memory.get_stats()
        disk_stats = self.disk.get_stats()
        
        total_hits = memory_stats.get('hits', 0)
        total_misses = memory_stats.get('misses', 0)
        total_requests = total_hits + total_misses
        
        return {
            'memory': memory_stats,
            'disk': disk_stats,
            'combined_hit_rate': round((total_hits / total_requests * 100), 2) if total_requests > 0 else 0,
            'total_entries': memory_stats.get('entries', 0) + disk_stats.get('entries', 0),
            'total_size_bytes': memory_stats.get('size_bytes', 0) + disk_stats.get('size_bytes', 0)
        }

# Global cache manager instance
_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def cache_result(key_func: Optional[Callable] = None, ttl: float = 300):
    """
    Decorator to cache function results
    
    Args:
        key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
                
            # Try to get from cache
            cache = get_cache_manager()
            result = cache.get(cache_key)
            
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
                
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, memory_ttl=ttl, disk_ttl=ttl*2)
            
            return result
            
        return wrapper
    return decorator
