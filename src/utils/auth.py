"""
API authentication utilities.

This module provides API key-based authentication for the financial analysis API.
"""

import os
import secrets
import logging
from typing import Optional
from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment or generate a secure one if not present
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logger.warning("API_KEY not found in environment. Generating a random key.")
    API_KEY = secrets.token_urlsafe(32)
    logger.info(f"Generated API_KEY: {API_KEY}")
    logger.warning("This key will change on restart unless added to your .env file.")

API_KEY_NAME = "X-API-Key"

# Create API key header security scheme
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)) -> Optional[str]:
    """
    Validate API key from request header.
    
    Args:
        api_key: API key from request header
        
    Returns:
        Validated API key if valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        logger.warning("API request missing API key")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, 
            detail="Missing API key"
        )
    
    if api_key != API_KEY:
        # Log the attempt but not the actual key for security
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, 
            detail="Invalid API key"
        )
    
    return api_key

def has_valid_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Check if the API key is valid without raising an exception.
    
    Args:
        api_key: API key from request header
        
    Returns:
        True if API key is valid, False otherwise
    """
    return api_key == API_KEY 