"""
Compact number formatter for financial data.

This module provides utilities for formatting numerical data in financial contexts
in a way that optimizes context window utilization.
"""

from typing import Dict, List, Any, Union, Optional
import re
import numpy as np


class CompactNumberFormatter:
    """
    Formats numerical financial data in compact, context-efficient ways.
    
    Features:
    - Scale-appropriate suffixes (K, M, B, T)
    - Financial notation conventions
    - Consistent decimal precision
    - Special handling for percentages, basis points, ratios
    """
    
    def __init__(self, precision: int = 2):
        """
        Initialize the compact number formatter.
        
        Args:
            precision: Default decimal precision
        """
        self.precision = precision
        
        # Define scale thresholds for different numerical ranges
        self.scales = [
            (1e12, 'T'),  # Trillion
            (1e9, 'B'),   # Billion
            (1e6, 'M'),   # Million
            (1e3, 'K')    # Thousand
        ]
    
    def format_number(
        self, 
        value: Union[int, float], 
        number_type: str = 'default',
        precision: Optional[int] = None,
        compact: bool = True
    ) -> str:
        """
        Format a number according to financial conventions.
        
        Args:
            value: The numerical value to format
            number_type: Type of number ('currency', 'percentage', 'ratio', 'basis_points', 'default')
            precision: Decimal precision (overrides default)
            compact: Whether to use compact notation with suffixes
            
        Returns:
            Formatted number as a string
        """
        if value is None or np.isnan(value):
            return "N/A"
        
        precision = precision if precision is not None else self.precision
        
        # Handle specific number types
        if number_type == 'currency':
            return self._format_currency(value, precision, compact)
        elif number_type == 'percentage':
            return self._format_percentage(value, precision)
        elif number_type == 'basis_points':
            return self._format_basis_points(value)
        elif number_type == 'ratio':
            return self._format_ratio(value, precision)
        else:
            # Default formatting
            if compact and abs(value) >= 1000:
                return self._apply_scale(value, precision)
            else:
                return f"{value:.{precision}f}"
    
    def format_financial_metrics(self, metrics: Dict[str, Any], compact: bool = True) -> Dict[str, str]:
        """
        Format a dictionary of financial metrics with appropriate conventions.
        
        Args:
            metrics: Dictionary of financial metrics
            compact: Whether to use compact notation
            
        Returns:
            Dictionary of formatted metrics
        """
        result = {}
        
        # Common financial metric types
        metric_types = {
            # Percentage-based metrics
            'return': 'percentage',
            'yield': 'percentage',
            'growth': 'percentage',
            'change': 'percentage',
            'margin': 'percentage',
            'rate': 'percentage',
            'volatility': 'percentage',
            'drawdown': 'percentage',
            'allocation': 'percentage',
            'exposure': 'percentage',
            
            # Currency-based metrics
            'price': 'currency',
            'value': 'currency',
            'cost': 'currency',
            'expense': 'currency',
            'revenue': 'currency',
            'income': 'currency',
            'cash': 'currency',
            'debt': 'currency',
            'assets': 'currency',
            'liabilities': 'currency',
            
            # Ratio-based metrics
            'ratio': 'ratio',
            'multiple': 'ratio',
            'sharpe': 'ratio',
            'sortino': 'ratio',
            'beta': 'ratio',
            'alpha': 'ratio',
            'pe': 'ratio',
            'pb': 'ratio',
            'ps': 'ratio',
        }
        
        for key, value in metrics.items():
            # Skip non-numeric values
            if not isinstance(value, (int, float)) or np.isnan(value):
                result[key] = "N/A"
                continue
                
            # Determine metric type based on key name
            number_type = 'default'
            for pattern, type_name in metric_types.items():
                if pattern in key.lower():
                    number_type = type_name
                    break
            
            # Format the value
            result[key] = self.format_number(value, number_type, compact=compact)
        
        return result
    
    def _format_currency(self, value: float, precision: int, compact: bool) -> str:
        """Format a currency value with dollar sign and appropriate scale."""
        if compact and abs(value) >= 1000:
            scaled_value = self._apply_scale(value, precision)
            return f"${scaled_value}"
        else:
            return f"${value:.{precision}f}"
    
    def _format_percentage(self, value: float, precision: int) -> str:
        """Format a percentage value with % symbol."""
        # Convert decimal percentage (0.05) to display percentage (5.00%)
        if abs(value) < 0.1 and value != 0 and abs(value) < 1:
            # It's likely already in decimal form (e.g., 0.05 for 5%)
            return f"{value * 100:.{precision}f}%"
        else:
            # It's likely already in percentage form (e.g., 5 for 5%)
            return f"{value:.{precision}f}%"
    
    def _format_basis_points(self, value: float) -> str:
        """Format a value in basis points (1/100th of a percent)."""
        # Convert to basis points (1% = 100 bps)
        if abs(value) < 0.1 and value != 0:
            # It's likely in decimal form (e.g., 0.0025 for 25 bps)
            return f"{value * 10000:.0f} bps"
        elif abs(value) < 10:
            # It's likely in percentage (e.g., 0.25 for 25 bps)
            return f"{value * 100:.0f} bps"
        else:
            # It's likely already in bps (e.g., 25 for 25 bps)
            return f"{value:.0f} bps"
    
    def _format_ratio(self, value: float, precision: int) -> str:
        """Format a ratio value with 'x' suffix."""
        return f"{value:.{precision}f}x"
    
    def _apply_scale(self, value: float, precision: int) -> str:
        """Apply appropriate scale suffix (K, M, B, T) to a number."""
        sign = "-" if value < 0 else ""
        abs_value = abs(value)
        
        for scale, suffix in self.scales:
            if abs_value >= scale:
                scaled = abs_value / scale
                return f"{sign}{scaled:.{precision}f}{suffix}"
        
        # No scaling needed
        return f"{sign}{abs_value:.{precision}f}"
    
    @staticmethod
    def parse_compact_number(text: str) -> Optional[float]:
        """
        Parse a compact number string back to a float.
        
        Args:
            text: String representation of a number, potentially with K/M/B/T suffix
            
        Returns:
            Parsed float value or None if parsing failed
        """
        if not text or text == 'N/A':
            return None
            
        # Remove $ and % symbols
        text = text.replace('$', '').replace('%', '')
        
        # Define scaling factors
        scales = {
            'K': 1e3,
            'M': 1e6,
            'B': 1e9,
            'T': 1e12
        }
        
        # Check for scaling suffix
        match = re.search(r'^(-?\d+\.?\d*)([KMBT])?$', text.strip())
        if match:
            value = float(match.group(1))
            suffix = match.group(2)
            
            if suffix and suffix in scales:
                value *= scales[suffix]
                
            return value
        
        # Try direct conversion
        try:
            return float(text)
        except ValueError:
            return None 