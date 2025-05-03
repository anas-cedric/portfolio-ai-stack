"""
Comprehensive RAG (Retrieval-Augmented Generation) System.

This module provides a complete RAG implementation for financial portfolio advice,
integrating retrieval, context processing, and response generation.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple

from src.rag.query_processor import QueryProcessor
from src.rag.retriever import Retriever
from src.rag.response_generator import ResponseGenerator
from src.knowledge.embedding import get_embedding_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """
    End-to-end RAG system for financial portfolio advice.
    
    This system integrates:
    1. Query processing with financial entity extraction
    2. Hybrid retrieval (semantic + keyword)
    3. Response generation with source attribution
    4. Evaluation metrics and confidence scoring
    """
    
    def __init__(
        self,
        embedding_model: str = "voyage",
        llm_model: Optional[str] = "o3",
        use_hyde: bool = True,
        reranking_enabled: bool = True,
        confidence_threshold: float = 0.6,
        test_mode: bool = False
    ):
        """
        Initialize the RAG system.
        
        Args:
            embedding_model: Model to use for embeddings ("voyage", "llama", etc.)
            llm_model: Model to use for LLM operations (defaults to o3)
            use_hyde: Whether to use HyDE (Hypothetical Document Embeddings)
            reranking_enabled: Whether to use reranking of retrieved documents
            confidence_threshold: Minimum confidence threshold for responses
            test_mode: Whether to run in test mode (no API calls)
        """
        self.query_processor = QueryProcessor()
        self.retriever = Retriever(embedding_client_type=embedding_model)
        
        # Ensure we have a valid model name
        model_name = llm_model if llm_model else "o3"
        self.response_generator = ResponseGenerator(model=model_name, test_mode=test_mode)
        
        self.use_hyde = use_hyde
        self.reranking_enabled = reranking_enabled
        self.confidence_threshold = confidence_threshold
        self.test_mode = test_mode
        
        logger.info(
            f"Initialized RAG system with {embedding_model} embeddings, "
            f"HyDE={'enabled' if use_hyde else 'disabled'}, "
            f"reranking={'enabled' if reranking_enabled else 'disabled'}, "
            f"LLM model={model_name}, "
            f"test_mode={'enabled' if test_mode else 'disabled'}"
        )
    
    def process_query(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        portfolio_data: Optional[Dict[str, Any]] = None,
        market_state: Optional[Dict[str, Any]] = None,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """
        Process a query through the complete RAG pipeline.
        
        Args:
            query: The user's query string
            user_profile: Optional user profile information
            portfolio_data: Optional portfolio data
            market_state: Optional market state information
            include_details: Whether to include detailed processing info in output
            
        Returns:
            Dictionary containing the response and optional details
        """
        try:
            start_time = import_time_module().time()
            
            logger.info(f"Processing RAG query: '{query}'")
            
            # 1. Process the query
            processed_query = self.query_processor.process_query(query)
            
            logger.info(f"Query type: {processed_query['query_type'].value}")
            logger.info(f"Expanded query: {processed_query['expanded_query']}")
            
            # 2. Enhance query with user profile and portfolio data
            self._enhance_query(processed_query, user_profile, portfolio_data, market_state)
            
            # 3. Apply HyDE if enabled
            if self.use_hyde:
                processed_query = self._apply_hyde(processed_query)
            
            # 4. Retrieve relevant context
            retrieval_results = self.retriever.retrieve(
                query=query,
                processed_query=processed_query,
                top_k=5
            )
            
            contexts = retrieval_results["contexts"]
            sources = retrieval_results["sources"]
            relevance_scores = retrieval_results.get("relevance_scores", [])
            
            logger.info(f"Retrieved {len(contexts)} contexts")
            
            # 5. Generate the response
            generation_input = {
                "query": query,
                "contexts": contexts,
                "sources": sources,
                "query_type": processed_query["query_type"].value,
                "entities": processed_query.get("entities", {}),
                "user_profile": user_profile or {},
                "portfolio_data": portfolio_data or {},
                "market_state": market_state or {}
            }
            
            generation_output = self.response_generator.generate_response(generation_input)
            
            response = generation_output["response"]
            formatted_response = generation_output.get("formatted_response", response)
            reasoning = generation_output.get("reasoning", "")
            confidence = generation_output.get("confidence", 0.0)
            sources_used = generation_output.get("sources_used", [])
            
            # Log completion information
            elapsed_time = import_time_module().time() - start_time
            logger.info(f"Query processed in {elapsed_time:.2f}s with confidence {confidence:.2f}")
            
            # 6. Prepare the output
            result = {
                "query": query,
                "response": formatted_response,
                "confidence": confidence,
                "sources": sources_used
            }
            
            # Include detailed processing information if requested
            if include_details:
                result["details"] = {
                    "query_type": processed_query["query_type"].value,
                    "entities": processed_query.get("entities", {}),
                    "contexts": contexts,
                    "raw_sources": sources,
                    "reasoning": reasoning,
                    "relevance_scores": relevance_scores,
                    "processing_time_seconds": elapsed_time
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "query": query,
                "response": "I apologize, but I encountered an error processing your query. Please try again or rephrase your question.",
                "confidence": 0.0,
                "sources": []
            }
    
    def _enhance_query(
        self,
        processed_query: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]],
        portfolio_data: Optional[Dict[str, Any]],
        market_state: Optional[Dict[str, Any]]
    ) -> None:
        """
        Enhance the processed query with user profile and portfolio data.
        
        Args:
            processed_query: The processed query object
            user_profile: Optional user profile information
            portfolio_data: Optional portfolio data
            market_state: Optional market state information
        """
        # Enhance with user profile
        if user_profile:
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
        
        # Enhance with portfolio data
        if portfolio_data:
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
        
        # Enhance with market state
        if market_state:
            # Add market trend information to query expansion if available
            market_trend = market_state.get("trend")
            if market_trend:
                expanded_query = processed_query["expanded_query"]
                processed_query["expanded_query"] = f"{expanded_query} market trend {market_trend}"
    
    def _apply_hyde(self, processed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply Hypothetical Document Embeddings (HyDE) to enhance retrieval.
        
        Args:
            processed_query: The processed query object
            
        Returns:
            Enhanced processed query with hypothetical document
        """
        try:
            # Get the expanded query
            query = processed_query["expanded_query"]
            query_type = processed_query["query_type"].value
            
            # Generate a hypothetical document using the response generator
            hyde_input = {
                "query": query,
                "query_type": query_type,
                "entities": processed_query.get("entities", {}),
                "hyde_mode": True  # Signal to response generator that this is for HyDE
            }
            
            hyde_output = self.response_generator.generate_hypothetical_document(hyde_input)
            hypothetical_document = hyde_output.get("document", "")
            
            if hypothetical_document:
                logger.info(f"Generated hypothetical document: {hypothetical_document[:100]}...")
                
                # Add the hypothetical document to the processed query
                processed_query["hypothetical_document"] = hypothetical_document
                
                # Use the hypothetical document for embedding instead of the original query
                processed_query["embedding_text"] = hypothetical_document
            else:
                logger.warning("Failed to generate hypothetical document, falling back to standard retrieval")
            
            return processed_query
            
        except Exception as e:
            logger.warning(f"Error applying HyDE, falling back to standard retrieval: {str(e)}")
            return processed_query


def import_time_module():
    """Import the time module (to avoid import at module level for testability)."""
    import time
    return time 