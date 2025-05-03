"""
Data services for market, economic, and ETF data.

This package contains:
- Market data services for real-time and historical price data
- Economic data services for macroeconomic indicators
- ETF data services for fund information
"""

from src.data.alpaca_client import AlpacaClient
from src.data.market_data_service import MarketDataService
from src.data.fred_client import FredClient
from src.data.bls_client import BLSClient
from src.data.bea_client import BEAClient
from src.data.economic_data_service import EconomicDataService
from src.data.etf_registry import ETFRegistry, AssetClass, ETFProvider

__all__ = [
    'AlpacaClient',
    'MarketDataService',
    'FredClient',
    'BLSClient',
    'BEAClient',
    'EconomicDataService',
    'ETFRegistry',
    'AssetClass',
    'ETFProvider'
]

# This file marks the directory as a Python package 