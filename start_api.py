#!/usr/bin/env python
"""
Start the Portfolio Advisor API server.

This script starts the FastAPI server for the Portfolio Advisor API.
"""

import uvicorn
import logging
from dotenv import load_dotenv
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Start the API server."""
    logger.info("Starting Portfolio Advisor API server...")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set. Please set it before starting the server.")
        sys.exit(1)
    
    # Start the server
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Server will be available at http://{host}:{port}")
    logger.info("API documentation will be available at http://localhost:8000/docs")
    
    uvicorn.run(
        "src.api.portfolio_api:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    main() 