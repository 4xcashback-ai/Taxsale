"""
Redis Caching Utilities for Tax Sale Compass
Provides performance optimization through intelligent caching
"""

import json
import os
import logging
from typing import Optional, Any, Union
from datetime import timedelta
import redis
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based caching manager for performance optimization"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        self.default_ttl = int(os.getenv('CACHE_TTL', 3600))  # 1 hour default
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("✅ Redis caching enabled")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, caching disabled: {e}")
            self.enabled = False
    
    def _make_key(self, key: str, prefix: str = "taxsale") -> str:
        """Create a standardized cache key"""
        return f"{prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            cached_value = self.redis_client.get(self._make_key(key))
            if cached_value:
                return json.loads(cached_value)
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(
                self._make_key(key), 
                ttl, 
                serialized_value
            )
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            return bool(self.redis_client.delete(self._make_key(key)))
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(self._make_key(pattern))
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache flush error for pattern {pattern}: {e}")
        return 0

# Global cache manager instance
cache_manager = CacheManager()

def cache_response(key_func=None, ttl: int = 3600):
    """
    Decorator to cache API responses
    
    Args:
        key_func: Function to generate cache key, defaults to endpoint + params
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key based on function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args if isinstance(arg, (str, int, float)))
                for k, v in kwargs.items():
                    if isinstance(v, (str, int, float, bool)):
                        key_parts.append(f"{k}:{v}")
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            # Cache the result (only cache successful responses)
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
                logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator

def property_cache_key(assessment_number: str, data_type: str = "basic") -> str:
    """Generate cache key for property data"""
    return f"property:{assessment_number}:{data_type}"

def municipality_cache_key(municipality_id: str) -> str:
    """Generate cache key for municipality data"""
    return f"municipality:{municipality_id}"

def search_cache_key(municipality: str, status: str, page: int = 1) -> str:
    """Generate cache key for search results"""
    return f"search:{municipality}:{status}:{page}"

# Cache invalidation helpers
def invalidate_property_cache(assessment_number: str):
    """Invalidate all cache entries for a property"""
    cache_manager.flush_pattern(f"property:{assessment_number}:*")

def invalidate_municipality_cache(municipality_id: str):
    """Invalidate cache for municipality"""
    cache_manager.delete(municipality_cache_key(municipality_id))
    cache_manager.flush_pattern(f"search:*")  # Invalidate search results too

def get_cache_stats() -> dict:
    """Get cache statistics for monitoring"""
    if not cache_manager.enabled:
        return {"enabled": False}
    
    try:
        info = cache_manager.redis_client.info()
        return {
            "enabled": True,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
        }
    except Exception as e:
        logger.warning(f"Error getting cache stats: {e}")
        return {"enabled": True, "error": str(e)}