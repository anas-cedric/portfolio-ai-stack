"""
Market-aware retrieval module.

This module contains components for adjusting retrieval patterns based on market conditions,
such as retrieving more context during periods of high volatility.
"""

from src.document_processing.market_aware.volatility_aware_retriever import VolatilityAwareRetriever

__all__ = ["VolatilityAwareRetriever"] 