"""
Volatility-aware document retrieval.

This module provides a retriever that adjusts retrieval depth and breadth
based on market volatility conditions. During periods of high volatility,
the retriever prioritizes more comprehensive context retrieval.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VolatilityAwareRetriever:
    """
    Document retriever that adjusts retrieval depth based on market volatility.
    
    Features:
    - Dynamic context window scaling based on volatility
    - Historical volatility calculation
    - Adaptive document retrieval
    - Market event sensitivity
    """
    
    def __init__(
        self,
        base_document_count: int = 3,
        max_document_count: int = 10,
        volatility_threshold: float = 1.5,
        high_volatility_multiplier: float = 2.0,
        market_data_source: Optional[str] = None
    ):
        """
        Initialize the volatility-aware retriever.
        
        Args:
            base_document_count: Base number of documents to retrieve in normal conditions
            max_document_count: Maximum number of documents to retrieve in high volatility
            volatility_threshold: Threshold for determining high volatility
                                 (as a multiplier of average volatility)
            high_volatility_multiplier: Multiplier for document count during high volatility
            market_data_source: Optional source for market data (default uses a simple API)
        """
        self.base_document_count = base_document_count
        self.max_document_count = max_document_count
        self.volatility_threshold = volatility_threshold
        self.high_volatility_multiplier = high_volatility_multiplier
        self.market_data_source = market_data_source
        
        # Volatility cache to avoid repeated calculations
        self._volatility_cache = {}
        self._volatility_cache_expiry = datetime.now() - timedelta(days=1)  # Start expired
        
        logger.info("VolatilityAwareRetriever initialized with threshold: %s", volatility_threshold)
    
    def retrieve(
        self,
        query: str,
        base_retriever: Any,
        market_index: str = "SPY",
        window_days: int = 30,
        k: Optional[int] = None,
        **kwargs
    ) -> List[Any]:
        """
        Retrieve documents with volatility-aware adjustments.
        
        Args:
            query: The search query
            base_retriever: Base retriever object that has a search/get_relevant_documents method
            market_index: Market index to use for volatility calculation
            window_days: Window of days to consider for volatility calculation
            k: Optional override for number of documents to retrieve
            **kwargs: Additional arguments to pass to the base retriever
            
        Returns:
            List of retrieved documents
        """
        # If k is explicitly provided, use it without volatility adjustment
        if k is not None:
            logger.info("Using explicit k=%d (overriding volatility adjustment)", k)
            return self._retrieve_documents(query, base_retriever, k, **kwargs)
        
        # Check market volatility
        current_volatility, is_high_volatility = self._check_volatility(market_index, window_days)
        
        # Determine how many documents to retrieve based on volatility
        if is_high_volatility:
            # Calculate adjusted count but cap at maximum
            adjusted_count = min(
                int(self.base_document_count * self.high_volatility_multiplier),
                self.max_document_count
            )
            logger.info("High volatility detected (%.2f). Retrieving %d documents.", 
                       current_volatility, adjusted_count)
        else:
            adjusted_count = self.base_document_count
            logger.info("Normal volatility (%.2f). Retrieving %d documents.", 
                       current_volatility, adjusted_count)
        
        # Retrieve documents with adjusted count
        return self._retrieve_documents(query, base_retriever, adjusted_count, **kwargs)
    
    def _retrieve_documents(
        self,
        query: str,
        base_retriever: Any,
        count: int,
        **kwargs
    ) -> List[Any]:
        """
        Retrieve documents using the base retriever.
        
        Args:
            query: The search query
            base_retriever: Base retriever object
            count: Number of documents to retrieve
            **kwargs: Additional arguments to pass to the base retriever
            
        Returns:
            List of retrieved documents
        """
        # Check which retrieval method the base retriever supports
        if hasattr(base_retriever, "get_relevant_documents"):
            return base_retriever.get_relevant_documents(query, k=count, **kwargs)
        elif hasattr(base_retriever, "search"):
            return base_retriever.search(query, k=count, **kwargs)
        else:
            raise ValueError(
                "Base retriever must have either get_relevant_documents or search method"
            )
    
    def _check_volatility(
        self,
        market_index: str = "SPY",
        window_days: int = 30
    ) -> Tuple[float, bool]:
        """
        Check current market volatility and determine if it's high.
        
        Args:
            market_index: Market index to use (e.g., "SPY" for S&P 500)
            window_days: Number of days to calculate volatility over
            
        Returns:
            Tuple of (current volatility value, boolean indicating high volatility)
        """
        # Check if we have a recent cached value
        cache_key = f"{market_index}_{window_days}"
        if (
            cache_key in self._volatility_cache
            and datetime.now() < self._volatility_cache_expiry
        ):
            vol_value, is_high = self._volatility_cache[cache_key]
            logger.debug("Using cached volatility value: %.2f", vol_value)
            return vol_value, is_high
        
        # Get market data and calculate volatility
        try:
            # If a market data source is provided, use it
            if self.market_data_source:
                vol_value = self._get_volatility_from_source(
                    market_index, window_days
                )
            else:
                # Otherwise use a simple calculation with sample data
                vol_value = self._calculate_sample_volatility(window_days)
            
            # Determine if volatility is high based on threshold
            is_high_volatility = vol_value > self.volatility_threshold
            
            # Cache the result for 1 hour
            self._volatility_cache[cache_key] = (vol_value, is_high_volatility)
            self._volatility_cache_expiry = datetime.now() + timedelta(hours=1)
            
            return vol_value, is_high_volatility
            
        except Exception as e:
            logger.error("Error calculating volatility: %s", str(e))
            # Default to normal volatility in case of error
            return 1.0, False
    
    def _get_volatility_from_source(
        self,
        market_index: str,
        window_days: int
    ) -> float:
        """
        Get volatility from the configured market data source.
        
        Args:
            market_index: Market index symbol
            window_days: Window for volatility calculation
            
        Returns:
            Volatility value
        """
        # This would implement the specific market data source integration
        # For now, use the sample calculation as a fallback
        logger.warning("Market data source not implemented, using sample data")
        return self._calculate_sample_volatility(window_days)
    
    def _calculate_sample_volatility(self, window_days: int) -> float:
        """
        Calculate a sample volatility value for demonstration.
        
        In a real implementation, this would fetch actual market data.
        
        Args:
            window_days: Window for calculation
            
        Returns:
            Volatility value
        """
        # For simplicity, generate a random volatility value 
        # that's higher on certain days of the week (e.g., Monday and Friday)
        # This is just for demonstration purposes
        today = datetime.now()
        weekday = today.weekday()  # 0=Monday, 4=Friday
        
        # Base volatility with some randomness
        base_vol = 1.0 + np.random.normal(0, 0.3)
        
        # Increase volatility on Monday and Friday
        if weekday == 0 or weekday == 4:
            base_vol *= 1.5
        
        # Ensure volatility is positive and has reasonable bounds
        return max(0.5, min(base_vol, 3.0))
    
    def get_market_context(
        self,
        market_index: str = "SPY",
        window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get market context information for enriching the retrieval context.
        
        Args:
            market_index: Market index to use
            window_days: Window of days to consider
            
        Returns:
            Dictionary with market context information
        """
        vol_value, is_high = self._check_volatility(market_index, window_days)
        
        # Generate market context message
        if is_high:
            volatility_desc = "high"
            context_msg = (
                "Note: Market volatility is currently elevated. "
                "Consider recent market movements in your analysis."
            )
        else:
            volatility_desc = "normal"
            context_msg = "Market volatility is within normal ranges."
        
        return {
            "volatility": vol_value,
            "volatility_description": volatility_desc,
            "is_high_volatility": is_high,
            "market_index": market_index,
            "window_days": window_days,
            "timestamp": datetime.now().isoformat(),
            "context_message": context_msg
        }
    
    def adjust_prompt_for_volatility(
        self,
        prompt: str,
        market_index: str = "SPY",
        window_days: int = 30
    ) -> str:
        """
        Adjust a prompt based on current market volatility.
        
        Args:
            prompt: The original prompt
            market_index: Market index to use for volatility
            window_days: Window of days for volatility calculation
            
        Returns:
            Adjusted prompt with volatility context
        """
        market_context = self.get_market_context(market_index, window_days)
        
        # Append volatility context to the prompt
        if market_context["is_high_volatility"]:
            volatility_note = (
                "\n\nImportant market context: "
                f"Market volatility is currently {market_context['volatility_description']} "
                f"({market_context['volatility']:.2f}). "
                "Consider providing more comprehensive analysis and context in your response, "
                "accounting for recent market movements and potential impacts."
            )
        else:
            volatility_note = (
                f"\n\nMarket context: Volatility is {market_context['volatility_description']} "
                f"({market_context['volatility']:.2f})."
            )
        
        return prompt + volatility_note 