"""
Context Retrieval System for Financial Data.

This module provides a comprehensive system for retrieving relevant financial contexts
from multiple sources, including vector databases, market data APIs, and user-specific data.
"""

import os
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Union, TypedDict

from src.rag.rag_system import RAGSystem
from src.knowledge.vector_store import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context that can be retrieved."""
    GENERAL = "general"
    FUND = "fund"
    STOCK = "stock"
    MARKET = "market"
    ECONOMIC = "economic"
    TAX = "tax"
    REGULATORY = "regulatory"
    USER_SPECIFIC = "user_specific"
    STRATEGY = "strategy"
    HISTORICAL = "historical"


class RetrievalRequest(TypedDict, total=False):
    """Type definition for context retrieval requests."""
    query: str
    context_types: List[ContextType]
    portfolio_id: Optional[str]
    user_id: Optional[str]
    filters: Dict[str, Any]
    limit: int
    include_market_data: bool
    include_user_data: bool


class RetrievalResult(TypedDict):
    """Type definition for context retrieval results."""
    contexts: List[Dict[str, Any]]
    sources: List[str]
    metadata: Dict[str, Any]


class ContextRetrievalSystem:
    """
    System for retrieving relevant financial contexts from multiple sources.
    
    This system integrates:
    1. RAG-based vector database retrieval
    2. Market data API integration
    3. User-specific data retrieval
    4. Context merging and ranking
    """
    
    def __init__(
        self,
        embedding_model: str = "voyage",
        llm_model: Optional[str] = "gemini-2.5-pro-exp-03-25",
        vector_db: Optional[PineconeManager] = None,
        max_contexts: int = 10,
        enable_market_data: bool = True,
        enable_user_data: bool = True,
        test_mode: bool = False
    ):
        """
        Initialize the context retrieval system.
        
        Args:
            embedding_model: Model to use for embeddings
            llm_model: Model to use for LLM operations
            vector_db: Optional vector database manager
            max_contexts: Maximum number of contexts to retrieve
            enable_market_data: Whether to enable market data integration
            enable_user_data: Whether to enable user data integration
            test_mode: Whether to run in test mode (no API calls)
        """
        self.rag_system = RAGSystem(
            embedding_model=embedding_model,
            llm_model=llm_model,
            test_mode=test_mode
        )
        self.vector_db = vector_db or PineconeManager()
        self.max_contexts = max_contexts
        self.enable_market_data = enable_market_data
        self.enable_user_data = enable_user_data
        self.test_mode = test_mode
        
        logger.info(
            f"Initialized context retrieval system with {embedding_model} model, "
            f"market_data={'enabled' if enable_market_data else 'disabled'}, "
            f"user_data={'enabled' if enable_user_data else 'disabled'}, "
            f"llm_model={llm_model}, "
            f"test_mode={'enabled' if test_mode else 'disabled'}"
        )
    
    def retrieve_context(self, request: RetrievalRequest) -> RetrievalResult:
        """
        Retrieve relevant contexts based on the request.
        
        Args:
            request: Context retrieval request
            
        Returns:
            Context retrieval result
        """
        query = request["query"]
        context_types = request.get("context_types", [ContextType.GENERAL])
        limit = request.get("limit", self.max_contexts)
        include_market_data = request.get("include_market_data", self.enable_market_data)
        include_user_data = request.get("include_user_data", self.enable_user_data)
        
        logger.info(f"Retrieving context for query: '{query}'")
        logger.info(f"Context types: {[ct.value for ct in context_types]}")
        
        # Combine results from different sources
        all_contexts = []
        all_sources = []
        all_metadata = {}
        
        # 1. Get user profile and portfolio data if available
        user_profile = self._get_user_profile(request.get("user_id")) if include_user_data else None
        portfolio_data = self._get_portfolio_data(request.get("portfolio_id")) if include_user_data else None
        
        # 2. Get market data if requested
        market_data = self._get_market_data() if include_market_data else None
        
        # 3. Retrieve context from RAG system
        rag_result = self.rag_system.process_query(
            query=query,
            user_profile=user_profile,
            portfolio_data=portfolio_data,
            market_state=market_data,
            include_details=True
        )
        
        if "details" in rag_result:
            rag_contexts = rag_result["details"].get("contexts", [])
            rag_sources = rag_result["details"].get("raw_sources", [])
            
            # Add contexts from RAG system
            for i, (context, source) in enumerate(zip(rag_contexts, rag_sources)):
                all_contexts.append({
                    "content": context,
                    "source": source,
                    "type": "vector_db",
                    "relevance": 1.0 - (i * 0.1)  # Simple relevance scoring
                })
                all_sources.append(source)
        
        # 4. Add context-type specific information
        for context_type in context_types:
            type_contexts = self._get_context_by_type(
                context_type=context_type,
                query=query,
                user_id=request.get("user_id"),
                portfolio_id=request.get("portfolio_id")
            )
            
            if type_contexts:
                all_contexts.extend(type_contexts)
                all_sources.extend([ctx.get("source", "unknown") for ctx in type_contexts])
        
        # 5. Add user-specific contexts if available
        if include_user_data and user_profile:
            user_contexts = self._get_user_specific_contexts(
                user_profile=user_profile,
                portfolio_data=portfolio_data,
                query=query
            )
            
            if user_contexts:
                all_contexts.extend(user_contexts)
                all_sources.extend([ctx.get("source", "user_data") for ctx in user_contexts])
        
        # 6. Add market data contexts if available
        if include_market_data and market_data:
            market_contexts = self._get_market_specific_contexts(
                market_data=market_data,
                query=query
            )
            
            if market_contexts:
                all_contexts.extend(market_contexts)
                all_sources.extend([ctx.get("source", "market_data") for ctx in market_contexts])
        
        # 7. Rank and limit contexts
        ranked_contexts = self._rank_contexts(all_contexts, query)
        limited_contexts = ranked_contexts[:limit]
        
        # Prepare result metadata
        metadata = {
            "total_contexts_found": len(all_contexts),
            "contexts_returned": len(limited_contexts),
            "context_types": [ct.value for ct in context_types],
            "user_data_included": include_user_data and user_profile is not None,
            "market_data_included": include_market_data and market_data is not None
        }
        
        # Extract the content from the ranked contexts
        result_contexts = [
            {
                "content": ctx["content"],
                "source": ctx["source"],
                "type": ctx["type"],
                "relevance": ctx["relevance"]
            }
            for ctx in limited_contexts
        ]
        
        # Extract unique sources
        unique_sources = list(set(src for src in all_sources if src))
        
        logger.info(f"Retrieved {len(result_contexts)} contexts from {len(unique_sources)} sources")
        
        return {
            "contexts": result_contexts,
            "sources": unique_sources,
            "metadata": metadata
        }
    
    def _get_context_by_type(
        self,
        context_type: ContextType,
        query: str,
        user_id: Optional[str] = None,
        portfolio_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get context specific to a particular type.
        
        Args:
            context_type: The type of context to retrieve
            query: The query string
            user_id: Optional user ID
            portfolio_id: Optional portfolio ID
            
        Returns:
            List of context dictionaries
        """
        try:
            # Prepare metadata filters based on context type
            metadata_filters = {}
            namespace = ""
            
            if context_type == ContextType.FUND:
                metadata_filters = {"content_type": "fund"}
                namespace = "funds"
            elif context_type == ContextType.STOCK:
                metadata_filters = {"content_type": "stock"}
                namespace = "stocks"
            elif context_type == ContextType.MARKET:
                metadata_filters = {"content_type": "market"}
                namespace = "market"
            elif context_type == ContextType.ECONOMIC:
                metadata_filters = {"content_type": "economic"}
                namespace = "economic"
            elif context_type == ContextType.TAX:
                metadata_filters = {"content_type": "tax"}
                namespace = "regulations"
            elif context_type == ContextType.REGULATORY:
                metadata_filters = {"content_type": "regulatory"}
                namespace = "regulations"
            elif context_type == ContextType.STRATEGY:
                metadata_filters = {"content_type": "strategy"}
                namespace = "strategies"
            elif context_type == ContextType.HISTORICAL:
                metadata_filters = {"content_type": "historical"}
                namespace = "historical"
            
            # Extract entities from query to enhance retrieval
            # This is a simplified implementation
            query_tokens = query.lower().split()
            fund_tickers = [token.upper() for token in query_tokens if token.isalpha() and 2 <= len(token) <= 5]
            
            # Add fund tickers to filters if found and relevant
            if context_type in [ContextType.FUND, ContextType.STOCK] and fund_tickers:
                # Just use the first potential ticker for simplicity
                potential_ticker = fund_tickers[0].upper()
                metadata_filters["ticker"] = potential_ticker
            
            # Query vector database with type-specific filters
            # This is a simplified version; in a real implementation, 
            # you would use the query embedding here
            embedding_client = self.rag_system.retriever.embedding_client
            query_embedding = embedding_client.embed_text(query)
            
            # Get filtered results from vector database
            if metadata_filters:
                try:
                    results = self.vector_db.query(
                        query_vector=query_embedding,
                        top_k=5,
                        filter=metadata_filters,
                        namespace=namespace
                    )
                    
                    # Format results
                    contexts = []
                    for result in results:
                        if hasattr(result, 'metadata') and hasattr(result, 'score'):
                            content = result.metadata.get("content", "")
                            source = self._format_source_from_metadata(result.metadata)
                            
                            contexts.append({
                                "content": content,
                                "source": source,
                                "type": context_type.value,
                                "relevance": float(result.score) if hasattr(result, 'score') else 0.5
                            })
                    
                    return contexts
                    
                except Exception as e:
                    logger.warning(f"Error querying vector database for {context_type.value}: {str(e)}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting context for type {context_type.value}: {str(e)}")
            return []
    
    def _get_user_profile(self, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Get user profile information.
        
        Args:
            user_id: The user ID
            
        Returns:
            User profile dictionary or None if not available
        """
        if not user_id:
            return None
            
        # In a real implementation, this would fetch from a user database
        # This is a mock implementation
        return {
            "user_id": user_id,
            "risk_tolerance": "moderate",
            "investment_goals": ["retirement", "education"],
            "time_horizon": "long_term"
        }
    
    def _get_portfolio_data(self, portfolio_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Get portfolio data.
        
        Args:
            portfolio_id: The portfolio ID
            
        Returns:
            Portfolio data dictionary or None if not available
        """
        if not portfolio_id:
            return None
            
        # In a real implementation, this would fetch from a portfolio database
        # This is a mock implementation
        return {
            "portfolio_id": portfolio_id,
            "holdings": [
                {"ticker": "AAPL", "weight": 0.15},
                {"ticker": "MSFT", "weight": 0.12},
                {"ticker": "GOOGL", "weight": 0.10}
            ],
            "total_value": 100000,
            "allocation": {
                "stocks": 0.70,
                "bonds": 0.20,
                "cash": 0.10
            }
        }
    
    def _get_market_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current market data.
        
        Returns:
            Market data dictionary or None if not available
        """
        # In a real implementation, this would fetch from market data APIs
        # This is a mock implementation
        return {
            "trend": "bullish",
            "volatility": "moderate",
            "interest_rates": "rising",
            "major_indices": {
                "SP500": 4200,
                "NASDAQ": 14000,
                "DOW": 33000
            }
        }
    
    def _get_user_specific_contexts(
        self,
        user_profile: Dict[str, Any],
        portfolio_data: Optional[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Generate user-specific contexts based on user profile and portfolio.
        
        Args:
            user_profile: User profile information
            portfolio_data: Optional portfolio data
            query: The query string
            
        Returns:
            List of user-specific context dictionaries
        """
        contexts = []
        
        # Add risk tolerance context
        risk_tolerance = user_profile.get("risk_tolerance")
        if risk_tolerance:
            contexts.append({
                "content": f"The user has a {risk_tolerance} risk tolerance profile.",
                "source": "User Profile",
                "type": "user_data",
                "relevance": 0.9
            })
        
        # Add investment goals context
        investment_goals = user_profile.get("investment_goals", [])
        if investment_goals:
            goals_text = ", ".join(investment_goals)
            contexts.append({
                "content": f"The user's investment goals include: {goals_text}.",
                "source": "User Profile",
                "type": "user_data",
                "relevance": 0.85
            })
        
        # Add portfolio allocation context if available
        if portfolio_data and "allocation" in portfolio_data:
            allocation = portfolio_data["allocation"]
            allocation_text = ", ".join([f"{k}: {v*100:.1f}%" for k, v in allocation.items()])
            
            contexts.append({
                "content": f"Current portfolio allocation: {allocation_text}.",
                "source": "Portfolio Data",
                "type": "user_data",
                "relevance": 0.8
            })
        
        # Add holdings context if available
        if portfolio_data and "holdings" in portfolio_data:
            holdings = portfolio_data["holdings"]
            holdings_text = ", ".join([f"{h['ticker']}: {h['weight']*100:.1f}%" for h in holdings])
            
            contexts.append({
                "content": f"Current portfolio holdings: {holdings_text}.",
                "source": "Portfolio Data",
                "type": "user_data",
                "relevance": 0.75
            })
        
        return contexts
    
    def _get_market_specific_contexts(
        self,
        market_data: Dict[str, Any],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Generate market-specific contexts based on current market data.
        
        Args:
            market_data: Current market data
            query: The query string
            
        Returns:
            List of market-specific context dictionaries
        """
        contexts = []
        
        # Add market trend context
        trend = market_data.get("trend")
        volatility = market_data.get("volatility")
        if trend and volatility:
            contexts.append({
                "content": f"Current market trend is {trend} with {volatility} volatility.",
                "source": "Market Analysis",
                "type": "market_data",
                "relevance": 0.8
            })
        
        # Add interest rate context
        interest_rates = market_data.get("interest_rates")
        if interest_rates:
            contexts.append({
                "content": f"Interest rates are currently {interest_rates}.",
                "source": "Economic Data",
                "type": "market_data",
                "relevance": 0.7
            })
        
        # Add major indices context
        indices = market_data.get("major_indices", {})
        if indices:
            indices_text = ", ".join([f"{k}: {v}" for k, v in indices.items()])
            contexts.append({
                "content": f"Major indices: {indices_text}.",
                "source": "Market Data",
                "type": "market_data",
                "relevance": 0.6
            })
        
        return contexts
    
    def _rank_contexts(
        self,
        contexts: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Rank contexts by relevance to the query.
        
        Args:
            contexts: List of context dictionaries
            query: The query string
            
        Returns:
            Ranked list of context dictionaries
        """
        # In a real implementation, this would use a more sophisticated 
        # re-ranking approach, possibly with an LLM or specific re-ranker model
        
        # Simple ranking by relevance score
        sorted_contexts = sorted(contexts, key=lambda x: x.get("relevance", 0), reverse=True)
        
        # For diversity, try to include at least one context from each type
        # in the top results if possible
        type_seen = set()
        diverse_contexts = []
        
        for ctx in sorted_contexts:
            ctx_type = ctx.get("type")
            
            # Prioritize types we haven't seen yet
            if ctx_type and ctx_type not in type_seen:
                diverse_contexts.append(ctx)
                type_seen.add(ctx_type)
            else:
                # If we've seen all types, just add by relevance
                diverse_contexts.append(ctx)
        
        return diverse_contexts
    
    def _format_source_from_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format a source string from metadata.
        
        Args:
            metadata: Context metadata
            
        Returns:
            Formatted source string
        """
        source_parts = []
        
        # Add document title if available
        if "title" in metadata:
            source_parts.append(metadata["title"])
        
        # Add document type if available
        if "content_type" in metadata:
            source_parts.append(metadata["content_type"].capitalize())
        
        # Add ticker if it's a financial instrument
        if "ticker" in metadata:
            source_parts.append(f"Ticker: {metadata['ticker']}")
        
        # Add date if available
        if "date" in metadata:
            source_parts.append(f"Date: {metadata['date']}")
        
        if source_parts:
            return " | ".join(source_parts)
        else:
            return "Unknown source" 