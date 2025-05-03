"""
Test script for API caching functionality.

This script tests whether identical queries are properly cached.
"""

import os
import time
import argparse
import requests
import json
from src.prompts.financial_prompts import FinancialPrompts

# Default values
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_API_KEY = os.environ.get("API_KEY", "")

def test_cache_efficiency(api_url, api_key, query="Analyze Apple's financial performance", num_requests=3):
    """Test if identical requests are properly cached."""
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query
    }
    
    # Store response times
    response_times = []
    cached_responses = 0
    total_responses = 0
    
    print(f"\n🔍 Testing caching efficiency with {num_requests} identical requests\n")
    print(f"Query: '{query}'\n")
    
    for i in range(num_requests):
        print(f"Request {i+1}/{num_requests}...")
        
        # Measure response time
        start_time = time.time()
        response = requests.post(f"{api_url}/analyze", headers=headers, json=payload)
        end_time = time.time()
        
        # Process response
        if response.status_code == 200:
            response_data = response.json()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            total_responses += 1
            
            # Check if response was cached
            is_cached = response_data.get("cached", False)
            if is_cached:
                cached_responses += 1
                cache_status = "✅ CACHED"
            else:
                cache_status = "❌ NOT CACHED"
            
            # Print result
            print(f"  {cache_status} - Response time: {response_time:.2f}ms")
            response_times.append((response_time, is_cached))
        else:
            print(f"  ❌ ERROR: {response.status_code} - {response.text}")
    
    # Calculate statistics
    if total_responses > 0:
        cache_hit_rate = (cached_responses / total_responses) * 100
        
        # Calculate average response times for cached vs non-cached
        cached_times = [t for t, cached in response_times if cached]
        non_cached_times = [t for t, cached in response_times if not cached]
        
        avg_cached_time = sum(cached_times) / len(cached_times) if cached_times else 0
        avg_non_cached_time = sum(non_cached_times) / len(non_cached_times) if non_cached_times else 0
        
        # Print summary
        print("\n📊 Cache Efficiency Summary:")
        print(f"  Total requests: {total_responses}")
        print(f"  Cache hits: {cached_responses}")
        print(f"  Cache hit rate: {cache_hit_rate:.1f}%")
        
        if avg_non_cached_time > 0 and avg_cached_time > 0:
            speedup = avg_non_cached_time / avg_cached_time
            print(f"  Average time (non-cached): {avg_non_cached_time:.2f}ms")
            print(f"  Average time (cached): {avg_cached_time:.2f}ms")
            print(f"  Speedup factor: {speedup:.2f}x")
        
        # Evaluate results
        if cache_hit_rate >= 66:  # At least 2/3 should be cached
            print("\n✅ PASS: Caching system is working correctly!")
        else:
            print("\n❌ FAIL: Caching system is not working as expected.")
    else:
        print("\n❌ FAIL: No successful responses received.")

def clear_cache(api_url, api_key):
    """Clear the API cache."""
    
    print("\n🧹 Clearing API cache...")
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{api_url}/cache/clear", headers=headers)
    
    if response.status_code == 200:
        print("  ✅ Cache cleared successfully")
    else:
        print(f"  ❌ Failed to clear cache: {response.status_code} - {response.text}")

def main():
    parser = argparse.ArgumentParser(description='Test the API caching functionality')
    parser.add_argument('--api-url', default=DEFAULT_API_URL, help='API URL')
    parser.add_argument('--api-key', default=DEFAULT_API_KEY, help='API Key')
    parser.add_argument('--query', default="Analyze Apple's financial performance", help='Query to test with')
    parser.add_argument('--requests', type=int, default=3, help='Number of identical requests to make')
    parser.add_argument('--clear-cache', action='store_true', help='Clear the cache before testing')
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key:
        print("❌ ERROR: API key is required. Set it with --api-key or the API_KEY environment variable.")
        return
    
    # Clear cache if requested
    if args.clear_cache:
        clear_cache(args.api_url, args.api_key)
    
    # Run the test
    test_cache_efficiency(args.api_url, args.api_key, args.query, args.requests)

if __name__ == "__main__":
    main() 