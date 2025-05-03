#!/usr/bin/env python3
"""
OpenAI API Key Checker CLI Tool

This tool helps diagnose API key issues and check model availability.
"""

import os
import sys
import argparse
import json
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.api_key_validator import (
    validate_openai_key,
    get_available_models,
    check_model_availability,
    recommend_fallback_model,
    diagnose_api_key_issues
)

def setup_args():
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description='Check OpenAI API key and model availability.')
    
    parser.add_argument('api_key', help='API key to check')
    parser.add_argument('--model', default='o3', help='Model to check availability for')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--diagnose', action='store_true', help='Run full API key diagnostics')
    parser.add_argument('--list-models', action='store_true', help='List all available models')
    parser.add_argument('--test-model', action='store_true', help='Test a simple API call with the model')
    
    return parser.parse_args()

def format_output(success, message, data=None, json_output=False):
    """Format output as text or JSON."""
    if json_output:
        result = {
            "success": success,
            "message": message
        }
        if data:
            result["data"] = data
        print(json.dumps(result, indent=2))
    else:
        status = "SUCCESS" if success else "ERROR"
        print(f"[{status}] {message}")
        if data:
            if isinstance(data, list):
                for item in data:
                    print(f"  - {item}")
            elif isinstance(data, dict):
                for key, value in data.items():
                    print(f"  {key}: {value}")

def test_model_call(api_key, model_name):
    """Test a simple API call with the specified model."""
    import openai
    
    client = openai.OpenAI(api_key=api_key)
    try:
        kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Say hello world"}]
        }
        
        # Add model-specific parameters
        if "o3-mini" in model_name:
            kwargs["reasoning_effort"] = "high" if model_name.endswith("-high") else "medium"
        
        response = client.chat.completions.create(**kwargs)
        return {
            "success": True,
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point."""
    args = setup_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from args or environment
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        format_output(False, "No API key provided or found in environment", json_output=args.json)
        return 1
    
    # Run full diagnostics
    if args.diagnose:
        results = diagnose_api_key_issues()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("API Key Diagnostics:")
            print(f"API Key: {results['api_key_prefix']}")
            print(f"Valid: {results['is_valid']}")
            print(f"Preferred Model: {results['preferred_model']}")
            print(f"Preferred Model Available: {results['preferred_model_available']}")
            
            if results['available_models']:
                print("Available Models:")
                for model in results['available_models']:
                    print(f"  - {model}")
            else:
                print("No models available")
                
            if results['recommended_fallback']:
                print(f"Recommended Fallback: {results['recommended_fallback']}")
                
            if results['error_message']:
                print(f"Error: {results['error_message']}")
        return 0
    
    # Validate API key
    is_valid, message = validate_openai_key(api_key)
    if not is_valid:
        format_output(False, message, json_output=args.json)
        return 1
    
    # List all available models
    if args.list_models:
        available_models = get_available_models(api_key)
        if available_models:
            format_output(True, f"Found {len(available_models)} available models:", 
                         data=available_models, json_output=args.json)
        else:
            format_output(False, "No models available with this API key", json_output=args.json)
        return 0
    
    # Check specific model availability
    model_name = args.model
    model_available = check_model_availability(model_name, api_key)
    
    if model_available:
        format_output(True, f"Model '{model_name}' is available", json_output=args.json)
        
        # Test model if requested
        if args.test_model:
            print(f"\nTesting model '{model_name}'...")
            result = test_model_call(api_key, model_name)
            if result["success"]:
                format_output(True, f"Successfully tested model '{model_name}'", 
                             data={"response": result["content"], "usage": result["usage"]}, 
                             json_output=args.json)
            else:
                format_output(False, f"Error testing model '{model_name}'", 
                             data={"error": result["error"]}, json_output=args.json)
    else:
        fallback = recommend_fallback_model(model_name, api_key)
        format_output(False, f"Model '{model_name}' is not available", 
                     data={"recommended_fallback": fallback}, json_output=args.json)
        
        # Test fallback model if requested
        if args.test_model and fallback:
            print(f"\nTesting fallback model '{fallback}'...")
            result = test_model_call(api_key, fallback)
            if result["success"]:
                format_output(True, f"Successfully tested fallback model '{fallback}'", 
                             data={"response": result["content"], "usage": result["usage"]}, 
                             json_output=args.json)
            else:
                format_output(False, f"Error testing fallback model '{fallback}'", 
                             data={"error": result["error"]}, json_output=args.json)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 