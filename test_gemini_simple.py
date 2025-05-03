#!/usr/bin/env python3
"""
Simple test script for Gemini 2.5 Pro Experimental model.

This script follows the exact approach recommended in the documentation
to test if the Gemini 2.5 Pro Experimental model is accessible and working.
"""

import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    exit(1)

logger.info(f"Using API key: {GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-5:]}")

def test_gemini_simple():
    """Test the Gemini 2.5 Pro Experimental model using the standard approach."""
    try:
        # Configure the API with your key
        logger.info("Configuring API with key")
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Initialize the model
        model_name = "gemini-2.5-pro-exp-03-25"
        logger.info(f"Initializing model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        # Simple prompt
        prompt = "Explain how neural networks work in simple terms."
        logger.info(f"Sending prompt: '{prompt}'")
        
        # Generate content
        logger.info("Generating content...")
        response = model.generate_content(prompt)
        
        # Print response
        logger.info("Response received:")
        logger.info("-" * 50)
        logger.info(response.text if hasattr(response, 'text') else "No text in response")
        logger.info("-" * 50)
        
        # Save response to file
        output = {
            "prompt": prompt,
            "response": response.text if hasattr(response, 'text') else None,
            "model": model_name
        }
        
        with open("gemini_simple_test_result.json", "w") as f:
            json.dump(output, f, indent=2)
            
        logger.info("Response saved to gemini_simple_test_result.json")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Gemini model: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting simple Gemini test")
    success = test_gemini_simple()
    logger.info(f"Test {'succeeded' if success else 'failed'}")
    exit(0 if success else 1) 