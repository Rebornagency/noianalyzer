"""
Common Utility Functions for NOI Analyzer

This module contains utility functions that are used across multiple modules
in the NOI Analyzer application, reducing code duplication.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache
import json
import re
from datetime import datetime
import math

from constants import CURRENCY_SYMBOL, DISPLAY_PRECISION, FINANCIAL_TOLERANCE, MAIN_METRICS, OPEX_COMPONENTS, INCOME_COMPONENTS, FIELD_SYNONYMS, FINANCIAL_EPS
from utils.error_handler import setup_logger, handle_errors, NOIAnalyzerError

logger = setup_logger(__name__)


@handle_errors(default_return=0.0)
def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with custom default.
    Now recognises accounting negatives formatted like "(1,234)".
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    if value is None:
        return default
    
    # Handle numpy types
    if hasattr(value, 'item'):
        try:
            return float(value.item())
        except (ValueError, TypeError):
            return default
    
    # Handle string values
    if isinstance(value, str):
        s = value.strip()
        # Detect parentheses negative e.g. (1,234.50)
        is_negative_paren = s.startswith('(') and s.endswith(')')
        if is_negative_paren:
            s = s[1:-1]
        # Remove currency symbols, commas, and whitespace
        clean_value = re.sub(r'[^\d.-]', '', s)
        if not clean_value or clean_value == '.':
            return default
        try:
            num = float(clean_value)
            return -num if is_negative_paren else num
        except ValueError:
            return default
    
    # Handle numeric values
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


@handle_errors(default_return=0)
def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int with custom default.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    if value is None:
        return default
    
    # Handle string values
    if isinstance(value, str):
        # Remove non-numeric characters except negative sign
        clean_value = re.sub(r'[^\d-]', '', value.strip())
        if not clean_value:
            return default
        try:
            return int(clean_value)
        except ValueError:
            return default
    
    # Handle numeric values
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


@handle_errors(default_return="")
def safe_string(value: Any, default: str = "") -> str:
    """
    Safely convert value to string with custom default.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        String value or default
    """
    if value is None:
        return default
    
    try:
        return str(value).strip()
    except Exception:
        return default


def format_currency(value: Optional[float], symbol: str = CURRENCY_SYMBOL, precision: int = DISPLAY_PRECISION) -> str:
    """
    Format a numeric value as currency.
    
    Args:
        value: Numeric value to format
        symbol: Currency symbol
        precision: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    if value is None:
        return f"{symbol}0.00"
    
    try:
        # Handle negative values
        if value < 0:
            return f"-{symbol}{abs(value):,.{precision}f}"
        else:
            return f"{symbol}{value:,.{precision}f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"


def format_percent(value: Optional[float], precision: int = 1) -> str:
    """
    Format a numeric value as percentage.
    
    Args:
        value: Numeric value to format (as decimal, e.g., 0.1 for 10%)
        precision: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "0.0%"
    
    try:
        return f"{value * 100:.{precision}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def format_change(value: Optional[float], is_favorable: bool = True, show_sign: bool = True) -> str:
    """
    Format a change value with appropriate styling indicators.
    
    Args:
        value: Change value
        is_favorable: Whether positive changes are favorable
        show_sign: Whether to show +/- signs
        
    Returns:
        Formatted change string with indicators
    """
    if value is None:
        return "0.00"
    
    try:
        formatted_value = f"{value:,.2f}"
        
        if show_sign and value > 0:
            formatted_value = f"+{formatted_value}"
        
        # Add indicators for favorable/unfavorable changes
        if value > 0:
            indicator = "↑" if is_favorable else "↓"
        elif value < 0:
            indicator = "↓" if is_favorable else "↑"
        else:
            indicator = "→"
        
        return f"{indicator} {formatted_value}"
        
    except (ValueError, TypeError):
        return "0.00"


@lru_cache(maxsize=32)
def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Calculate percentage change between two values with memoization.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Percentage change as decimal (e.g., 0.1 for 10% increase)
    """
    if previous == 0:
        return 0.0 if current == 0 else float('inf')
    
    return (current - previous) / previous


def is_significant_change(current: float, previous: float, threshold: float = 0.05) -> bool:
    """
    Determine if the change between two values is significant.
    
    Args:
        current: Current value
        previous: Previous value
        threshold: Minimum percentage change to be considered significant
        
    Returns:
        True if change is significant, False otherwise
    """
    try:
        change = abs(calculate_percentage_change(current, previous))
        return change >= threshold
    except (ValueError, TypeError, ZeroDivisionError):
        return False


def clean_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and normalize financial data dictionary.
    
    Args:
        data: Raw financial data dictionary
        
    Returns:
        Cleaned financial data dictionary
    """
    cleaned_data = {}
    
    for key, value in data.items():
        if key in ['gpr', 'vacancy_loss', 'other_income', 'egi', 'opex', 'noi']:
            # Financial fields should be floats
            cleaned_data[key] = safe_float(value)
        elif key in ['property_id', 'period', 'document_type']:
            # Identifier fields should be strings
            cleaned_data[key] = safe_string(value)
        else:
            # Other fields, keep as is but safely convert
            if isinstance(value, (int, float)):
                cleaned_data[key] = safe_float(value)
            else:
                cleaned_data[key] = safe_string(value)
    
    return cleaned_data


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary (base)
        dict2: Second dictionary (update)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that all required fields are present and non-empty.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        True if all required fields are present and valid
        
    Raises:
        NOIAnalyzerError: If validation fails
    """
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            empty_fields.append(field)
    
    if missing_fields:
        raise NOIAnalyzerError(
            f"Missing required fields: {', '.join(missing_fields)}",
            error_type="MISSING_REQUIRED_FIELDS",
            details={"missing_fields": missing_fields}
        )
    
    if empty_fields:
        raise NOIAnalyzerError(
            f"Empty required fields: {', '.join(empty_fields)}",
            error_type="EMPTY_REQUIRED_FIELDS", 
            details={"empty_fields": empty_fields}
        )
    
    return True


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores and spaces
    sanitized = sanitized.strip('_ ')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return sanitized


def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get value from nested dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated key path (e.g., "user.profile.name")
        default: Default value if key not found
        
    Returns:
        Value at key path or default
    """
    keys = key_path.split('.')
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError, AttributeError):
        return default


def summarize_dict_for_logging(data: Dict[str, Any], max_items: int = 5, max_length: int = 100) -> Dict[str, Any]:
    """
    Create a summarized version of a dictionary for logging purposes.
    
    Args:
        data: Dictionary to summarize
        max_items: Maximum number of items to include
        max_length: Maximum length for string values
        
    Returns:
        Summarized dictionary
    """
    if not isinstance(data, dict):
        return {"type": type(data).__name__, "value": str(data)[:max_length]}
    
    summary = {}
    items_count = 0
    
    for key, value in data.items():
        if items_count >= max_items:
            summary["..."] = f"and {len(data) - max_items} more items"
            break
        
        if isinstance(value, dict):
            summary[key] = {"type": "dict", "keys": list(value.keys())[:3]}
        elif isinstance(value, list):
            summary[key] = {"type": "list", "length": len(value)}
        elif isinstance(value, str):
            summary[key] = truncate_text(value, max_length)
        else:
            summary[key] = value
        
        items_count += 1
    
    return summary


def compare_with_tolerance(value1: float, value2: float, tolerance: float = FINANCIAL_TOLERANCE) -> bool:
    """
    Compare two float values with tolerance for financial calculations.
    
    Args:
        value1: First value
        value2: Second value
        tolerance: Acceptable difference
        
    Returns:
        True if values are within tolerance, False otherwise
    """
    return abs(value1 - value2) <= tolerance


@handle_errors(default_return={})
def parse_json_safely(json_string: str) -> Dict[str, Any]:
    """
    Safely parse JSON string with error handling.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed dictionary or empty dict on error
    """
    if not json_string or not isinstance(json_string, str):
        return {}
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {str(e)}")
        return {}


def generate_unique_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique identifier.
    
    Args:
        prefix: Prefix for the ID
        length: Length of the random part
        
    Returns:
        Unique identifier string
    """
    import random
    import string
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}"
    else:
        return f"{timestamp}_{random_part}"


def create_fallback_financial_data() -> Dict[str, Any]:
    """
    Create a fallback financial data structure with zero values for all required fields.
    
    Returns:
        Dictionary containing all required financial fields initialized to zero
    """
    fallback_data = {}
    
    # Initialize main metrics
    for metric in MAIN_METRICS:
        fallback_data[metric] = 0.0
    
    # Initialize OpEx components
    for component in OPEX_COMPONENTS:
        fallback_data[component] = 0.0
    
    # Initialize income components
    for component in INCOME_COMPONENTS:
        fallback_data[component] = 0.0
    
    # Add additional commonly used fields
    additional_fields = [
        "property_taxes", "insurance", "repairs_maintenance", "utilities", "management_fees",
        "concessions", "bad_debt", "total_revenue", "total_expenses", "net_operating_income"
    ]
    
    for field in additional_fields:
        fallback_data[field] = 0.0
    
    return fallback_data


def safe_percent_change(current: float, previous: float) -> float:
    """Calculate percent change with consistent rules.
    If |previous| <= FINANCIAL_EPS →
        • both zero  → 0.0
        • current > 0 → 100.0
        • current < 0 → -100.0
    """
    try:
        curr = safe_float(current)
        prev = safe_float(previous)
    except Exception:
        return 0.0
    if abs(prev) <= FINANCIAL_EPS:
        if abs(curr) <= FINANCIAL_EPS:
            return 0.0
        return 100.0 if curr > 0 else -100.0
    return ((curr - prev) / prev) * 100.0


def normalize_field_names(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new dict where all synonym keys are mapped to canonical field names."""
    if not isinstance(data, dict):
        return data  # type: ignore
    normalized = {}
    for k, v in data.items():
        canonical = FIELD_SYNONYMS.get(k, k)
        normalized[canonical] = v
    return normalized 