"""
Context Retriever for LangGraph-based Portfolio Engine.

This module is responsible for retrieving relevant context for portfolio decisions
including market data, fund information, economic indicators, etc.
"""

from typing import Dict, List, Any, Optional, Tuple, TypedDict
from src.rag.retriever import Retriever
from src.rag.query_processor import QueryProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetrievalInput(TypedDict):
    """Type definition for retrieval input."""
    query: str
    user_profile: Dict[str, Any]
    portfolio_data: Optional[Dict[str, Any]]
    market_state: Optional[Dict[str, Any]]
    

class RetrievalOutput(TypedDict):
    """Type definition for retrieval output."""
    query: str
    contexts: List[str]
    sources: List[str]
    user_profile: Dict[str, Any]
    portfolio_data: Optional[Dict[str, Any]]
    market_state: Optional[Dict[str, Any]]
    retrieval_metadata: Dict[str, Any]


class ContextRetriever:
    """
    Enhanced context retriever for LangGraph-based portfolio engine.
    
    This class leverages the existing RAG retrieval system but enhances it with:
    1. User profile-aware context retrieval
    2. Portfolio state-aware context retrieval
    3. Market state-aware context retrieval
    """
    
    def __init__(self, embedding_client_type: str = "llama"):
        """
        Initialize the context retriever.
        
        Args:
            embedding_client_type: Type of embedding client to use (default: llama to match index)
        """
        self.retriever = Retriever(embedding_client_type=embedding_client_type)
        self.query_processor = QueryProcessor()
        logger.info("ContextRetriever initialized with %s embedding client", embedding_client_type)
    
    def retrieve(self, input_data: RetrievalInput) -> RetrievalOutput:
        """
        Retrieve relevant context for the given query and state.
        
        Args:
            input_data: Retrieval input containing query and state information
            
        Returns:
            Retrieval output containing contexts and state information
        """
        query = input_data["query"]
        user_profile = input_data.get("user_profile", {})
        portfolio_data = input_data.get("portfolio_data", {})
        market_state = input_data.get("market_state", {})
        
        logger.info("Processing query: %s", query)
        
        # Process the query to extract entities, expand it, etc.
        processed_query = self.query_processor.process_query(query)
        
        # Log the processed query details for debugging
        logger.info("Query type: %s", processed_query["query_type"].value)
        logger.info("Expanded query: %s", processed_query["expanded_query"])
        logger.info("Extracted entities: %s", processed_query["entities"])
        logger.info("Metadata filters: %s", processed_query["metadata_filters"])
        
        # Enhance the query processing with user profile information
        self._enhance_with_user_profile(processed_query, user_profile)
        
        # Enhance the query processing with portfolio data
        if portfolio_data:
            self._enhance_with_portfolio_data(processed_query, portfolio_data)
        
        # Enhance the query processing with market state
        if market_state:
            self._enhance_with_market_state(processed_query, market_state)
        
        # Retrieve relevant contexts
        retrieval_results = self.retriever.retrieve(
            query=query,
            processed_query=processed_query,
            top_k=7  # Retrieve more contexts for better decision making
        )
        
        # Log raw results for debugging
        if "raw_results" in retrieval_results:
            logger.info("Raw results: %s", retrieval_results["raw_results"])
        
        # Log number of contexts retrieved
        logger.info("Retrieved %d contexts", len(retrieval_results["contexts"]))
        
        # Log contexts if any were retrieved
        if retrieval_results["contexts"]:
            for i, context in enumerate(retrieval_results["contexts"]):
                logger.info("Context %d: %s", i+1, context[:100] + "..." if len(context) > 100 else context)
        else:
            logger.warning("No contexts retrieved - check semantic search and filters")
        
        # Return the retrieved contexts and state information
        return {
            "query": query,
            "contexts": retrieval_results["contexts"],
            "sources": retrieval_results["sources"],
            "user_profile": user_profile,
            "portfolio_data": portfolio_data,
            "market_state": market_state,
            "retrieval_metadata": {
                "query_type": processed_query["query_type"].value,
                "entities": processed_query["entities"],
                "relevance_scores": retrieval_results.get("relevance_scores", [])
            }
        }
    
    def _enhance_with_user_profile(self, processed_query: Dict[str, Any], user_profile: Dict[str, Any]) -> None:
        """
        Enhance query processing with user profile information.
        
        Args:
            processed_query: The processed query
            user_profile: The user profile information
        """
        if not user_profile:
            return
        
        # Add risk tolerance to query expansion if available
        risk_tolerance = user_profile.get("risk_tolerance")
        if risk_tolerance:
            expanded_query = processed_query["expanded_query"]
            processed_query["expanded_query"] = f"{expanded_query} risk tolerance {risk_tolerance}"
        
        # Add investment goals to query expansion if available
        investment_goals = user_profile.get("investment_goals", [])
        if investment_goals:
            goals_text = " ".join(investment_goals)
            expanded_query = processed_query["expanded_query"]
            processed_query["expanded_query"] = f"{expanded_query} investment goals {goals_text}"
    
    def _enhance_with_portfolio_data(self, processed_query: Dict[str, Any], portfolio_data: Dict[str, Any]) -> None:
        """
        Enhance query processing with portfolio data.
        
        Args:
            processed_query: The processed query
            portfolio_data: The portfolio data
        """
        if not portfolio_data:
            return
        
        # Add current holdings to entity extraction if relevant
        holdings = portfolio_data.get("holdings", [])
        if holdings:
            tickers = [holding["ticker"] for holding in holdings if "ticker" in holding]
            if tickers:
                entities = processed_query.get("entities", {})
                existing_tickers = set(entities.get("tickers", []))
                combined_tickers = list(existing_tickers.union(set(tickers)))
                
                if "entities" not in processed_query:
                    processed_query["entities"] = {}
                
                processed_query["entities"]["tickers"] = combined_tickers
    
    def _enhance_with_market_state(self, processed_query: Dict[str, Any], market_state: Dict[str, Any]) -> None:
        """
        Enhance query processing with market state information.
        
        Args:
            processed_query: The processed query
            market_state: The market state information
        """
        if not market_state:
            return
        
        # Add market trend information to query expansion if available
        market_trend = market_state.get("trend")
        if market_trend:
            expanded_query = processed_query["expanded_query"]
            processed_query["expanded_query"] = f"{expanded_query} market trend {market_trend}" 