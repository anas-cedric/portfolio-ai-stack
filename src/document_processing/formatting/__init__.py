"""
Formatting module for financial data.

This module contains components for formatting financial data in ways that are
optimized for LLM context utilization, including tabular formatting and
compact numerical representations.
"""

from src.document_processing.formatting.tabular_formatter import TabularFormatter
from src.document_processing.formatting.number_formatter import CompactNumberFormatter

__all__ = ["TabularFormatter", "CompactNumberFormatter"] 