"""
Caching service for improved performance
"""
import json
import logging
from typing import Any, Optional, Union
from functools import wraps
from datetime import datetime, timedelta
import hashlib

try:
    from flask_caching import Cache
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    Cache = None


class CacheService:
    """Service for handling application caching"""
    
    def __init__(self, app=None):
        self.logger = logging.getLogger(__name__)
        self.cache = None
        self._memory_cache = {}  # Fallback in-memory cache
        self._cache_expiry = {}  # Track expiry times for memory cache
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize caching with Flask app"""
        if CACHING_AVAILABLE:
            try:
                # Configure cache based on environment
                if app.config.get('TESTING'):
                    cache_config = {'CACHE_TYPE': 'SimpleCache'}
                else:
                    cache_config = {
                        'CACHE_TYPE': 'SimpleCache',  # Use simple cache by default
                        'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default
                    }
                
                # Try to use Redis if available
                redis_url = app.config.get('REDIS_URL')
                if redis_url:
                    cache_config.update({
                        'CACHE_TYPE': 'RedisCache',
                        'CACHE_REDIS_URL': redis_url
                    })
                
                self.cache = Cache(app, config=cache_config)
                self.logger.info(f"Cache initialized with type: {cache_config['CACHE_TYPE']}")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize cache: {e}. Using memory fallback.")
                self.cache = None
        else:
            self.logger.warning("Flask-Caching not available. Using memory fallback.")
    
    def _generate_key(self, key: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        if args or kwargs:
            # Create a hash of the arguments for consistent keys
            key_data = f"{key}:{str(args)}:{str(sorted(kwargs.items()))}"
            return hashlib.md5(key_data.encode()).hexdigest()
        return key
    
    def get(self, key: str, *args, **kwargs) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(key, *args, **kwargs)
        
        if self.cache:
            try:
                return self.cache.get(cache_key)
            except Exception as e:
                self.logger.warning(f"Cache get error: {e}")
        
        # Fallback to memory cache
        return self._memory_get(cache_key)
    
    def set(self, key: str, value: Any, timeout: int = 300, *args, **kwargs) -> bool:
        """Set value in cache"""
        cache_key = self._generate_key(key, *args, **kwargs)
        
        if self.cache:
            try:
                return self.cache.set(cache_key, value, timeout=timeout)
            except Exception as e:
                self.logger.warning(f"Cache set error: {e}")
        
        # Fallback to memory cache
        return self._memory_set(cache_key, value, timeout)
    
    def delete(self, key: str, *args, **kwargs) -> bool:
        """Delete value from cache"""
        cache_key = self._generate_key(key, *args, **kwargs)
        
        if self.cache:
            try:
                return self.cache.delete(cache_key)
            except Exception as e:
                self.logger.warning(f"Cache delete error: {e}")
        
        # Fallback to memory cache
        return self._memory_delete(cache_key)
    
    def clear(self) -> bool:
        """Clear all cache"""
        if self.cache:
            try:
                return self.cache.clear()
            except Exception as e:
                self.logger.warning(f"Cache clear error: {e}")
        
        # Clear memory cache
        self._memory_cache.clear()
        self._cache_expiry.clear()
        return True
    
    def _memory_get(self, key: str) -> Optional[Any]:
        """Get from memory cache with expiry check"""
        if key in self._memory_cache:
            expiry = self._cache_expiry.get(key)
            if expiry and datetime.now() > expiry:
                # Expired, remove it
                del self._memory_cache[key]
                del self._cache_expiry[key]
                return None
            return self._memory_cache[key]
        return None
    
    def _memory_set(self, key: str, value: Any, timeout: int) -> bool:
        """Set in memory cache with expiry"""
        try:
            self._memory_cache[key] = value
            self._cache_expiry[key] = datetime.now() + timedelta(seconds=timeout)
            
            # Clean up expired entries periodically
            if len(self._memory_cache) > 1000:  # Arbitrary limit
                self._cleanup_memory_cache()
            
            return True
        except Exception as e:
            self.logger.error(f"Memory cache set error: {e}")
            return False
    
    def _memory_delete(self, key: str) -> bool:
        """Delete from memory cache"""
        try:
            if key in self._memory_cache:
                del self._memory_cache[key]
            if key in self._cache_expiry:
                del self._cache_expiry[key]
            return True
        except Exception as e:
            self.logger.error(f"Memory cache delete error: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache"""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self._cache_expiry.items()
            if expiry and now > expiry
        ]
        
        for key in expired_keys:
            self._memory_delete(key)
        
        self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


def cached(timeout=300, key_prefix=''):
    """
    Decorator for caching function results
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            func_key = f"{key_prefix}:{func.__name__}" if key_prefix else func.__name__
            
            # Try to get from cache first
            cache_service = getattr(wrapper, '_cache_service', None)
            if cache_service:
                cached_result = cache_service.get(func_key, *args, **kwargs)
                if cached_result is not None:
                    return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            if cache_service and result is not None:
                cache_service.set(func_key, result, timeout, *args, **kwargs)
            
            return result
        
        return wrapper
    return decorator


# Global cache service instance
cache_service = CacheService()
