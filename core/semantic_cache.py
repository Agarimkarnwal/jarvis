"""
JARVIS Semantic Cache - Smart caching using sentence embeddings
Research: 5x better cache hit rate than exact matching
"""

import numpy as np
import hashlib
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SemanticCacheEntry:
    """Cache entry with embedding vector"""
    query: str
    response: str
    embedding: np.ndarray
    created_at: datetime
    access_count: int = 1
    ttl_seconds: int = 300
    
    def is_valid(self) -> bool:
        age = (datetime.now() - self.created_at).seconds
        return age < self.ttl_seconds

class SemanticCache:
    """
    Semantic cache using sentence embeddings
    Finds similar queries even with different wording
    """
    
    def __init__(self, similarity_threshold: float = 0.85, max_size: int = 100):
        self.threshold = similarity_threshold
        self.max_size = max_size
        self.cache: Dict[str, SemanticCacheEntry] = {}
        
        # Lazy load encoder
        self._encoder = None
        self._stats = {
            'hits': 0,
            'misses': 0,
            'insertions': 0,
            'evictions': 0
        }
        
    @property
    def encoder(self):
        """Lazy load sentence transformer"""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Use fast, lightweight model
                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence encoder loaded")
            except ImportError:
                logger.warning("sentence-transformers not installed, semantic cache disabled")
                return None
        return self._encoder
        
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding vector for text"""
        if self.encoder is None:
            return None
            
        try:
            embedding = self.encoder.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None
            
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    def get(self, query: str) -> Optional[str]:
        """
        Find semantically similar cached response
        
        Args:
            query: User query
            
        Returns:
            Cached response if similar enough, else None
        """
        if not self.cache or self.encoder is None:
            self._stats['misses'] += 1
            return None
            
        query_emb = self._get_embedding(query)
        if query_emb is None:
            self._stats['misses'] += 1
            return None
            
        # Find best match
        best_match = None
        best_score = 0.0
        
        for key, entry in self.cache.items():
            if not entry.is_valid():
                continue
                
            similarity = self._cosine_similarity(query_emb, entry.embedding)
            
            if similarity > best_score and similarity > self.threshold:
                best_score = similarity
                best_match = entry
                
        if best_match:
            best_match.access_count += 1
            self._stats['hits'] += 1
            logger.debug(f"Semantic cache hit: {best_match.query[:30]}... (score: {best_score:.2f})")
            return best_match.response
            
        self._stats['misses'] += 1
        return None
        
    def set(self, query: str, response: str, ttl: int = 300):
        """
        Cache response with embedding
        
        Args:
            query: User query
            response: AI response
            ttl: Time to live in seconds
        """
        if self.encoder is None:
            return
            
        # Check cache size
        if len(self.cache) >= self.max_size:
            # Remove oldest or least accessed
            lru_key = min(self.cache.items(), key=lambda x: x[1].access_count)[0]
            del self.cache[lru_key]
            self._stats['evictions'] += 1
            
        # Get embedding
        embedding = self._get_embedding(query)
        if embedding is None:
            return
            
        # Create cache key
        key = hashlib.md5(query.encode()).hexdigest()
        
        self.cache[key] = SemanticCacheEntry(
            query=query,
            response=response,
            embedding=embedding,
            created_at=datetime.now(),
            ttl_seconds=ttl
        )
        
        self._stats['insertions'] += 1
        logger.debug(f"Cached: {query[:30]}...")
        
    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        
    def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if not entry.is_valid()
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)
        
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            **self._stats,
            'hit_rate': round(hit_rate, 2),
            'entries': len(self.cache),
            'threshold': self.threshold
        }

# Global instance
_semantic_cache = None

def get_semantic_cache():
    """Get or create global semantic cache"""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache
