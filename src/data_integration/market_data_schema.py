"""
Market Data Schema Module

Defines the data structures for storing stock and ETF information,
including price data, fundamentals, and metadata.
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from enum import Enum

class AssetType(str, Enum):
    """Types of financial assets tracked in the system."""
    STOCK = "stock"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    CRYPTO = "crypto"
    FOREX = "forex"
    OTHER = "other"

class AssetSector(str, Enum):
    """Standard market sectors for categorization."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIALS = "financials"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIALS = "industrials"
    ENERGY = "energy"
    UTILITIES = "utilities"
    MATERIALS = "materials"
    REAL_ESTATE = "real_estate"
    COMMUNICATION_SERVICES = "communication_services"
    OTHER = "other"

@dataclass
class PriceBar:
    """A single price bar/candle for a financial asset."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str = "alpaca"  # Data source identifier
    
    # Optional fields that might not be available from all sources
    vwap: Optional[float] = None  # Volume-weighted average price
    trade_count: Optional[int] = None  # Number of trades
    adjusted_close: Optional[float] = None  # Split/dividend adjusted close
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        # Convert datetime to ISO string
        result["timestamp"] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceBar':
        """Create from dictionary."""
        # Convert ISO string to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
    
    @classmethod
    def from_alpaca_bar(cls, bar: Dict[str, Any]) -> 'PriceBar':
        """Create from Alpaca API bar format."""
        timestamp = bar.get("t")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        
        return cls(
            timestamp=timestamp,
            open=float(bar.get("o", 0)),
            high=float(bar.get("h", 0)),
            low=float(bar.get("l", 0)),
            close=float(bar.get("c", 0)),
            volume=int(bar.get("v", 0)),
            source="alpaca",
            vwap=float(bar.get("vw", 0)) if "vw" in bar else None,
            trade_count=int(bar.get("n", 0)) if "n" in bar else None
        )

@dataclass
class MarketAsset:
    """
    Complete representation of a financial asset with metadata and price history.
    
    This is the primary data structure for storing asset information in the database.
    """
    # Core identification fields
    symbol: str
    name: str
    asset_type: AssetType
    
    # Metadata fields
    description: Optional[str] = None
    sector: Optional[AssetSector] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    currency: str = "USD"
    country: Optional[str] = None
    
    # ETF-specific fields
    is_etf: bool = False
    etf_holdings: Optional[List[Dict[str, Any]]] = None
    etf_expense_ratio: Optional[float] = None
    etf_aum: Optional[float] = None  # Assets under management
    etf_nav: Optional[float] = None  # Net asset value
    
    # Stock-specific fields
    market_cap: Optional[float] = None
    shares_outstanding: Optional[int] = None
    
    # Trading information
    tradable: bool = True
    shortable: bool = False
    marginable: bool = False
    fractionable: bool = False
    
    # Price data - stored separately for efficient updates
    current_price: Optional[float] = None
    price_updated_at: Optional[datetime] = None
    
    # Performance metrics
    ytd_return: Optional[float] = None  # Year-to-date return
    one_year_return: Optional[float] = None
    three_year_return: Optional[float] = None
    
    # System fields
    data_source: str = "alpaca"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        
        # Convert enum values to strings
        if isinstance(self.asset_type, AssetType):
            result["asset_type"] = self.asset_type.value
        
        if isinstance(self.sector, AssetSector):
            result["sector"] = self.sector.value
        
        # Convert datetime objects
        if self.price_updated_at:
            result["price_updated_at"] = self.price_updated_at.isoformat()
        
        result["created_at"] = self.created_at.isoformat()
        result["updated_at"] = self.updated_at.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketAsset':
        """Create from dictionary."""
        # Handle enum conversions
        if "asset_type" in data and isinstance(data["asset_type"], str):
            data["asset_type"] = AssetType(data["asset_type"])
        
        if "sector" in data and isinstance(data["sector"], str) and data["sector"]:
            try:
                data["sector"] = AssetSector(data["sector"])
            except ValueError:
                data["sector"] = AssetSector.OTHER
        
        # Convert datetime strings
        for dt_field in ["price_updated_at", "created_at", "updated_at"]:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field])
        
        return cls(**data)
    
    @classmethod
    def from_alpaca_asset(cls, asset: Dict[str, Any]) -> 'MarketAsset':
        """Create from Alpaca API asset data."""
        # Determine asset type
        symbol = asset.get("symbol", "")
        name = asset.get("name", "")
        
        is_etf = name.endswith("ETF") or "ETF" in name
        asset_type = AssetType.ETF if is_etf else AssetType.STOCK
        
        return cls(
            symbol=symbol,
            name=name,
            asset_type=asset_type,
            exchange=asset.get("exchange"),
            is_etf=is_etf,
            tradable=asset.get("tradable", True),
            shortable=asset.get("shortable", False),
            marginable=asset.get("marginable", False),
            fractionable=asset.get("fractionable", False),
            data_source="alpaca"
        )

@dataclass
class MarketSnapshot:
    """
    A snapshot of market data at a point in time.
    
    Used for capturing the state of multiple assets or the overall market.
    """
    timestamp: datetime
    market_open: bool
    
    # Major indices
    sp500_level: Optional[float] = None
    nasdaq_level: Optional[float] = None
    dow_level: Optional[float] = None
    
    # Sector performance (daily change %)
    sector_performance: Dict[str, float] = field(default_factory=dict)
    
    # Market breadth indicators
    advancing_stocks: Optional[int] = None
    declining_stocks: Optional[int] = None
    
    # Volatility indicator
    vix_level: Optional[float] = None
    
    # General sentiment (simplified)
    sentiment: Optional[str] = None  # "bullish", "bearish", "neutral"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketSnapshot':
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

def create_db_schema_sql() -> str:
    """
    Generate SQL for creating the database schema.
    
    Returns:
        SQL string for creating the necessary tables
    """
    return """
    -- Assets table for storing metadata
    CREATE TABLE IF NOT EXISTS market_assets (
        symbol VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        asset_type VARCHAR(20) NOT NULL,
        description TEXT,
        sector VARCHAR(50),
        industry VARCHAR(100),
        exchange VARCHAR(20),
        currency VARCHAR(10) NOT NULL DEFAULT 'USD',
        country VARCHAR(50),
        is_etf BOOLEAN NOT NULL DEFAULT FALSE,
        etf_holdings JSONB,
        etf_expense_ratio NUMERIC(10,5),
        etf_aum NUMERIC(20,2),
        etf_nav NUMERIC(10,2),
        market_cap NUMERIC(20,2),
        shares_outstanding BIGINT,
        tradable BOOLEAN NOT NULL DEFAULT TRUE,
        shortable BOOLEAN NOT NULL DEFAULT FALSE,
        marginable BOOLEAN NOT NULL DEFAULT FALSE,
        fractionable BOOLEAN NOT NULL DEFAULT FALSE,
        current_price NUMERIC(10,2),
        price_updated_at TIMESTAMP WITH TIME ZONE,
        ytd_return NUMERIC(10,4),
        one_year_return NUMERIC(10,4),
        three_year_return NUMERIC(10,4),
        data_source VARCHAR(20) NOT NULL DEFAULT 'alpaca',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    -- Time-series table for price data with TimescaleDB hypertable
    CREATE TABLE IF NOT EXISTS price_bars (
        symbol VARCHAR(20) NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        open NUMERIC(10,2) NOT NULL,
        high NUMERIC(10,2) NOT NULL,
        low NUMERIC(10,2) NOT NULL,
        close NUMERIC(10,2) NOT NULL,
        volume BIGINT NOT NULL,
        vwap NUMERIC(10,2),
        trade_count INTEGER,
        adjusted_close NUMERIC(10,2),
        source VARCHAR(20) NOT NULL DEFAULT 'alpaca',
        PRIMARY KEY (symbol, timestamp)
    );

    -- Index for faster queries on price_bars
    CREATE INDEX IF NOT EXISTS idx_price_bars_symbol_timestamp ON price_bars (symbol, timestamp DESC);
    
    -- Convert to TimescaleDB hypertable if TimescaleDB extension is available
    SELECT create_hypertable('price_bars', 'timestamp', if_not_exists => TRUE);

    -- Market snapshots table
    CREATE TABLE IF NOT EXISTS market_snapshots (
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL PRIMARY KEY,
        market_open BOOLEAN NOT NULL,
        sp500_level NUMERIC(10,2),
        nasdaq_level NUMERIC(10,2),
        dow_level NUMERIC(10,2),
        sector_performance JSONB,
        advancing_stocks INTEGER,
        declining_stocks INTEGER,
        vix_level NUMERIC(10,2),
        sentiment VARCHAR(20)
    );

    -- Convert to TimescaleDB hypertable if TimescaleDB extension is available
    SELECT create_hypertable('market_snapshots', 'timestamp', if_not_exists => TRUE);
    """

def save_schema_to_file(output_file: str = "schema.sql") -> None:
    """
    Save the schema SQL to a file.
    
    Args:
        output_file: Path to the output file
    """
    with open(output_file, "w") as f:
        f.write(create_db_schema_sql())
    
    print(f"Schema SQL saved to {output_file}")

if __name__ == "__main__":
    save_schema_to_file() 