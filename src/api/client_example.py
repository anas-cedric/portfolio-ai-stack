"""
Example client for the Financial Analysis API.

This script demonstrates how to interact with the Financial Analysis API.
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Any, Optional

# Base URL for API (change as needed)
BASE_URL = "http://localhost:8000"


def get_datasets() -> Dict[str, Any]:
    """
    Get list of available datasets.
    
    Returns:
        API response with datasets
    """
    response = requests.get(f"{BASE_URL}/datasets")
    return response.json()


def get_market_conditions() -> Dict[str, Any]:
    """
    Get current market conditions.
    
    Returns:
        API response with market conditions
    """
    response = requests.get(f"{BASE_URL}/market_conditions")
    return response.json()


def analyze_data(
    query: str,
    dataset_name: Optional[str] = None,
    dataset_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze financial data with a query.
    
    Args:
        query: Analysis query
        dataset_name: Optional dataset name
        dataset_type: Optional dataset type
        
    Returns:
        API response with analysis
    """
    payload = {
        "query": query,
        "dataset_name": dataset_name,
        "dataset_type": dataset_type
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    return response.json()


def print_json(data: Dict[str, Any]):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))


def main():
    """Run the example client."""
    parser = argparse.ArgumentParser(description="Financial Analysis API Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List datasets command
    subparsers.add_parser("datasets", help="List available datasets")
    
    # Get market conditions command
    subparsers.add_parser("market", help="Get current market conditions")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze financial data")
    analyze_parser.add_argument("query", help="Analysis query")
    analyze_parser.add_argument("--dataset", help="Dataset name")
    analyze_parser.add_argument("--type", help="Dataset type")
    
    args = parser.parse_args()
    
    # Execute command
    try:
        if args.command == "datasets":
            datasets = get_datasets()
            print("\nAvailable Datasets:")
            print("==================")
            for dataset in datasets:
                print(f"- {dataset['name']} ({dataset['type']}, {dataset['format']}, {dataset['size_mb']} MB)")
            
        elif args.command == "market":
            market = get_market_conditions()
            print("\nCurrent Market Conditions:")
            print("========================")
            print(f"Volatility: {market['volatility']:.2f} ({'HIGH' if market['is_high_volatility'] else 'Normal'})")
            print(f"Message: {market['context_message']}")
            
        elif args.command == "analyze":
            print(f"\nAnalyzing query: {args.query}")
            if args.dataset:
                print(f"Using dataset: {args.dataset}")
            
            analysis = analyze_data(args.query, args.dataset, args.type)
            
            print("\nAnalysis Result:")
            print("===============")
            print(analysis["analysis"])
            
            if analysis.get("error"):
                print(f"\nError: {analysis['error']}")
                
        else:
            parser.print_help()
            
    except requests.RequestException as e:
        print(f"Error connecting to API: {str(e)}")
        print(f"Make sure the API server is running at {BASE_URL}")
        sys.exit(1)


if __name__ == "__main__":
    main() 