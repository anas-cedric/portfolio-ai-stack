"""
Knowledge base schemas for the financial assistant.

This module defines the schemas for various types of knowledge stored in the system,
including fund metadata, financial principles, regulatory frameworks, and user profiles.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Enumeration of asset types."""
    EQUITY = "equity"
    BOND = "bond"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    CRYPTOCURRENCY = "cryptocurrency"
    ALTERNATIVE = "alternative"


class FundType(str, Enum):
    """Enumeration of fund types."""
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    INDEX_FUND = "index_fund"
    ACTIVELY_MANAGED = "actively_managed"
    CLOSED_END = "closed_end"
    HEDGE_FUND = "hedge_fund"


class InvestmentStyle(str, Enum):
    """Enumeration of investment styles."""
    VALUE = "value"
    GROWTH = "growth"
    BLEND = "blend"
    MOMENTUM = "momentum"
    QUALITY = "quality"
    DIVIDEND = "dividend"
    LOW_VOLATILITY = "low_volatility"


class Taxability(str, Enum):
    """Enumeration of taxability types."""
    TAXABLE = "taxable"
    TAX_DEFERRED = "tax_deferred"
    TAX_FREE = "tax_free"


class RiskTolerance(str, Enum):
    """Enumeration of risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATELY_CONSERVATIVE = "moderately_conservative"
    MODERATE = "moderate"
    MODERATELY_AGGRESSIVE = "moderately_aggressive"
    AGGRESSIVE = "aggressive"


class TimeHorizon(str, Enum):
    """Enumeration of investment time horizons."""
    SHORT_TERM = "short_term"  # < 3 years
    MEDIUM_TERM = "medium_term"  # 3-7 years
    LONG_TERM = "long_term"  # 7-15 years
    VERY_LONG_TERM = "very_long_term"  # > 15 years


class KnowledgeCategory(str, Enum):
    """Enumeration of knowledge categories."""
    FUND_METADATA = "fund_metadata"
    INVESTMENT_PRINCIPLES = "investment_principles"
    REGULATORY = "regulatory"
    TAX_RULES = "tax_rules"
    USER_PROFILE = "user_profile"
    MARKET_DATA = "market_data"
    ECONOMIC_INDICATORS = "economic_indicators"


class SectorExposure(BaseModel):
    """Sector exposure for a fund."""
    technology: float = 0.0
    healthcare: float = 0.0
    financials: float = 0.0
    consumer_discretionary: float = 0.0
    consumer_staples: float = 0.0
    industrials: float = 0.0
    energy: float = 0.0
    utilities: float = 0.0
    materials: float = 0.0
    real_estate: float = 0.0
    communication_services: float = 0.0
    other: float = 0.0


class GeographicExposure(BaseModel):
    """Geographic exposure for a fund."""
    north_america: float = 0.0
    europe: float = 0.0
    asia_pacific: float = 0.0
    japan: float = 0.0
    emerging_markets: float = 0.0
    other: float = 0.0


class PerformanceMetrics(BaseModel):
    """Performance metrics for a fund."""
    ytd_return: Optional[float] = None
    one_year_return: Optional[float] = None
    three_year_return: Optional[float] = None
    five_year_return: Optional[float] = None
    ten_year_return: Optional[float] = None
    since_inception_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    standard_deviation: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    r_squared: Optional[float] = None
    max_drawdown: Optional[float] = None


class FundMetadata(BaseModel):
    """Metadata for a fund."""
    ticker: str
    name: str
    fund_type: FundType
    asset_type: AssetType
    investment_style: Optional[InvestmentStyle] = None
    expense_ratio: float
    inception_date: str
    aum: float  # in millions USD
    tracking_error: Optional[float] = None
    dividend_yield: Optional[float] = None
    provider: str
    sector_exposure: Optional[SectorExposure] = None
    geographic_exposure: Optional[GeographicExposure] = None
    performance: Optional[PerformanceMetrics] = None
    liquidity: Optional[float] = None  # Average daily volume in USD
    holdings_count: Optional[int] = None
    top_holdings: Optional[Dict[str, float]] = None  # Ticker to weight mapping
    tax_efficiency_score: Optional[float] = None  # 0-100 score
    description: Optional[str] = None
    knowledge_category: str = KnowledgeCategory.FUND_METADATA


class InvestmentPrinciple(BaseModel):
    """Model for investment principles."""
    title: str
    principle_type: str  # e.g., "Modern Portfolio Theory", "Factor Investing"
    description: str
    key_concepts: List[str]
    practical_applications: List[str]
    additional_resources: Optional[List[str]] = None
    source: Optional[str] = None
    knowledge_category: str = KnowledgeCategory.INVESTMENT_PRINCIPLES


class AssetCorrelation(BaseModel):
    """Correlation matrix between asset classes."""
    asset_classes: List[str]
    correlation_matrix: List[List[float]]
    time_period: str  # e.g., "2010-2020"
    source: Optional[str] = None
    updated_date: str
    knowledge_category: str = KnowledgeCategory.INVESTMENT_PRINCIPLES


class RiskReturnProfile(BaseModel):
    """Risk and return profile for an asset class."""
    asset_class: str
    expected_return: float
    standard_deviation: float
    sharpe_ratio: Optional[float] = None
    time_period: str
    source: Optional[str] = None
    updated_date: str
    knowledge_category: str = KnowledgeCategory.INVESTMENT_PRINCIPLES


class TaxRule(BaseModel):
    """Tax rule or guideline."""
    title: str
    rule_type: str  # e.g., "Tax-Loss Harvesting", "Wash Sale"
    description: str
    considerations: List[str]
    exceptions: Optional[List[str]] = None
    relevant_account_types: List[str]
    updated_date: str
    source: Optional[str] = None
    knowledge_category: str = KnowledgeCategory.TAX_RULES


class AccountTypeTaxation(BaseModel):
    """Taxation details for different account types."""
    account_type: str  # e.g., "401(k)", "Traditional IRA", "Roth IRA"
    taxability: Taxability
    contribution_tax_treatment: str
    withdrawal_tax_treatment: str
    early_withdrawal_penalties: Optional[str] = None
    contribution_limits: Optional[str] = None
    rmd_requirements: Optional[str] = None  # Required Minimum Distributions
    specialized_rules: Optional[List[str]] = None
    updated_date: str
    source: Optional[str] = None
    knowledge_category: str = KnowledgeCategory.TAX_RULES


class DividendTaxation(BaseModel):
    """Taxation details for different dividend types."""
    dividend_type: str  # e.g., "Qualified", "Non-qualified"
    description: str
    tax_rates: Dict[str, str]  # Income bracket to rate mapping
    holding_period_requirements: Optional[str] = None
    fund_type_considerations: Dict[str, str]
    updated_date: str
    source: Optional[str] = None
    knowledge_category: str = KnowledgeCategory.TAX_RULES


class UserFinancialProfile(BaseModel):
    """User financial profile details."""
    user_id: str
    risk_tolerance: RiskTolerance
    time_horizon: TimeHorizon
    age: Optional[int] = None
    retirement_age: Optional[int] = None
    annual_income: Optional[float] = None
    liquid_assets: Optional[float] = None
    investment_goals: List[str]
    existing_holdings: Optional[Dict[str, float]] = None  # Asset to allocation mapping
    tax_bracket: Optional[str] = None
    account_types: Optional[List[str]] = None
    special_considerations: Optional[List[str]] = None
    debt_obligations: Optional[Dict[str, float]] = None
    updated_date: str
    knowledge_category: str = KnowledgeCategory.USER_PROFILE


class MarketDataPoint(BaseModel):
    """Data point for real-time market data."""
    timestamp: str
    symbol: str
    price: float
    price_change: float
    price_change_percent: float
    volume: Optional[int] = None
    volume_change_percent: Optional[float] = None
    rsi_14d: Optional[float] = None  # Relative Strength Index
    volatility_30d: Optional[float] = None
    unusual_volume: bool = False
    source: str
    knowledge_category: str = KnowledgeCategory.MARKET_DATA


class SectorPerformance(BaseModel):
    """Performance data for market sectors."""
    timestamp: str
    sector: str  # Corresponds to SectorExposure fields
    daily_return: float
    weekly_return: Optional[float] = None
    monthly_return: Optional[float] = None
    ytd_return: Optional[float] = None
    relative_strength: Optional[float] = None  # Compared to broader market
    source: str
    knowledge_category: str = KnowledgeCategory.MARKET_DATA


class EconomicIndicator(BaseModel):
    """Economic indicator data point."""
    timestamp: str
    name: str  # e.g., "Interest Rate", "CPI", "Unemployment"
    value: float
    previous_value: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    forecast_value: Optional[float] = None
    surprise: Optional[float] = None  # Difference from forecast
    impact: Optional[str] = None  # "high", "medium", "low"
    source: str
    knowledge_category: str = KnowledgeCategory.ECONOMIC_INDICATORS
    

class YieldCurvePoint(BaseModel):
    """Data point for yield curve analysis."""
    timestamp: str
    maturity: str  # e.g., "3M", "1Y", "5Y", "10Y", "30Y"
    yield_value: float
    previous_yield: Optional[float] = None
    change: Optional[float] = None
    source: str
    knowledge_category: str = KnowledgeCategory.ECONOMIC_INDICATORS


class FinancialNews(BaseModel):
    """Financial news item with sentiment analysis."""
    timestamp: str
    headline: str
    summary: str
    full_text: Optional[str] = None
    source: str
    url: Optional[str] = None
    sentiment_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    relevance_score: Optional[float] = None  # 0.0 to 1.0
    entities: Optional[List[Dict[str, Any]]] = None  # Companies, people, etc.
    categories: Optional[List[str]] = None  # "earnings", "macro", "merger", etc.
    knowledge_category: str = KnowledgeCategory.MARKET_DATA


class PortfolioStatus(BaseModel):
    """Current portfolio status and metrics."""
    timestamp: str
    user_id: str
    portfolio_value: float
    cash_balance: float
    daily_change: float
    daily_change_percent: float
    ytd_return: Optional[float] = None
    asset_allocation: Dict[str, float]  # Asset class to percentage
    sector_allocation: Dict[str, float]  # Sector to percentage
    target_drift: Dict[str, float]  # Asset class to drift percentage
    tax_loss_opportunities: Optional[List[Dict[str, Any]]] = None
    upcoming_dividends: Optional[List[Dict[str, Any]]] = None
    tracking_error: Optional[float] = None
    knowledge_category: str = KnowledgeCategory.USER_PROFILE


class KnowledgeItem(BaseModel):
    """Generic knowledge item for storage in vector database."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    vector_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True 