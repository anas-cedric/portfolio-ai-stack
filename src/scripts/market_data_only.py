"""
Simple Market Data Demo

This script demonstrates fetching market data from Alpaca without 
storing it in the knowledge base, to avoid vector database issues.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data_integration.alpaca_market_data import AlpacaMarketData

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def run_simple_demo():
    """Run a simple demonstration of market data fetching."""
    logger.info("Starting simple market data demo")
    
    # Check if Alpaca keys are present
    if not os.getenv("ALPACA_DATA_API_KEY") or not os.getenv("ALPACA_DATA_API_SECRET"):
        logger.error("Alpaca API keys not found in .env file")
        logger.error("Please set ALPACA_DATA_API_KEY and ALPACA_DATA_API_SECRET in your .env file")
        return
    
    # Initialize Alpaca market data client with the correct environment variable names
    alpaca_client = AlpacaMarketData(
        api_key=os.getenv("ALPACA_DATA_API_KEY"),
        api_secret=os.getenv("ALPACA_DATA_API_SECRET"),
        base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        is_free_tier=True  # Using free tier (15-min delay)
    )
    
    # Watchlist of symbols to check
    symbols = [
        "SPY",   # S&P 500 ETF
        "QQQ",   # Nasdaq 100 ETF
        "DIA",   # Dow Jones Industrial Average ETF
        "IWM",   # Russell 2000 ETF
        "VTI",   # Total Stock Market ETF
        "AAPL",  # Apple (popular stock example)
        "TSLA",  # Tesla (popular stock example)
        "XLK",   # Technology Sector ETF
        "XLF",   # Financial Sector ETF
        "XLE",   # Energy Sector ETF
    ]
    
    try:
        # Display current watchlist
        logger.info(f"Watchlist: {', '.join(symbols)}")
        
        # Get account info
        try:
            account_info = alpaca_client.get_account_info()
            logger.info(f"Account Status: {account_info.get('status', 'Unknown')}")
            logger.info(f"Account Cash: ${float(account_info.get('cash', 0)):.2f}")
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
        
        # Get current prices
        logger.info("\n=== Current Market Prices (15-min delayed) ===")
        for symbol in symbols:
            price = alpaca_client.get_current_price(symbol)
            if price:
                logger.info(f"{symbol}: ${price:.2f}")
            else:
                logger.info(f"{symbol}: Data not available")
        
        # Get historical data for first symbol
        logger.info(f"\n=== Historical Data for {symbols[0]} ===")
        
        # Use absolute dates in 2023-2024 instead of relative dates
        # since the system time appears to be in 2025
        end_date = datetime(2024, 3, 30)     # March 30, 2024
        start_date = datetime(2024, 3, 1)    # March 1, 2024
        
        logger.info(f"Fetching historical data from {start_date.date()} to {end_date.date()}")
        
        try:
            # Try with 1Day timeframe first since we're using dates from a few months ago
            historical_bars = alpaca_client.get_historical_bars(
                symbol=symbols[0],
                timeframe="1Day",
                start=start_date,
                end=end_date,
                limit=10
            )
            
            if not historical_bars.empty:
                logger.info(f"Last {len(historical_bars)} days of data:")
                for idx, row in historical_bars.iterrows():
                    logger.info(f"  {idx.date()} - Open: ${row['open']:.2f}, Close: ${row['close']:.2f}, Volume: {row['volume']:,}")
            else:
                # If daily data fails, try with hourly data
                logger.warning(f"No daily data available for {symbols[0]}, trying hourly data")
                
                # Narrower time range for hourly data
                hourly_end = datetime(2024, 3, 30, 16, 0)     # March 30, 2024 at 4 PM
                hourly_start = datetime(2024, 3, 30, 9, 30)   # March 30, 2024 at 9:30 AM
                
                historical_bars = alpaca_client.get_historical_bars(
                    symbol=symbols[0],
                    timeframe="1Hour",
                    start=hourly_start,
                    end=hourly_end,
                    limit=10
                )
                
                if not historical_bars.empty:
                    logger.info(f"Last {len(historical_bars)} hours of data:")
                    for idx, row in historical_bars.iterrows():
                        logger.info(f"  {idx} - Open: ${row['open']:.2f}, Close: ${row['close']:.2f}, Volume: {row['volume']:,}")
                else:
                    logger.warning(f"No historical data available for {symbols[0]}")
                
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
        
        # Allow the user to check a custom symbol
        custom_symbol = input("\nEnter a stock symbol to check (or press Enter to skip): ").strip().upper()
        if custom_symbol:
            logger.info(f"Checking price for {custom_symbol}...")
            
            # Get price for the new symbol
            price = alpaca_client.get_current_price(custom_symbol)
            if price:
                logger.info(f"{custom_symbol}: ${price:.2f}")
                
                # Try to get some historical data
                try:
                    # Use absolute dates in 2023-2024 instead of relative dates
                    hist_end_date = datetime(2024, 3, 15)    # March 15, 2024
                    hist_start_date = datetime(2024, 3, 1)   # March 1, 2024
                    
                    logger.info(f"Fetching historical data for {custom_symbol} from {hist_start_date.date()} to {hist_end_date.date()}")
                    
                    historical_bars = alpaca_client.get_historical_bars(
                        symbol=custom_symbol,
                        timeframe="1Day",  # Daily data
                        start=hist_start_date,
                        end=hist_end_date,
                        limit=10
                    )
                    
                    if not historical_bars.empty:
                        logger.info(f"Recent data for {custom_symbol}:")
                        for idx, row in historical_bars.iterrows():
                            logger.info(f"  {idx.date()} - Open: ${row['open']:.2f}, Close: ${row['close']:.2f}")
                    else:
                        logger.warning(f"No historical data available for {custom_symbol}")
                        
                except Exception as e:
                    logger.error(f"Error fetching historical data for {custom_symbol}: {str(e)}")
            else:
                logger.info(f"{custom_symbol}: Data not available")
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        logger.info("Demo completed")


if __name__ == "__main__":
    print("Simple Market Data Demo")
    print("This demo requires Alpaca API keys (ALPACA_DATA_API_KEY and ALPACA_DATA_API_SECRET) in your .env file")
    run_simple_demo() 