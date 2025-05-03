"""
ETF Data Collector for fetching ETF information via Alpaca.

This module is responsible for:
1. Connecting to Alpaca for ETF data
2. Fetching core ETF metrics
3. Transforming raw data into structured ETF information
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

from src.data.etf_registry import ETFRegistry, AssetClass, ETFProvider
from src.data.alpaca_client import AlpacaClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ETFDataCollector:
    """
    Collector for ETF data using Alpaca.
    
    This class fetches ETF information and pricing data from Alpaca API.
    """
    
    def __init__(self, registry: Optional[ETFRegistry] = None):
        """
        Initialize the ETF Data Collector.
        
        Args:
            registry: Optional ETF registry (will create a new one if not provided)
        """
        self.registry = registry or ETFRegistry()
        self.alpaca_client = AlpacaClient()
        
        # Common ETF provider mappings
        self.provider_keywords = {
            ETFProvider.VANGUARD.value: ["vanguard"],
            ETFProvider.BLACKROCK.value: ["ishares", "blackrock"],
            ETFProvider.STATE_STREET.value: ["spdr", "state street"],
            ETFProvider.INVESCO.value: ["invesco"],
            ETFProvider.CHARLES_SCHWAB.value: ["schwab"],
            ETFProvider.FIDELITY.value: ["fidelity"],
            ETFProvider.FIRST_TRUST.value: ["first trust"],
            ETFProvider.WISDOMTREE.value: ["wisdomtree"],
            ETFProvider.JPMORGAN.value: ["jpmorgan", "jpm"]
        }
    
    def fetch_etf_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch ETF data from Alpaca.
        
        Args:
            ticker: ETF ticker symbol
            
        Returns:
            Dictionary with ETF data
        """
        ticker = ticker.upper()
        logger.info(f"Fetching data for {ticker} from Alpaca")
        
        try:
            # Get latest quotes for basic information
            quotes = self.alpaca_client.get_latest_quotes([ticker])
            
            # Get historical bars for price data and analytics
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Get last quarter's data
            
            bars_data = self.alpaca_client.get_historical_bars(
                symbols=[ticker],
                timeframe='1Day',
                start=start_date,
                end=end_date
            )
            
            # Check if we got data back
            if ticker not in quotes and ticker not in bars_data:
                logger.warning(f"No data found for {ticker}")
                return {"ticker": ticker, "error": "No data found"}
            
            # Extract quote data
            quote_data = quotes.get(ticker, {})
            
            # Extract historical bars
            bars_df = bars_data.get(ticker, pd.DataFrame())
            
            # Start building ETF data
            etf_data = {
                "ticker": ticker,
                "name": self._get_etf_name(ticker),  # Get name from registry or default
                "exchange": "UNKNOWN",  # Alpaca doesn't easily provide exchange in free tier
                "asset_class": self._get_etf_asset_class(ticker),  # Get from registry
                "provider": self._get_etf_provider(ticker),  # Get from registry
                "last_updated": datetime.now().isoformat()
            }
            
            # Add price and volume data if available from quote
            if quote_data:
                etf_data.update({
                    "price": quote_data.get("close_price"),
                    "volume": quote_data.get("volume"),
                    "trade_date": quote_data.get("timestamp")
                })
            
            # Add analytics if we have historical data
            if not bars_df.empty and len(bars_df) > 1:
                # Calculate simple metrics
                returns = bars_df["close"].pct_change().dropna()
                
                etf_data.update({
                    "open": float(bars_df["open"].iloc[-1]),
                    "high": float(bars_df["high"].iloc[-1]),
                    "low": float(bars_df["low"].iloc[-1]),
                    "avg_daily_volume": int(bars_df["volume"].mean()),
                    "price_30d_ago": float(bars_df["close"].iloc[-min(30, len(bars_df))]),
                    "volatility_30d": float(returns.tail(30).std() * (252 ** 0.5)) if len(returns) >= 30 else None,  # Annualized
                    "max_price_90d": float(bars_df["high"].max()),
                    "min_price_90d": float(bars_df["low"].min()),
                })
            
            # Generate a fund info URL
            etf_data["fund_info_url"] = self._generate_fund_url(ticker, etf_data.get("provider", ETFProvider.OTHER.value))
            
            return self._clean_etf_data(etf_data)
            
        except Exception as e:
            logger.error(f"Error fetching Alpaca data for {ticker}: {str(e)}")
            return {"ticker": ticker, "error": str(e)}
    
    def _get_etf_name(self, ticker: str) -> str:
        """Get ETF name from registry or return a default name."""
        try:
            etf = self.registry.get_etf(ticker)
            if etf and etf.get("name"):
                return etf.get("name")
        except:
            pass
        return f"{ticker} ETF"
    
    def _get_etf_asset_class(self, ticker: str) -> str:
        """Get ETF asset class from registry or infer it."""
        try:
            etf = self.registry.get_etf(ticker)
            if etf and etf.get("asset_class"):
                return etf.get("asset_class")
        except:
            pass
        
        # Try to infer from ticker
        ticker_upper = ticker.upper()
        
        # Look for bond/fixed income indicators
        if any(term in ticker_upper for term in ["AGG", "BND", "TLT", "SHY", "LQD", "MBB", "TIP"]):
            return AssetClass.FIXED_INCOME.value
            
        # Look for commodity indicators
        elif any(term in ticker_upper for term in ["GLD", "SLV", "USO", "DBC", "GSG"]):
            return AssetClass.COMMODITY.value
            
        # Look for real estate indicators
        elif any(term in ticker_upper for term in ["VNQ", "IYR", "SCHH", "RWR"]):
            return AssetClass.REAL_ESTATE.value
            
        # Default to equity for most ETFs
        else:
            return AssetClass.EQUITY.value
    
    def _get_etf_provider(self, ticker: str) -> str:
        """Get ETF provider from registry or return a default."""
        try:
            etf = self.registry.get_etf(ticker)
            if etf and etf.get("provider"):
                return etf.get("provider")
        except:
            pass
        return ETFProvider.OTHER.value
    
    def _map_asset_class(self, alpaca_class: str, ticker: str, name: str) -> str:
        """Map Alpaca asset class to our AssetClass enum."""
        # Alpaca primarily classifies securities as 'us_equity', but we need more granular classification
        
        # Check ticker and name for hints
        name_lower = name.lower()
        ticker_upper = ticker.upper()
        
        # Look for bond/fixed income indicators
        if any(term in name_lower for term in ["bond", "treasury", "aggregate", "fixed income"]) or \
           any(term in ticker_upper for term in ["AGG", "BND", "TLT", "SHY", "LQD", "MBB", "TIP"]):
            return AssetClass.FIXED_INCOME.value
            
        # Look for commodity indicators
        elif any(term in name_lower for term in ["gold", "silver", "oil", "commodity", "natural gas"]) or \
             any(term in ticker_upper for term in ["GLD", "SLV", "USO", "DBC", "GSG"]):
            return AssetClass.COMMODITY.value
            
        # Look for real estate indicators
        elif any(term in name_lower for term in ["real estate", "reit", "property"]) or \
             any(term in ticker_upper for term in ["VNQ", "IYR", "SCHH", "RWR"]):
            return AssetClass.REAL_ESTATE.value
            
        # Default to equity for most ETFs
        else:
            return AssetClass.EQUITY.value
    
    def _infer_provider(self, name: str) -> str:
        """
        Infer the ETF provider from the fund name.
        
        Args:
            name: Fund name
            
        Returns:
            Provider enum value
        """
        name_lower = name.lower()
        
        # Check each provider's keywords
        for provider, keywords in self.provider_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return provider
        
        # Default to OTHER if no match
        return ETFProvider.OTHER.value
    
    def _generate_fund_url(self, ticker: str, provider: str) -> str:
        """Generate a fund info URL based on the provider."""
        ticker_lower = ticker.lower()
        
        if provider == ETFProvider.VANGUARD.value:
            return f"https://investor.vanguard.com/investment-products/etfs/profile/{ticker_lower}"
        elif provider == ETFProvider.BLACKROCK.value:
            return f"https://www.ishares.com/us/products/search?q={ticker}"
        elif provider == ETFProvider.STATE_STREET.value:
            return f"https://www.ssga.com/us/en/individual/etfs/funds/{ticker_lower}"
        else:
            return f"https://finance.yahoo.com/quote/{ticker}"
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert a value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _clean_etf_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate ETF data.
        
        Args:
            data: Raw ETF data
            
        Returns:
            Cleaned ETF data
        """
        # Remove None or empty string values
        cleaned = {k: v for k, v in data.items() if v is not None and v != ""}
        
        # Format any percentage fields if needed
        for field in ["expense_ratio", "yield", "dividend_yield"]:
            if field in cleaned and isinstance(cleaned[field], (int, float)):
                if cleaned[field] > 1:  # If greater than 1, assume it's in basis points or percentage * 100
                    cleaned[field] = cleaned[field] / 100
        
        return cleaned
    
    def collect_etf_data(self, ticker: str, update_registry: bool = True) -> Dict[str, Any]:
        """
        Collect ETF data from Alpaca.
        
        Args:
            ticker: ETF ticker symbol
            update_registry: Whether to update the ETF registry
            
        Returns:
            ETF data
        """
        ticker = ticker.upper()
        logger.info(f"Collecting data for ETF: {ticker}")
        
        # Fetch data from Alpaca
        etf_data = self.fetch_etf_data(ticker)
        
        # Update registry if requested
        if update_registry and "error" not in etf_data:
            existing_etf = self.registry.get_etf(ticker)
            
            if existing_etf:
                # Update existing ETF
                self.registry.update_etf(ticker, etf_data)
                logger.info(f"Updated ETF in registry: {ticker}")
            else:
                # Add new ETF
                self.registry.add_etf(etf_data)
                logger.info(f"Added new ETF to registry: {ticker}")
        
        return etf_data
    
    def collect_etfs_batch(self, tickers: List[str], update_registry: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Collect data for multiple ETFs.
        
        Args:
            tickers: List of ETF ticker symbols
            update_registry: Whether to update the ETF registry
            
        Returns:
            Dictionary mapping tickers to ETF data
        """
        results = {}
        
        for ticker in tickers:
            results[ticker] = self.collect_etf_data(ticker, update_registry)
            
        return results
    
    def collect_all_registered_etfs(self) -> int:
        """
        Update data for all ETFs in the registry.
        
        Returns:
            Number of ETFs updated
        """
        etfs = self.registry.get_all_etfs()
        
        if etfs.empty:
            logger.warning("No ETFs found in registry")
            return 0
        
        tickers = etfs["ticker"].tolist()
        logger.info(f"Updating data for {len(tickers)} ETFs")
        
        updated_count = 0
        for ticker in tickers:
            try:
                self.collect_etf_data(ticker, update_registry=True)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating {ticker}: {str(e)}")
        
        logger.info(f"Updated {updated_count} ETFs")
        return updated_count
    
    def convert_to_knowledge_items(self, ticker: str) -> Dict[str, Any]:
        """
        Convert ETF data to knowledge items for storage in knowledge base.
        
        Args:
            ticker: ETF ticker symbol
            
        Returns:
            Dictionary with knowledge item data
        """
        ticker = ticker.upper()
        
        # Get ETF data from registry
        etf_data = self.registry.get_etf(ticker)
        if not etf_data:
            logger.error(f"ETF {ticker} not found in registry")
            return {"error": f"ETF {ticker} not found in registry"}
        
        # Generate a unique ID for the knowledge item
        knowledge_id = f"etf_{ticker.lower()}"
        
        # Build a detailed description of the ETF
        content = [
            f"# {etf_data.get('name', ticker)}",
            f"Ticker: {ticker}",
            f"Asset Class: {etf_data.get('asset_class', 'unknown').replace('_', ' ').title()}",
            f"Provider: {etf_data.get('provider', 'unknown').replace('_', ' ').title()}"
        ]
        
        # Add price information if available
        if 'price' in etf_data:
            content.append(f"\n## Current Price Information")
            content.append(f"Price: ${etf_data.get('price', 'N/A')}")
            content.append(f"Volume: {etf_data.get('volume', 'N/A')}")
            
            # Add high/low if available
            if all(k in etf_data for k in ['high', 'low']):
                content.append(f"Daily Range: ${etf_data.get('low', 'N/A')} - ${etf_data.get('high', 'N/A')}")
            
        # Add analytics if available
        analytics_fields = ['avg_daily_volume', 'price_30d_ago', 'volatility_30d', 'max_price_90d', 'min_price_90d']
        if any(field in etf_data for field in analytics_fields):
            content.append(f"\n## Analytics")
            
            if 'avg_daily_volume' in etf_data:
                content.append(f"Average Daily Volume: {etf_data.get('avg_daily_volume', 'N/A')}")
            
            if 'price_30d_ago' in etf_data and 'price' in etf_data:
                try:
                    price_change = ((etf_data['price'] / etf_data['price_30d_ago']) - 1) * 100
                    content.append(f"30-Day Price Change: {price_change:.2f}%")
                except:
                    pass
            
            if 'volatility_30d' in etf_data:
                content.append(f"30-Day Volatility: {etf_data.get('volatility_30d', 'N/A'):.2%}")
            
            if 'max_price_90d' in etf_data and 'min_price_90d' in etf_data:
                content.append(f"90-Day Price Range: ${etf_data.get('min_price_90d', 'N/A')} - ${etf_data.get('max_price_90d', 'N/A')}")
        
        # Add expense ratio if available
        if 'expense_ratio' in etf_data:
            content.append(f"\n## Fund Information")
            content.append(f"Expense Ratio: {etf_data.get('expense_ratio', 'N/A'):.2%}")
        
        # Add link to fund info
        if 'fund_info_url' in etf_data:
            content.append(f"\nMore Information: {etf_data.get('fund_info_url', '')}")
        
        # Join content into a single string
        content_str = "\n".join(content)
        
        # Create metadata
        metadata = {
            "id": knowledge_id,
            "type": "etf",
            "ticker": ticker,
            "name": etf_data.get('name', f"{ticker} ETF"),
            "asset_class": etf_data.get('asset_class', 'unknown'),
            "provider": etf_data.get('provider', 'unknown'),
            "price": etf_data.get('price', None),
            "updated": etf_data.get('last_updated', datetime.now().isoformat()),
            "source": "alpaca"
        }
        
        # Create the knowledge item
        knowledge_item = {
            "id": knowledge_id,
            "content": content_str,
            "metadata": metadata
        }
        
        return knowledge_item 