#!/usr/bin/env python3
"""
Simple test script for Gemini 2.5 Pro with basic financial questions.

This script provides a minimal test to see if the Gemini 2.5 Pro model can handle
basic financial queries.
"""

import os
import sys
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

def test_simple_finance():
    """Test Gemini with a simple financial question."""
    try:
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return False

        # Configure API
        logger.info("Configuring API with key")
        genai.configure(api_key=api_key)
        
        # Initialize model
        model_name = "gemini-2.5-pro-exp-03-25"
        logger.info(f"Initializing Gemini model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        # Simple financial question
        prompt = """
        What are the benefits of index funds compared to actively managed funds?
        Please provide a concise analysis that covers:
        1. Cost differences
        2. Performance considerations
        3. Tax implications
        4. Simplicity and management effort
        """
        
        logger.info(f"Sending simple financial prompt (length: {len(prompt)})")
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Process response safely
        logger.info("Response received, extracting text...")
        
        try:
            # Try to access text property
            text = response.text
            success = True
        except Exception as e:
            # If .text fails, try extracting manually
            logger.warning(f"Could not access .text property: {str(e)}")
            
            text = "No text could be extracted"
            success = False
            
            # Try manual extraction
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts:
                            text = parts[0].text
                            success = True
            except Exception as inner_e:
                logger.error(f"Manual extraction failed: {str(inner_e)}")
        
        # Log and save result
        if success:
            logger.info(f"Extracted response text (length: {len(text)})")
            logger.info("-" * 50)
            logger.info(text[:500] + "..." if len(text) > 500 else text)
            logger.info("-" * 50)
        else:
            logger.error("Failed to extract text from response")
            logger.error(f"Response structure: {dir(response)}")
        
        # Save result regardless
        result = {
            "prompt": prompt,
            "response": text,
            "model": model_name,
            "success": success
        }
        
        output_file = "simple_finance_result.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"Result saved to {output_file}")
        return success
        
    except Exception as e:
        logger.error(f"Error in simple finance test: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting simple finance test")
    success = test_simple_finance()
    logger.info(f"Test {'succeeded' if success else 'failed'}")
    sys.exit(0 if success else 1) 