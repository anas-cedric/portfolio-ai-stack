#!/usr/bin/env python
"""
Portfolio Advisor CLI - LangGraph Implementation with LangSmith.

This command-line tool demonstrates the LangGraph-based portfolio advisor,
which uses context retrieval and Claude AI to make portfolio decisions.
Now with LangSmith integration for tracking and prompt versioning.

Usage:
  python portfolio_advisor.py "Should I buy more AAPL?"
  python portfolio_advisor.py -i  # Interactive mode
  python portfolio_advisor.py -p profiles/conservative.json  # Use a specific profile
  python portfolio_advisor.py -l  # Enable LangSmith tracking
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from src.langgraph_engine.graph import run_portfolio_graph
from src.langgraph_engine.langsmith_integration import (
    init_langsmith, 
    get_langsmith_integration,
    LangSmithIntegration
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default user profile
DEFAULT_USER_PROFILE = {
    "risk_tolerance": "moderate",
    "investment_goals": ["retirement", "growth"],
    "time_horizon": "long-term",
    "age": 35,
    "income": "mid-range"
}

# Default portfolio data
DEFAULT_PORTFOLIO = {
    "total_value": 125000.00,
    "holdings": [
        {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "value": 50000.00, "percentage": 40.0},
        {"ticker": "VXUS", "name": "Vanguard Total International Stock ETF", "value": 25000.00, "percentage": 20.0},
        {"ticker": "BND", "name": "Vanguard Total Bond Market ETF", "value": 30000.00, "percentage": 24.0},
        {"ticker": "BNDX", "name": "Vanguard Total International Bond ETF", "value": 15000.00, "percentage": 12.0},
        {"ticker": "AAPL", "name": "Apple Inc.", "value": 5000.00, "percentage": 4.0}
    ],
    "allocations": {
        "US Stocks": 44.0,
        "International Stocks": 20.0,
        "US Bonds": 24.0,
        "International Bonds": 12.0
    }
}


def load_user_profile(profile_path: str) -> Dict[str, Any]:
    """
    Load a user profile from a JSON file.
    
    Args:
        profile_path: Path to the profile JSON file
        
    Returns:
        User profile dictionary
    """
    try:
        with open(profile_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading profile from {profile_path}: {str(e)}")
        logger.info("Using default profile instead")
        return DEFAULT_USER_PROFILE


def format_portfolio_holdings(portfolio: Dict[str, Any]) -> str:
    """
    Format portfolio holdings for display.
    
    Args:
        portfolio: Portfolio data
        
    Returns:
        Formatted portfolio holdings string
    """
    if not portfolio or "holdings" not in portfolio:
        return "No portfolio data available"
    
    result = [
        f"Portfolio Value: ${portfolio['total_value']:,.2f}",
        "\nHoldings:"
    ]
    
    for holding in portfolio["holdings"]:
        result.append(
            f"  {holding['ticker']:<5} {holding['name']:<40} "
            f"${holding['value']:>10,.2f} ({holding['percentage']:>5.1f}%)"
        )
    
    if "allocations" in portfolio:
        result.append("\nAllocations:")
        for asset_class, percentage in portfolio["allocations"].items():
            result.append(f"  {asset_class:<20} {percentage:>5.1f}%")
    
    return "\n".join(result)


def format_decision_result(result: Dict[str, Any]) -> str:
    """
    Format the decision result for display.
    
    Args:
        result: Decision result from the portfolio graph
        
    Returns:
        Formatted decision result string
    """
    if not result:
        return "No result available"
    
    output = []
    
    # Add LangSmith run ID if available
    if "langsmith_run_id" in result:
        output.append(f"LangSmith Run ID: {result['langsmith_run_id']}")
        output.append("")
    
    # Add decision
    if "decision" in result and result["decision"]:
        decision = result["decision"]
        output.append("DECISION:")
        if isinstance(decision, dict):
            if "action" in decision:
                output.append(f"Action: {decision['action']}")
            if "details" in decision:
                output.append(f"Details: {decision['details']}")
        else:
            output.append(str(decision))
    
    # Add reasoning
    if "reasoning" in result and result["reasoning"]:
        output.append("\nREASONING:")
        output.append(result["reasoning"])
    
    # Add recommendations
    if "recommendations" in result and result["recommendations"]:
        output.append("\nRECOMMENDATIONS:")
        for i, rec in enumerate(result["recommendations"], 1):
            if isinstance(rec, dict):
                output.append(f"{i}. {rec.get('type', 'Recommendation')}: {rec.get('details', '')}")
                if "rationale" in rec:
                    output.append(f"   Rationale: {rec['rationale']}")
            else:
                output.append(f"{i}. {rec}")
    
    # Add confidence
    if "confidence" in result and result["confidence"]:
        output.append(f"\nConfidence: {result['confidence'] * 100:.1f}%")
    
    # Add sources
    if "sources_used" in result and result["sources_used"]:
        output.append("\nSOURCES:")
        for source in result["sources_used"]:
            output.append(f"- {source}")
    
    return "\n".join(output)


def run_advisor(
    query: str,
    user_profile: Dict[str, Any],
    portfolio_data: Optional[Dict[str, Any]] = None,
    market_state: Optional[Dict[str, Any]] = None,
    use_langsmith: bool = False
) -> Dict[str, Any]:
    """
    Run the portfolio advisor with the given query and data.
    
    Args:
        query: The user's query
        user_profile: User profile information
        portfolio_data: Current portfolio state
        market_state: Current market conditions
        use_langsmith: Whether to use LangSmith tracking
        
    Returns:
        The decision result
    """
    logger.info(f"Running advisor with query: {query}")
    logger.info(f"LangSmith tracking: {'enabled' if use_langsmith else 'disabled'}")
    
    if use_langsmith:
        # Use LangSmith integration
        langsmith = get_langsmith_integration()
        result = langsmith.run_tracked_portfolio_graph(
            query=query,
            user_profile=user_profile,
            portfolio_data=portfolio_data,
            market_state=market_state
        )
    else:
        # Use standard portfolio graph
        result = run_portfolio_graph(
            query=query,
            user_profile=user_profile,
            portfolio_data=portfolio_data,
            market_state=market_state
        )
    
    return result


def interactive_mode(
    user_profile: Dict[str, Any],
    portfolio_data: Optional[Dict[str, Any]] = None,
    use_langsmith: bool = False
):
    """
    Run the portfolio advisor in interactive mode.
    
    Args:
        user_profile: User profile information
        portfolio_data: Current portfolio state
        use_langsmith: Whether to use LangSmith tracking
    """
    print("\n===== Portfolio Advisor =====")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'profile' to see your profile")
    print("Type 'portfolio' to see your portfolio")
    if use_langsmith:
        print("Type 'prompts' to list available prompt versions")
        print("Type 'set prompt [name] [version]' to change prompt version")
    print("=====================================\n")
    
    # Initialize LangSmith if needed
    if use_langsmith:
        langsmith = get_langsmith_integration()
    
    while True:
        try:
            query = input("\nWhat would you like to know about your portfolio? ").strip()
            
            if not query:
                continue
                
            if query.lower() in ('exit', 'quit'):
                print("Exiting advisor session. Goodbye!")
                break
                
            if query.lower() == 'profile':
                print("\nYOUR PROFILE:")
                print(json.dumps(user_profile, indent=2))
                continue
                
            if query.lower() == 'portfolio':
                print("\nYOUR PORTFOLIO:")
                print(format_portfolio_holdings(portfolio_data))
                continue
            
            if use_langsmith and query.lower() == 'prompts':
                # List available prompts
                print("\nAVAILABLE PROMPTS:")
                for prompt_name in ["decision_maker", "context_retriever"]:
                    print(f"\n{prompt_name.upper()}:")
                    versions = langsmith.get_prompt_versions(prompt_name)
                    for v in versions:
                        active = "*" if v.get("version") == langsmith.prompt_manager.current_versions.get(prompt_name) else " "
                        print(f"{active} {v.get('version')} - {v.get('description', 'No description')} "
                              f"[{v.get('source', 'unknown')}]")
                continue
            
            if use_langsmith and query.lower().startswith('set prompt '):
                # Set prompt version
                parts = query.split()
                if len(parts) >= 4:
                    prompt_name = parts[2]
                    version = parts[3]
                    success = langsmith.set_active_prompt_version(prompt_name, version)
                    if success:
                        print(f"Set {prompt_name} to version {version}")
                    else:
                        print(f"Failed to set {prompt_name} to version {version}")
                else:
                    print("Usage: set prompt [name] [version]")
                continue
            
            # Process the query
            result = run_advisor(
                query=query,
                user_profile=user_profile,
                portfolio_data=portfolio_data,
                use_langsmith=use_langsmith
            )
            
            # Display the result
            print("\n" + "=" * 50)
            print(format_decision_result(result))
            print("=" * 50)
            
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            logger.exception("Error in interactive mode")


def main():
    """Main entry point for the portfolio advisor CLI."""
    parser = argparse.ArgumentParser(description="Portfolio Advisor CLI")
    parser.add_argument("query", nargs="?", default="", help="Query about portfolio")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("-p", "--profile", help="Path to user profile JSON file")
    parser.add_argument("-o", "--portfolio", help="Path to portfolio JSON file")
    parser.add_argument("-l", "--langsmith", action="store_true", help="Enable LangSmith tracking")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load user profile
    user_profile = DEFAULT_USER_PROFILE
    if args.profile:
        user_profile = load_user_profile(args.profile)
    
    # Load portfolio data
    portfolio_data = DEFAULT_PORTFOLIO
    if args.portfolio:
        try:
            with open(args.portfolio, "r") as f:
                portfolio_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading portfolio from {args.portfolio}: {str(e)}")
            logger.info("Using default portfolio instead")
    
    # Initialize LangSmith if requested
    if args.langsmith:
        init_langsmith(
            project_name="portfolio-advisor-cli",
            enable_tracking=True,
            enable_prompt_versioning=True
        )
        logger.info("LangSmith integration initialized")
    
    # Run in interactive mode or process a single query
    if args.interactive:
        interactive_mode(user_profile, portfolio_data, args.langsmith)
    elif args.query:
        result = run_advisor(
            query=args.query,
            user_profile=user_profile,
            portfolio_data=portfolio_data,
            use_langsmith=args.langsmith
        )
        print(format_decision_result(result))
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 