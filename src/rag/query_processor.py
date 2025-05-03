"""
Query Processing Module for RAG System.

This module is responsible for:
1. Query understanding/classification
2. Query expansion
3. Supporting different question types
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import os
from dotenv import load_dotenv

load_dotenv()

class QueryType(Enum):
    """Types of queries that the system can handle."""
    FUND_COMPARISON = "fund_comparison"  # Compare multiple funds
    FUND_INFO = "fund_info"  # Information about a specific fund
    TAX_QUESTION = "tax_question"  # Tax-related questions
    INVESTMENT_STRATEGY = "investment_strategy"  # Investment strategy questions
    MARKET_TREND = "market_trend"  # Market trend questions
    GENERAL = "general"  # General investment questions


class QueryProcessor:
    """
    Processes user queries to enhance retrieval quality.
    
    This class is responsible for:
    1. Classifying the query type
    2. Expanding the query to improve retrieval
    3. Extracting entities like fund tickers, time periods, etc.
    """
    
    def __init__(self):
        """Initialize the query processor."""
        # Common fund tickers pattern
        self.ticker_pattern = r'\b[A-Z]{2,5}\b'
        
        # Keyword patterns for query classification
        self.classification_patterns = {
            QueryType.FUND_COMPARISON: r'\b(compar(e|ing|ison)|vs|versus|better|between|difference)\b',
            QueryType.FUND_INFO: r'\b(what is|tell me about|details|info|information about|describe|buy|sell|invest in|more|purchase|add|reduce|increase|decrease)\b',
            QueryType.TAX_QUESTION: r'\b(tax|taxes|taxation|taxable|tax-advantaged|capital gain|dividend|distribution)\b',
            QueryType.INVESTMENT_STRATEGY: r'\b(strategy|allocation|portfolio|diversif|rebalance|invest|risk|time horizon)\b',
            QueryType.MARKET_TREND: r'\b(trend|market|economy|recession|inflation|rate|yield|curve|forecast|outlook)\b'
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query to enhance retrieval.
        
        Args:
            query: The raw user query
            
        Returns:
            Dict containing processed query information:
            - cleaned_query: The cleaned query text
            - query_type: The classified query type
            - expanded_query: An expanded version of the query
            - entities: Extracted entities (tickers, etc.)
            - metadata_filters: Any filters to apply to the retrieval
        """
        # Clean the query
        cleaned_query = self._clean_query(query)
        
        # Classify the query type
        query_type = self._classify_query(cleaned_query)
        
        # Extract entities
        entities = self._extract_entities(cleaned_query)
        
        # Expand the query
        expanded_query = self._expand_query(cleaned_query, query_type, entities)
        
        # Generate metadata filters based on query type and entities
        metadata_filters = self._generate_metadata_filters(query_type, entities)
        
        return {
            "original_query": query,
            "cleaned_query": cleaned_query,
            "query_type": query_type,
            "expanded_query": expanded_query,
            "entities": entities,
            "metadata_filters": metadata_filters
        }
    
    def _clean_query(self, query: str) -> str:
        """
        Clean the query by removing extra whitespace and normalizing punctuation.
        
        Args:
            query: The raw user query
            
        Returns:
            The cleaned query
        """
        # Convert to lowercase
        cleaned = query.lower()
        
        # Replace multiple spaces with a single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _classify_query(self, query: str) -> QueryType:
        """
        Classify the query type based on keywords and patterns.
        
        Args:
            query: The cleaned user query
            
        Returns:
            The query type
        """
        for query_type, pattern in self.classification_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return query_type
        
        # Default to general if no specific type is matched
        return QueryType.GENERAL
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract entities from the query, such as fund tickers, time periods, etc.
        
        Args:
            query: The cleaned user query
            
        Returns:
            Dict of extracted entities by type
        """
        entities = {
            "tickers": [],
            "time_periods": [],
            "asset_classes": []
        }
        
        # Extract fund tickers (uppercase 2-5 letters)
        tickers = re.findall(self.ticker_pattern, query.upper())
        
        # Filter out common words that match the ticker pattern
        ticker_stopwords = {"BUY", "MORE", "SELL", "FOR", "THE", "AND", "ETF", "FUND"}
        real_tickers = [ticker for ticker in tickers if ticker not in ticker_stopwords]
        
        if real_tickers:
            entities["tickers"] = real_tickers
        
        # Extract time periods (simple regex patterns)
        time_patterns = [
            (r'\b\d+ year(s)?\b', 'years'),
            (r'\b\d+ month(s)?\b', 'months'),
            (r'\blong[ -]term\b', 'long-term'),
            (r'\bshort[ -]term\b', 'short-term'),
            (r'\bmedium[ -]term\b', 'medium-term'),
        ]
        
        for pattern, period_type in time_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                entities["time_periods"].append(period_type)
        
        # Extract asset classes
        asset_classes = [
            'equity', 'stock', 'bond', 'fixed income', 'commodity', 
            'real estate', 'reit', 'international', 'emerging market',
            'small cap', 'mid cap', 'large cap'
        ]
        
        for asset_class in asset_classes:
            if asset_class in query.lower():
                entities["asset_classes"].append(asset_class)
        
        return entities
    
    def _expand_query(self, query: str, query_type: QueryType, entities: Dict[str, List[str]]) -> str:
        """
        Expand the query with additional terms based on the query type and entities.
        
        Args:
            query: The cleaned user query
            query_type: The classified query type
            entities: Extracted entities from the query
            
        Returns:
            The expanded query
        """
        expansions = []
        
        # Add type-specific expansions
        if query_type == QueryType.FUND_COMPARISON:
            expansions.append("comparison difference similarities differences")
            if entities["tickers"]:
                for ticker in entities["tickers"]:
                    expansions.append(f"{ticker} etf index fund")
        
        elif query_type == QueryType.FUND_INFO:
            if entities["tickers"]:
                for ticker in entities["tickers"]:
                    expansions.append(f"{ticker} fund etf details information expense ratio tracking error")
        
        elif query_type == QueryType.TAX_QUESTION:
            expansions.append("tax implications tax efficiency tax treatment capital gains dividends distributions")
        
        elif query_type == QueryType.INVESTMENT_STRATEGY:
            expansions.append("investment strategy portfolio allocation asset allocation risk management diversification")
            if entities["time_periods"]:
                time_period = " ".join(entities["time_periods"])
                expansions.append(f"{time_period} time horizon investment period")
        
        elif query_type == QueryType.MARKET_TREND:
            expansions.append("market trends economic indicators outlook forecast predictions")
        
        # Combine original query with expansions
        expanded_query = f"{query} {' '.join(expansions)}"
        
        return expanded_query
    
    def _generate_metadata_filters(self, query_type: QueryType, entities: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
        """
        Generate metadata filters for vector database retrieval based on query type and entities.
        
        Args:
            query_type: The classified query type
            entities: Extracted entities from the query
            
        Returns:
            Optional dictionary of metadata filters
        """
        filters = {}
        
        # Add category filters based on query type
        if query_type == QueryType.FUND_INFO or query_type == QueryType.FUND_COMPARISON:
            filters["category"] = "fund_knowledge"
        elif query_type == QueryType.TAX_QUESTION:
            filters["category"] = "regulatory_tax"
        elif query_type == QueryType.INVESTMENT_STRATEGY:
            filters["category"] = "investment_principles"
        elif query_type == QueryType.MARKET_TREND:
            filters["category"] = "market_patterns"
        
        # Add entity-based filters
        if entities.get("tickers"):
            # Handle tickers in all query types, not just FUND_INFO
            if len(entities["tickers"]) == 1:
                filters["fund_ticker"] = entities["tickers"][0]
                
        # Special case for US-based tax questions
        if query_type == QueryType.TAX_QUESTION and "us" in entities:
            filters["jurisdiction"] = "United States"
        
        return filters if filters else None 