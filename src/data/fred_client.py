"""
Federal Reserve Economic Data (FRED) API client for retrieving economic indicators.
"""
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import pandas as pd
from fredapi import Fred
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class FredClient:
    """Client for interacting with the Federal Reserve Economic Data (FRED) API."""
    
    def __init__(self):
        """Initialize the FRED client with API key."""
        # Get API key from environment variable
        self.api_key = os.getenv('FRED_API_KEY')
        if not self.api_key:
            print("Warning: FRED_API_KEY not found in environment variables.")
            print("Please set your FRED API key to use this client.")
            print("You can obtain a key at https://fred.stlouisfed.org/docs/api/api_key.html")
        
        # Initialize FRED client
        self.fred = Fred(api_key=self.api_key) if self.api_key else None
    
    def is_initialized(self) -> bool:
        """Check if the client is properly initialized."""
        return self.fred is not None
    
    def get_series(self, series_id: str, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve a time series from FRED.
        
        Args:
            series_id: The FRED series ID (e.g., 'GDPC1', 'UNRATE')
            start_date: Start date in 'YYYY-MM-DD' format (default: 5 years ago)
            end_date: End date in 'YYYY-MM-DD' format (default: today)
            
        Returns:
            DataFrame with the time series data
        """
        if not self.is_initialized():
            raise ValueError("FRED client not initialized. Please set FRED_API_KEY.")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
            
        # Fetch the series
        try:
            series = self.fred.get_series(series_id, start_date, end_date)
            # Convert to DataFrame
            df = pd.DataFrame(series)
            df.reset_index(inplace=True)
            df.columns = ['date', 'value']
            
            # Get series info for additional metadata
            series_info = self.fred.get_series_info(series_id)
            
            # Add metadata columns
            df['series_id'] = series_id
            df['units'] = series_info.get('units', '')
            df['seasonally_adjusted'] = 'sa' in series_id.lower() or 'adjusted' in series_info.get('title', '').lower()
            
            return df
        except Exception as e:
            print(f"Error fetching FRED series {series_id}: {e}")
            return pd.DataFrame()
    
    def store_series(self, series_id: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> bool:
        """
        Fetch and store a FRED series in the database.
        
        Args:
            series_id: The FRED series ID
            start_date: Start date (default: 5 years ago)
            end_date: End date (default: today)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch the series
            df = self.get_series(series_id, start_date, end_date)
            if df.empty:
                return False
            
            # Convert to list of records for Supabase
            records = []
            for _, row in df.iterrows():
                record = {
                    'series_id': row['series_id'],
                    'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], datetime) else row['date'],
                    'value': float(row['value']) if not pd.isna(row['value']) else None,
                    'units': row['units'],
                    'seasonally_adjusted': row['seasonally_adjusted'],
                    'source': 'FRED'
                }
                records.append(record)
            
            # Insert into Supabase
            result = supabase.table('fed_economic_data').upsert(records).execute()
            print(f"Stored {len(records)} records for FRED series {series_id}")
            return True
            
        except Exception as e:
            print(f"Error storing FRED series {series_id}: {e}")
            return False
    
    def fetch_common_indicators(self) -> bool:
        """
        Fetch and store commonly used economic indicators.
        
        Returns:
            True if all fetches succeeded, False if any failed
        """
        # Common economic indicators
        indicators = [
            'GDPC1',       # Real GDP
            'UNRATE',      # Unemployment Rate
            'CPIAUCSL',    # CPI (All Items)
            'CPILFESL',    # Core CPI (Less Food and Energy)
            'FEDFUNDS',    # Federal Funds Rate
            'T10YIE',      # 10-Year Breakeven Inflation Rate
            'MORTGAGE30US',# 30-Year Fixed Mortgage Rate
            'INDPRO',      # Industrial Production Index
            'HOUST',       # Housing Starts
            'UMCSENT',     # Consumer Sentiment Index
            'PAYEMS',      # All Employees: Total Nonfarm
            'PCE',         # Personal Consumption Expenditures
            'RSXFSN',      # Retail Sales
            'MICH',        # University of Michigan: Inflation Expectation
            'DGS10',       # 10-Year Treasury Constant Maturity Rate
        ]
        
        success = True
        for indicator in indicators:
            print(f"Fetching {indicator}...")
            result = self.store_series(indicator)
            if not result:
                success = False
            # Add a small delay to avoid rate limits
            time.sleep(1)
        
        return success

if __name__ == "__main__":
    # Example usage
    client = FredClient()
    if client.is_initialized():
        # Fetch and store unemployment rate
        client.store_series('UNRATE')
        
        # Fetch multiple common indicators
        client.fetch_common_indicators()
    else:
        print("Please set your FRED API key in the environment variables.")
        print("FRED_API_KEY=your_api_key") 