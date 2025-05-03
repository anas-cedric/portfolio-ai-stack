#!/usr/bin/env python3
"""
Test script for financial prompts with Gemini 2.5 Pro.

This script tests the FinancialPrompts class with the Gemini 2.5 Pro Experimental model.
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

def test_portfolio_analysis():
    """Test the portfolio analysis prompt with OpenAI models."""
    logger.info("Testing portfolio analysis with OpenAI o3/o4 models")
    
    # Sample portfolio data
    portfolio_data = {
        "total_value": 250000,
        "holdings": [
            {
                "ticker": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "value": 100000,
                "percentage": 40.0
            },
            {
                "ticker": "QQQ",
                "name": "Invesco QQQ Trust",
                "value": 50000,
                "percentage": 20.0
            },
            {
                "ticker": "BND",
                "name": "Vanguard Total Bond Market ETF",
                "value": 75000,
                "percentage": 30.0
            },
            {
                "ticker": "VNQ",
                "name": "Vanguard Real Estate ETF",
                "value": 25000,
                "percentage": 10.0
            }
        ],
        "allocations": {
            "US Stocks": 60.0,
            "Bonds": 30.0,
            "Real Estate": 10.0,
            "International": 0.0
        }
    }
    
    # Sample market data
    market_data = {
        "S&P 500": "+15% YTD",
        "Nasdaq": "+20% YTD",
        "10-Year Treasury Yield": "3.8%",
        "Inflation Rate": "3.2%",
        "Market Trend": "Bullish with increased volatility"
    }
    
    # Sample risk profile
    risk_profile = {
        "risk_tolerance": "Moderate",
        "investment_goals": ["Long-term growth", "Retirement"],
        "time_horizon": "15-20 years",
        "age": 42
    }
    
    # Test 1: Mathematical portfolio calculations with o4-mini-high
    logger.info("Testing portfolio calculations with o4-mini-high...")
    calculation_result = FinancialPrompts.analyze_portfolio_calculations(portfolio_data)
    
    # Log the calculation result
    logger.info(f"Calculation model used: {calculation_result.get('model_used', 'unknown')}")
    if 'error' in calculation_result:
        logger.error(f"Calculation error: {calculation_result['error']}")
    else:
        logger.info("Portfolio calculations received successfully")
        logger.info("-" * 50)
        logger.info(calculation_result['analysis'][:500] + "..." if len(calculation_result['analysis']) > 500 else calculation_result['analysis'])
        logger.info("-" * 50)
    
    # Test 2: Strategy explanations with o3
    logger.info("Testing portfolio strategy explanation with o3...")
    explanation_result = FinancialPrompts.explain_portfolio_strategy(portfolio_data, market_data)
    
    # Log the explanation result
    logger.info(f"Explanation model used: {explanation_result.get('model_used', 'unknown')}")
    if 'error' in explanation_result:
        logger.error(f"Explanation error: {explanation_result['error']}")
    else:
        logger.info("Portfolio explanation received successfully")
        logger.info("-" * 50)
        logger.info(explanation_result['analysis'][:500] + "..." if len(explanation_result['analysis']) > 500 else explanation_result['analysis'])
        logger.info("-" * 50)
    
    # Save the results
    calculation_file = "portfolio_calculation_result.json"
    with open(calculation_file, "w") as f:
        json.dump(calculation_result, f, indent=2)
    
    explanation_file = "portfolio_explanation_result.json"
    with open(explanation_file, "w") as f:
        json.dump(explanation_result, f, indent=2)
    
    logger.info(f"Calculation results saved to {calculation_file}")
    logger.info(f"Explanation results saved to {explanation_file}")
    
    return 'error' not in calculation_result and 'error' not in explanation_result

if __name__ == "__main__":
    logger.info("Starting financial prompts test")
    success = test_portfolio_analysis()
    logger.info(f"Test {'succeeded' if success else 'failed'}")
    sys.exit(0 if success else 1) 