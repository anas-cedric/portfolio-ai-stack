"""
Test script for the caching system.

This script tests both in-memory and file-based caching for the financial API.
"""

import os
import sys
import json
import time
import logging
import shutil
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import cache implementations
from src.utils.cache import InMemoryCache, DynamicTTLCache, FileCache

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

class MockFinancialAnalyzer:
    """Mock class to simulate financial analysis."""
    
    def __init__(self, response_time=1.0):
        self.call_count = 0
        self.response_time = response_time
    
    def analyze(self, query, context=None):
        """Simulate financial analysis with a delay."""
        self.call_count += 1
        # Simulate processing time
        time.sleep(self.response_time)
        return {
            "analysis": f"Analysis #{self.call_count} for: {query}",
            "timestamp": time.time(),
            "context": context
        }

def test_in_memory_cache():
    """Test the in-memory cache implementation."""
    logger.info("=== Testing InMemoryCache ===")
    
    # Create cache
    cache = InMemoryCache(default_ttl=5)  # Short TTL for testing
    
    # Create mock analyzer
    analyzer = MockFinancialAnalyzer()
    
    # First request (cache miss)
    query = "What is the financial outlook for AAPL?"
    
    logger.info("Making first request (should be a cache miss)...")
    start_time = time.time()
    cache_key = cache.generate_cache_key(query=query)
    
    # Check for cached result
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        # Cache miss - run analysis
        logger.info("Cache miss")
        result = analyzer.analyze(query)
        cache.set(cache_key, result)
    else:
        # Cache hit
        logger.info("Cache hit")
        result = cached_result
    
    first_request_time = time.time() - start_time
    logger.info(f"First request took: {first_request_time:.2f} seconds")
    logger.info(f"Result: {result}")
    
    # Second request (should be a cache hit)
    logger.info("\nMaking second request (should be a cache hit)...")
    start_time = time.time()
    
    # Check for cached result
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        # Cache miss - run analysis
        logger.info("Cache miss")
        result = analyzer.analyze(query)
        cache.set(cache_key, result)
    else:
        # Cache hit
        logger.info("Cache hit")
        result = cached_result
    
    second_request_time = time.time() - start_time
    logger.info(f"Second request took: {second_request_time:.2f} seconds")
    logger.info(f"Result: {result}")
    
    # Check for performance improvement
    speedup = first_request_time / second_request_time
    logger.info(f"Cache speedup: {speedup:.2f}x faster")
    logger.info(f"Analyzer called {analyzer.call_count} times")
    
    # Wait for TTL to expire
    logger.info("\nWaiting for cache to expire (6 seconds)...")
    time.sleep(6)
    
    # Third request (should be a cache miss due to expiration)
    logger.info("Making third request (should be a cache miss due to expiration)...")
    start_time = time.time()
    
    # Check for cached result
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        # Cache miss - run analysis
        logger.info("Cache miss")
        result = analyzer.analyze(query)
        cache.set(cache_key, result)
    else:
        # Cache hit
        logger.info("Cache hit")
        result = cached_result
    
    third_request_time = time.time() - start_time
    logger.info(f"Third request took: {third_request_time:.2f} seconds")
    logger.info(f"Result: {result}")
    logger.info(f"Analyzer called {analyzer.call_count} times")

def test_file_cache():
    """Test the file-based cache implementation."""
    logger.info("\n=== Testing FileCache ===")
    
    # Create test cache directory
    cache_dir = ".test_cache"
    
    # Clean up any previous test files
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
    
    # Create cache
    cache = FileCache(cache_dir=cache_dir, default_ttl=5)  # Short TTL for testing
    
    # Create mock analyzer
    analyzer = MockFinancialAnalyzer()
    
    # First request (cache miss)
    query = "What is the financial outlook for AAPL?"
    
    logger.info("Making first request (should be a cache miss)...")
    start_time = time.time()
    cache_key = cache.generate_cache_key(query=query)
    
    # Check for cached result
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        # Cache miss - run analysis
        logger.info("Cache miss")
        result = analyzer.analyze(query)
        cache.set(cache_key, result)
    else:
        # Cache hit
        logger.info("Cache hit")
        result = cached_result
    
    first_request_time = time.time() - start_time
    logger.info(f"First request took: {first_request_time:.2f} seconds")
    logger.info(f"Result: {result}")
    
    # Verify that the cache file was created
    cache_path = cache._get_cache_path(cache_key)
    logger.info(f"Cache file created: {os.path.exists(cache_path)}")
    
    # Second request (should be a cache hit)
    logger.info("\nMaking second request (should be a cache hit)...")
    start_time = time.time()
    
    # Check for cached result
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        # Cache miss - run analysis
        logger.info("Cache miss")
        result = analyzer.analyze(query)
        cache.set(cache_key, result)
    else:
        # Cache hit
        logger.info("Cache hit")
        result = cached_result
    
    second_request_time = time.time() - start_time
    logger.info(f"Second request took: {second_request_time:.2f} seconds")
    logger.info(f"Result: {result}")
    
    # Check for performance improvement
    speedup = first_request_time / second_request_time
    logger.info(f"Cache speedup: {speedup:.2f}x faster")
    logger.info(f"Analyzer called {analyzer.call_count} times")
    
    # Wait for TTL to expire
    logger.info("\nWaiting for cache to expire (6 seconds)...")
    time.sleep(6)
    
    # Third request (should be a cache miss due to expiration)
    logger.info("Making third request (should be a cache miss due to expiration)...")
    start_time = time.time()
    
    # Check for cached result
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        # Cache miss - run analysis
        logger.info("Cache miss")
        result = analyzer.analyze(query)
        cache.set(cache_key, result)
    else:
        # Cache hit
        logger.info("Cache hit")
        result = cached_result
    
    third_request_time = time.time() - start_time
    logger.info(f"Third request took: {third_request_time:.2f} seconds")
    logger.info(f"Result: {result}")
    logger.info(f"Analyzer called {analyzer.call_count} times")
    
    # Test cache cleanup
    logger.info("\nTesting cache cleanup...")
    removed = cache.cleanup_expired()
    logger.info(f"Removed {removed} expired entries")
    
    # Clean up test directory
    shutil.rmtree(cache_dir)
    logger.info(f"Cleaned up test cache directory: {cache_dir}")

def test_dynamic_ttl_cache():
    """Test the dynamic TTL cache implementation with different volatilities."""
    logger.info("\n=== Testing DynamicTTLCache ===")
    
    # Create base cache
    base_cache = InMemoryCache()
    
    # Mock volatility function - starts normal, then becomes high
    volatility_values = [0.5, 2.0]
    volatility_index = 0
    
    def get_volatility():
        nonlocal volatility_index
        value = volatility_values[volatility_index % len(volatility_values)]
        volatility_index += 1
        return value
    
    # Create dynamic TTL cache
    cache = DynamicTTLCache(
        base_cache=base_cache,
        volatility_evaluator=get_volatility,
        high_volatility_threshold=1.5,
        low_volatility_ttl=60,
        high_volatility_ttl=5
    )
    
    # Check TTL values for different volatility states
    logger.info("Testing TTL values for different volatility states...")
    
    # Reset volatility index
    volatility_index = 0
    
    # Low volatility
    ttl = cache._get_current_ttl()
    logger.info(f"Volatility: {volatility_values[0]}, TTL: {ttl}s")
    
    # High volatility
    ttl = cache._get_current_ttl()
    logger.info(f"Volatility: {volatility_values[1]}, TTL: {ttl}s")

if __name__ == "__main__":
    test_in_memory_cache()
    test_file_cache()
    test_dynamic_ttl_cache() 