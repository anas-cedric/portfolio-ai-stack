"""
Unified service for gathering, processing, and storing economic data from multiple sources.
"""
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

# Import our data clients
from src.data.fred_client import FredClient
from src.data.bls_client import BLSClient
from src.data.bea_client import BEAClient

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class EconomicDataService:
    """Service for gathering and processing economic data from multiple sources."""
    
    def __init__(self):
        """Initialize all data clients."""
        self.fred_client = FredClient()
        self.bls_client = BLSClient()
        self.bea_client = BEAClient()
        
        # Check which clients are properly initialized
        self.fred_available = self.fred_client.is_initialized()
        self.bls_available = True  # BLS available even without key (limited)
        self.bea_available = self.bea_client.is_initialized()
        
        # Print availability status
        print(f"FRED client available: {self.fred_available}")
        print(f"BLS client available: {self.bls_available}")
        print(f"BEA client available: {self.bea_available}")
    
    def fetch_all_indicators(self) -> Dict[str, bool]:
        """
        Fetch all economic indicators from all available sources.
        
        Returns:
            Dictionary with results for each data source
        """
        results = {}
        
        # Fetch FRED data if available
        if self.fred_available:
            print("\n--- Fetching FRED Economic Data ---")
            fred_result = self.fred_client.fetch_common_indicators()
            results['fred'] = fred_result
        
        # Fetch BLS data
        print("\n--- Fetching BLS Labor Statistics ---")
        bls_result = self.bls_client.fetch_common_indicators()
        results['bls'] = bls_result
        
        # Fetch BEA data if available
        if self.bea_available:
            print("\n--- Fetching BEA Economic Accounts Data ---")
            bea_result = self.bea_client.fetch_common_indicators()
            results['bea'] = bea_result
        
        return results
    
    def calculate_derived_indicators(self) -> bool:
        """
        Calculate derived economic indicators from raw data.
        
        This combines data from different sources to create higher-level
        indicators that might be useful for economic analysis.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate indicators only if we have data
            indicators = []
            
            # Get latest real GDP (GDPC1) from FRED
            try:
                gdp_result = supabase.table('fed_economic_data').select('*') \
                    .eq('series_id', 'GDPC1') \
                    .order('date', desc=True) \
                    .limit(8) \
                    .execute()
                
                if gdp_result.data and len(gdp_result.data) >= 2:
                    # Calculate GDP growth rate (quarter-over-quarter)
                    gdp_data = pd.DataFrame(gdp_result.data)
                    gdp_data = gdp_data.sort_values('date')
                    
                    # Calculate QoQ percent change
                    current_gdp = gdp_data.iloc[-1]['value']
                    previous_gdp = gdp_data.iloc[-2]['value']
                    qoq_growth = ((current_gdp / previous_gdp) - 1) * 100
                    
                    # Calculate YoY percent change if we have data from a year ago
                    if len(gdp_data) >= 5:  # Current quarter + 4 previous quarters
                        year_ago_gdp = gdp_data.iloc[-5]['value']
                        yoy_growth = ((current_gdp / year_ago_gdp) - 1) * 100
                        
                        # Add YoY GDP growth indicator
                        indicators.append({
                            'indicator_name': 'GDP Growth Rate (YoY)',
                            'date': gdp_data.iloc[-1]['date'],
                            'value': yoy_growth,
                            'calculation_method': 'YoY%',
                            'source_table': 'fed_economic_data',
                            'source_series': 'GDPC1'
                        })
                    
                    # Add QoQ GDP growth indicator
                    indicators.append({
                        'indicator_name': 'GDP Growth Rate (QoQ)',
                        'date': gdp_data.iloc[-1]['date'],
                        'value': qoq_growth,
                        'calculation_method': 'QoQ%',
                        'source_table': 'fed_economic_data',
                        'source_series': 'GDPC1'
                    })
            except Exception as e:
                print(f"Error calculating GDP growth indicators: {e}")
            
            # Get inflation rate from CPI data
            try:
                cpi_result = supabase.table('fed_economic_data').select('*') \
                    .eq('series_id', 'CPIAUCSL') \
                    .order('date', desc=True) \
                    .limit(13) \
                    .execute()
                
                if cpi_result.data and len(cpi_result.data) >= 13:
                    # Calculate inflation rate (year-over-year)
                    cpi_data = pd.DataFrame(cpi_result.data)
                    cpi_data = cpi_data.sort_values('date')
                    
                    current_cpi = cpi_data.iloc[-1]['value']
                    year_ago_cpi = cpi_data.iloc[-13]['value']  # 12 months ago
                    inflation_rate = ((current_cpi / year_ago_cpi) - 1) * 100
                    
                    # Add inflation rate indicator
                    indicators.append({
                        'indicator_name': 'Inflation Rate',
                        'date': cpi_data.iloc[-1]['date'],
                        'value': inflation_rate,
                        'calculation_method': 'YoY%',
                        'source_table': 'fed_economic_data',
                        'source_series': 'CPIAUCSL'
                    })
            except Exception as e:
                print(f"Error calculating inflation indicators: {e}")
            
            # Add more derived indicators here
            
            # Store calculated indicators
            if indicators:
                result = supabase.table('economic_indicators').upsert(indicators).execute()
                print(f"Stored {len(indicators)} calculated economic indicators")
                return True
            else:
                print("No indicators calculated")
                return False
            
        except Exception as e:
            print(f"Error calculating derived indicators: {e}")
            return False
    
    def run_data_pipeline(self) -> bool:
        """
        Run the complete economic data pipeline.
        
        This fetches data from all sources and calculates derived indicators.
        
        Returns:
            True if successful, False otherwise
        """
        print("Starting economic data pipeline...")
        
        # Fetch raw data from all sources
        fetch_results = self.fetch_all_indicators()
        
        # Check if we got data from any source
        if not any(fetch_results.values()):
            print("Failed to fetch data from any source")
            return False
        
        print("\n--- Calculating Derived Indicators ---")
        calc_result = self.calculate_derived_indicators()
        
        print("\nEconomic data pipeline complete")
        return calc_result

if __name__ == "__main__":
    # Example usage
    service = EconomicDataService()
    service.run_data_pipeline() 