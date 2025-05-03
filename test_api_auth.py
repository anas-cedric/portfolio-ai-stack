#!/usr/bin/env python
"""
Test script for API authentication and numerical validation.

This script sends test requests to the financial analysis API
to verify authentication and numerical validation.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from pprint import pprint

# Load environment variables
load_dotenv()

# API settings
API_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY")

def test_unauthenticated_access():
    """Test API access without authentication."""
    print("\n=== Testing Unauthenticated Access ===")
    
    # Test access to protected endpoint without API key
    response = requests.post(
        f"{API_URL}/analyze",
        json={"query": "What is the current market volatility?"}
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Should be 403 Forbidden
    assert response.status_code == 403, "Expected 403 Forbidden for unauthenticated access"
    print("✅ Unauthenticated test passed!")

def test_authenticated_access():
    """Test API access with authentication."""
    print("\n=== Testing Authenticated Access ===")
    
    if not API_KEY:
        print("❌ API_KEY not found in environment variables")
        return
    
    # Test access to protected endpoint with API key
    headers = {"X-API-Key": API_KEY}
    response = requests.post(
        f"{API_URL}/analyze",
        headers=headers,
        json={"query": "What is the current market volatility?"}
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response contains {len(response.text)} characters")
    
    # Should be 200 OK
    assert response.status_code == 200, "Expected 200 OK for authenticated access"
    print("✅ Authenticated test passed!")
    
    return response.json()

def test_numerical_validation():
    """Test numerical validation with portfolio allocation query."""
    print("\n=== Testing Numerical Validation ===")
    
    if not API_KEY:
        print("❌ API_KEY not found in environment variables")
        return
    
    # Test a query that should trigger numerical validation
    headers = {"X-API-Key": API_KEY}
    response = requests.post(
        f"{API_URL}/analyze",
        headers=headers,
        json={"query": "Create a balanced portfolio allocation for a moderate risk investor"}
    )
    
    print(f"Status code: {response.status_code}")
    
    # Check if we got a successful response
    if response.status_code == 200:
        result = response.json()
        analysis = result.get("analysis", "")
        
        # Check if the analysis contains portfolio allocation percentages
        contains_percentages = "%" in analysis
        
        print(f"Response contains percentages: {contains_percentages}")
        if contains_percentages:
            print("Sample of analysis:")
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
        print("✅ Numerical validation test completed!")
        return result
    else:
        print(f"❌ Request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_invalid_api_key():
    """Test access with invalid API key."""
    print("\n=== Testing Invalid API Key ===")
    
    # Test access with invalid API key
    headers = {"X-API-Key": "invalid-key"}
    response = requests.post(
        f"{API_URL}/analyze",
        headers=headers,
        json={"query": "What is the current market volatility?"}
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Should be 403 Forbidden
    assert response.status_code == 403, "Expected 403 Forbidden for invalid API key"
    print("✅ Invalid API key test passed!")

def main():
    """Run all tests."""
    print("\n🔒 API Authentication and Numerical Validation Tests\n")
    
    try:
        # Test API access
        test_unauthenticated_access()
        test_invalid_api_key()
        result = test_authenticated_access()
        test_numerical_validation()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 