"""
A final test script that uses direct HTTP requests to test the API caching.
"""

import os
import sys
import json
import time
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API settings
API_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("API_KEY", "test_api_key_for_development")
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def test_api_direct():
    """
    Test API caching with direct HTTP requests, bypassing any Python wrappers.
    """
    # First, clear the cache to ensure a clean test
    logger.info("Clearing cache before test...")
    response = requests.post(f"{API_URL}/cache/clear", headers=HEADERS)
    logger.info(f"Cache clear response: {response.status_code} - {response.text}")
    
    # Make first request (should be a cache miss)
    query = "What is Apple's financial performance?"
    
    logger.info("Making first request (should be a cache miss)...")
    start_time = time.time()
    response = requests.post(
        f"{API_URL}/analyze",
        data=json.dumps({"query": query}),
        headers=HEADERS
    )
    first_request_time = time.time() - start_time
    
    # Check if response is valid
    if response.status_code != 200:
        logger.error(f"Request failed: {response.status_code} - {response.text}")
        return
    
    first_response = response.json()
    logger.info(f"First request took: {first_request_time:.2f} seconds")
    logger.info(f"Cached flag: {first_response.get('cached', False)}")
    logger.info(f"Response preview: {json.dumps(first_response)[:200]}...")
    
    # Wait a moment to ensure caching completes
    logger.info("Waiting 1 second...")
    time.sleep(1)
    
    # Make second request (should be a cache hit)
    logger.info("Making second request (should be a cache hit)...")
    start_time = time.time()
    response = requests.post(
        f"{API_URL}/analyze",
        data=json.dumps({"query": query}),
        headers=HEADERS
    )
    second_request_time = time.time() - start_time
    
    # Check if response is valid
    if response.status_code != 200:
        logger.error(f"Request failed: {response.status_code} - {response.text}")
        return
    
    second_response = response.json()
    logger.info(f"Second request took: {second_request_time:.2f} seconds")
    logger.info(f"Cached flag: {second_response.get('cached', False)}")
    logger.info(f"Response preview: {json.dumps(second_response)[:200]}...")
    
    # Check for performance improvement
    if second_request_time < first_request_time:
        speedup = first_request_time / second_request_time
        logger.info(f"Cache speedup: {speedup:.2f}x faster")
    
    # Check if responses match
    if first_response.get('analysis') == second_response.get('analysis'):
        logger.info("Responses match ✓")
    else:
        logger.warning("Responses don't match!")

def test_with_different_queries():
    """
    Test API caching with different queries to ensure proper key generation.
    """
    # First, clear the cache to ensure a clean test
    logger.info("\nTesting with different queries...")
    response = requests.post(f"{API_URL}/cache/clear", headers=HEADERS)
    logger.info(f"Cache clear response: {response.status_code}")
    
    # Make requests with similar but different queries
    queries = [
        "Analyze Apple's financial performance",
        "Analyze Apple's financial performance",  # Same query, should hit cache
        "analyze apple's financial performance",  # Different case, should still hit cache if implementation is good
        "Analyze Microsoft's financial performance"  # Different company, should miss cache
    ]
    
    previous_response = None
    
    for i, query in enumerate(queries):
        logger.info(f"\nQuery {i+1}: {query}")
        
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/analyze",
            data=json.dumps({"query": query}),
            headers=HEADERS
        )
        request_time = time.time() - start_time
        
        if response.status_code != 200:
            logger.error(f"Request failed: {response.status_code} - {response.text}")
            continue
        
        result = response.json()
        logger.info(f"Request took: {request_time:.2f} seconds")
        logger.info(f"Cached: {result.get('cached', False)}")
        
        if previous_response and i in [1, 2]:
            if previous_response.get('analysis') == result.get('analysis'):
                logger.info("Response matches previous query ✓")
            else:
                logger.warning("Response doesn't match previous query!")
                
        previous_response = result
        
        # Brief pause between requests
        time.sleep(0.5)

if __name__ == "__main__":
    test_api_direct()
    test_with_different_queries() 