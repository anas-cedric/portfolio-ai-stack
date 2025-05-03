# Response Caching System

This document outlines the response caching system implemented for the financial AI stack.

## Overview

The caching system is designed to optimize performance and reduce costs associated with LLM API calls by storing and reusing responses for identical queries. The system supports multiple storage backends and features dynamic TTL (Time-To-Live) based on market volatility.

## Cache Implementation Types

The system supports three types of cache storage:

1. **In-Memory Cache**: Fast but ephemeral. Data is lost when the application restarts.
2. **File Cache**: Persistent storage using the filesystem. Data persists across application restarts.
3. **Redis Cache**: Distributed cache for production environments. Supports high availability and scalability.

## Features

- **Configurable TTL**: Control how long responses are cached before expiring.
- **Dynamic TTL**: Automatically adjust cache TTL based on market volatility.
- **Cache key generation**: Deterministic generation of cache keys based on query content and context.
- **Fallback mechanism**: Gracefully degrade to file cache if Redis is unavailable.
- **Cache cleanup**: Automatic cleaning of expired entries.

## Configuration

Configure the caching system using environment variables:

```
# Cache Type: "in_memory", "file", or "redis"
CACHE_TYPE=file

# Default TTL in seconds (1 hour)
CACHE_TTL=3600

# Directory for file cache storage
CACHE_DIR=.cache

# Redis configuration (if using Redis cache)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=password
```

## API Routes

The API includes several endpoints for cache management:

- `POST /cache/clear`: Clear all cached responses.
- `GET /cache/status`: Get information about the current cache state.
- `GET /debug/cache`: Get detailed debug information about the cache.

## Cache Key Generation

Cache keys are generated from:

1. The query string
2. Additional context that affects the response
3. Any other parameters that could influence the result

The system uses MD5 hashing of a sorted JSON representation of these inputs to create a deterministic cache key.

## Dynamic TTL Based on Market Volatility

The system can adjust the cache TTL based on market volatility:

- During periods of low volatility: Longer TTL (default: 1 hour)
- During periods of high volatility: Shorter TTL (default: 5 minutes)

This ensures that responses remain fresh and relevant during rapidly changing market conditions.

## Usage Example

```python
from src.utils.cache import InMemoryCache, FileCache, RedisCache, DynamicTTLCache

# Create a base cache
base_cache = FileCache(cache_dir=".cache", default_ttl=3600)

# Wrap with dynamic TTL
cache = DynamicTTLCache(
    base_cache=base_cache,
    volatility_evaluator=lambda: get_market_volatility(),
    high_volatility_threshold=1.5,
    low_volatility_ttl=3600,
    high_volatility_ttl=300
)

# Generate a cache key
query = "What is Apple's financial performance?"
cache_key = cache.generate_cache_key(query=query, dataset_name="quarterly_reports")

# Check for cached result
cached_result = cache.get(cache_key)

if cached_result:
    # Use cached result
    result = cached_result
else:
    # Generate new result
    result = run_financial_analysis(query)
    
    # Cache the result
    cache.set(cache_key, result)
```

## Testing

Test scripts are provided to verify the functionality of each cache implementation:

- `src/test_cache.py`: Tests all cache implementations with simulated load.
- `src/final_cache_test.py`: Tests the API caching functionality via HTTP requests.

## Monitoring

Cache performance and status can be monitored through the `/cache/status` endpoint, which provides:

- Cache type in use
- Number of cached entries
- TTL settings
- Memory usage (for Redis)
- Cache directory (for File cache)

## Benefits

- **Improved performance**: Cached responses are returned up to 10-100x faster than generating new ones.
- **Cost reduction**: Fewer LLM API calls means lower operating costs.
- **Reduced latency**: Users experience faster response times for common queries.
- **Consistency**: Users receive identical responses for identical queries within the TTL window.

## Limitations

- Caching is only effective for repeated identical queries.
- Cache invalidation is time-based rather than event-based.
- In-memory cache doesn't persist across application restarts.
- File cache may not be suitable for high-concurrency environments. 