"""
Bureau of Economic Analysis (BEA) API client for retrieving economic accounts data.
"""
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
import pandas as pd
import requests
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class BEAClient:
    """Client for interacting with the Bureau of Economic Analysis (BEA) API."""
    
    def __init__(self):
        """Initialize the BEA client with API key."""
        # Get API key from environment variable
        self.api_key = os.getenv('BEA_API_KEY')
        if not self.api_key:
            print("Warning: BEA_API_KEY not found in environment variables.")
            print("Please set your BEA API key to use this client.")
            print("You can register for an API key at https://apps.bea.gov/API/signup/")
        
        # BEA API endpoint
        self.endpoint = "https://apps.bea.gov/api/data"
    
    def is_initialized(self) -> bool:
        """Check if the client is properly initialized."""
        return self.api_key is not None
    
    def get_gdp_data(self, frequency: str = 'Q', years: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve GDP data from BEA.
        
        Args:
            frequency: Frequency of data ('A' for annual, 'Q' for quarterly)
            years: Years to retrieve, e.g., '2010,2011,2012' or '2010-2020' (default: last 5 years)
            
        Returns:
            DataFrame with GDP data
        """
        if not self.is_initialized():
            raise ValueError("BEA client not initialized. Please set BEA_API_KEY.")
        
        # Set default years if not provided
        if not years:
            current_year = datetime.now().year
            years = f"{current_year-5}-{current_year}"
        
        # Prepare request parameters
        params = {
            'UserID': self.api_key,
            'method': 'GetData',
            'datasetname': 'NIPA',
            'TableName': 'T10101',  # GDP table
            'Frequency': frequency,
            'Year': years,
            'ResultFormat': 'JSON'
        }
        
        try:
            # Make the API request
            response = requests.get(self.endpoint, params=params)
            data = response.json()
            
            # Check for errors
            if 'BEAAPI' not in data or 'Results' not in data['BEAAPI']:
                print(f"BEA API Error: {data.get('Message', 'Unknown error')}")
                return pd.DataFrame()
            
            # Extract and process the data
            results = data['BEAAPI']['Results']
            if 'Data' not in results:
                print("No data found in BEA response")
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(results['Data'])
            return df
            
        except Exception as e:
            print(f"Error fetching BEA GDP data: {e}")
            return pd.DataFrame()
    
    def get_personal_income(self, frequency: str = 'Q', years: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve personal income data from BEA.
        
        Args:
            frequency: Frequency of data ('A' for annual, 'Q' for quarterly, 'M' for monthly)
            years: Years to retrieve (default: last 5 years)
            
        Returns:
            DataFrame with personal income data
        """
        if not self.is_initialized():
            raise ValueError("BEA client not initialized. Please set BEA_API_KEY.")
        
        # Set default years if not provided
        if not years:
            current_year = datetime.now().year
            years = f"{current_year-5}-{current_year}"
        
        # Prepare request parameters
        params = {
            'UserID': self.api_key,
            'method': 'GetData',
            'datasetname': 'NIPA',
            'TableName': 'T20100',  # Personal Income table
            'Frequency': frequency,
            'Year': years,
            'ResultFormat': 'JSON'
        }
        
        try:
            # Make the API request
            response = requests.get(self.endpoint, params=params)
            data = response.json()
            
            # Extract and process the data
            results = data['BEAAPI']['Results']
            if 'Data' not in results:
                print("No data found in BEA response")
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(results['Data'])
            return df
            
        except Exception as e:
            print(f"Error fetching BEA personal income data: {e}")
            return pd.DataFrame()
    
    def store_bea_data(self, table_name: str, series_data: pd.DataFrame) -> bool:
        """
        Store BEA data in the database.
        
        Args:
            table_name: BEA table name (e.g., 'NIPA', 'GDP')
            series_data: DataFrame with BEA data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if series_data.empty:
                return False
            
            # Convert to list of records for Supabase
            records = []
            for _, row in series_data.iterrows():
                # Extract key information
                series_code = row.get('SeriesCode', row.get('LineNumber', ''))
                line_number = row.get('LineNumber', '')
                time_period = row.get('TimePeriod', '')
                year = time_period[:4] if time_period else ''
                
                # Parse date based on time period format
                date_str = None
                frequency = 'A'  # Default to annual
                
                if time_period:
                    if len(time_period) == 4:  # Annual: 2020
                        date_str = f"{time_period}-01-01"
                        frequency = 'A'
                    elif len(time_period) == 6 and time_period[4:5] == 'Q':  # Quarterly: 2020Q1
                        quarter = int(time_period[5:6])
                        month = (quarter - 1) * 3 + 1
                        date_str = f"{time_period[:4]}-{month:02d}-01"
                        frequency = 'Q'
                    elif len(time_period) == 7 and time_period[4:5] == 'M':  # Monthly: 2020M01
                        date_str = f"{time_period[:4]}-{time_period[5:7]}-01"
                        frequency = 'M'
                
                # Skip if we couldn't parse a date
                if not date_str:
                    continue
                
                # Get data value and handle comma formatting
                data_value = row.get('DataValue', '')
                if data_value and isinstance(data_value, str):
                    # Remove commas from numeric strings
                    data_value = data_value.replace(',', '')
                
                # Create the record
                record = {
                    'table_name': table_name,
                    'line_number': line_number,
                    'series_code': series_code,
                    'date': date_str,
                    'value': float(data_value) if data_value else None,
                    'units': row.get('CL_UNIT', ''),
                    'frequency': frequency,
                    'seasonally_adjusted': 'adjusted' in row.get('SeriesName', '').lower(),
                    'source': 'BEA'
                }
                records.append(record)
            
            # Insert into Supabase
            if records:
                result = supabase.table('bea_economic_data').upsert(records).execute()
                print(f"Stored {len(records)} records for BEA {table_name} data")
                return True
            else:
                print(f"No valid records found for BEA {table_name} data")
                return False
            
        except Exception as e:
            print(f"Error storing BEA {table_name} data: {e}")
            return False
    
    def fetch_common_indicators(self) -> bool:
        """
        Fetch and store commonly used BEA indicators.
        
        Returns:
            True if all fetches succeeded, False if any failed
        """
        success = True
        
        # GDP Data
        gdp_data = self.get_gdp_data(frequency='Q')
        if not gdp_data.empty:
            gdp_result = self.store_bea_data('GDP', gdp_data)
            if not gdp_result:
                success = False
        else:
            success = False
        
        # Personal Income Data
        income_data = self.get_personal_income(frequency='Q')
        if not income_data.empty:
            income_result = self.store_bea_data('PERSONAL_INCOME', income_data)
            if not income_result:
                success = False
        else:
            success = False
        
        # Add more indicators as needed
        
        return success

if __name__ == "__main__":
    # Example usage
    client = BEAClient()
    if client.is_initialized():
        # Fetch GDP data
        gdp_data = client.get_gdp_data()
        client.store_bea_data('GDP', gdp_data)
        
        # Fetch all common indicators
        client.fetch_common_indicators()
    else:
        print("Please set your BEA API key in the environment variables.")
        print("BEA_API_KEY=your_api_key") 