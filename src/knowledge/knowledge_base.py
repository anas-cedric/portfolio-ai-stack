"""
Knowledge base management for financial data.

This module provides functionality for creating, managing, and querying
a comprehensive financial knowledge base including fund metadata, investment principles,
regulatory frameworks, and user profiles.
"""

import os
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple, Type
from datetime import datetime

from src.knowledge.schema import (
    KnowledgeCategory, 
    KnowledgeItem,
    FundMetadata, 
    InvestmentPrinciple,
    AssetCorrelation,
    RiskReturnProfile,
    TaxRule,
    AccountTypeTaxation,
    DividendTaxation,
    UserFinancialProfile,
    MarketDataPoint,
    SectorPerformance,
    EconomicIndicator,
    YieldCurvePoint,
    FinancialNews,
    PortfolioStatus
)
from src.knowledge.embedding import get_embedding_client
from src.knowledge.vector_store import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Comprehensive financial knowledge base manager.
    
    This class provides methods for adding, retrieving, and managing various types
    of financial knowledge, including fund metadata, investment principles,
    regulatory frameworks, and user profiles.
    """
    
    def __init__(
        self,
        embedding_client_type: str = "voyage",
        vector_db_manager: Optional[PineconeManager] = None,
        namespace: str = "financial_knowledge",
    ):
        """
        Initialize the knowledge base.
        
        Args:
            embedding_client_type: Type of embedding client to use
            vector_db_manager: Optional pre-configured vector DB manager
            namespace: Namespace for the knowledge base in the vector DB
        """
        self.embedding_client = get_embedding_client(embedding_client_type)
        self.vector_db = vector_db_manager or PineconeManager()
        self.namespace = namespace
        
        # Stats tracking
        self.stats = {
            "items_added": 0,
            "items_retrieved": 0,
            "items_by_category": {cat.value: 0 for cat in KnowledgeCategory},
            "last_updated": None
        }
        
        logger.info(f"Initialized KnowledgeBase with {embedding_client_type} embeddings")

    def _create_knowledge_item(
        self,
        content: str,
        metadata: Dict[str, Any],
        id_prefix: str = ""
    ) -> KnowledgeItem:
        """
        Create a knowledge item with embedded vector.
        
        Args:
            content: The text content of the item
            metadata: Metadata for the item
            id_prefix: Optional prefix for the ID
            
        Returns:
            A KnowledgeItem with embedded vector
        """
        item_id = f"{id_prefix}{uuid.uuid4()}"
        
        # Generate embedding for the content
        embedding = self.embedding_client.embed_text(content)
        
        # Create the knowledge item
        knowledge_item = KnowledgeItem(
            id=item_id,
            content=content,
            metadata=metadata,
            embedding=embedding
        )
        
        return knowledge_item

    def _store_knowledge_item(self, item: KnowledgeItem) -> str:
        """
        Store a knowledge item in the vector database.
        
        Args:
            item: The knowledge item to store
            
        Returns:
            The ID of the stored item
        """
        # Store in vector database
        vector_id = self.vector_db.upsert_vectors(
            vectors=[item.embedding],
            metadata=[item.metadata],
            ids=[item.id]
        )
        
        # Update stats
        self.stats["items_added"] += 1
        category = item.metadata.get("knowledge_category")
        if category and category in self.stats["items_by_category"]:
            self.stats["items_by_category"][category] += 1
        self.stats["last_updated"] = datetime.now().isoformat()
        
        logger.info(f"Added knowledge item: {item.id} ({item.metadata.get('knowledge_category')})")
        
        return item.id

    def add_fund_metadata(self, fund: FundMetadata) -> str:
        """
        Add fund metadata to the knowledge base.
        
        Args:
            fund: The fund metadata to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the fund metadata
        content = (
            f"Fund Metadata for {fund.ticker} - {fund.name}\n\n"
            f"Fund Type: {fund.fund_type}\n"
            f"Asset Type: {fund.asset_type}\n"
            f"Investment Style: {fund.investment_style or 'N/A'}\n"
            f"Expense Ratio: {fund.expense_ratio}%\n"
            f"Inception Date: {fund.inception_date}\n"
            f"AUM: ${fund.aum} million\n"
            f"Provider: {fund.provider}\n"
            f"Description: {fund.description or 'N/A'}\n"
        )
        
        # Add sector exposure if available
        if fund.sector_exposure:
            content += "\nSector Exposure:\n"
            for sector, weight in fund.sector_exposure.dict().items():
                if weight > 0:
                    content += f"- {sector.replace('_', ' ').title()}: {weight:.2f}%\n"
        
        # Add geographic exposure if available
        if fund.geographic_exposure:
            content += "\nGeographic Exposure:\n"
            for region, weight in fund.geographic_exposure.dict().items():
                if weight > 0:
                    content += f"- {region.replace('_', ' ').title()}: {weight:.2f}%\n"
        
        # Add performance metrics if available
        if fund.performance:
            content += "\nPerformance Metrics:\n"
            perf_dict = fund.performance.dict()
            for metric, value in perf_dict.items():
                if value is not None:
                    metric_name = metric.replace('_', ' ').title()
                    content += f"- {metric_name}: {value}\n"
        
        # Convert FundMetadata to a KnowledgeItem
        metadata = {
            "knowledge_category": KnowledgeCategory.FUND_METADATA.value,
            "ticker": fund.ticker,
            "name": fund.name,
            "fund_type": fund.fund_type.value,
            "asset_type": fund.asset_type.value,
            "expense_ratio": fund.expense_ratio,
            "provider": fund.provider,
            "aum": fund.aum
        }
        
        if fund.investment_style:
            metadata["investment_style"] = fund.investment_style.value
            
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="fund_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)

    def add_investment_principle(self, principle: InvestmentPrinciple) -> str:
        """
        Add investment principle to the knowledge base.
        
        Args:
            principle: The investment principle to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the investment principle
        content = (
            f"{principle.title}\n\n"
            f"Type: {principle.principle_type}\n\n"
            f"{principle.description}\n\n"
            f"Key Concepts:\n"
        )
        
        for concept in principle.key_concepts:
            content += f"- {concept}\n"
        
        content += "\nPractical Applications:\n"
        for application in principle.practical_applications:
            content += f"- {application}\n"
        
        if principle.additional_resources:
            content += "\nAdditional Resources:\n"
            for resource in principle.additional_resources:
                content += f"- {resource}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.INVESTMENT_PRINCIPLES.value,
            "title": principle.title,
            "principle_type": principle.principle_type,
            "source": principle.source
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="principle_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)

    def add_asset_correlation(self, correlation: AssetCorrelation) -> str:
        """
        Add asset correlation data to the knowledge base.
        
        Args:
            correlation: The asset correlation data to add
            
        Returns:
            The ID of the stored item
        """
        # Create content for the correlation matrix
        content = f"Asset Correlation Matrix ({correlation.time_period})\n\n"
        
        # Add correlation matrix
        content += "Correlation Matrix:\n"
        # Header row
        content += "Asset Class"
        for asset_class in correlation.asset_classes:
            content += f" | {asset_class}"
        content += "\n"
        
        # Add divider
        content += "-" * (len(content.split("\n")[-2])) + "\n"
        
        # Data rows
        for i, asset_class in enumerate(correlation.asset_classes):
            row = asset_class
            for j in range(len(correlation.asset_classes)):
                row += f" | {correlation.correlation_matrix[i][j]:.2f}"
            content += row + "\n"
        
        # Add source and date
        if correlation.source:
            content += f"\nSource: {correlation.source}\n"
        content += f"Updated: {correlation.updated_date}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.INVESTMENT_PRINCIPLES.value,
            "type": "asset_correlation",
            "time_period": correlation.time_period,
            "asset_classes": correlation.asset_classes,
            "updated_date": correlation.updated_date,
            "source": correlation.source
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="correlation_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)

    def add_risk_return_profile(self, profile: RiskReturnProfile) -> str:
        """
        Add risk-return profile to the knowledge base.
        
        Args:
            profile: The risk-return profile to add
            
        Returns:
            The ID of the stored item
        """
        # Create content for the risk-return profile
        content = (
            f"Risk-Return Profile: {profile.asset_class}\n\n"
            f"Time Period: {profile.time_period}\n"
            f"Expected Return: {profile.expected_return:.2f}%\n"
            f"Standard Deviation (Risk): {profile.standard_deviation:.2f}%\n"
        )
        
        if profile.sharpe_ratio:
            content += f"Sharpe Ratio: {profile.sharpe_ratio:.2f}\n"
        
        if profile.source:
            content += f"\nSource: {profile.source}\n"
        
        content += f"Updated: {profile.updated_date}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.INVESTMENT_PRINCIPLES.value,
            "type": "risk_return_profile",
            "asset_class": profile.asset_class,
            "time_period": profile.time_period,
            "expected_return": profile.expected_return,
            "standard_deviation": profile.standard_deviation,
            "updated_date": profile.updated_date,
            "source": profile.source
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="risk_return_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)

    def add_tax_rule(self, rule: TaxRule) -> str:
        """
        Add tax rule to the knowledge base.
        
        Args:
            rule: The tax rule to add
            
        Returns:
            The ID of the stored item
        """
        # Create content for the tax rule
        content = (
            f"Tax Rule: {rule.title}\n\n"
            f"Type: {rule.rule_type}\n\n"
            f"{rule.description}\n\n"
            f"Key Considerations:\n"
        )
        
        for consideration in rule.considerations:
            content += f"- {consideration}\n"
        
        if rule.exceptions:
            content += "\nExceptions:\n"
            for exception in rule.exceptions:
                content += f"- {exception}\n"
        
        content += "\nRelevant Account Types:\n"
        for account_type in rule.relevant_account_types:
            content += f"- {account_type}\n"
        
        if rule.source:
            content += f"\nSource: {rule.source}\n"
        
        content += f"Updated: {rule.updated_date}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.TAX_RULES.value,
            "title": rule.title,
            "rule_type": rule.rule_type,
            "relevant_account_types": rule.relevant_account_types,
            "updated_date": rule.updated_date,
            "source": rule.source
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="tax_rule_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)

    def add_account_taxation(self, account_tax: AccountTypeTaxation) -> str:
        """
        Add account taxation details to the knowledge base.
        
        Args:
            account_tax: The account taxation details to add
            
        Returns:
            The ID of the stored item
        """
        # Create content for the account taxation
        content = (
            f"Account Type Taxation: {account_tax.account_type}\n\n"
            f"Taxability: {account_tax.taxability.value}\n"
            f"Contribution Tax Treatment: {account_tax.contribution_tax_treatment}\n"
            f"Withdrawal Tax Treatment: {account_tax.withdrawal_tax_treatment}\n"
        )
        
        if account_tax.early_withdrawal_penalties:
            content += f"Early Withdrawal Penalties: {account_tax.early_withdrawal_penalties}\n"
        
        if account_tax.contribution_limits:
            content += f"Contribution Limits: {account_tax.contribution_limits}\n"
        
        if account_tax.rmd_requirements:
            content += f"Required Minimum Distributions: {account_tax.rmd_requirements}\n"
        
        if account_tax.specialized_rules:
            content += "\nSpecialized Rules:\n"
            for rule in account_tax.specialized_rules:
                content += f"- {rule}\n"
        
        if account_tax.source:
            content += f"\nSource: {account_tax.source}\n"
        
        content += f"Updated: {account_tax.updated_date}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.TAX_RULES.value,
            "type": "account_taxation",
            "account_type": account_tax.account_type,
            "taxability": account_tax.taxability.value,
            "updated_date": account_tax.updated_date,
            "source": account_tax.source
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="account_tax_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)

    def add_dividend_taxation(self, dividend_tax: DividendTaxation) -> str:
        """
        Add dividend taxation details to the knowledge base.
        
        Args:
            dividend_tax: The dividend taxation details to add
            
        Returns:
            The ID of the stored item
        """
        # Create content for the dividend taxation
        content = (
            f"Dividend Taxation: {dividend_tax.dividend_type}\n\n"
            f"{dividend_tax.description}\n\n"
            f"Tax Rates by Income Bracket:\n"
        )
        
        for bracket, rate in dividend_tax.tax_rates.items():
            content += f"- {bracket}: {rate}\n"
        
        if dividend_tax.holding_period_requirements:
            content += f"\nHolding Period Requirements:\n{dividend_tax.holding_period_requirements}\n"
        
        content += "\nConsiderations by Fund Type:\n"
        for fund_type, consideration in dividend_tax.fund_type_considerations.items():
            content += f"- {fund_type}: {consideration}\n"
        
        if dividend_tax.source:
            content += f"\nSource: {dividend_tax.source}\n"
        
        content += f"Updated: {dividend_tax.updated_date}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.TAX_RULES.value,
            "type": "dividend_taxation",
            "dividend_type": dividend_tax.dividend_type,
            "updated_date": dividend_tax.updated_date,
            "source": dividend_tax.source
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="dividend_tax_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)
    
    def add_user_profile(self, profile: UserFinancialProfile) -> str:
        """
        Add user financial profile to the knowledge base.
        
        Args:
            profile: The user financial profile to add
            
        Returns:
            The ID of the stored item
        """
        # Create content for the user profile
        content = (
            f"User Financial Profile: {profile.user_id}\n\n"
            f"Risk Tolerance: {profile.risk_tolerance.value}\n"
            f"Time Horizon: {profile.time_horizon.value}\n"
        )
        
        if profile.age:
            content += f"Age: {profile.age}\n"
        
        if profile.retirement_age:
            content += f"Retirement Age: {profile.retirement_age}\n"
        
        if profile.annual_income:
            content += f"Annual Income: ${profile.annual_income:,.2f}\n"
        
        if profile.liquid_assets:
            content += f"Liquid Assets: ${profile.liquid_assets:,.2f}\n"
        
        content += "\nInvestment Goals:\n"
        for goal in profile.investment_goals:
            content += f"- {goal}\n"
        
        if profile.existing_holdings:
            content += "\nExisting Holdings:\n"
            for asset, allocation in profile.existing_holdings.items():
                content += f"- {asset}: {allocation:.2f}%\n"
        
        if profile.tax_bracket:
            content += f"\nTax Bracket: {profile.tax_bracket}\n"
        
        if profile.account_types:
            content += "\nAccount Types:\n"
            for account_type in profile.account_types:
                content += f"- {account_type}\n"
        
        if profile.special_considerations:
            content += "\nSpecial Considerations:\n"
            for consideration in profile.special_considerations:
                content += f"- {consideration}\n"
        
        if profile.debt_obligations:
            content += "\nDebt Obligations:\n"
            for debt_type, amount in profile.debt_obligations.items():
                content += f"- {debt_type}: ${amount:,.2f}\n"
        
        content += f"\nUpdated: {profile.updated_date}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.USER_PROFILE.value,
            "user_id": profile.user_id,
            "risk_tolerance": profile.risk_tolerance.value,
            "time_horizon": profile.time_horizon.value,
            "investment_goals": profile.investment_goals,
            "updated_date": profile.updated_date
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="user_profile_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)

    def query_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        knowledge_category: Optional[KnowledgeCategory] = None,
        additional_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base for relevant information.
        
        Args:
            query: The query string
            top_k: Number of results to return
            knowledge_category: Optional category to filter by
            additional_filters: Additional filter criteria
            
        Returns:
            List of matching knowledge items with their content and metadata
        """
        # Generate embedding for the query
        query_embedding = self.embedding_client.embed_text(query)
        
        # Prepare filters
        filters = {}
        if knowledge_category:
            filters["knowledge_category"] = knowledge_category.value
        
        if additional_filters:
            filters.update(additional_filters)
        
        # Query the vector database
        results = self.vector_db.query(
            query_vector=query_embedding,
            top_k=top_k,
            filter=filters if filters else None,
            namespace=self.namespace
        )
        
        # Format the results
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.id,
                "score": result.score,
                "content": result.metadata.get("content", ""),
                "metadata": {k: v for k, v in result.metadata.items() if k != "content"}
            }
            formatted_results.append(formatted_result)
        
        # Update stats
        self.stats["items_retrieved"] += len(formatted_results)
        
        return formatted_results
    
    def search_by_field(
        self,
        field_name: str,
        field_value: Any,
        top_k: int = 5,
        knowledge_category: Optional[KnowledgeCategory] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge items by a specific field value.
        
        Args:
            field_name: Name of the field to search
            field_value: Value to match
            top_k: Number of results to return
            knowledge_category: Optional category to filter by
            
        Returns:
            List of matching knowledge items
        """
        # Prepare filters
        filters = {field_name: field_value}
        if knowledge_category:
            filters["knowledge_category"] = knowledge_category.value
        
        # Query the vector database
        results = self.vector_db.list_items(
            filter=filters,
            limit=top_k,
            namespace=self.namespace
        )
        
        # Format the results
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.id,
                "content": result.metadata.get("content", ""),
                "metadata": {k: v for k, v in result.metadata.items() if k != "content"}
            }
            formatted_results.append(formatted_result)
        
        # Update stats
        self.stats["items_retrieved"] += len(formatted_results)
        
        return formatted_results
    
    def get_all_by_category(
        self, 
        category: KnowledgeCategory,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all knowledge items by category.
        
        Args:
            category: The knowledge category to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of knowledge items in the specified category
        """
        # Prepare filters
        filters = {"knowledge_category": category.value}
        
        # Query the vector database
        results = self.vector_db.list_items(
            filter=filters,
            limit=limit,
            namespace=self.namespace
        )
        
        # Format the results
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.id,
                "content": result.metadata.get("content", ""),
                "metadata": {k: v for k, v in result.metadata.items() if k != "content"}
            }
            formatted_results.append(formatted_result)
        
        # Update stats
        self.stats["items_retrieved"] += len(formatted_results)
        
        return formatted_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary of statistics
        """
        return self.stats
    
    # Real-Time Input Methods
    
    def add_market_data_point(self, data_point: MarketDataPoint) -> str:
        """
        Add a market data point to the knowledge base.
        
        Args:
            data_point: The market data point to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the market data point
        content = (
            f"Market Data for {data_point.symbol}\n\n"
            f"Timestamp: {data_point.timestamp}\n"
            f"Price: ${data_point.price:.2f}\n"
            f"Change: ${data_point.price_change:.2f} ({data_point.price_change_percent:.2f}%)\n"
        )
        
        if data_point.volume is not None:
            content += f"Volume: {data_point.volume:,}\n"
            
            if data_point.volume_change_percent is not None:
                content += f"Volume Change: {data_point.volume_change_percent:.2f}%\n"
                
        if data_point.rsi_14d is not None:
            content += f"RSI (14d): {data_point.rsi_14d:.2f}\n"
            
        if data_point.volatility_30d is not None:
            content += f"30-Day Volatility: {data_point.volatility_30d:.2f}%\n"
            
        if data_point.unusual_volume:
            content += "Unusual Volume: Yes\n"
            
        content += f"Source: {data_point.source}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.MARKET_DATA.value,
            "symbol": data_point.symbol,
            "price": data_point.price,
            "price_change_percent": data_point.price_change_percent,
            "timestamp": data_point.timestamp,
            "unusual_volume": data_point.unusual_volume,
            "source": data_point.source
        }
        
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="market_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)
    
    def add_sector_performance(self, performance: SectorPerformance) -> str:
        """
        Add sector performance data to the knowledge base.
        
        Args:
            performance: The sector performance data to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the sector performance data
        content = (
            f"Sector Performance: {performance.sector.replace('_', ' ').title()}\n\n"
            f"Timestamp: {performance.timestamp}\n"
            f"Daily Return: {performance.daily_return:.2f}%\n"
        )
        
        if performance.weekly_return is not None:
            content += f"Weekly Return: {performance.weekly_return:.2f}%\n"
            
        if performance.monthly_return is not None:
            content += f"Monthly Return: {performance.monthly_return:.2f}%\n"
            
        if performance.ytd_return is not None:
            content += f"YTD Return: {performance.ytd_return:.2f}%\n"
            
        if performance.relative_strength is not None:
            content += f"Relative Strength: {performance.relative_strength:.2f}\n"
            
        content += f"Source: {performance.source}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.MARKET_DATA.value,
            "sector": performance.sector,
            "daily_return": performance.daily_return,
            "timestamp": performance.timestamp,
            "source": performance.source
        }
        
        if performance.relative_strength is not None:
            metadata["relative_strength"] = performance.relative_strength
            
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="sector_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)
    
    def add_economic_indicator(self, indicator: EconomicIndicator) -> str:
        """
        Add economic indicator data to the knowledge base.
        
        Args:
            indicator: The economic indicator data to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the economic indicator
        content = (
            f"Economic Indicator: {indicator.name}\n\n"
            f"Timestamp: {indicator.timestamp}\n"
            f"Value: {indicator.value}\n"
        )
        
        if indicator.previous_value is not None:
            content += f"Previous Value: {indicator.previous_value}\n"
            
        if indicator.change is not None:
            content += f"Change: {indicator.change}\n"
            
        if indicator.change_percent is not None:
            content += f"Change Percent: {indicator.change_percent:.2f}%\n"
            
        if indicator.forecast_value is not None:
            content += f"Forecast: {indicator.forecast_value}\n"
            
        if indicator.surprise is not None:
            content += f"Surprise: {indicator.surprise}\n"
            
        if indicator.impact is not None:
            content += f"Impact: {indicator.impact.title()}\n"
            
        content += f"Source: {indicator.source}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.ECONOMIC_INDICATORS.value,
            "name": indicator.name,
            "value": indicator.value,
            "timestamp": indicator.timestamp,
            "source": indicator.source
        }
        
        if indicator.impact is not None:
            metadata["impact"] = indicator.impact
            
        if indicator.change_percent is not None:
            metadata["change_percent"] = indicator.change_percent
            
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="economic_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)
    
    def add_yield_curve_point(self, yield_point: YieldCurvePoint) -> str:
        """
        Add yield curve data point to the knowledge base.
        
        Args:
            yield_point: The yield curve data point to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the yield curve point
        content = (
            f"Yield Curve Point: {yield_point.maturity}\n\n"
            f"Timestamp: {yield_point.timestamp}\n"
            f"Yield: {yield_point.yield_value:.2f}%\n"
        )
        
        if yield_point.previous_yield is not None:
            content += f"Previous Yield: {yield_point.previous_yield:.2f}%\n"
            
        if yield_point.change is not None:
            content += f"Change: {yield_point.change:.3f}%\n"
            
        content += f"Source: {yield_point.source}\n"
        
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.ECONOMIC_INDICATORS.value,
            "maturity": yield_point.maturity,
            "yield_value": yield_point.yield_value,
            "timestamp": yield_point.timestamp,
            "source": yield_point.source
        }
        
        if yield_point.change is not None:
            metadata["change"] = yield_point.change
            
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="yield_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)
    
    def add_financial_news(self, news: FinancialNews) -> str:
        """
        Add financial news to the knowledge base.
        
        Args:
            news: The financial news to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the financial news
        content = (
            f"{news.headline}\n\n"
            f"Timestamp: {news.timestamp}\n"
            f"Summary: {news.summary}\n"
        )
        
        if news.full_text:
            # Truncate full text if it's very long
            full_text = news.full_text
            if len(full_text) > 1000:
                full_text = full_text[:997] + "..."
            content += f"Full Text: {full_text}\n"
            
        content += f"Source: {news.source}\n"
        
        if news.url:
            content += f"URL: {news.url}\n"
            
        content += f"Sentiment Score: {news.sentiment_score:.2f} (Confidence: {news.confidence:.2f})\n"
        
        if news.relevance_score is not None:
            content += f"Relevance: {news.relevance_score:.2f}\n"
            
        if news.entities:
            content += "Entities:\n"
            for entity in news.entities[:5]:  # Limit to first 5 entities
                entity_type = entity.get("type", "Unknown")
                entity_name = entity.get("name", "Unknown")
                content += f"- {entity_name} ({entity_type})\n"
                
        if news.categories:
            content += "Categories: " + ", ".join(news.categories) + "\n"
            
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.MARKET_DATA.value,
            "headline": news.headline,
            "source": news.source,
            "timestamp": news.timestamp,
            "sentiment_score": news.sentiment_score,
            "confidence": news.confidence
        }
        
        if news.categories:
            metadata["categories"] = news.categories
            
        if news.entities:
            entity_names = [e.get("name") for e in news.entities if "name" in e]
            if entity_names:
                metadata["entities"] = entity_names[:10]  # Limit to 10 entities
            
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="news_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item)
    
    def add_portfolio_status(self, status: PortfolioStatus) -> str:
        """
        Add portfolio status to the knowledge base.
        
        Args:
            status: The portfolio status to add
            
        Returns:
            The ID of the stored item
        """
        # Create content from the portfolio status
        content = (
            f"Portfolio Status for User {status.user_id}\n\n"
            f"Timestamp: {status.timestamp}\n"
            f"Portfolio Value: ${status.portfolio_value:,.2f}\n"
            f"Cash Balance: ${status.cash_balance:,.2f}\n"
            f"Daily Change: ${status.daily_change:,.2f} ({status.daily_change_percent:.2f}%)\n"
        )
        
        if status.ytd_return is not None:
            content += f"YTD Return: {status.ytd_return:.2f}%\n"
            
        content += "\nAsset Allocation:\n"
        for asset_class, allocation in status.asset_allocation.items():
            content += f"- {asset_class.replace('_', ' ').title()}: {allocation:.2f}%\n"
            
        content += "\nSector Allocation:\n"
        for sector, allocation in status.sector_allocation.items():
            content += f"- {sector.replace('_', ' ').title()}: {allocation:.2f}%\n"
            
        content += "\nTarget Drift:\n"
        for asset_class, drift in status.target_drift.items():
            content += f"- {asset_class.replace('_', ' ').title()}: {drift:+.2f}%\n"
            
        if status.tax_loss_opportunities:
            content += "\nTax Loss Opportunities:\n"
            for opportunity in status.tax_loss_opportunities[:5]:  # Limit to 5
                symbol = opportunity.get("symbol", "Unknown")
                loss = opportunity.get("unrealized_loss", 0)
                content += f"- {symbol}: ${loss:,.2f}\n"
                
        if status.upcoming_dividends:
            content += "\nUpcoming Dividends:\n"
            for dividend in status.upcoming_dividends[:5]:  # Limit to 5
                symbol = dividend.get("symbol", "Unknown")
                amount = dividend.get("amount", 0)
                date = dividend.get("ex_date", "Unknown")
                content += f"- {symbol}: ${amount:.2f} (Ex-Date: {date})\n"
                
        if status.tracking_error is not None:
            content += f"\nTracking Error: {status.tracking_error:.2f}%\n"
            
        # Create metadata
        metadata = {
            "knowledge_category": KnowledgeCategory.USER_PROFILE.value,
            "user_id": status.user_id,
            "portfolio_value": status.portfolio_value,
            "timestamp": status.timestamp,
            "daily_change_percent": status.daily_change_percent,
        }
        
        if status.ytd_return is not None:
            metadata["ytd_return"] = status.ytd_return
            
        # Add simplified asset allocation for filtering
        top_assets = sorted(status.asset_allocation.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_assets:
            metadata["top_asset_classes"] = [asset[0] for asset in top_assets]
            
        # Add target drift signals
        drift_signals = [asset for asset, drift in status.target_drift.items() if abs(drift) > 5.0]
        if drift_signals:
            metadata["significant_drift"] = drift_signals
            
        # Create knowledge item
        knowledge_item = self._create_knowledge_item(content, metadata, id_prefix="portfolio_")
        
        # Store in vector DB
        return self._store_knowledge_item(knowledge_item) 