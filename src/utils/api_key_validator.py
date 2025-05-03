"""
API Key Validator utility.

This module provides functions to validate API keys and check available models.
"""

import os
import logging
import openai
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_openai_key(api_key: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate an OpenAI API key by making a simple request.
    
    Args:
        api_key: The API key to validate, or None to use environment variable
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
    if not api_key:
        return False, "No API key provided or found in environment"
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Try to list models as a simple validation
        models = client.models.list()
        return True, f"API key is valid. Found {len(models.data)} available models."
    except Exception as e:
        error_message = str(e)
        if "invalid_project" in error_message:
            return False, "API key project issue: You do not have access to the project tied to the API key."
        elif "invalid_request_error" in error_message:
            return False, f"Invalid request error: {error_message}"
        elif "invalid_api_key" in error_message:
            return False, "Invalid API key: The API key provided is not valid."
        else:
            return False, f"API key validation failed: {error_message}"

def get_available_models(api_key: Optional[str] = None) -> List[str]:
    """
    Get a list of available models for the API key.
    
    Args:
        api_key: The API key to use, or None to use environment variable
        
    Returns:
        List of available model IDs
    """
    if not api_key:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
    if not api_key:
        logger.error("No API key provided or found in environment")
        return []
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return []

def check_model_availability(model_id: str, api_key: Optional[str] = None) -> bool:
    """
    Check if a specific model is available for the API key.
    
    Args:
        model_id: The model ID to check
        api_key: The API key to use, or None to use environment variable
        
    Returns:
        True if the model is available, False otherwise
    """
    available_models = get_available_models(api_key)
    return model_id in available_models

def recommend_fallback_model(preferred_model: str, api_key: Optional[str] = None) -> str:
    """
    Recommend a fallback model if the preferred model is not available.
    
    Args:
        preferred_model: The preferred model ID
        api_key: The API key to use, or None to use environment variable
        
    Returns:
        A recommended fallback model ID
    """
    available_models = get_available_models(api_key)
    
    # If the preferred model is available, use it
    if preferred_model in available_models:
        return preferred_model
    
    # Define fallbacks for each model
    MODEL_FALLBACKS = {
        "o4-mini-2025-04-16": ["o3", "o3-mini", "o1"],
        "o3": ["o3-mini", "o1", "gpt-4", "gpt-3.5-turbo"],
        "o3-mini": ["o1", "gpt-4", "gpt-3.5-turbo"],
        "o1": ["gpt-4", "gpt-3.5-turbo"],
        "gpt-4": ["gpt-3.5-turbo"]
    }
    
    # Get fallback options for the preferred model
    fallback_options = MODEL_FALLBACKS.get(preferred_model, ["gpt-3.5-turbo"])
    
    # Find the first available fallback model
    for model in fallback_options:
        if model in available_models:
            logger.info(f"Recommended fallback model for {preferred_model}: {model}")
            return model
    
    # If no fallback model is available, return the first available model or a default
    return available_models[0] if available_models else "gpt-3.5-turbo"

def diagnose_api_key_issues() -> Dict[str, Any]:
    """
    Run a comprehensive diagnosis of API key issues.
    
    Returns:
        Dictionary with diagnosis results
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    model_env = os.getenv("OPENAI_MODEL", "o1")
    
    results = {
        "api_key_present": bool(api_key),
        "api_key_prefix": api_key[:7] + "..." if api_key else None,
        "preferred_model": model_env,
        "is_valid": False,
        "available_models": [],
        "preferred_model_available": False,
        "recommended_fallback": None,
        "error_message": None
    }
    
    if not api_key:
        results["error_message"] = "No API key found in environment"
        return results
    
    # Validate the API key
    is_valid, message = validate_openai_key(api_key)
    results["is_valid"] = is_valid
    
    if not is_valid:
        results["error_message"] = message
        return results
    
    # Get available models
    available_models = get_available_models(api_key)
    results["available_models"] = available_models
    results["preferred_model_available"] = model_env in available_models
    results["recommended_fallback"] = recommend_fallback_model(model_env, api_key)
    
    return results

if __name__ == "__main__":
    # If run directly, perform a diagnosis and print results
    results = diagnose_api_key_issues()
    print("API Key Diagnosis:")
    print(f"API Key Present: {results['api_key_present']}")
    print(f"API Key Prefix: {results['api_key_prefix']}")
    print(f"API Key Valid: {results['is_valid']}")
    print(f"Preferred Model: {results['preferred_model']}")
    print(f"Preferred Model Available: {results['preferred_model_available']}")
    print(f"Available Models: {', '.join(results['available_models']) if results['available_models'] else 'None'}")
    print(f"Recommended Fallback: {results['recommended_fallback']}")
    
    if results["error_message"]:
        print(f"Error: {results['error_message']}") 