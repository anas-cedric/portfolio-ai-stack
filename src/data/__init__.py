"""
Data services for market, economic, and ETF data.

This package contains:
- Market data services for real-time and historical price data
- Economic data services for macroeconomic indicators
- ETF data services for fund information
"""

"""
NOTE: We intentionally avoid importing heavy submodules here to prevent
ImportError during application startup when optional dependencies (e.g.,
fredapi, alpaca-py) are not installed. Import the specific clients where
they are used, for example:

    from src.data.alpaca_client import AlpacaClient
    from src.data.fred_client import FredClient

This keeps package import side-effect free.
"""

__all__ = []

# This file marks the directory as a Python package