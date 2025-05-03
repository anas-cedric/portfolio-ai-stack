#!/usr/bin/env python
"""
Test script for the ETF Registry functionality.
"""

import os
import argparse
from dotenv import load_dotenv
import pandas as pd

from src.data.etf_registry import ETFRegistry, AssetClass, ETFProvider

# Load environment variables
load_dotenv()

def main():
    """Run the ETF Registry test."""
    parser = argparse.ArgumentParser(description="ETF Registry Test")
    parser.add_argument("--local", action="store_true", help="Use local storage instead of Supabase")
    parser.add_argument("--export", type=str, help="Export ETF data to CSV file")
    parser.add_argument("--seed", action="store_true", help="Seed the registry with initial ETFs")
    parser.add_argument("--seed-file", type=str, help="CSV file to seed ETFs from")
    parser.add_argument("--search", type=str, help="Search for ETFs by name or ticker")
    parser.add_argument("--provider", type=str, help="Filter ETFs by provider")
    parser.add_argument("--asset-class", type=str, help="Filter ETFs by asset class")
    parser.add_argument("--ticker", type=str, help="Look up a specific ETF by ticker")
    args = parser.parse_args()

    # Create ETF Registry instance
    registry = ETFRegistry(use_supabase=not args.local)
    print(f"Using {'local storage' if args.local else 'Supabase'} for ETF Registry")

    # Seed the registry if requested
    if args.seed:
        registry.seed_initial_etfs(args.seed_file)

    # Perform actions based on arguments
    if args.ticker:
        print(f"\nLooking up ETF: {args.ticker}")
        etf = registry.get_etf(args.ticker)
        if etf:
            print_etf_details(etf)
        else:
            print(f"ETF with ticker {args.ticker} not found")

    if args.search:
        print(f"\nSearching for ETFs matching: {args.search}")
        results = registry.search_etfs(args.search)
        print_etf_dataframe(results)

    if args.provider:
        try:
            # Try to use the enum if it matches
            provider = ETFProvider(args.provider.lower())
        except ValueError:
            # Otherwise use the string directly
            provider = args.provider
        
        print(f"\nFetching ETFs from provider: {provider}")
        results = registry.get_etfs_by_provider(provider)
        print_etf_dataframe(results)

    if args.asset_class:
        try:
            # Try to use the enum if it matches
            asset_class = AssetClass(args.asset_class.lower())
        except ValueError:
            # Otherwise use the string directly
            asset_class = args.asset_class
        
        print(f"\nFetching ETFs of asset class: {asset_class}")
        results = registry.get_etfs_by_asset_class(asset_class)
        print_etf_dataframe(results)

    # If no specific action was requested, show all ETFs
    if not any([args.ticker, args.search, args.provider, args.asset_class]):
        print("\nFetching all ETFs:")
        results = registry.get_all_etfs()
        print_etf_dataframe(results)

    # Export if requested
    if args.export:
        registry.export_to_csv(args.export)

    # Flush local storage if using local mode
    if args.local:
        registry.flush_to_storage()

def print_etf_details(etf):
    """Print details of a single ETF."""
    print("-" * 50)
    print(f"Ticker: {etf.get('ticker')}")
    print(f"Name: {etf.get('name')}")
    print(f"Provider: {etf.get('provider')}")
    print(f"Asset Class: {etf.get('asset_class')}")
    print(f"Inception Date: {etf.get('inception_date')}")
    print(f"Expense Ratio: {etf.get('expense_ratio')}%")
    print(f"URL: {etf.get('fund_info_url')}")
    print(f"Last Updated: {etf.get('last_updated')}")
    print("-" * 50)

def print_etf_dataframe(df):
    """Print a DataFrame of ETFs in a formatted way."""
    if len(df) == 0:
        print("No ETFs found")
        return
    
    # Select a subset of columns for display
    display_columns = ['ticker', 'name', 'provider', 'asset_class', 'expense_ratio']
    display_df = df[display_columns] if all(col in df.columns for col in display_columns) else df
    
    # Print the count and the table
    print(f"Found {len(df)} ETFs")
    print(display_df.to_string(index=False))

if __name__ == "__main__":
    main() 