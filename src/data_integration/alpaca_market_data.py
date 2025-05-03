"""
Alpaca Market Data Integration Module

This module handles:
1. Connection to Alpaca's API with free tier considerations (15-min delay)
2. Fetching market data for stocks and ETFs
3. Data transformation and storage
4. Handling rate limits and API restrictions

Note: This implementation accounts for free tier limitations including:
- 15-minute delayed market data
- Limited ETF coverage
- API rate limits
"""

import os
import time
import json
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class AlpacaMarketData:
    """
    Client for Alpaca Market Data API with free tier considerations.
    
    Features:
    - Handles 15-minute delayed data appropriately
    - Implements retry and backoff for API rate limits
    - Provides utilities for common data retrieval patterns
    - Supports both historical and current data (with delay on free tier)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        data_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        is_free_tier: bool = True
    ):
        """
        Initialize the Alpaca Market Data client.
        
        Args:
            api_key: Alpaca API key (defaults to ALPACA_DATA_API_KEY env var)
            api_secret: Alpaca API secret (defaults to ALPACA_DATA_API_SECRET env var)
            base_url: Base API URL (defaults to ALPACA_BASE_URL env var or prod URL)
            data_url: Data API URL (defaults to ALPACA_DATA_URL env var or prod URL)
            max_retries: Maximum number of retries for failed API calls
            retry_delay: Delay between retries in seconds
            is_free_tier: Whether using the free tier (affects data processing)
        """
        self.api_key = api_key or os.getenv("ALPACA_DATA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_DATA_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API key and secret must be provided or set in environment variables (ALPACA_DATA_API_KEY and ALPACA_DATA_API_SECRET)")
        
        self.base_url = base_url or os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        self.data_url = data_url or os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")
        
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.is_free_tier = is_free_tier
        
        # Track the data delay for free tier (typically 15 minutes)
        self.data_delay_minutes = 15 if is_free_tier else 0
        
        # Initialize the Alpaca REST client
        try:
            import alpaca_trade_api as tradeapi
            
            # Check if the current version supports data_url
            try:
                # Try to initialize with data_url parameter
                self.api = tradeapi.REST(
                    key_id=self.api_key,
                    secret_key=self.api_secret,
                    base_url=self.base_url,
                    data_url=self.data_url
                )
            except TypeError:
                # If it fails, try without data_url (newer versions might handle it differently)
                logger.info("Initializing Alpaca client without explicit data_url parameter")
                self.api = tradeapi.REST(
                    key_id=self.api_key,
                    secret_key=self.api_secret,
                    base_url=self.base_url
                )
                
            logger.info("Alpaca Market Data client initialized successfully")
        except ImportError:
            logger.error("alpaca-trade-api package not installed. Please install it with 'pip install alpaca-trade-api'")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            raise
        
        # Cache for account information
        self._account_info = None
        
        # Set of supported ETFs on free tier (will be populated on first call)
        self._supported_etfs = set()
        
    def get_account_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get account information from Alpaca.
        
        Args:
            force_refresh: Whether to force a refresh of cached account data
            
        Returns:
            Dictionary with account information
        """
        if self._account_info is None or force_refresh:
            for attempt in range(self.max_retries):
                try:
                    self._account_info = self.api.get_account()._raw
                    return self._account_info
                except Exception as e:
                    logger.warning(f"Get account attempt {attempt+1}/{self.max_retries} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                    else:
                        logger.error(f"Failed to get account information after {self.max_retries} attempts")
                        raise
        
        return self._account_info
    
    def get_current_price(self, symbol: str, adjust_for_delay: bool = True) -> Optional[float]:
        """
        Get the current price for a symbol, accounting for free tier delay.
        
        Args:
            symbol: Stock or ETF symbol
            adjust_for_delay: Whether to note the delay in logs
            
        Returns:
            Current price or None if unavailable
        """
        try:
            # For free tier, note this is 15-min delayed data
            if self.is_free_tier and adjust_for_delay:
                logger.info(f"Fetching price for {symbol} (note: free tier data is ~15 minutes delayed)")
            
            # Get the latest bar for the symbol
            latest_bar = self.api.get_latest_bar(symbol)
            
            if latest_bar:
                timestamp = pd.Timestamp(latest_bar.t).tz_convert('America/New_York')
                now = pd.Timestamp.now(tz='America/New_York')
                delay_mins = (now - timestamp).total_seconds() / 60
                
                # Log the actual delay observed
                if delay_mins > 5:  # Only log if delay is significant
                    logger.info(f"Data for {symbol} is {delay_mins:.1f} minutes delayed")
                
                return float(latest_bar.c)  # Return the closing price
            else:
                logger.warning(f"No data available for symbol {symbol}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get current price for {symbol}: {str(e)}")
            return None
    
    def get_historical_bars(
        self, 
        symbol: str,
        timeframe: str = "1Day",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get historical bars for a symbol.
        
        Args:
            symbol: Stock or ETF symbol
            timeframe: Bar timeframe (e.g., "1Min", "1Hour", "1Day")
            start: Start datetime (defaults to limit bars ago)
            end: End datetime (defaults to now)
            limit: Maximum number of bars to return
            
        Returns:
            DataFrame with historical bars
        """
        if end is None:
            end = datetime.now()
            
        if start is None:
            # Calculate a reasonable start date based on the timeframe and limit
            if timeframe.endswith('Min'):
                mins = int(timeframe.replace('Min', ''))
                start = end - timedelta(minutes=mins * limit)
            elif timeframe.endswith('Hour'):
                hours = int(timeframe.replace('Hour', ''))
                start = end - timedelta(hours=hours * limit)
            elif timeframe.endswith('Day'):
                days = int(timeframe.replace('Day', ''))
                start = end - timedelta(days=days * limit)
            else:
                # Default to 100 days
                start = end - timedelta(days=100)
        
        # Ensure start date is in the past (not future)
        now = datetime.now()
        if start > now:
            start = now - timedelta(days=30)  # Default to 30 days ago if start is in future
            
        # Ensure end date is not in the future
        if end > now:
            end = now
            
        # Ensure start is before end
        if start >= end:
            start = end - timedelta(days=30)
        
        logger.info(f"Fetching {timeframe} bars for {symbol} from {start.date()} to {end.date()}")
        
        for attempt in range(self.max_retries):
            try:
                # Convert datetime objects to strings in ISO format
                start_str = start.isoformat()
                end_str = end.isoformat()
                
                # Fetch the bars
                bars = self.api.get_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    start=start_str,
                    end=end_str,
                    limit=limit
                )
                
                # Convert to DataFrame
                if bars and len(bars) > 0:
                    df = pd.DataFrame([bar._raw for bar in bars])
                    
                    # Convert timestamp to datetime and set as index
                    if 't' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['t'])
                        df.set_index('timestamp', inplace=True)
                    
                    # Rename columns for clarity
                    column_mapping = {
                        'o': 'open',
                        'h': 'high',
                        'l': 'low',
                        'c': 'close',
                        'v': 'volume'
                    }
                    df.rename(columns=column_mapping, inplace=True)
                    
                    return df
                else:
                    logger.warning(f"No historical data available for {symbol} in the specified timeframe")
                    return pd.DataFrame()
                    
            except Exception as e:
                logger.warning(f"Historical bars attempt {attempt+1}/{self.max_retries} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to get historical bars after {self.max_retries} attempts")
                    return pd.DataFrame()  # Return empty DataFrame on failure
    
    def get_multiple_symbols_data(
        self, 
        symbols: List[str], 
        timeframe: str = "1Day",
        days: int = 5
    ) -> Dict[str, pd.DataFrame]:
        """
        Get recent data for multiple symbols with rate limiting protection.
        
        Args:
            symbols: List of symbols to fetch
            timeframe: Bar timeframe
            days: Number of days of data to fetch
            
        Returns:
            Dictionary of symbol to DataFrame mappings
        """
        end = datetime.now()
        start = end - timedelta(days=days)
        
        results = {}
        
        for i, symbol in enumerate(symbols):
            # Add a small delay between requests to avoid hitting rate limits
            if i > 0:
                time.sleep(0.2)  # 200ms delay between requests
            
            logger.info(f"Fetching data for {symbol} ({i+1}/{len(symbols)})")
            
            df = self.get_historical_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end
            )
            
            if not df.empty:
                results[symbol] = df
                logger.info(f"Successfully fetched {len(df)} bars for {symbol}")
            else:
                logger.warning(f"No data available for {symbol}")
        
        return results
    
    def is_etf_supported(self, symbol: str) -> bool:
        """
        Check if an ETF is supported on the free tier.
        
        Args:
            symbol: ETF symbol to check
            
        Returns:
            Boolean indicating if the ETF is supported
        """
        if not self.is_free_tier:
            return True  # On paid tier, all ETFs are supported
            
        # First, check if it's in our cache
        if symbol in self._supported_etfs:
            return True
            
        # Try to get data for the ETF
        try:
            price = self.get_current_price(symbol, adjust_for_delay=False)
            if price is not None:
                # Cache successful ETFs to avoid repeated checks
                self._supported_etfs.add(symbol)
                return True
            return False
        except Exception:
            return False
    
    def get_fundamental_data(
        self, 
        symbol: str
    ) -> Dict[str, Any]:
        """
        Get fundamental data for a symbol if available.
        
        Note: This may be limited on free tier.
        
        Args:
            symbol: Stock or ETF symbol
            
        Returns:
            Dictionary with fundamental data if available
        """
        # On free tier, we might not have access to full fundamental data
        # This is a placeholder implementation - actual free tier capabilities may vary
        try:
            # Basic asset info
            asset = self.api.get_asset(symbol)
            
            # Start with basic data
            fundamentals = {
                "symbol": symbol,
                "name": asset.name,
                "exchange": asset.exchange,
                "status": asset.status,
                "tradable": asset.tradable,
                "marginable": asset.marginable,
                "shortable": asset.shortable,
                "easy_to_borrow": asset.easy_to_borrow,
                "fractionable": asset.fractionable
            }
            
            # Check for additional fundamental data
            # On free tier, this may raise an error or return limited data
            # Try a few different endpoints that might be available
            
            return fundamentals
            
        except Exception as e:
            logger.warning(f"Limited or no fundamental data available for {symbol} (free tier limitation): {str(e)}")
            return {"symbol": symbol, "error": "Limited fundamental data on free tier"}
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get the current market status.
        
        Returns:
            Dictionary with market status information
        """
        try:
            clock = self.api.get_clock()
            calendar = self.api.get_calendar(start=date.today().isoformat())
            
            status = {
                "is_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if hasattr(clock, 'next_open') else None,
                "next_close": clock.next_close.isoformat() if hasattr(clock, 'next_close') else None,
                "timestamp": clock.timestamp.isoformat() if hasattr(clock, 'timestamp') else None,
            }
            
            if calendar and len(calendar) > 0:
                today = calendar[0]
                status.update({
                    "open_time": today.open.isoformat() if hasattr(today, 'open') else None,
                    "close_time": today.close.isoformat() if hasattr(today, 'close') else None,
                    "session_open": today.session_open.isoformat() if hasattr(today, 'session_open') else None,
                    "session_close": today.session_close.isoformat() if hasattr(today, 'session_close') else None,
                })
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get market status: {str(e)}")
            return {"error": str(e)}
    
    def save_daily_data(
        self, 
        symbols: List[str], 
        output_dir: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Save daily data for a list of symbols to CSV files.
        
        Args:
            symbols: List of symbols to fetch data for
            output_dir: Directory to save the files
            days: Number of days of historical data to fetch
            
        Returns:
            Dictionary with statistics about the operation
        """
        from pathlib import Path
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "total_symbols": len(symbols),
            "successful": 0,
            "failed": 0,
            "skipped_etfs": 0,
            "failures": []
        }
        
        # Get data for all symbols
        for i, symbol in enumerate(symbols):
            logger.info(f"Processing {symbol} ({i+1}/{len(symbols)})")
            
            # Check if it's an ETF and supported (if free tier)
            if self.is_free_tier and symbol.endswith('ETF'):
                if not self.is_etf_supported(symbol):
                    logger.warning(f"Skipping ETF {symbol} - not supported on free tier")
                    stats["skipped_etfs"] += 1
                    continue
            
            try:
                # Get daily data
                df = self.get_historical_bars(
                    symbol=symbol,
                    timeframe="1Day",
                    limit=days
                )
                
                if df.empty:
                    logger.warning(f"No data available for {symbol}")
                    stats["failed"] += 1
                    stats["failures"].append({"symbol": symbol, "reason": "No data available"})
                    continue
                
                # Save to CSV
                output_file = output_path / f"{symbol}_daily.csv"
                df.to_csv(output_file)
                
                logger.info(f"Saved {len(df)} days of data for {symbol} to {output_file}")
                stats["successful"] += 1
                
                # Add a small delay to avoid rate limits
                if i < len(symbols) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {str(e)}")
                stats["failed"] += 1
                stats["failures"].append({"symbol": symbol, "reason": str(e)})
        
        return stats 