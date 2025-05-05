"""
Market data service for gathering, processing, and storing market data from Alpaca.
"""
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client

# Import our Alpaca client
from src.data.alpaca_client import AlpacaClient

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
# Prefer generic SUPABASE_KEY, fall back to legacy SUPABASE_ANON_KEY for backwards-compatibility
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

# Fail fast with a clear error if credentials are missing. This prevents obscure runtime crashes.
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing Supabase environment variables. Please set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY) in your environment."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class MarketDataService:
    """Service for gathering and processing market data from Alpaca."""
    
    def __init__(self):
        """Initialize the Alpaca client."""
        self.alpaca_client = AlpacaClient()
        
        # Default list of symbols to track (ETFs covering major asset classes)
        self.default_symbols = [
            'SPY',   # S&P 500
            'QQQ',   # Nasdaq 100
            'IWM',   # Russell 2000
            'DIA',   # Dow Jones
            'VEA',   # Developed Markets
            'VWO',   # Emerging Markets
            'AGG',   # US Aggregate Bond
            'LQD',   # Corporate Bonds
            'SHY',   # 1-3 Year Treasury
            'TLT',   # 20+ Year Treasury
            'GLD',   # Gold
            'USO',   # Oil
            'VNQ',   # Real Estate
            'XLF',   # Financials
            'XLK',   # Technology
            'XLV',   # Healthcare
        ]
        
        # Print initialization message
        print("Market Data Service initialized")
    
    def get_watched_symbols(self) -> List[str]:
        """
        Get list of symbols being watched from the database.
        
        Returns:
            List of stock symbols to track
        """
        try:
            # Query watched symbols from database
            result = supabase.table('watched_symbols').select('symbol').eq('is_active', True).execute()
            
            if result.data:
                symbols = [item['symbol'] for item in result.data]
                return symbols
            else:
                # If no watched symbols in DB, create them from default list
                self._initialize_watched_symbols()
                return self.default_symbols
                
        except Exception as e:
            print(f"Error fetching watched symbols: {e}")
            return self.default_symbols
    
    def _initialize_watched_symbols(self) -> bool:
        """
        Initialize the watched_symbols table with default ETFs.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create records for default symbols
            records = []
            for symbol in self.default_symbols:
                record = {
                    'symbol': symbol,
                    'is_active': True,
                    'asset_type': 'ETF'
                }
                records.append(record)
            
            # Insert into database
            result = supabase.table('watched_symbols').upsert(records).execute()
            print(f"Initialized {len(records)} default symbols to watch")
            return True
            
        except Exception as e:
            print(f"Error initializing watched symbols: {e}")
            return False
    
    def fetch_historical_bars(self, 
                             symbols: Optional[List[str]] = None, 
                             timeframe: str = '1Day',
                             days_back: int = 30) -> bool:
        """
        Fetch historical bar data for specified symbols and store in database.
        
        Args:
            symbols: List of symbols to fetch (default: watched symbols)
            timeframe: Bar timeframe ('1Day', '1Hour', '1Min')
            days_back: Number of days of history to fetch
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use watched symbols if none provided
            if not symbols:
                symbols = self.get_watched_symbols()
            
            # Set date range
            end = datetime.now()
            start = end - timedelta(days=days_back)
            
            # Fetch bars from Alpaca
            bars_dict = self.alpaca_client.get_historical_bars(
                symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end
            )
            
            stored_count = 0
            skipped_count = 0
            
            # Process each symbol's data
            for symbol, df in bars_dict.items():
                if df.empty:
                    continue
                
                # For each symbol, first check what data we already have to avoid duplicates
                try:
                    # Get existing timestamps for this symbol and timeframe
                    result = (supabase.table('stock_price_bars')
                             .select('timestamp')
                             .eq('symbol', symbol)
                             .eq('timeframe', timeframe)
                             .execute())
                    
                    # Extract timestamps as strings for easy comparison
                    existing_timestamps = set()
                    if result.data:
                        for record in result.data:
                            # Convert timestamp strings to a comparable format
                            ts = record['timestamp']
                            if isinstance(ts, str):
                                # Remove timezone info and microseconds for comparison
                                ts = ts.split('.')[0].replace('Z', '').replace('T', ' ')
                                existing_timestamps.add(ts)
                    
                    # Convert DataFrame to list of records, skipping existing timestamps
                    records = []
                    for timestamp, row in df.iterrows():
                        # Convert timestamp to string for comparison
                        ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Skip if we already have this timestamp
                        if ts_str in existing_timestamps:
                            skipped_count += 1
                            continue
                        
                        record = {
                            'symbol': symbol,
                            'timestamp': timestamp.isoformat(),
                            'timeframe': timeframe,
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': int(row['volume']),
                            'vwap': float(row['vwap']) if 'vwap' in row else None,
                            'trade_count': int(row['trade_count']) if 'trade_count' in row else None,
                            'source': 'Alpaca'
                        }
                        records.append(record)
                    
                    # Store in database
                    if records:
                        result = supabase.table('stock_price_bars').upsert(records).execute()
                        stored_count += len(records)
                
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
            
            print(f"Stored {stored_count} new price bars for {len(bars_dict)} symbols (skipped {skipped_count} existing records)")
            
            # Calculate technical indicators
            if stored_count > 0 or skipped_count > 0:
                self.calculate_indicators(symbols, timeframe)
            
            return True
            
        except Exception as e:
            print(f"Error fetching historical bars: {e}")
            return False
    
    def fetch_latest_quotes(self, symbols: Optional[List[str]] = None) -> bool:
        """
        Fetch latest quotes for specified symbols and store in database.
        
        Args:
            symbols: List of symbols to fetch (default: watched symbols)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use watched symbols if none provided
            if not symbols:
                symbols = self.get_watched_symbols()
            
            # Fetch quotes from Alpaca
            quotes_dict = self.alpaca_client.get_latest_quotes(symbols)
            
            # Get existing quotes timestamps to avoid duplicates
            existing_quotes = {}
            try:
                # Get all symbol/timestamp pairs that exist in the quotes table
                result = supabase.table('stock_quotes').select('symbol,timestamp').execute()
                
                if result.data:
                    for record in result.data:
                        symbol = record.get('symbol')
                        timestamp = record.get('timestamp')
                        if symbol:
                            # Store as symbol -> set of timestamps
                            if symbol not in existing_quotes:
                                existing_quotes[symbol] = set()
                            
                            if timestamp:
                                # Normalize timestamp for comparison
                                if isinstance(timestamp, str):
                                    timestamp = timestamp.split('.')[0].replace('Z', '').replace('T', ' ')
                                existing_quotes[symbol].add(timestamp)
            except Exception as e:
                print(f"Error fetching existing quotes: {e}")
            
            # Process each symbol's data
            records = []
            for symbol, quote in quotes_dict.items():
                try:
                    # Skip if we already have this exact timestamp
                    timestamp_str = None
                    if 'timestamp' in quote:
                        ts = quote['timestamp']
                        if isinstance(ts, str):
                            timestamp_str = ts.split('.')[0].replace('Z', '').replace('T', ' ')
                    
                    # Skip if this exact timestamp already exists
                    if (symbol in existing_quotes and 
                        timestamp_str and 
                        timestamp_str in existing_quotes[symbol]):
                        print(f"Skipping existing quote for {symbol} at {timestamp_str}")
                        continue
                    
                    # Create record
                    record = {
                        'symbol': symbol,
                        'timestamp': quote['timestamp'],
                        'ask_price': float(quote.get('ask_price', quote.get('close_price', 0))),
                        'ask_size': float(quote.get('ask_size', 0)),
                        'bid_price': float(quote.get('bid_price', quote.get('close_price', 0))),
                        'bid_size': float(quote.get('bid_size', 0)),
                        'spread': float(quote.get('ask_price', 0)) - float(quote.get('bid_price', 0)) if quote.get('ask_price') and quote.get('bid_price') else None,
                        'source': 'Alpaca',
                        'data_delay': quote.get('data_delay', '15 minutes')
                    }
                    records.append(record)
                except Exception as e:
                    print(f"Error processing quote for {symbol}: {e}")
            
            # Store in database
            if records:
                result = supabase.table('stock_quotes').upsert(records).execute()
                print(f"Stored {len(records)} new quotes")
                return True
            else:
                print("No new quotes to store")
                return True
            
        except Exception as e:
            print(f"Error fetching latest quotes: {e}")
            return False
    
    def calculate_indicators(self, 
                           symbols: Optional[List[str]] = None, 
                           timeframe: str = '1Day') -> bool:
        """
        Calculate technical indicators for specified symbols and store in database.
        
        Args:
            symbols: List of symbols to calculate for (default: watched symbols)
            timeframe: Bar timeframe ('1Day', '1Hour', '1Min')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use watched symbols if none provided
            if not symbols:
                symbols = self.get_watched_symbols()
            
            indicators_stored = 0
            
            # Process each symbol
            for symbol in symbols:
                # Fetch price data for this symbol
                result = (supabase.table('stock_price_bars')
                        .select('*')
                        .eq('symbol', symbol)
                        .eq('timeframe', timeframe)
                        .order('timestamp', desc=False)
                        .limit(200)  # Get enough data for calculating indicators
                        .execute())
                
                if not result.data:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(result.data)
                
                # Skip if not enough data
                if len(df) < 14:
                    continue
                    
                # Calculate indicators
                indicators = []
                
                # 1. RSI (14)
                rsi_values = self._calculate_rsi(df, period=14)
                
                # 2. Moving Averages (20 and 50 day)
                ma20 = df['close'].rolling(window=20).mean()
                ma50 = df['close'].rolling(window=50).mean()
                
                # 3. Bollinger Bands (20, 2)
                middle_band = df['close'].rolling(window=20).mean()
                std_dev = df['close'].rolling(window=20).std()
                upper_band = middle_band + (std_dev * 2)
                lower_band = middle_band - (std_dev * 2)
                
                # 4. MACD (12, 26, 9)
                ema12 = df['close'].ewm(span=12, adjust=False).mean()
                ema26 = df['close'].ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_histogram = macd_line - signal_line
                
                # Create records for each indicator
                for i, row in df.iterrows():
                    idx = df.index.get_loc(i)
                    timestamp = row['timestamp']
                    
                    # Only store indicators for points where we have enough data
                    if idx >= 14:
                        # RSI
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'RSI',
                            'timeframe': timeframe,
                            'value': float(rsi_values[idx]),
                            'parameters': json.dumps({'period': 14})
                        })
                    
                    if idx >= 20:
                        # MA20
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'MA20',
                            'timeframe': timeframe,
                            'value': float(ma20[idx]),
                            'parameters': json.dumps({'period': 20})
                        })
                        
                        # Bollinger Bands
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'BB_UPPER',
                            'timeframe': timeframe,
                            'value': float(upper_band[idx]),
                            'parameters': json.dumps({'period': 20, 'std_dev': 2})
                        })
                        
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'BB_LOWER',
                            'timeframe': timeframe,
                            'value': float(lower_band[idx]),
                            'parameters': json.dumps({'period': 20, 'std_dev': 2})
                        })
                    
                    if idx >= 26:
                        # MACD
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'MACD_LINE',
                            'timeframe': timeframe,
                            'value': float(macd_line[idx]),
                            'parameters': json.dumps({'fast_period': 12, 'slow_period': 26})
                        })
                        
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'MACD_SIGNAL',
                            'timeframe': timeframe,
                            'value': float(signal_line[idx]),
                            'parameters': json.dumps({'fast_period': 12, 'slow_period': 26, 'signal_period': 9})
                        })
                        
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'MACD_HIST',
                            'timeframe': timeframe,
                            'value': float(macd_histogram[idx]),
                            'parameters': json.dumps({'fast_period': 12, 'slow_period': 26, 'signal_period': 9})
                        })
                    
                    if idx >= 50:
                        # MA50
                        indicators.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'indicator_name': 'MA50',
                            'timeframe': timeframe,
                            'value': float(ma50[idx]),
                            'parameters': json.dumps({'period': 50})
                        })
                
                # Store indicators in batches to avoid too large requests
                if indicators:
                    # Only store the most recent indicators (last 30 days)
                    recent_indicators = indicators[-300:]
                    
                    # Split into smaller batches (100 at a time)
                    batch_size = 100
                    for i in range(0, len(recent_indicators), batch_size):
                        batch = recent_indicators[i:i+batch_size]
                        result = supabase.table('stock_indicators').upsert(batch).execute()
                        indicators_stored += len(batch)
            
            print(f"Stored {indicators_stored} indicators for {len(symbols)} symbols")
            return True
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return False
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        Args:
            df: DataFrame with price data
            period: RSI period
            
        Returns:
            Series with RSI values
        """
        # Calculate price changes
        delta = df['close'].diff()
        
        # Separate gains and losses
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def run_data_pipeline(self, timeframe: str = '1Day', days_back: int = 30) -> bool:
        """
        Run the complete market data pipeline.
        
        This fetches historical bars, latest quotes, and calculates indicators.
        
        Args:
            timeframe: Bar timeframe to use
            days_back: How many days of history to fetch
            
        Returns:
            True if successful, False otherwise
        """
        print("\nStarting market data pipeline...")
        
        # Step 1: Fetch historical bars
        print("\n--- Fetching Historical Price Data ---")
        bars_result = self.fetch_historical_bars(timeframe=timeframe, days_back=days_back)
        
        # Step 2: Fetch latest quotes
        print("\n--- Fetching Latest Quotes ---")
        quotes_result = self.fetch_latest_quotes()
        
        # Note: Technical indicators are calculated within fetch_historical_bars
        
        print("\nMarket data pipeline complete")
        return bars_result and quotes_result

if __name__ == "__main__":
    # Example usage
    service = MarketDataService()
    service.run_data_pipeline() 