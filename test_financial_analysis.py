#!/usr/bin/env python3
"""
Test script for FinancialPrompts with Gemini 2.5 Pro.

This script tests the updated FinancialPrompts class with the Gemini 2.5 Pro Experimental model.
"""

import sys
import json
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.prompts.financial_prompts import FinancialPrompts

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_simple_financial_analysis():
    """Test a simple financial analysis using the FinancialPrompts class."""
    logger.info("Testing simple financial analysis")
    
    # Simple prompt for index fund comparison
    prompt = """
    What are the benefits of index funds compared to actively managed funds?
    Please provide a concise analysis that covers:
    1. Cost differences
    2. Performance considerations
    3. Tax implications
    4. Simplicity and management effort
    """
    
    logger.info("Sending prompt for analysis")
    
    # Get analysis
    result = FinancialPrompts.analyze_financial_data(prompt)
    
    # Check result
    if "error" in result:
        logger.error(f"Analysis failed: {result['error']}")
        success = False
    else:
        logger.info(f"Analysis successful with model: {result['model_used']}")
        logger.info("-" * 50)
        logger.info(result['analysis'][:500] + "..." if len(result['analysis']) > 500 else result['analysis'])
        logger.info("-" * 50)
        success = True
    
    # Save results
    output_file = "financial_analysis_class_test.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Results saved to {output_file}")
    return success

if __name__ == "__main__":
    logger.info("Starting financial prompts class test")
    success = test_simple_financial_analysis()
    logger.info(f"Test {'succeeded' if success else 'failed'}")
    sys.exit(0 if success else 1) 