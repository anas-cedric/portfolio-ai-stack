#!/usr/bin/env python
"""
Fund Metadata Ingestion Script.

This script ingests fund metadata from CSV or JSON files and adds it to the knowledge base.
"""

import os
import sys
import json
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Add the project root to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.append(project_root)

from src.knowledge.schema import (
    FundMetadata, 
    FundType, 
    AssetType, 
    InvestmentStyle,
    SectorExposure,
    GeographicExposure,
    PerformanceMetrics
)
from src.knowledge.knowledge_base import KnowledgeBase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a JSON file containing fund metadata.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of fund metadata dictionaries
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Handle both single object and array of objects
    if isinstance(data, dict):
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected JSON format in {file_path}")


def parse_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a CSV file containing fund metadata.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of fund metadata dictionaries
    """
    funds = []
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            funds.append(row)
    
    return funds


def convert_to_fund_metadata(fund_dict: Dict[str, Any]) -> FundMetadata:
    """
    Convert a dictionary to a FundMetadata object.
    
    Args:
        fund_dict: Dictionary containing fund metadata
        
    Returns:
        FundMetadata object
    """
    # Process sector exposure if available
    sector_exposure = None
    if any(key.startswith('sector_') for key in fund_dict.keys()):
        sector_data = {}
        for key, value in fund_dict.items():
            if key.startswith('sector_'):
                sector_name = key.replace('sector_', '')
                try:
                    sector_data[sector_name] = float(value) if value else 0.0
                except (ValueError, TypeError):
                    sector_data[sector_name] = 0.0
        
        sector_exposure = SectorExposure(**sector_data)
    
    # Process geographic exposure if available
    geographic_exposure = None
    if any(key.startswith('geo_') for key in fund_dict.keys()):
        geo_data = {}
        for key, value in fund_dict.items():
            if key.startswith('geo_'):
                region_name = key.replace('geo_', '')
                try:
                    geo_data[region_name] = float(value) if value else 0.0
                except (ValueError, TypeError):
                    geo_data[region_name] = 0.0
        
        geographic_exposure = GeographicExposure(**geo_data)
    
    # Process performance metrics if available
    performance = None
    perf_keys = [
        'ytd_return', 'one_year_return', 'three_year_return', 
        'five_year_return', 'ten_year_return', 'since_inception_return',
        'sharpe_ratio', 'standard_deviation', 'beta', 'alpha',
        'r_squared', 'max_drawdown'
    ]
    
    if any(key in fund_dict for key in perf_keys):
        perf_data = {}
        for key in perf_keys:
            if key in fund_dict and fund_dict[key]:
                try:
                    perf_data[key] = float(fund_dict[key])
                except (ValueError, TypeError):
                    pass  # Skip if not a valid float
        
        if perf_data:
            performance = PerformanceMetrics(**perf_data)
    
    # Process top holdings if available
    top_holdings = None
    if 'top_holdings' in fund_dict and fund_dict['top_holdings']:
        if isinstance(fund_dict['top_holdings'], str):
            # Parse from string representation "AAPL:5.2,MSFT:4.8,..."
            try:
                holdings_pairs = fund_dict['top_holdings'].split(',')
                top_holdings = {}
                for pair in holdings_pairs:
                    ticker, weight = pair.split(':')
                    top_holdings[ticker.strip()] = float(weight.strip())
            except Exception as e:
                logger.warning(f"Error parsing top_holdings string: {e}")
        elif isinstance(fund_dict['top_holdings'], dict):
            top_holdings = fund_dict['top_holdings']
    
    # Convert string enums to actual enum values
    try:
        fund_type = FundType(fund_dict.get('fund_type', 'etf').lower())
    except ValueError:
        logger.warning(f"Invalid fund_type: {fund_dict.get('fund_type')}, using 'etf'")
        fund_type = FundType.ETF
    
    try:
        asset_type = AssetType(fund_dict.get('asset_type', 'equity').lower())
    except ValueError:
        logger.warning(f"Invalid asset_type: {fund_dict.get('asset_type')}, using 'equity'")
        asset_type = AssetType.EQUITY
    
    investment_style = None
    if 'investment_style' in fund_dict and fund_dict['investment_style']:
        try:
            investment_style = InvestmentStyle(fund_dict['investment_style'].lower())
        except ValueError:
            logger.warning(f"Invalid investment_style: {fund_dict.get('investment_style')}")
    
    # Convert expense_ratio and AUM to proper types
    try:
        expense_ratio = float(fund_dict.get('expense_ratio', 0.0))
    except (ValueError, TypeError):
        logger.warning(f"Invalid expense_ratio: {fund_dict.get('expense_ratio')}, using 0.0")
        expense_ratio = 0.0
    
    try:
        aum = float(fund_dict.get('aum', 0.0))
    except (ValueError, TypeError):
        logger.warning(f"Invalid aum: {fund_dict.get('aum')}, using 0.0")
        aum = 0.0
    
    # Create FundMetadata object
    fund_metadata = FundMetadata(
        ticker=fund_dict.get('ticker', '').upper(),
        name=fund_dict.get('name', f"Fund {fund_dict.get('ticker', 'Unknown')}"),
        fund_type=fund_type,
        asset_type=asset_type,
        investment_style=investment_style,
        expense_ratio=expense_ratio,
        inception_date=fund_dict.get('inception_date', ''),
        aum=aum,
        tracking_error=float(fund_dict.get('tracking_error', 0.0)) if fund_dict.get('tracking_error') else None,
        dividend_yield=float(fund_dict.get('dividend_yield', 0.0)) if fund_dict.get('dividend_yield') else None,
        provider=fund_dict.get('provider', ''),
        sector_exposure=sector_exposure,
        geographic_exposure=geographic_exposure,
        performance=performance,
        liquidity=float(fund_dict.get('liquidity', 0.0)) if fund_dict.get('liquidity') else None,
        holdings_count=int(fund_dict.get('holdings_count', 0)) if fund_dict.get('holdings_count') else None,
        top_holdings=top_holdings,
        tax_efficiency_score=float(fund_dict.get('tax_efficiency_score', 0.0)) if fund_dict.get('tax_efficiency_score') else None,
        description=fund_dict.get('description', '')
    )
    
    return fund_metadata


def ingest_file(
    file_path: str,
    knowledge_base: KnowledgeBase,
    skip_existing: bool = False
) -> int:
    """
    Ingest a file into the knowledge base.
    
    Args:
        file_path: Path to the file
        knowledge_base: Knowledge base instance
        skip_existing: Whether to skip existing funds
        
    Returns:
        Number of funds added
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 0
    
    # Determine file type and parse accordingly
    if file_path.suffix.lower() == '.json':
        fund_dicts = parse_json_file(file_path)
    elif file_path.suffix.lower() == '.csv':
        fund_dicts = parse_csv_file(file_path)
    else:
        logger.error(f"Unsupported file type: {file_path.suffix}")
        return 0
    
    logger.info(f"Parsed {len(fund_dicts)} funds from {file_path}")
    
    # Check for required fields
    funds_added = 0
    for fund_dict in fund_dicts:
        # Skip funds without a ticker
        if not fund_dict.get('ticker'):
            logger.warning(f"Skipping fund without ticker")
            continue
        
        try:
            # Convert to FundMetadata
            fund_metadata = convert_to_fund_metadata(fund_dict)
            
            # Add to knowledge base
            knowledge_base.add_fund_metadata(fund_metadata)
            funds_added += 1
            
        except Exception as e:
            logger.error(f"Error processing fund {fund_dict.get('ticker')}: {e}")
    
    logger.info(f"Added {funds_added} funds to knowledge base")
    return funds_added


def ingest_directory(
    directory_path: str,
    knowledge_base: KnowledgeBase,
    recursive: bool = False,
    skip_existing: bool = False
) -> int:
    """
    Ingest all supported files in a directory.
    
    Args:
        directory_path: Path to the directory
        knowledge_base: Knowledge base instance
        recursive: Whether to recursively process subdirectories
        skip_existing: Whether to skip existing funds
        
    Returns:
        Number of funds added
    """
    directory_path = Path(directory_path)
    
    if not directory_path.is_dir():
        logger.error(f"Directory not found: {directory_path}")
        return 0
    
    # Get file patterns
    patterns = ['*.json', '*.csv']
    
    # Find all matching files
    files = []
    for pattern in patterns:
        if recursive:
            files.extend(directory_path.glob(f"**/{pattern}"))
        else:
            files.extend(directory_path.glob(pattern))
    
    logger.info(f"Found {len(files)} files in {directory_path}")
    
    # Process each file
    total_funds_added = 0
    for file_path in files:
        funds_added = ingest_file(file_path, knowledge_base, skip_existing)
        total_funds_added += funds_added
    
    logger.info(f"Total: Added {total_funds_added} funds to knowledge base")
    return total_funds_added


def main():
    """Main function to run the ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest fund metadata into the knowledge base")
    
    # Create mutual exclusive group for file vs directory
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", "-f", help="Path to a CSV or JSON file")
    input_group.add_argument("--directory", "-d", help="Path to a directory of CSV/JSON files")
    
    # Add other arguments
    parser.add_argument("--recursive", "-r", action="store_true", help="Process subdirectories recursively")
    parser.add_argument("--skip-existing", "-s", action="store_true", help="Skip existing funds")
    
    args = parser.parse_args()
    
    # Initialize knowledge base
    knowledge_base = KnowledgeBase()
    
    # Process file or directory
    if args.file:
        ingest_file(args.file, knowledge_base, args.skip_existing)
    elif args.directory:
        ingest_directory(args.directory, knowledge_base, args.recursive, args.skip_existing)
    
    # Print statistics
    stats = knowledge_base.get_statistics()
    print(f"\nKnowledge Base Statistics:")
    print(f"Total items added: {stats['items_added']}")
    print(f"Last updated: {stats['last_updated']}")


if __name__ == "__main__":
    main() 