"""
Alpaca client for market data operations using the alpaca-py SDK.
Configured for the free subscription level which includes:
- Historical data with 15-minute delay
- End-of-day data
- No real-time quotes
"""
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.common.exceptions import APIError
from dotenv import load_dotenv

class AlpacaClient:
    """Client for interacting with Alpaca API for market data."""
    
    def __init__(self):
        """Initialize Alpaca client with API credentials."""
        load_dotenv()
        
        # Market Data API credentials
        api_key = os.getenv('ALPACA_DATA_API_KEY')
        api_secret = os.getenv('ALPACA_DATA_API_SECRET')
        
        # Debug logging
        print("\nEnvironment variables check:")
        print(f"ALPACA_DATA_API_KEY exists: {api_key is not None}")
        if api_key:
            print(f"ALPACA_DATA_API_KEY length: {len(api_key)}")
        print(f"ALPACA_DATA_API_SECRET exists: {api_secret is not None}")
        if api_secret:
            print(f"ALPACA_DATA_API_SECRET length: {len(api_secret)}")
        
        if not api_key or not api_secret:
            raise ValueError("Alpaca Market Data API credentials not found in environment variables. "
                           "Please set ALPACA_DATA_API_KEY and ALPACA_DATA_API_SECRET.")
        
        # Initialize the data API client for market data
        self.client = StockHistoricalDataClient(api_key, api_secret)
        print("Initialized Alpaca client with data API key length:", len(api_key))
        
    def get_historical_bars(
        self,
        symbols: List[str],
        timeframe: str = '1Day',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical bar data for given symbols.
        Note: Data has a 15-minute delay on free subscription.
        
        Args:
            symbols: List of stock symbols
            timeframe: Bar timeframe (e.g., '1Day', '1Hour')
            start: Start datetime
            end: End datetime
            limit: Maximum number of bars to return
            
        Returns:
            Dictionary mapping symbols to DataFrames containing bar data
        """
        if not start:
            start = datetime.now() - timedelta(days=7)
        if not end:
            end = datetime.now()
            
        # Ensure we account for the 15-minute delay
        end = min(end, datetime.now() - timedelta(minutes=15))
            
        # Convert timeframe string to TimeFrame enum
        tf_map = {
            '1Day': TimeFrame.Day,
            '1Hour': TimeFrame.Hour,
            '1Min': TimeFrame.Minute
        }
        tf = tf_map.get(timeframe, TimeFrame.Day)
            
        try:
            print(f"\nFetching bars for {symbols}...")
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=tf,
                start=start,
                end=end,
                limit=limit
            )
            bars = self.client.get_stock_bars(request)
            
            # Convert to dictionary of DataFrames
            results = {}
            if bars:
                df = bars.df
                # Split multi-index DataFrame into separate DataFrames per symbol
                for symbol in symbols:
                    if symbol in df.index.get_level_values('symbol').unique():
                        results[symbol] = df.xs(symbol, level='symbol')
                        print(f"Successfully fetched {len(results[symbol])} bars for {symbol}")
                    else:
                        print(f"No data found for {symbol}")
            
            return results
                
        except APIError as e:
            print(f"API Error fetching bars: {str(e)}")
            if "subscription does not permit" in str(e):
                print("Note: Free subscription has limited data access and 15-minute delay")
            raise
        except Exception as e:
            print(f"Error fetching bars: {str(e)}")
            raise
    
    def get_latest_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch delayed quotes for given symbols.
        Note: This method returns delayed data (15-minute delay) due to free subscription limitations.
        For real-time quotes, a paid subscription is required.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to their delayed quotes
        """
        try:
            # Instead of real-time quotes, we'll get the most recent bar data
            # which is available with 15-minute delay
            end = datetime.now()
            start = end - timedelta(days=1)  # Get last day of data to ensure we have something
            
            print(f"\nFetching delayed quotes for {symbols}...")
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Day,  # Use daily data which is more reliable on free tier
                start=start,
                end=end,
                limit=1  # We only want the latest bar
            )
            
            results = {}
            
            try:
                bars = self.client.get_stock_bars(request)
                
                if bars and hasattr(bars, 'df') and not bars.df.empty:
                    # Process the data frame
                    df = bars.df
                    
                    # Check if it's a multi-index DataFrame
                    is_multi_index = isinstance(df.index, pd.MultiIndex)
                    
                    # Process each symbol
                    for symbol in symbols:
                        try:
                            # Extract data for this symbol
                            if is_multi_index and 'symbol' in df.index.names:
                                # Try to get data using xs
                                try:
                                    symbol_data = df.xs(symbol, level='symbol')
                                    if not symbol_data.empty:
                                        row = symbol_data.iloc[-1]
                                        timestamp = symbol_data.index[-1]
                                        
                                        quote_data = {
                                            'symbol': symbol,
                                            'timestamp': timestamp.isoformat() if isinstance(timestamp, pd.Timestamp) else timestamp,
                                            'close_price': float(row['close']),
                                            'volume': int(row['volume']),
                                            'vwap': float(row['vwap']) if 'vwap' in row else 0.0,
                                            'trade_count': int(row['trade_count']) if 'trade_count' in row else 0,
                                            'ask_price': float(row['close']) * 1.0001,  # Simulate ask price
                                            'bid_price': float(row['close']) * 0.9999,  # Simulate bid price
                                            'ask_size': 100,
                                            'bid_size': 100,
                                            'data_delay': '15 minutes'
                                        }
                                        results[symbol] = quote_data
                                        print(f"Successfully fetched delayed quote for {symbol}")
                                except KeyError:
                                    print(f"Symbol {symbol} not found in index")
                            else:
                                # Fallback method - iterate and check for symbol
                                found = False
                                for idx, row in df.iterrows():
                                    try:
                                        # Get symbol from index if possible
                                        if is_multi_index:
                                            idx_symbol = idx[df.index.names.index('symbol')] if 'symbol' in df.index.names else None
                                        else:
                                            idx_symbol = None
                                        
                                        # Check if this row is for our symbol
                                        if idx_symbol == symbol:
                                            found = True
                                            quote_data = {
                                                'symbol': symbol,
                                                'timestamp': idx[0].isoformat() if isinstance(idx[0], pd.Timestamp) else idx[0],
                                                'close_price': float(row['close']),
                                                'volume': int(row['volume']),
                                                'vwap': float(row['vwap']) if 'vwap' in row else 0.0,
                                                'trade_count': int(row['trade_count']) if 'trade_count' in row else 0,
                                                'ask_price': float(row['close']) * 1.0001,  # Simulate ask price
                                                'bid_price': float(row['close']) * 0.9999,  # Simulate bid price
                                                'ask_size': 100,
                                                'bid_size': 100,
                                                'data_delay': '15 minutes'
                                            }
                                            results[symbol] = quote_data
                                            print(f"Successfully fetched delayed quote for {symbol}")
                                            break
                                    except (KeyError, IndexError):
                                        continue
                                
                                if not found:
                                    # Create a fallback quote entry from historical data
                                    historical_request = StockBarsRequest(
                                        symbol_or_symbols=symbol,
                                        timeframe=TimeFrame.Day,
                                        start=start - timedelta(days=5),  # Look back further
                                        end=end,
                                        limit=1
                                    )
                                    
                                    try:
                                        historical_bars = self.client.get_stock_bars(historical_request)
                                        if historical_bars and hasattr(historical_bars, 'df') and not historical_bars.df.empty:
                                            hist_df = historical_bars.df
                                            # Get the first row, regardless of indexing
                                            hist_row = hist_df.iloc[0]
                                            
                                            quote_data = {
                                                'symbol': symbol,
                                                'timestamp': end.isoformat(),  # Use current time
                                                'close_price': float(hist_row['close']),
                                                'volume': int(hist_row['volume']),
                                                'vwap': float(hist_row['vwap']) if 'vwap' in hist_row else 0.0,
                                                'trade_count': int(hist_row['trade_count']) if 'trade_count' in hist_row else 0,
                                                'ask_price': float(hist_row['close']) * 1.0001,  # Simulate ask price
                                                'bid_price': float(hist_row['close']) * 0.9999,  # Simulate bid price
                                                'ask_size': 100,
                                                'bid_size': 100,
                                                'data_delay': 'historical'
                                            }
                                            results[symbol] = quote_data
                                            print(f"Using historical data for {symbol}")
                                    except Exception as e:
                                        print(f"Could not get historical data for {symbol}: {e}")
                                
                        except Exception as e:
                            print(f"Error processing quote for {symbol}: {e}")
                else:
                    print("No data returned from Alpaca API")
            except Exception as e:
                print(f"Error with Alpaca API request: {e}")
                
                # Fallback to historical daily data for each symbol individually
                for symbol in symbols:
                    try:
                        print(f"Attempting fallback for {symbol}...")
                        single_request = StockBarsRequest(
                            symbol_or_symbols=symbol,
                            timeframe=TimeFrame.Day,
                            start=start - timedelta(days=5),  # Look back further
                            end=end,
                            limit=1
                        )
                        
                        single_bars = self.client.get_stock_bars(single_request)
                        if single_bars and not single_bars.df.empty:
                            row = single_bars.df.iloc[0]
                            quote_data = {
                                'symbol': symbol,
                                'timestamp': end.isoformat(),  # Use current time
                                'close_price': float(row['close']),
                                'volume': int(row['volume']),
                                'vwap': float(row['vwap']) if 'vwap' in row else 0.0,
                                'trade_count': int(row['trade_count']) if 'trade_count' in row else 0,
                                'ask_price': float(row['close']) * 1.0001,  # Simulate ask price
                                'bid_price': float(row['close']) * 0.9999,  # Simulate bid price
                                'ask_size': 100,
                                'bid_size': 100,
                                'data_delay': 'fallback'
                            }
                            results[symbol] = quote_data
                            print(f"Fallback quote retrieved for {symbol}")
                    except Exception as inner_e:
                        print(f"Fallback also failed for {symbol}: {inner_e}")
            
            return results
                
        except APIError as e:
            print(f"API Error fetching quotes: {str(e)}")
            if "subscription does not permit" in str(e):
                print("Note: Free subscription does not support real-time quotes. Using delayed data instead.")
            raise
        except Exception as e:
            print(f"Error fetching quotes: {str(e)}")
            raise 