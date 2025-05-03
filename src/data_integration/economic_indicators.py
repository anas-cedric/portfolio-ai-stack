"""
Economic Indicators Integration Module

This module handles:
1. Fetching economic data from FRED (Federal Reserve Economic Data) and other sources
2. Processing and formatting economic indicators
3. Storing indicator data in the knowledge base
4. Tracking key economic metrics for portfolio decisions
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.schema import EconomicIndicator, YieldCurvePoint, KnowledgeCategory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# FRED API key
FRED_API_KEY = os.getenv("FRED_API_KEY")


class EconomicDataIntegration:
    """
    Integration for economic data from various sources, including FRED.
    
    This class handles:
    1. Connection to economic data APIs
    2. Regular updates of key economic indicators
    3. Processing and storage in the knowledge base
    4. Tracking historical trends and forecasts
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        fred_api_key: Optional[str] = None,
        track_indicators: Optional[List[str]] = None
    ):
        """
        Initialize the economic data integration.
        
        Args:
            knowledge_base: Knowledge base instance for storing data
            fred_api_key: FRED API key for accessing economic data
            track_indicators: List of indicator IDs to track
        """
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.fred_api_key = fred_api_key or FRED_API_KEY
        
        # Default indicators to track
        self.track_indicators = track_indicators or [
            # Interest rates
            "DFF",      # Federal Funds Effective Rate
            "DGS2",     # 2-Year Treasury Rate
            "DGS10",    # 10-Year Treasury Rate
            "T10Y2Y",   # 10-Year - 2-Year Treasury Spread
            "T10Y3M",   # 10-Year - 3-Month Treasury Spread
            # Inflation
            "CPIAUCSL", # Consumer Price Index
            "PCEPI",    # Personal Consumption Expenditures Price Index
            # Employment
            "UNRATE",   # Unemployment Rate
            "PAYEMS",   # Total Nonfarm Payroll
            # Economic activity
            "GDP",      # Gross Domestic Product
            "INDPRO",   # Industrial Production Index
            "RSAFS",    # Retail Sales
            # Housing
            "HOUST",    # Housing Starts
            "CSUSHPISA", # Case-Shiller Home Price Index
        ]
        
        # Indicator metadata for better descriptions
        self.indicator_metadata = {
            "DFF": {"name": "Federal Funds Rate", "frequency": "daily", "units": "percent", "impact": "high"},
            "DGS2": {"name": "2-Year Treasury Rate", "frequency": "daily", "units": "percent", "impact": "medium"},
            "DGS10": {"name": "10-Year Treasury Rate", "frequency": "daily", "units": "percent", "impact": "high"},
            "T10Y2Y": {"name": "10Y-2Y Treasury Spread", "frequency": "daily", "units": "percent", "impact": "high"},
            "T10Y3M": {"name": "10Y-3M Treasury Spread", "frequency": "daily", "units": "percent", "impact": "high"},
            "CPIAUCSL": {"name": "Consumer Price Index", "frequency": "monthly", "units": "index", "impact": "high"},
            "PCEPI": {"name": "PCE Price Index", "frequency": "monthly", "units": "index", "impact": "high"},
            "UNRATE": {"name": "Unemployment Rate", "frequency": "monthly", "units": "percent", "impact": "high"},
            "PAYEMS": {"name": "Nonfarm Payroll", "frequency": "monthly", "units": "thousands", "impact": "high"},
            "GDP": {"name": "Gross Domestic Product", "frequency": "quarterly", "units": "billions", "impact": "high"},
            "INDPRO": {"name": "Industrial Production", "frequency": "monthly", "units": "index", "impact": "medium"},
            "RSAFS": {"name": "Retail Sales", "frequency": "monthly", "units": "millions", "impact": "medium"},
            "HOUST": {"name": "Housing Starts", "frequency": "monthly", "units": "thousands", "impact": "medium"},
            "CSUSHPISA": {"name": "Case-Shiller HPI", "frequency": "monthly", "units": "index", "impact": "medium"},
        }
        
        # Cache for previous values
        self.previous_values = {}
        
        if not self.fred_api_key:
            logger.warning("FRED API key not provided. Some functionality will be limited.")
        
        logger.info(f"Initialized EconomicDataIntegration with {len(self.track_indicators)} indicators")
        
    def update_economic_indicators(self):
        """
        Update economic indicators from FRED.
        
        Fetches the latest data for all tracked indicators and stores them in the knowledge base.
        """
        if not self.fred_api_key:
            logger.error("FRED API key not available. Cannot update economic indicators.")
            return
            
        logger.info(f"Updating economic indicators from FRED")
        current_time = datetime.now().isoformat()
        
        for indicator_id in self.track_indicators:
            try:
                # Get metadata for this indicator
                metadata = self.indicator_metadata.get(indicator_id, {})
                indicator_name = metadata.get("name", indicator_id)
                
                # Fetch the latest data
                data = self._fetch_fred_data(indicator_id)
                
                if data.empty:
                    logger.warning(f"No data available for indicator {indicator_id}")
                    continue
                
                # Get the latest value
                latest_row = data.iloc[-1]
                latest_value = float(latest_row["value"])
                latest_date = latest_row["date"]
                
                # Get previous value if available
                previous_value = None
                if len(data) > 1:
                    previous_value = float(data.iloc[-2]["value"])
                else:
                    previous_value = self.previous_values.get(indicator_id)
                
                # Store this value for next time
                self.previous_values[indicator_id] = latest_value
                
                # Calculate change
                change = None
                change_percent = None
                if previous_value is not None:
                    change = latest_value - previous_value
                    if previous_value != 0:
                        change_percent = (change / previous_value) * 100
                
                # Create economic indicator
                indicator = EconomicIndicator(
                    timestamp=current_time,
                    name=indicator_name,
                    value=latest_value,
                    previous_value=previous_value,
                    change=change,
                    change_percent=change_percent,
                    impact=metadata.get("impact", "medium"),
                    source="fred"
                )
                
                # Store in knowledge base
                self.knowledge_base.add_economic_indicator(indicator)
                logger.debug(f"Added economic indicator: {indicator_name}: {latest_value}")
                
            except Exception as e:
                logger.error(f"Error updating economic indicator {indicator_id}: {str(e)}")
        
        logger.info(f"Updated {len(self.track_indicators)} economic indicators")
        
        # Also update yield curve data
        self.update_yield_curve()
        
    def update_yield_curve(self):
        """
        Update the Treasury yield curve data.
        
        Fetches the latest Treasury rates for various maturities and stores them in the knowledge base.
        """
        if not self.fred_api_key:
            logger.error("FRED API key not available. Cannot update yield curve.")
            return
            
        logger.info("Updating Treasury yield curve")
        current_time = datetime.now().isoformat()
        
        # Treasury rate series for different maturities
        maturities = {
            "DGS1MO": "1M",
            "DGS3MO": "3M",
            "DGS6MO": "6M",
            "DGS1": "1Y",
            "DGS2": "2Y",
            "DGS3": "3Y",
            "DGS5": "5Y",
            "DGS7": "7Y",
            "DGS10": "10Y",
            "DGS20": "20Y",
            "DGS30": "30Y"
        }
        
        for fred_id, maturity in maturities.items():
            try:
                # Fetch the latest data
                data = self._fetch_fred_data(fred_id)
                
                if data.empty:
                    logger.warning(f"No data available for Treasury rate {fred_id}")
                    continue
                
                # Get the latest value
                latest_row = data.iloc[-1]
                latest_value = float(latest_row["value"])
                latest_date = latest_row["date"]
                
                # Get previous value if available
                previous_value = None
                if len(data) > 1:
                    previous_value = float(data.iloc[-2]["value"])
                
                # Calculate change
                change = None
                if previous_value is not None:
                    change = latest_value - previous_value
                
                # Create yield curve point
                yield_point = YieldCurvePoint(
                    timestamp=current_time,
                    maturity=maturity,
                    yield_value=latest_value,
                    previous_yield=previous_value,
                    change=change,
                    source="fred"
                )
                
                # Store in knowledge base
                self.knowledge_base.add_yield_curve_point(yield_point)
                logger.debug(f"Added yield curve point: {maturity}: {latest_value:.2f}%")
                
            except Exception as e:
                logger.error(f"Error updating yield curve point {fred_id}: {str(e)}")
        
        logger.info(f"Updated yield curve with {len(maturities)} points")
    
    def _fetch_fred_data(self, series_id, limit=5):
        """
        Fetch data from FRED API.
        
        Args:
            series_id: FRED series identifier
            limit: Maximum number of observations to retrieve
            
        Returns:
            DataFrame with date and value columns
        """
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])
            
            if not observations:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(observations)
            
            # Convert date to datetime and value to float
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            
            # Drop rows with missing values
            df = df.dropna(subset=["value"])
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from FRED for {series_id}: {str(e)}")
            return pd.DataFrame()


def main():
    """Test the economic data integration."""
    load_dotenv()
    
    # Check if API key is available
    if not FRED_API_KEY:
        logger.error("FRED API key not available. Set FRED_API_KEY in .env file.")
        return
    
    # Initialize knowledge base and economic data integration
    kb = KnowledgeBase(namespace="economic_test")
    economic = EconomicDataIntegration(knowledge_base=kb)
    
    # Update economic indicators
    economic.update_economic_indicators()
    
    # Query for economic data
    query = "interest rates and inflation trends"
    results = kb.query(
        query_text=query,
        filter_categories=[KnowledgeCategory.ECONOMIC_INDICATORS.value],
        top_k=3
    )
    
    print("\nEconomic Data Query Results:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result.content}")


if __name__ == "__main__":
    main() 