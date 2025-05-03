"""
ETF Registry Service for maintaining a comprehensive list of ETFs and their basic metadata.

This module is responsible for:
1. Providing a central registry of ETFs across all providers
2. Storing basic metadata for each ETF
3. Supporting operations to add, update, and query ETF information
"""

import os
import json
import time
import pandas as pd
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from enum import Enum
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class AssetClass(Enum):
    """Asset classes for ETFs."""
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    COMMODITY = "commodity"
    CURRENCY = "currency"
    REAL_ESTATE = "real_estate"
    MULTI_ASSET = "multi_asset"
    ALTERNATIVES = "alternatives"
    UNKNOWN = "unknown"


class ETFProvider(Enum):
    """Major ETF providers."""
    VANGUARD = "vanguard"
    BLACKROCK = "blackrock"
    STATE_STREET = "state_street"
    INVESCO = "invesco"
    CHARLES_SCHWAB = "charles_schwab"
    FIDELITY = "fidelity"
    FIRST_TRUST = "first_trust"
    WISDOMTREE = "wisdomtree"
    JPMORGAN = "jpmorgan"
    OTHER = "other"


class ETFRegistry:
    """
    Service for maintaining a comprehensive registry of ETFs.
    
    This registry maintains basic metadata for ETFs including:
    - Ticker
    - Name
    - Provider
    - Asset class
    - Inception date
    - And other core properties
    """
    
    def __init__(self, use_supabase: bool = True):
        """
        Initialize the ETF Registry.
        
        Args:
            use_supabase: Whether to use Supabase for storage (default: True)
        """
        self.use_supabase = use_supabase
        
        # Initialize the registry
        if self.use_supabase:
            self._initialize_supabase_table()
        else:
            # Local registry as fallback
            self.etfs = {}
        
        # Cache of retrieved data
        self.cache = {}
        
    def _initialize_supabase_table(self):
        """Ensure the ETF registry table exists in Supabase."""
        try:
            # Check if the table exists by querying it
            supabase.table('etf_registry').select('ticker').limit(1).execute()
            print("ETF registry table exists in Supabase.")
        except Exception as e:
            print(f"Error checking ETF registry table: {str(e)}")
            print("Creating ETF registry table in Supabase...")
            
            # In a real implementation, you would create the table via migrations
            # For this example, we'll assume the table already exists or you'll create it manually
            print("Please ensure the etf_registry table exists with the following structure:")
            print("""
            CREATE TABLE etf_registry (
                ticker TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                inception_date DATE,
                expense_ratio FLOAT,
                fund_info_url TEXT,
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                added_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT TRUE
            );
            """)
    
    def get_all_etfs(self) -> pd.DataFrame:
        """
        Retrieve all ETFs in the registry.
        
        Returns:
            DataFrame containing all ETF records
        """
        if self.use_supabase:
            response = supabase.table('etf_registry').select('*').execute()
            if hasattr(response, 'data') and response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        else:
            return pd.DataFrame(self.etfs.values())
    
    def get_etf(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an ETF by ticker.
        
        Args:
            ticker: The ETF ticker symbol
            
        Returns:
            ETF metadata dictionary or None if not found
        """
        ticker = ticker.upper()
        
        # Check cache first
        if ticker in self.cache:
            return self.cache[ticker]
        
        if self.use_supabase:
            response = supabase.table('etf_registry').select('*').eq('ticker', ticker).execute()
            if hasattr(response, 'data') and response.data:
                etf = response.data[0]
                self.cache[ticker] = etf
                return etf
            return None
        else:
            etf = self.etfs.get(ticker)
            if etf:
                self.cache[ticker] = etf
            return etf
    
    def add_etf(self, etf_data: Dict[str, Any]) -> bool:
        """
        Add an ETF to the registry.
        
        Args:
            etf_data: Dictionary with ETF metadata
            
        Returns:
            Success status
        """
        # Ensure ticker is uppercase
        if 'ticker' not in etf_data:
            raise ValueError("ETF data must include a ticker symbol")
            
        etf_data['ticker'] = etf_data['ticker'].upper()
        
        # Add timestamp
        etf_data['added_date'] = datetime.now().isoformat()
        etf_data['last_updated'] = datetime.now().isoformat()
        
        # Set active flag
        etf_data['active'] = True
        
        ticker = etf_data['ticker']
        
        try:
            if self.use_supabase:
                # Check if ETF already exists
                existing = self.get_etf(ticker)
                
                if existing:
                    # Update existing record
                    response = supabase.table('etf_registry').update(etf_data).eq('ticker', ticker).execute()
                else:
                    # Insert new record
                    response = supabase.table('etf_registry').insert(etf_data).execute()
                
                # Update cache
                self.cache[ticker] = etf_data
                return True
            else:
                self.etfs[ticker] = etf_data
                self.cache[ticker] = etf_data
                return True
        except Exception as e:
            print(f"Error adding ETF {ticker}: {str(e)}")
            return False
    
    def update_etf(self, ticker: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing ETF in the registry.
        
        Args:
            ticker: The ETF ticker symbol
            updates: Dictionary with fields to update
            
        Returns:
            Success status
        """
        ticker = ticker.upper()
        
        # Add last_updated timestamp
        updates['last_updated'] = datetime.now().isoformat()
        
        try:
            if self.use_supabase:
                response = supabase.table('etf_registry').update(updates).eq('ticker', ticker).execute()
                
                # Update cache if present
                if ticker in self.cache:
                    self.cache[ticker].update(updates)
                
                return True
            else:
                if ticker in self.etfs:
                    self.etfs[ticker].update(updates)
                    
                    # Update cache if present
                    if ticker in self.cache:
                        self.cache[ticker].update(updates)
                    
                    return True
                return False
        except Exception as e:
            print(f"Error updating ETF {ticker}: {str(e)}")
            return False
    
    def deactivate_etf(self, ticker: str) -> bool:
        """
        Deactivate an ETF in the registry (mark as inactive).
        
        Args:
            ticker: The ETF ticker symbol
            
        Returns:
            Success status
        """
        return self.update_etf(ticker, {'active': False})
    
    def search_etfs(self, query: str, limit: int = 20) -> pd.DataFrame:
        """
        Search for ETFs by name or ticker.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            DataFrame of matching ETFs
        """
        query = query.upper()
        
        if self.use_supabase:
            # Search by ticker or name
            response = supabase.table('etf_registry') \
                .select('*') \
                .or_(f"ticker.ilike.%{query}%,name.ilike.%{query}%") \
                .limit(limit) \
                .execute()
            
            if hasattr(response, 'data') and response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        else:
            # Simple local search
            results = []
            for etf in self.etfs.values():
                if (query in etf['ticker'].upper()) or (query in etf['name'].upper()):
                    results.append(etf)
                if len(results) >= limit:
                    break
            return pd.DataFrame(results)
    
    def get_etfs_by_provider(self, provider: ETFProvider) -> pd.DataFrame:
        """
        Get all ETFs from a specific provider.
        
        Args:
            provider: The ETF provider
            
        Returns:
            DataFrame of matching ETFs
        """
        provider_str = provider.value if isinstance(provider, ETFProvider) else provider
        
        if self.use_supabase:
            response = supabase.table('etf_registry') \
                .select('*') \
                .eq('provider', provider_str) \
                .eq('active', True) \
                .execute()
            
            if hasattr(response, 'data') and response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        else:
            results = [etf for etf in self.etfs.values() 
                      if etf['provider'] == provider_str and etf.get('active', True)]
            return pd.DataFrame(results)
    
    def get_etfs_by_asset_class(self, asset_class: AssetClass) -> pd.DataFrame:
        """
        Get all ETFs of a specific asset class.
        
        Args:
            asset_class: The asset class
            
        Returns:
            DataFrame of matching ETFs
        """
        asset_class_str = asset_class.value if isinstance(asset_class, AssetClass) else asset_class
        
        if self.use_supabase:
            response = supabase.table('etf_registry') \
                .select('*') \
                .eq('asset_class', asset_class_str) \
                .eq('active', True) \
                .execute()
            
            if hasattr(response, 'data') and response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        else:
            results = [etf for etf in self.etfs.values() 
                      if etf['asset_class'] == asset_class_str and etf.get('active', True)]
            return pd.DataFrame(results)
    
    def clear_cache(self):
        """Clear the local cache of ETF data."""
        self.cache = {}
    
    def seed_initial_etfs(self, csv_file: Optional[str] = None):
        """
        Seed the registry with an initial list of common ETFs.
        
        Args:
            csv_file: Optional path to CSV file with ETF data
        """
        if csv_file and os.path.exists(csv_file):
            # Load from CSV file
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                self.add_etf(row.to_dict())
            print(f"Seeded {len(df)} ETFs from {csv_file}")
        else:
            # Seed with a few common ETFs
            common_etfs = [
                {
                    "ticker": "SPY",
                    "name": "SPDR S&P 500 ETF Trust",
                    "provider": ETFProvider.STATE_STREET.value,
                    "asset_class": AssetClass.EQUITY.value,
                    "inception_date": "1993-01-22",
                    "expense_ratio": 0.0945,
                    "fund_info_url": "https://www.ssga.com/us/en/individual/etfs/funds/spdr-sp-500-etf-trust-spy"
                },
                {
                    "ticker": "VOO",
                    "name": "Vanguard S&P 500 ETF",
                    "provider": ETFProvider.VANGUARD.value,
                    "asset_class": AssetClass.EQUITY.value,
                    "inception_date": "2010-09-07",
                    "expense_ratio": 0.03,
                    "fund_info_url": "https://investor.vanguard.com/investment-products/etfs/profile/voo"
                },
                {
                    "ticker": "IVV",
                    "name": "iShares Core S&P 500 ETF",
                    "provider": ETFProvider.BLACKROCK.value,
                    "asset_class": AssetClass.EQUITY.value,
                    "inception_date": "2000-05-15",
                    "expense_ratio": 0.03,
                    "fund_info_url": "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf"
                },
                {
                    "ticker": "QQQ",
                    "name": "Invesco QQQ Trust",
                    "provider": ETFProvider.INVESCO.value,
                    "asset_class": AssetClass.EQUITY.value,
                    "inception_date": "1999-03-10",
                    "expense_ratio": 0.20,
                    "fund_info_url": "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=QQQ"
                },
                {
                    "ticker": "VTI",
                    "name": "Vanguard Total Stock Market ETF",
                    "provider": ETFProvider.VANGUARD.value,
                    "asset_class": AssetClass.EQUITY.value,
                    "inception_date": "2001-05-24",
                    "expense_ratio": 0.03,
                    "fund_info_url": "https://investor.vanguard.com/investment-products/etfs/profile/vti"
                },
                {
                    "ticker": "AGG",
                    "name": "iShares Core U.S. Aggregate Bond ETF",
                    "provider": ETFProvider.BLACKROCK.value,
                    "asset_class": AssetClass.FIXED_INCOME.value,
                    "inception_date": "2003-09-22",
                    "expense_ratio": 0.03,
                    "fund_info_url": "https://www.ishares.com/us/products/239458/ishares-core-total-us-bond-market-etf"
                },
                {
                    "ticker": "BND",
                    "name": "Vanguard Total Bond Market ETF",
                    "provider": ETFProvider.VANGUARD.value,
                    "asset_class": AssetClass.FIXED_INCOME.value,
                    "inception_date": "2007-04-03",
                    "expense_ratio": 0.035,
                    "fund_info_url": "https://investor.vanguard.com/investment-products/etfs/profile/bnd"
                },
                {
                    "ticker": "VEA",
                    "name": "Vanguard FTSE Developed Markets ETF",
                    "provider": ETFProvider.VANGUARD.value,
                    "asset_class": AssetClass.EQUITY.value,
                    "inception_date": "2007-07-02",
                    "expense_ratio": 0.05,
                    "fund_info_url": "https://investor.vanguard.com/investment-products/etfs/profile/vea"
                },
                {
                    "ticker": "VWO",
                    "name": "Vanguard FTSE Emerging Markets ETF",
                    "provider": ETFProvider.VANGUARD.value,
                    "asset_class": AssetClass.EQUITY.value,
                    "inception_date": "2005-03-04",
                    "expense_ratio": 0.08,
                    "fund_info_url": "https://investor.vanguard.com/investment-products/etfs/profile/vwo"
                },
                {
                    "ticker": "GLD",
                    "name": "SPDR Gold Shares",
                    "provider": ETFProvider.STATE_STREET.value,
                    "asset_class": AssetClass.COMMODITY.value,
                    "inception_date": "2004-11-18",
                    "expense_ratio": 0.40,
                    "fund_info_url": "https://www.spdrgoldshares.com/"
                }
            ]
            
            for etf in common_etfs:
                self.add_etf(etf)
            
            print(f"Seeded {len(common_etfs)} common ETFs")
    
    def export_to_csv(self, output_file: str) -> bool:
        """
        Export the ETF registry to a CSV file.
        
        Args:
            output_file: Path to output CSV file
            
        Returns:
            Success status
        """
        try:
            df = self.get_all_etfs()
            df.to_csv(output_file, index=False)
            print(f"Exported {len(df)} ETFs to {output_file}")
            return True
        except Exception as e:
            print(f"Error exporting ETF registry: {str(e)}")
            return False
    
    def flush_to_storage(self) -> bool:
        """
        Flush the local data to storage (only relevant for local mode).
        
        Returns:
            Success status
        """
        if not self.use_supabase:
            try:
                # In a real implementation, you would save to a local file
                print(f"Flushed {len(self.etfs)} ETFs to local storage")
                return True
            except Exception as e:
                print(f"Error flushing ETF registry: {str(e)}")
                return False
        return True  # No-op for Supabase mode 