"""
Financial validation utilities.

This module provides validators for financial data and calculations to ensure
numerical accuracy and prevent errors in financial analysis.
"""

import re
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, TypeVar, Callable

# Set up logging
logger = logging.getLogger(__name__)

# Type for generic number
Number = TypeVar('Number', int, float)

class ValidationError(Exception):
    """Exception raised for financial validation errors."""
    pass

# Basic Financial Validators

def validate_percentage(value: Union[str, float, int], 
                       min_val: float = 0.0, 
                       max_val: float = 100.0) -> Tuple[bool, float]:
    """
    Validate percentage values are within expected range.
    
    Args:
        value: Value to validate (can be string like "15.2%" or number)
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value
        
    Returns:
        Tuple of (is_valid, numeric_value)
    """
    try:
        # If it's a string, try to extract the number
        if isinstance(value, str):
            value = value.strip()
            if '%' in value:
                value = value.replace('%', '').strip()
            value = float(value)
        
        # Check the range
        if min_val <= float(value) <= max_val:
            return True, float(value)
        else:
            logger.warning(f"Percentage validation failed: {value} not in range {min_val}-{max_val}")
            return False, float(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Percentage validation error: {str(e)} for value {value}")
        return False, 0.0

def validate_currency(value: Union[str, float, int], 
                     min_val: Optional[float] = None, 
                     max_val: Optional[float] = None) -> Tuple[bool, float]:
    """
    Validate currency values are within expected range.
    
    Args:
        value: Value to validate (can be string like "$1,234.56" or number)
        min_val: Minimum acceptable value (or None for no minimum)
        max_val: Maximum acceptable value (or None for no maximum)
        
    Returns:
        Tuple of (is_valid, numeric_value)
    """
    try:
        # If it's a string, extract the number
        if isinstance(value, str):
            # Remove currency symbols, commas, and other formatting
            clean_val = re.sub(r'[^\d.-]', '', value)
            value = float(clean_val)
        
        # Convert to float for consistency
        value = float(value)
        
        # Check the range if specified
        if min_val is not None and value < min_val:
            logger.warning(f"Currency validation failed: {value} below minimum {min_val}")
            return False, value
        if max_val is not None and value > max_val:
            logger.warning(f"Currency validation failed: {value} above maximum {max_val}")
            return False, value
        
        return True, value
    except (ValueError, TypeError) as e:
        logger.warning(f"Currency validation error: {str(e)} for value {value}")
        return False, 0.0

def validate_ratio(value: Union[str, float, int],
                  min_val: float = 0.0,
                  max_val: Optional[float] = None) -> Tuple[bool, float]:
    """
    Validate financial ratio values.
    
    Args:
        value: Value to validate
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value (or None for no maximum)
        
    Returns:
        Tuple of (is_valid, numeric_value)
    """
    try:
        # If it's a string, extract the number
        if isinstance(value, str):
            # Handle formats like "1.5x" or "1.5:1"
            value = value.replace('x', '').replace('X', '')
            if ':' in value:
                parts = value.split(':')
                if len(parts) == 2:
                    value = float(parts[0].strip()) / float(parts[1].strip())
                else:
                    raise ValueError(f"Invalid ratio format: {value}")
            else:
                value = float(value)
        
        # Convert to float for consistency
        value = float(value)
        
        # Check the range
        if value < min_val:
            logger.warning(f"Ratio validation failed: {value} below minimum {min_val}")
            return False, value
        if max_val is not None and value > max_val:
            logger.warning(f"Ratio validation failed: {value} above maximum {max_val}")
            return False, value
        
        return True, value
    except (ValueError, TypeError, ZeroDivisionError) as e:
        logger.warning(f"Ratio validation error: {str(e)} for value {value}")
        return False, 0.0

# Portfolio Validation Functions

def validate_allocation_sum(allocations: Dict[str, float], 
                          tolerance: float = 0.5) -> Tuple[bool, str]:
    """
    Validate portfolio allocations sum to approximately 100%.
    
    Args:
        allocations: Dictionary of asset class to allocation percentage
        tolerance: Acceptable tolerance from 100% (e.g., 0.5 means 99.5-100.5%)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    total = sum(allocations.values())
    
    if 100 - tolerance <= total <= 100 + tolerance:
        return True, ""
    else:
        msg = f"Allocation total is {total:.2f}%, should be 100% (± {tolerance}%)"
        logger.warning(msg)
        return False, msg

def validate_allocation_values(allocations: Dict[str, float]) -> Tuple[bool, str]:
    """
    Validate individual allocation values are reasonable.
    
    Args:
        allocations: Dictionary of asset class to allocation percentage
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for negative allocations
    negatives = {k: v for k, v in allocations.items() if v < 0}
    if negatives:
        msg = f"Negative allocations found: {negatives}"
        logger.warning(msg)
        return False, msg
    
    # Check for unusually high single allocations (potential concentration risk)
    high_concen = {k: v for k, v in allocations.items() if v > 70}
    if high_concen:
        msg = f"High concentration risk in: {high_concen}"
        logger.warning(msg)
        return False, msg
    
    return True, ""

def validate_portfolio_allocation(allocations: Dict[str, float]) -> Tuple[bool, str]:
    """
    Validate complete portfolio allocation.
    
    Args:
        allocations: Dictionary of asset class to allocation percentage
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First validate the sum
    sum_valid, sum_error = validate_allocation_sum(allocations)
    if not sum_valid:
        return False, sum_error
    
    # Then validate individual values
    values_valid, values_error = validate_allocation_values(allocations)
    if not values_valid:
        return False, values_error
    
    return True, "Valid portfolio allocation"

# Anomaly Detection for Portfolio Recommendations

def detect_allocation_anomalies(allocations: Dict[str, float], 
                              benchmarks: Optional[Dict[str, float]] = None) -> List[str]:
    """
    Detect anomalies in portfolio asset allocations.
    
    Args:
        allocations: Dictionary of asset class to allocation percentage
        benchmarks: Optional benchmark allocations for comparison
        
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    # Check for high cash position
    if allocations.get('cash', 0) > 30:
        anomalies.append(f"Unusually high cash allocation ({allocations['cash']:.1f}%)")
    
    # Check for insufficient diversification
    if len(allocations) < 3:
        anomalies.append("Poor diversification - less than 3 asset classes")
    
    # Check for extreme allocations
    for asset, allocation in allocations.items():
        if allocation > 60:
            anomalies.append(f"Very high allocation to {asset} ({allocation:.1f}%)")
    
    # Compare with benchmarks if provided
    if benchmarks:
        for asset, bench_alloc in benchmarks.items():
            if asset in allocations:
                deviation = abs(allocations[asset] - bench_alloc)
                if deviation > 20:  # More than 20% deviation from benchmark
                    anomalies.append(
                        f"Large deviation in {asset}: {allocations[asset]:.1f}% vs benchmark {bench_alloc:.1f}%"
                    )
    
    return anomalies

def detect_risk_metric_anomalies(metrics: Dict[str, float],
                               benchmarks: Optional[Dict[str, float]] = None) -> List[str]:
    """
    Detect anomalies in portfolio risk metrics.
    
    Args:
        metrics: Dictionary of risk metrics (volatility, sharpe_ratio, etc.)
        benchmarks: Optional benchmark metrics for comparison
        
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    # Check for extreme volatility
    if 'volatility' in metrics and metrics['volatility'] > 25:
        anomalies.append(f"Very high volatility ({metrics['volatility']:.1f}%)")
    
    # Check for poor risk-adjusted return
    if 'sharpe_ratio' in metrics and metrics['sharpe_ratio'] < 0.5:
        anomalies.append(f"Low Sharpe ratio ({metrics['sharpe_ratio']:.2f})")
    
    # Check for high drawdown
    if 'max_drawdown' in metrics and metrics['max_drawdown'] < -25:
        anomalies.append(f"High maximum drawdown ({metrics['max_drawdown']:.1f}%)")
    
    # Compare with benchmarks if provided
    if benchmarks:
        for metric, bench_value in benchmarks.items():
            if metric in metrics:
                # Different logic based on metric type
                if metric == 'volatility':
                    if metrics[metric] > bench_value * 1.5:
                        anomalies.append(
                            f"Volatility ({metrics[metric]:.1f}%) significantly higher than benchmark ({bench_value:.1f}%)"
                        )
                elif metric == 'sharpe_ratio':
                    if metrics[metric] < bench_value * 0.7:
                        anomalies.append(
                            f"Sharpe ratio ({metrics[metric]:.2f}) significantly lower than benchmark ({bench_value:.2f})"
                        )
    
    return anomalies

def detect_portfolio_recommendation_anomalies(portfolio: Dict[str, Any], 
                                           benchmarks: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Comprehensive anomaly detection for portfolio recommendations.
    
    Args:
        portfolio: Portfolio recommendation data including allocations and metrics
        benchmarks: Optional benchmark data for comparison
        
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    # Check allocations
    if 'allocations' in portfolio:
        allocation_anomalies = detect_allocation_anomalies(
            portfolio['allocations'],
            benchmarks.get('allocations') if benchmarks else None
        )
        anomalies.extend(allocation_anomalies)
    
    # Check risk metrics
    if 'metrics' in portfolio:
        metric_anomalies = detect_risk_metric_anomalies(
            portfolio['metrics'],
            benchmarks.get('metrics') if benchmarks else None
        )
        anomalies.extend(metric_anomalies)
    
    # Check sector concentration
    if 'sector_allocation' in portfolio:
        for sector, allocation in portfolio['sector_allocation'].items():
            if allocation > 25:
                anomalies.append(f"High sector concentration in {sector} ({allocation:.1f}%)")
    
    # Check geographic concentration
    if 'geographic_allocation' in portfolio:
        for region, allocation in portfolio['geographic_allocation'].items():
            if allocation > 70:
                anomalies.append(f"High geographic concentration in {region} ({allocation:.1f}%)")
    
    return anomalies

# Validation Functions for o1 Model Outputs

def validate_o1_numerical_output(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract and validate all numerical values from o1 model output.
    
    Args:
        text: Raw text output from o1 model
        
    Returns:
        Dictionary containing validation results for different numeric types
    """
    # Results dictionary
    results = {
        'percentages': [],
        'currencies': [],
        'ratios': [],
        'raw_numbers': []
    }
    
    # Extract percentages
    percentage_pattern = r'(\d+\.?\d*)%'
    for match in re.finditer(percentage_pattern, text):
        value = match.group(1)
        is_valid, numeric_value = validate_percentage(value)
        results['percentages'].append({
            'original': match.group(0),
            'value': numeric_value,
            'is_valid': is_valid,
            'position': match.span()
        })
    
    # Extract currency values
    currency_pattern = r'[$€£¥](\d{1,3}(,\d{3})*(\.\d+)?)'
    for match in re.finditer(currency_pattern, text):
        value = match.group(0)
        is_valid, numeric_value = validate_currency(value)
        results['currencies'].append({
            'original': match.group(0),
            'value': numeric_value,
            'is_valid': is_valid,
            'position': match.span()
        })
    
    # Extract ratios (like 1.5x or 3:1)
    ratio_pattern = r'(\d+\.?\d*)[xX]|(\d+\.?\d*)\s*:\s*(\d+\.?\d*)'
    for match in re.finditer(ratio_pattern, text):
        value = match.group(0)
        is_valid, numeric_value = validate_ratio(value)
        results['ratios'].append({
            'original': match.group(0),
            'value': numeric_value,
            'is_valid': is_valid,
            'position': match.span()
        })
    
    # Extract raw numbers that aren't part of the above categories
    raw_number_pattern = r'(?<![a-zA-Z$€£¥\d])\d+\.?\d*(?![%xX:])'
    for match in re.finditer(raw_number_pattern, text):
        value = match.group(0)
        try:
            numeric_value = float(value)
            results['raw_numbers'].append({
                'original': match.group(0),
                'value': numeric_value,
                'position': match.span()
            })
        except (ValueError, TypeError):
            pass
    
    return results

def find_portfolio_allocations_in_text(text: str) -> Optional[Dict[str, float]]:
    """
    Attempt to extract portfolio allocations from o1 model text output.
    
    Args:
        text: Raw text output from o1 model
        
    Returns:
        Dictionary of asset class to allocation percentage, or None if not found
    """
    allocations = {}
    
    # Look for common asset class names followed by percentages
    asset_classes = [
        'stocks', 'equities', 'bonds', 'fixed income', 'cash', 'cash equivalents',
        'real estate', 'alternatives', 'commodities', 'gold', 'crypto', 'international',
        'domestic', 'emerging markets', 'developed markets', 'large cap', 'small cap',
        'mid cap', 'value', 'growth', 'treasuries', 'corporate bonds', 'municipal bonds',
        'tips', 'reits'
    ]
    
    # Create a pattern to match asset classes followed by percentages
    pattern = r'(' + '|'.join(asset_classes) + r')\s*[:=-]?\s*(\d+\.?\d*)%'
    
    found = False
    for match in re.finditer(pattern, text.lower()):
        found = True
        asset = match.group(1).strip()
        percentage = float(match.group(2))
        allocations[asset] = percentage
    
    # If we found allocations, return them
    if found:
        return allocations
    
    return None

def validate_and_fix_portfolio_allocation(allocations: Dict[str, float]) -> Dict[str, float]:
    """
    Validate portfolio allocations and attempt to fix them if invalid.
    
    Args:
        allocations: Dictionary of asset class to allocation percentage
        
    Returns:
        Corrected allocations (if possible) or original allocations
    """
    # First check if allocations are valid
    is_valid, _ = validate_portfolio_allocation(allocations)
    if is_valid:
        return allocations
    
    # Check if allocations sum to approximately 100%
    total = sum(allocations.values())
    
    # If way off, try to normalize
    if abs(total - 100) > 5:
        # Normalize to sum to 100%
        normalized = {k: (v / total) * 100 for k, v in allocations.items()}
        logger.info(f"Normalized allocations from sum of {total:.2f}% to 100%")
        return normalized
    
    # Handle negative allocations
    if any(v < 0 for v in allocations.values()):
        # Remove negative allocations and redistribute
        pos_allocations = {k: max(0, v) for k, v in allocations.items()}
        pos_total = sum(pos_allocations.values())
        normalized = {k: (v / pos_total) * 100 for k, v in pos_allocations.items()}
        logger.info("Removed negative allocations and normalized to 100%")
        return normalized
    
    # If close but not exactly 100%, adjust proportionally
    adjusted = {k: (v / total) * 100 for k, v in allocations.items()}
    logger.info(f"Adjusted allocations from {total:.2f}% to 100%")
    return adjusted 