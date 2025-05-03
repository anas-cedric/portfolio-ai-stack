"""
Tabular formatter for financial data.

This module contains utilities for formatting financial data in tabular format
that is optimized for LLM context utilization.
"""

import pandas as pd
from typing import Dict, List, Any, Union, Optional


class TabularFormatter:
    """
    Formats financial data in tabular format optimized for LLM context.
    
    Features:
    - Compact tabular representation
    - Intelligent column selection
    - Scale-aware formatting (K, M, B suffixes)
    - Prioritization of important data
    """
    
    def __init__(self, max_width: int = 80, precision: int = 2):
        """
        Initialize the tabular formatter.
        
        Args:
            max_width: Maximum width of the table in characters
            precision: Decimal precision for numerical values
        """
        self.max_width = max_width
        self.precision = precision
        
        # Financial data type formatting preferences
        self.format_specs = {
            'percentage': '{:.2f}%',
            'currency': '${:.2f}',
            'ratio': '{:.2f}x',
            'default': '{:.2f}'
        }
        
        # Column priority for different financial data types
        self.column_priority = {
            'holdings': ['ticker', 'name', 'value', 'percentage', 'cost_basis'],
            'performance': ['period', 'return', 'benchmark', 'alpha'],
            'ratios': ['name', 'value', 'category'],
            'allocations': ['category', 'percentage', 'value']
        }
    
    def format_dataframe(
        self, 
        df: pd.DataFrame, 
        data_type: str = 'default',
        include_header: bool = True,
        column_types: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Format a pandas DataFrame into a compact tabular string.
        
        Args:
            df: The DataFrame to format
            data_type: Type of financial data ('holdings', 'performance', etc.)
            include_header: Whether to include column headers
            column_types: Dictionary mapping column names to data types
                          (e.g., {'return': 'percentage', 'value': 'currency'})
            
        Returns:
            Formatted table as a string
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Select and order columns based on priority
        if data_type in self.column_priority:
            priority_cols = [col for col in self.column_priority[data_type] if col in df.columns]
            other_cols = [col for col in df.columns if col not in priority_cols]
            df = df[priority_cols + other_cols]
        
        # Format numerical values
        column_types = column_types or {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                col_type = column_types.get(col, 'default')
                df[col] = self._format_numeric_column(df[col], col_type)
        
        # Generate the table
        table_str = self._create_ascii_table(df, include_header)
        return table_str
    
    def format_dict(
        self, 
        data: Dict[str, Any], 
        data_type: str = 'default',
        title: Optional[str] = None
    ) -> str:
        """
        Format a dictionary of financial data into a tabular string.
        
        Args:
            data: Dictionary of financial data
            data_type: Type of financial data
            title: Optional title for the table
            
        Returns:
            Formatted table as a string
        """
        # Convert to DataFrame for consistent handling
        if isinstance(data, dict):
            # Handle nested dictionaries differently
            if any(isinstance(v, dict) for v in data.values()):
                # For nested dictionaries, create multi-row table
                rows = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            rows.append({'category': key, 'subcategory': subkey, 'value': subvalue})
                    else:
                        rows.append({'category': key, 'value': value})
                df = pd.DataFrame(rows)
            else:
                # For flat dictionaries, create two-column table
                df = pd.DataFrame({'item': data.keys(), 'value': data.values()})
        else:
            raise ValueError("Input must be a dictionary")
        
        # Format the DataFrame
        result = self.format_dataframe(df, data_type)
        
        # Add title if provided
        if title:
            title_line = f"--- {title} ---"
            result = f"{title_line}\n{result}"
        
        return result
    
    def format_holdings(self, holdings: List[Dict[str, Any]]) -> str:
        """
        Format portfolio holdings in an optimized tabular format.
        
        Args:
            holdings: List of holding dictionaries
            
        Returns:
            Formatted holdings table
        """
        df = pd.DataFrame(holdings)
        column_types = {
            'value': 'currency',
            'percentage': 'percentage',
            'cost_basis': 'currency',
            'gain_loss': 'currency',
            'gain_loss_pct': 'percentage'
        }
        return self.format_dataframe(df, 'holdings', column_types=column_types)
    
    def format_performance(self, performance_data: Dict[str, Any]) -> str:
        """
        Format performance data in an optimized tabular format.
        
        Args:
            performance_data: Performance metrics
            
        Returns:
            Formatted performance table
        """
        # Convert nested performance data to DataFrame
        rows = []
        for period, metrics in performance_data.items():
            row = {'period': period}
            row.update(metrics)
            rows.append(row)
        
        df = pd.DataFrame(rows)
        column_types = {
            'return': 'percentage',
            'benchmark': 'percentage',
            'alpha': 'percentage',
            'sharpe': 'ratio',
            'volatility': 'percentage'
        }
        return self.format_dataframe(df, 'performance', column_types=column_types)
    
    def _format_numeric_column(self, column: pd.Series, col_type: str) -> pd.Series:
        """
        Format a numeric column according to its type.
        
        Args:
            column: The pandas Series to format
            col_type: The type of the column ('percentage', 'currency', etc.)
            
        Returns:
            Formatted pandas Series
        """
        # Get the format specification
        format_spec = self.format_specs.get(col_type, self.format_specs['default'])
        
        # Format each value
        def format_value(val):
            if pd.isna(val):
                return 'N/A'
            
            # Apply K, M, B suffixes for large numbers in certain types
            if col_type == 'currency' and abs(val) >= 1000:
                if abs(val) >= 1e9:
                    return f"${val/1e9:.{self.precision}f}B"
                elif abs(val) >= 1e6:
                    return f"${val/1e6:.{self.precision}f}M"
                elif abs(val) >= 1e3:
                    return f"${val/1e3:.{self.precision}f}K"
            
            # Apply the format specification
            return format_spec.format(val)
        
        return column.apply(format_value)
    
    def _create_ascii_table(self, df: pd.DataFrame, include_header: bool) -> str:
        """
        Create a simple ASCII table from a DataFrame.
        
        Args:
            df: The DataFrame to format
            include_header: Whether to include column headers
            
        Returns:
            ASCII table as a string
        """
        # Get column widths (minimum width is the length of the column name)
        col_widths = {}
        for col in df.columns:
            col_width = max(
                len(str(col)) if include_header else 0,
                df[col].astype(str).str.len().max()
            )
            col_widths[col] = min(col_width, 30)  # Cap at 30 chars to avoid extremely wide columns
        
        # Check if we need to adjust column widths to fit max_width
        total_width = sum(col_widths.values()) + (3 * len(df.columns) - 1)
        if total_width > self.max_width:
            # Adjust column widths proportionally
            excess = total_width - self.max_width
            for col in sorted(col_widths, key=lambda x: col_widths[x], reverse=True):
                reduce_by = min(excess, max(0, col_widths[col] - 5))  # Don't go below 5 chars
                col_widths[col] -= reduce_by
                excess -= reduce_by
                if excess <= 0:
                    break
        
        # Generate header
        lines = []
        if include_header:
            header = " | ".join(f"{col:{col_widths[col]}s}" for col in df.columns)
            lines.append(header)
            lines.append("-" * len(header))
        
        # Generate rows
        for _, row in df.iterrows():
            row_str = " | ".join(f"{str(row[col]):{col_widths[col]}s}" for col in df.columns)
            lines.append(row_str)
        
        return "\n".join(lines) 