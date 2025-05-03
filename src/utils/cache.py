"""
Cache utilities for API responses.

This module provides caching mechanisms for API responses to improve performance
and reduce costs associated with repeated identical API calls.
"""

import json
import logging
import hashlib
import traceback
import os
import glob
from typing import Dict, Any, Optional, Callable
from datetime import timedelta
import time

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cache_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResponseCache:
    """
    Base class for implementing response caching.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.default_ttl = default_ttl
    
    def generate_cache_key(self, query: str, context: Any = None, **kwargs) -> str:
        """
        Generate a cache key from the query and context.
        
        Args:
            query: The user's query string
            context: Any additional context that affects the response
            kwargs: Additional parameters that affect the response
            
        Returns:
            Cache key as a string
        """
        # Create a dictionary of all inputs that affect the response
        cache_inputs = {
            "query": query
        }
        
        # Only add context if it's not None
        if context is not None:
            cache_inputs["context"] = context
        
        # Add any additional kwargs that aren't None
        for key, value in kwargs.items():
            if value is not None:
                cache_inputs[key] = value
        
        # Convert to JSON string and hash
        cache_string = json.dumps(cache_inputs, sort_keys=True)
        key = hashlib.md5(cache_string.encode('utf-8')).hexdigest()
        logger.debug(f"Generated cache key: {key} from input: {cache_string}")
        return key
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default_ttl if None)
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        raise NotImplementedError("Subclasses must implement this method")


class InMemoryCache(ResponseCache):
    """
    Simple in-memory cache implementation.
    Not suitable for production or distributed systems, but useful for development.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize the in-memory cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        super().__init__(default_ttl)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._expiry: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._cache:
            logger.debug(f"Cache miss for key: {key}")
            return None
        
        # Check if expired
        if time.time() > self._expiry.get(key, 0):
            logger.debug(f"Cache expired for key: {key}")
            self.delete(key)
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        try:
            # Make a deep copy to avoid modifying the cached value
            cached_data = self._cache[key].copy()
            logger.debug(f"Returning cached data: {json.dumps(cached_data)[:100]}...")
            return cached_data
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}\n{traceback.format_exc()}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default_ttl if None)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        try:
            # Make a copy to ensure we're not storing references to mutable objects
            self._cache[key] = value.copy()
            self._expiry[key] = time.time() + ttl
            logger.debug(f"Cached response for key: {key}, TTL: {ttl}s, value: {json.dumps(value)[:100]}...")
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}\n{traceback.format_exc()}")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        logger.debug(f"Deleted key from cache: {key}")
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        num_entries = len(self._cache)
        self._cache.clear()
        self._expiry.clear()
        logger.debug(f"Cleared {num_entries} entries from cache")


class FileCache(ResponseCache):
    """
    File-based cache implementation.
    Stores each cache entry in a separate JSON file.
    """
    
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600):
        """
        Initialize the file cache.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        super().__init__(default_ttl)
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        logger.debug(f"Initialized file cache in directory: {cache_dir}")
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to the cache file
        """
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            logger.debug(f"Cache miss for key: {key}")
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if expired
            if time.time() > cache_data.get("expires_at", 0):
                logger.debug(f"Cache expired for key: {key}")
                self.delete(key)
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            return cache_data.get("value")
            
        except Exception as e:
            logger.error(f"Error reading cache file {cache_path}: {str(e)}")
            # Delete corrupted cache file
            try:
                os.remove(cache_path)
            except:
                pass
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default_ttl if None)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                "value": value,
                "created_at": time.time(),
                "expires_at": time.time() + ttl
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
                
            logger.debug(f"Cached response for key: {key}, TTL: {ttl}s")
            
        except Exception as e:
            logger.error(f"Error writing cache file {cache_path}: {str(e)}")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        cache_path = self._get_cache_path(key)
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                logger.debug(f"Deleted cache file for key: {key}")
            except Exception as e:
                logger.error(f"Error deleting cache file {cache_path}: {str(e)}")
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        try:
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.json"))
            for file_path in cache_files:
                os.remove(file_path)
            
            logger.debug(f"Cleared {len(cache_files)} entries from cache directory")
            
        except Exception as e:
            logger.error(f"Error clearing cache directory: {str(e)}")
            
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of expired entries removed
        """
        removed_count = 0
        
        try:
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.json"))
            current_time = time.time()
            
            for file_path in cache_files:
                try:
                    with open(file_path, 'r') as f:
                        cache_data = json.load(f)
                    
                    if current_time > cache_data.get("expires_at", 0):
                        os.remove(file_path)
                        removed_count += 1
                except:
                    # Remove corrupted files
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except:
                        pass
            
            logger.debug(f"Cleaned up {removed_count} expired cache entries")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache entries: {str(e)}")
            return removed_count


class DynamicTTLCache(ResponseCache):
    """
    Cache with dynamic TTL based on market volatility or other factors.
    """
    
    def __init__(
        self, 
        base_cache: ResponseCache,
        volatility_evaluator: Callable[[], float] = None,
        high_volatility_threshold: float = 1.5,
        low_volatility_ttl: int = 3600,
        high_volatility_ttl: int = 300
    ):
        """
        Initialize the dynamic TTL cache.
        
        Args:
            base_cache: Underlying cache implementation
            volatility_evaluator: Function that returns current market volatility
            high_volatility_threshold: Threshold for high volatility
            low_volatility_ttl: TTL for low volatility periods (seconds)
            high_volatility_ttl: TTL for high volatility periods (seconds)
        """
        super().__init__(low_volatility_ttl)
        self.base_cache = base_cache
        # Use a simple default if no evaluator is provided
        self.volatility_evaluator = volatility_evaluator or (lambda: 0.5)
        self.high_volatility_threshold = high_volatility_threshold
        self.low_volatility_ttl = low_volatility_ttl
        self.high_volatility_ttl = high_volatility_ttl
        logger.debug(f"DynamicTTLCache initialized with threshold: {high_volatility_threshold}, " 
                    f"low_ttl: {low_volatility_ttl}s, high_ttl: {high_volatility_ttl}s")
    
    def _get_current_ttl(self) -> int:
        """
        Get the current TTL based on market volatility.
        
        Returns:
            TTL in seconds
        """
        try:
            volatility = self.volatility_evaluator()
            is_high_volatility = volatility >= self.high_volatility_threshold
            
            if is_high_volatility:
                logger.debug(f"High volatility detected ({volatility}), using shorter TTL of {self.high_volatility_ttl}s")
                return self.high_volatility_ttl
            else:
                logger.debug(f"Normal volatility ({volatility}), using standard TTL of {self.low_volatility_ttl}s")
                return self.low_volatility_ttl
                
        except Exception as e:
            logger.warning(f"Error evaluating volatility: {str(e)}, using default TTL of {self.default_ttl}s")
            return self.default_ttl
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from base cache with additional logging."""
        try:
            result = self.base_cache.get(key)
            if result:
                logger.debug(f"DynamicTTLCache: Cache hit for key: {key}")
            else:
                logger.debug(f"DynamicTTLCache: Cache miss for key: {key}")
            return result
        except Exception as e:
            logger.error(f"Error in DynamicTTLCache.get(): {str(e)}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set with dynamic TTL if not explicitly provided."""
        try:
            ttl = ttl if ttl is not None else self._get_current_ttl()
            logger.debug(f"DynamicTTLCache: Setting key {key} with TTL: {ttl}s")
            self.base_cache.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Error in DynamicTTLCache.set(): {str(e)}")
    
    def delete(self, key: str) -> None:
        """Delegate to base cache."""
        try:
            logger.debug(f"DynamicTTLCache: Deleting key: {key}")
            self.base_cache.delete(key)
        except Exception as e:
            logger.error(f"Error in DynamicTTLCache.delete(): {str(e)}")
    
    def clear(self) -> None:
        """Delegate to base cache."""
        try:
            logger.debug("DynamicTTLCache: Clearing all cache entries")
            self.base_cache.clear()
        except Exception as e:
            logger.error(f"Error in DynamicTTLCache.clear(): {str(e)}")
        
    def generate_cache_key(self, query: str, context: Any = None, **kwargs) -> str:
        """Delegate to base cache with additional logging."""
        try:
            key = self.base_cache.generate_cache_key(query, context, **kwargs)
            logger.debug(f"DynamicTTLCache: Generated key: {key} for query: {query}")
            return key
        except Exception as e:
            logger.error(f"Error in DynamicTTLCache.generate_cache_key(): {str(e)}")
            # Fallback to parent implementation
            return super().generate_cache_key(query, context, **kwargs)


try:
    import redis
    
    class RedisCache(ResponseCache):
        """
        Redis-based cache implementation for distributed systems.
        """
        
        def __init__(
            self, 
            redis_host: str = "localhost",
            redis_port: int = 6379,
            redis_db: int = 0,
            redis_password: Optional[str] = None,
            key_prefix: str = "financial_api:",
            default_ttl: int = 3600
        ):
            """
            Initialize the Redis cache.
            
            Args:
                redis_host: Redis server hostname
                redis_port: Redis server port
                redis_db: Redis database number
                redis_password: Redis password (if required)
                key_prefix: Prefix for all cache keys
                default_ttl: Default time-to-live in seconds (1 hour)
            """
            super().__init__(default_ttl)
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True  # Changed to True for string handling
            )
            self.key_prefix = key_prefix
            
            # Test connection
            try:
                self.redis.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            except redis.ConnectionError:
                logger.warning(f"Could not connect to Redis at {redis_host}:{redis_port}")
        
        def _format_key(self, key: str) -> str:
            """
            Format a cache key with the prefix.
            
            Args:
                key: Cache key
                
            Returns:
                Formatted cache key
            """
            return f"{self.key_prefix}{key}"
        
        def get(self, key: str) -> Optional[Dict[str, Any]]:
            """
            Get a value from the Redis cache.
            
            Args:
                key: Cache key
                
            Returns:
                Cached value or None if not found
            """
            logger.debug("TEST: RedisCache.get() called")  # Test log message
            formatted_key = self._format_key(key)
            logger.debug(f"Attempting to get key from Redis: {formatted_key}")
            
            try:
                data = self.redis.get(formatted_key)
                if data is None:
                    logger.debug(f"Cache miss for key: {formatted_key}")
                    return None
                    
                logger.debug(f"Cache hit for key: {formatted_key}, data: {data[:100]}...")
                return json.loads(data)
                
            except Exception as e:
                logger.warning(f"Error retrieving from Redis cache: {str(e)}")
                return None
        
        def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
            """
            Set a value in the Redis cache.
            
            Args:
                key: Cache key
                value: Value to cache
                ttl: Time-to-live in seconds (uses default_ttl if None)
            """
            formatted_key = self._format_key(key)
            ttl = ttl if ttl is not None else self.default_ttl
            logger.debug(f"Attempting to set key in Redis: {formatted_key}, TTL: {ttl}s")
            
            try:
                serialized_value = json.dumps(value)
                logger.debug(f"Serialized value: {serialized_value[:100]}...")
                self.redis.setex(
                    formatted_key,
                    ttl,
                    serialized_value
                )
                logger.debug(f"Successfully cached response in Redis for key: {formatted_key}")
                
            except Exception as e:
                logger.warning(f"Error setting Redis cache: {str(e)}")
        
        def delete(self, key: str) -> None:
            """
            Delete a value from the Redis cache.
            
            Args:
                key: Cache key
            """
            formatted_key = self._format_key(key)
            
            try:
                self.redis.delete(formatted_key)
                logger.debug(f"Deleted key from Redis cache: {key}")
                
            except Exception as e:
                logger.warning(f"Error deleting from Redis cache: {str(e)}")
        
        def clear(self) -> None:
            """
            Clear all values with this prefix from the Redis cache.
            """
            try:
                pattern = f"{self.key_prefix}*"
                keys = self.redis.keys(pattern)
                
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"Cleared {len(keys)} keys from Redis cache")
                    
            except Exception as e:
                logger.warning(f"Error clearing Redis cache: {str(e)}")

except ImportError:
    # Redis not available, create a stub class for type hints
    class RedisCache(ResponseCache):
        """Stub class when Redis is not available."""
        
        def __init__(self, *args, **kwargs):
            super().__init__()
            raise ImportError("Redis package is not installed. Please install it with 'pip install redis'.") 