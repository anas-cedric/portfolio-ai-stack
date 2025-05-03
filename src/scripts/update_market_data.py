#!/usr/bin/env python3
"""
Market Data Update Pipeline

This script fetches and updates market data for stocks and ETFs
from Alpaca's API, then stores it in the database. It's designed
to be run daily to keep price data and fundamentals up to date.

Usage:
    python update_market_data.py --symbols-file symbols.txt
"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Set

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data_integration.alpaca_market_data import AlpacaMarketData
from src.data_integration.market_data_schema import (
    AssetType, MarketAsset, PriceBar, MarketSnapshot
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"market_data_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Path for local data storage (for development/backup)
DATA_DIR = Path("data/market_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default indices to track
DEFAULT_INDICES = ["SPY", "QQQ", "DIA"]  # ETFs that track S&P 500, NASDAQ, Dow Jones

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update market data for stocks and ETFs"
    )
    
    parser.add_argument(
        "--symbols-file",
        type=str,
        help="Path to a file containing stock/ETF symbols to track (one per line)"
    )
    
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated list of symbols to track"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Number of days of historical data to fetch"
    )
    
    parser.add_argument(
        "--update-assets",
        action="store_true",
        help="Update asset information (not just prices)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/market_data",
        help="Directory to save data files"
    )
    
    parser.add_argument(
        "--include-indices",
        action="store_true",
        help=f"Include default indices ({', '.join(DEFAULT_INDICES)})"
    )
    
    parser.add_argument(
        "--db-only",
        action="store_true",
        help="Only update database, don't save local files"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level"
    )
    
    return parser.parse_args()

def load_symbols(args) -> List[str]:
    """
    Load symbols from file or command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        List of symbols to process
    """
    symbols = set()
    
    # Add symbols from file if provided
    if args.symbols_file:
        try:
            with open(args.symbols_file, 'r') as f:
                file_symbols = [line.strip() for line in f if line.strip()]
                symbols.update(file_symbols)
                logger.info(f"Loaded {len(file_symbols)} symbols from {args.symbols_file}")
        except Exception as e:
            logger.error(f"Error loading symbols from file: {e}")
    
    # Add symbols from command line if provided
    if args.symbols:
        cmd_symbols = [s.strip() for s in args.symbols.split(',')]
        symbols.update(cmd_symbols)
        logger.info(f"Added {len(cmd_symbols)} symbols from command line")
    
    # Add default indices if requested
    if args.include_indices:
        symbols.update(DEFAULT_INDICES)
        logger.info(f"Added default indices: {', '.join(DEFAULT_INDICES)}")
    
    symbols_list = sorted(list(symbols))
    
    if not symbols_list:
        logger.warning("No symbols specified. Please provide symbols via --symbols or --symbols-file.")
        return []
    
    logger.info(f"Processing {len(symbols_list)} symbols")
    return symbols_list

def update_asset_data(alpaca: AlpacaMarketData, symbols: List[str]) -> Dict[str, MarketAsset]:
    """
    Update asset information for the provided symbols.
    
    Args:
        alpaca: AlpacaMarketData client
        symbols: List of symbols to update
        
    Returns:
        Dictionary of symbol to MarketAsset mappings
    """
    assets = {}
    
    logger.info(f"Updating asset information for {len(symbols)} symbols")
    
    for i, symbol in enumerate(symbols):
        logger.info(f"Fetching asset info for {symbol} ({i+1}/{len(symbols)})")
        
        try:
            # Get asset information
            asset_info = alpaca.api.get_asset(symbol)
            
            if asset_info:
                # Create MarketAsset object
                market_asset = MarketAsset.from_alpaca_asset(asset_info._raw)
                
                # Try to get current price
                current_price = alpaca.get_current_price(symbol)
                if current_price:
                    market_asset.current_price = current_price
                    market_asset.price_updated_at = datetime.now()
                
                # Try to get additional fundamental data if available
                fundamental_data = alpaca.get_fundamental_data(symbol)
                
                # Store the asset
                assets[symbol] = market_asset
                logger.info(f"Successfully updated asset info for {symbol}")
            else:
                logger.warning(f"No asset information available for {symbol}")
        
        except Exception as e:
            logger.error(f"Error updating asset info for {symbol}: {e}")
        
        # Add a small delay to avoid rate limits
        if i < len(symbols) - 1:
            time.sleep(0.2)
    
    return assets

def save_assets_to_json(assets: Dict[str, MarketAsset], output_dir: str) -> None:
    """
    Save asset information to JSON files.
    
    Args:
        assets: Dictionary of symbol to MarketAsset mappings
        output_dir: Directory to save the files
    """
    output_path = Path(output_dir) / "assets"
    output_path.mkdir(parents=True, exist_ok=True)
    
    for symbol, asset in assets.items():
        try:
            # Convert to dictionary
            asset_dict = asset.to_dict()
            
            # Save to JSON file
            output_file = output_path / f"{symbol.lower()}_asset.json"
            with open(output_file, 'w') as f:
                json.dump(asset_dict, f, indent=2)
            
            logger.debug(f"Saved asset info for {symbol} to {output_file}")
        except Exception as e:
            logger.error(f"Error saving asset info for {symbol}: {e}")

def update_price_data(
    alpaca: AlpacaMarketData, 
    symbols: List[str], 
    days: int = 5
) -> Dict[str, List[PriceBar]]:
    """
    Update price data for the provided symbols.
    
    Args:
        alpaca: AlpacaMarketData client
        symbols: List of symbols to update
        days: Number of days of historical data to fetch
        
    Returns:
        Dictionary of symbol to list of PriceBar mappings
    """
    price_data = {}
    
    logger.info(f"Updating {days} days of price data for {len(symbols)} symbols")
    
    # Get data for all symbols
    symbol_data = alpaca.get_multiple_symbols_data(
        symbols=symbols,
        timeframe="1Day",
        days=days
    )
    
    # Convert to PriceBar objects
    for symbol, df in symbol_data.items():
        try:
            bars = []
            for _, row in df.iterrows():
                # Create a dictionary in the format expected by from_alpaca_bar
                bar_dict = {
                    "t": row.name.isoformat(),  # Convert pandas timestamp to ISO string
                    "o": row["open"],
                    "h": row["high"],
                    "l": row["low"],
                    "c": row["close"],
                    "v": row["volume"]
                }
                
                # Create PriceBar object
                price_bar = PriceBar.from_alpaca_bar(bar_dict)
                bars.append(price_bar)
            
            price_data[symbol] = bars
            logger.info(f"Successfully updated {len(bars)} price bars for {symbol}")
        except Exception as e:
            logger.error(f"Error converting price data for {symbol}: {e}")
    
    return price_data

def save_price_data_to_csv(price_data: Dict[str, List[PriceBar]], output_dir: str) -> None:
    """
    Save price data to CSV files.
    
    Args:
        price_data: Dictionary of symbol to list of PriceBar mappings
        output_dir: Directory to save the files
    """
    import pandas as pd
    
    output_path = Path(output_dir) / "prices"
    output_path.mkdir(parents=True, exist_ok=True)
    
    for symbol, bars in price_data.items():
        try:
            # Convert to DataFrame
            data = [bar.to_dict() for bar in bars]
            df = pd.DataFrame(data)
            
            # Save to CSV file
            output_file = output_path / f"{symbol.lower()}_daily.csv"
            df.to_csv(output_file, index=False)
            
            logger.debug(f"Saved price data for {symbol} to {output_file}")
        except Exception as e:
            logger.error(f"Error saving price data for {symbol}: {e}")

def create_market_snapshot(alpaca: AlpacaMarketData, price_data: Dict[str, List[PriceBar]]) -> MarketSnapshot:
    """
    Create a market snapshot based on current data.
    
    Args:
        alpaca: AlpacaMarketData client
        price_data: Dictionary of price data by symbol
        
    Returns:
        MarketSnapshot object
    """
    market_status = alpaca.get_market_status()
    is_market_open = market_status.get("is_open", False)
    
    # Create basic snapshot
    snapshot = MarketSnapshot(
        timestamp=datetime.now(),
        market_open=is_market_open
    )
    
    # Add index levels if available
    if "SPY" in price_data and price_data["SPY"]:
        snapshot.sp500_level = price_data["SPY"][-1].close
    
    if "QQQ" in price_data and price_data["QQQ"]:
        snapshot.nasdaq_level = price_data["QQQ"][-1].close
    
    if "DIA" in price_data and price_data["DIA"]:
        snapshot.dow_level = price_data["DIA"][-1].close
    
    # In a real implementation, you'd calculate these from market-wide data
    # For now, we'll leave them as placeholder values
    
    # Create a simplified sector performance dict based on sector ETFs if available
    sector_etfs = {
        "technology": "XLK",
        "healthcare": "XLV",
        "financials": "XLF",
        "consumer_discretionary": "XLY",
        "consumer_staples": "XLP",
        "industrials": "XLI",
        "energy": "XLE",
        "utilities": "XLU",
        "materials": "XLB",
        "real_estate": "XLRE",
        "communication_services": "XLC"
    }
    
    sector_performance = {}
    for sector, etf in sector_etfs.items():
        if etf in price_data and len(price_data[etf]) >= 2:
            bars = price_data[etf]
            if len(bars) >= 2:
                # Calculate percentage change from previous day
                current = bars[-1].close
                previous = bars[-2].close
                pct_change = ((current - previous) / previous) * 100
                sector_performance[sector] = round(pct_change, 2)
    
    snapshot.sector_performance = sector_performance
    
    return snapshot

def save_snapshot_to_json(snapshot: MarketSnapshot, output_dir: str) -> None:
    """
    Save market snapshot to a JSON file.
    
    Args:
        snapshot: MarketSnapshot object
        output_dir: Directory to save the file
    """
    output_path = Path(output_dir) / "snapshots"
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Convert to dictionary
        snapshot_dict = snapshot.to_dict()
        
        # Save to JSON file
        timestamp_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"snapshot_{timestamp_str}.json"
        with open(output_file, 'w') as f:
            json.dump(snapshot_dict, f, indent=2)
        
        logger.info(f"Saved market snapshot to {output_file}")
    except Exception as e:
        logger.error(f"Error saving market snapshot: {e}")

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Set log level from arguments
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Log script start
    logger.info(f"Starting market data update with args: {args}")
    
    try:
        # Load symbols to process
        symbols = load_symbols(args)
        if not symbols:
            return 1
        
        # Initialize Alpaca client
        try:
            logger.info("Initializing Alpaca Market Data client...")
            alpaca = AlpacaMarketData(is_free_tier=True)
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            return 1
        
        # Create output directory
        output_dir = args.output_dir
        if not args.db_only:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Check market status
        market_status = alpaca.get_market_status()
        logger.info(f"Market is {'open' if market_status.get('is_open', False) else 'closed'}")
        
        # Update asset information if requested
        assets = {}
        if args.update_assets:
            assets = update_asset_data(alpaca, symbols)
            
            # Save to JSON files if not db_only
            if not args.db_only and assets:
                save_assets_to_json(assets, output_dir)
        
        # Update price data
        price_data = update_price_data(alpaca, symbols, args.days)
        
        # Save to CSV files if not db_only
        if not args.db_only and price_data:
            save_price_data_to_csv(price_data, output_dir)
        
        # Create and save market snapshot
        snapshot = create_market_snapshot(alpaca, price_data)
        
        if not args.db_only:
            save_snapshot_to_json(snapshot, output_dir)
        
        # Here you would also update the database
        # For now, we just log the operation
        logger.info(f"Would update database with {len(assets)} assets and {sum(len(bars) for bars in price_data.values())} price bars")
        
        return 0
        
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 