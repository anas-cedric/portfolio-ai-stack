"""
Debug script to test the caching functionality directly.
"""

import os
import sys
import json
import time
import logging
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import cache components
from src.utils.cache import InMemoryCache, DynamicTTLCache

def test_in_memory_cache():
    """Test the InMemoryCache implementation directly."""
    logger.info("Testing InMemoryCache...")
    
    cache = InMemoryCache(default_ttl=10)  # Short TTL for testing
    
    # Test basic set/get
    test_key = cache.generate_cache_key("test_query")
    test_data = {"result": "This is a test result"}
    
    logger.info(f"Setting cache with key: {test_key}")
    cache.set(test_key, test_data)
    
    # Check if it's in the cache
    result = cache.get(test_key)
    logger.info(f"Cache hit: {result is not None}")
    logger.info(f"Cache data: {result}")
    
    # Test with the same query to ensure we get a cache hit
    same_key = cache.generate_cache_key("test_query")
    logger.info(f"Same key check: {same_key == test_key}")
    
    # Get with the same key
    result = cache.get(same_key)
    logger.info(f"Cache hit with same key: {result is not None}")
    
    # Test expiration
    logger.info("Testing expiration (waiting 11 seconds)...")
    time.sleep(11)
    expired_result = cache.get(test_key)
    logger.info(f"Result after expiration: {expired_result}")

def test_dynamic_ttl_cache():
    """Test the DynamicTTLCache implementation"""
    logger.info("\nTesting DynamicTTLCache...")
    
    base_cache = InMemoryCache(default_ttl=60)
    
    # Mock volatility function that alternates between high and low volatility
    volatility_counter = [0]
    def mock_volatility():
        volatility_counter[0] += 1
        return 2.0 if volatility_counter[0] % 2 == 0 else 0.5
    
    cache = DynamicTTLCache(
        base_cache=base_cache,
        volatility_evaluator=mock_volatility,
        high_volatility_threshold=1.5,
        low_volatility_ttl=60,
        high_volatility_ttl=5
    )
    
    # Test with low volatility
    test_key1 = cache.generate_cache_key("test_query_1")
    test_data1 = {"result": "Low volatility test result"}
    
    logger.info(f"Setting cache with key: {test_key1} (low volatility)")
    cache.set(test_key1, test_data1)
    
    # Test with high volatility
    test_key2 = cache.generate_cache_key("test_query_2")
    test_data2 = {"result": "High volatility test result"}
    
    logger.info(f"Setting cache with key: {test_key2} (high volatility)")
    cache.set(test_key2, test_data2)
    
    # Check both keys
    result1 = cache.get(test_key1)
    result2 = cache.get(test_key2)
    
    logger.info(f"Cache hit for key1: {result1 is not None}")
    logger.info(f"Cache hit for key2: {result2 is not None}")
    
    # Test expiration for high volatility (should expire in 5 seconds)
    logger.info("Testing high volatility expiration (waiting 6 seconds)...")
    time.sleep(6)
    
    result1 = cache.get(test_key1)
    result2 = cache.get(test_key2)
    
    logger.info(f"Cache hit for key1 (low volatility): {result1 is not None}")
    logger.info(f"Cache hit for key2 (high volatility): {result2 is not None}")

def test_with_sample_data():
    """Test the cache with data similar to the API."""
    logger.info("\nTesting with sample API data...")
    
    cache = InMemoryCache(default_ttl=30)
    
    query = "Analyze Apple's financial performance"
    
    # Generate cache key
    cache_key = cache.generate_cache_key(
        query=query,
        dataset_name=None,
        dataset_type=None
    )
    
    logger.info(f"Generated cache key: {cache_key}")
    
    # Create sample response data
    response_data = {
        "query": query,
        "analysis": "Mock analysis of Apple's performance",
        "data_info": {
            "dataset_name": None,
            "dataset_type": None,
            "num_records": 100,
            "columns": ["Date", "Revenue", "Profit"]
        },
        "market_context": {
            "volatility": 0.8,
            "trend": "upward"
        },
        "error": None
    }
    
    # Cache the data
    logger.info("Caching sample response data...")
    cache.set(cache_key, response_data)
    
    # Retrieve cached data
    cached_result = cache.get(cache_key)
    
    if cached_result:
        logger.info("Successfully retrieved cached data!")
        logger.info(f"Cached data: {json.dumps(cached_result)[:100]}...")
    else:
        logger.error("Failed to retrieve cached data!")
    
    # Create a new cache key with the same query to verify key generation
    same_key = cache.generate_cache_key(
        query=query,
        dataset_name=None,
        dataset_type=None
    )
    
    logger.info(f"Same key check: {same_key == cache_key}")
    
    # Retrieve with the same key
    same_result = cache.get(same_key)
    logger.info(f"Retrieved with same key: {same_result is not None}")

if __name__ == "__main__":
    test_in_memory_cache()
    test_dynamic_ttl_cache()
    test_with_sample_data() 