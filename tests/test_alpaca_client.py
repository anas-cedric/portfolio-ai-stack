"""
Tests for Alpaca client market data functionality.
"""
import pytest
from datetime import datetime, timedelta
from src.data.alpaca_client import AlpacaClient

def test_alpaca_client_initialization():
    """Test that AlpacaClient can be initialized."""
    client = AlpacaClient()
    assert client is not None
    assert client.client is not None

def test_get_historical_bars():
    """Test fetching historical bar data."""
    client = AlpacaClient()
    symbols = ['AAPL']  # Test with just one symbol first
    start = datetime.now() - timedelta(days=1)  # Just get yesterday's data
    end = datetime.now()
    
    try:
        print("\nFetching historical bars:")
        print(f"Symbols: {symbols}")
        print(f"Start: {start.strftime('%Y-%m-%d')}")
        print(f"End: {end.strftime('%Y-%m-%d')}")
        
        data = client.get_historical_bars(
            symbols=symbols,
            timeframe='1Day',
            start=start,
            end=end
        )
        
        print("\nReceived data:")
        for symbol, bars in data.items():
            print(f"{symbol}: {len(bars)} bars")
            if not bars.empty:
                print(f"Sample data:\n{bars.head(1)}")
        
        assert isinstance(data, dict)
        assert all(symbol in data for symbol in symbols)
        for symbol in symbols:
            assert not data[symbol].empty
            # Check that we have the expected columns
            expected_columns = ['open', 'high', 'low', 'close', 'volume', 'vwap', 'trade_count']
            assert all(col in data[symbol].columns for col in expected_columns)
            
    except Exception as e:
        print(f"\nError fetching historical bars: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

def test_get_latest_quotes():
    """Test fetching delayed quotes."""
    client = AlpacaClient()
    symbols = ['AAPL']  # Test with just one symbol first
    
    try:
        print("\nFetching delayed quotes:")
        print(f"Symbols: {symbols}")
        
        quotes = client.get_latest_quotes(symbols)
        
        print("\nReceived quotes:")
        for symbol, quote in quotes.items():
            print(f"{symbol}: {quote}")
        
        assert isinstance(quotes, dict)
        assert all(symbol in quotes for symbol in symbols)
        for symbol in symbols:
            quote = quotes[symbol]
            # Check that we have the expected fields for delayed quotes
            expected_fields = ['symbol', 'timestamp', 'close_price', 'volume', 'vwap', 'trade_count', 'data_delay']
            assert all(field in quote for field in expected_fields)
            # Verify this is delayed data
            assert quote['data_delay'] == '15 minutes'
            
    except Exception as e:
        print(f"\nError fetching delayed quotes: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise 