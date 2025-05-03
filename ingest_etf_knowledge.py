#!/usr/bin/env python
"""
Ingest ETF data into the knowledge base.

This script bulk collects ETF data using the ETFDataCollector and adds it
to the Pinecone knowledge base for retrieval.
"""

import os
import sys
import argparse
import logging
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv

from src.data.etf_registry import ETFRegistry
from src.data.etf_collector import ETFDataCollector
from add_fund_knowledge import add_knowledge_to_pinecone

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def main():
    """Bulk ingest ETF data into the knowledge base."""
    parser = argparse.ArgumentParser(description="Ingest ETF Data to Knowledge Base")
    parser.add_argument("--local", action="store_true", help="Use local storage instead of Supabase")
    parser.add_argument("--file", type=str, help="JSON file with list of tickers to ingest")
    parser.add_argument("--all", action="store_true", help="Ingest all ETFs in the registry")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of ETFs to ingest")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually add to knowledge base")
    parser.add_argument("--output", type=str, help="Output file for collected data (JSON)")
    args = parser.parse_args()

    # Validate arguments
    if not args.file and not args.all:
        logger.error("Either --file or --all must be provided")
        sys.exit(1)

    # Create ETF Registry
    registry = ETFRegistry(use_supabase=not args.local)
    
    # Create ETF Data Collector
    collector = ETFDataCollector(registry=registry)
    
    # Get list of tickers to process
    tickers = []
    if args.file:
        try:
            with open(args.file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    tickers = [t.upper() for t in data]
                elif isinstance(data, dict) and 'tickers' in data:
                    tickers = [t.upper() for t in data['tickers']]
                else:
                    logger.error(f"Invalid file format: {args.file}")
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading file {args.file}: {e}")
            sys.exit(1)
    elif args.all:
        # Get all ETFs from registry
        etfs = registry.get_all_etfs()
        tickers = [etf['ticker'] for etf in etfs]
    
    if args.limit and len(tickers) > args.limit:
        logger.info(f"Limiting to {args.limit} tickers (from {len(tickers)} total)")
        tickers = tickers[:args.limit]
    
    logger.info(f"Processing {len(tickers)} ETFs")
    
    # Track processed ETFs
    successful = []
    failed = []
    collected_data = {}
    
    # Process each ticker
    for ticker in tqdm(tickers, desc="Ingesting ETFs"):
        try:
            # Collect ETF data
            etf_data = collector.collect_etf_data(ticker)
            collected_data[ticker] = etf_data
            
            if "error" in etf_data:
                logger.warning(f"Error collecting data for {ticker}: {etf_data['error']}")
                failed.append(ticker)
                continue
            
            # Convert to knowledge item
            knowledge = collector.convert_to_knowledge_items(ticker)
            
            # Add to Pinecone
            if not args.dry_run:
                success = add_knowledge_to_pinecone(
                    id=knowledge["id"],
                    content=knowledge["content"],
                    metadata=knowledge
                )
                
                if success:
                    logger.info(f"Successfully added {ticker} to knowledge base")
                    successful.append(ticker)
                else:
                    logger.error(f"Failed to add {ticker} to knowledge base")
                    failed.append(ticker)
            else:
                logger.info(f"[DRY RUN] Would add {ticker} to knowledge base")
                successful.append(ticker)
            
            # Rate limit to avoid API throttling
            time.sleep(1)  
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            failed.append(ticker)
    
    # Output summary
    print(f"\nProcessed {len(tickers)} ETFs")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed tickers:")
        for ticker in failed:
            print(f"  - {ticker}")
    
    # Output data to file if requested
    if args.output and collected_data:
        with open(args.output, 'w') as f:
            json.dump(collected_data, f, indent=2)
        logger.info(f"Saved collected data to {args.output}")


if __name__ == "__main__":
    main() 