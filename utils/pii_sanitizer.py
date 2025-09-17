"""
PII Sanitization Utility for NOI Analyzer
Provides functions to sanitize sensitive data before logging or sending to external services
"""

import re
import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

# Patterns for detecting sensitive information
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b')
SSN_PATTERN = re.compile(r'\b[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{4}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{16}\b')
ADDRESS_PATTERN = re.compile(r'\b\d+\s+[A-Za-z0-9\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|court|ct|boulevard|blvd|place|pl|circle|cir|parkway|pkwy|way)\.?\b', re.IGNORECASE)
API_KEY_PATTERN = re.compile(r'\b(sk-[a-zA-Z0-9]{20,})\b')

# Financial data patterns
FINANCIAL_PATTERNS = [
    re.compile(r'\$(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{2})?\b'),  # Dollar amounts
    re.compile(r'\b\d+(?:\.\d{2})?\s*(?:dollars?|usd)\b', re.IGNORECASE),  # Dollar amounts with units
]

# Sensitive field names that should be filtered
SENSITIVE_FIELD_NAMES = [
    'email', 'phone', 'phone_number', 'mobile', 'cell', 'ssn', 'social_security',
    'credit_card', 'card_number', 'cc_number', 'address', 'street', 'city', 'state',
    'zip', 'zipcode', 'postal', 'api_key', 'password', 'secret', 'token', 'credential',
    'financial', 'revenue', 'expense', 'income', 'noi', 'cash_flow', 'property_name',
    'document_content', 'file_content', 'extracted_data', 'financial_data'
]

# Additional patterns for financial document content
FINANCIAL_CONTENT_PATTERNS = [
    re.compile(r'\b(?:gpr|egi|opex|noi|vacancy|concession|turnover)\b', re.IGNORECASE),
    re.compile(r'\b(?:rent|lease|tenant|unit|property|building)\b', re.IGNORECASE),
    re.compile(r'\b(?:maintenance|utilities|insurance|tax|management|payroll)\b', re.IGNORECASE),
]


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing or masking PII.
    
    Args:
        text (str): Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if not isinstance(text, str):
        return text
    
    # Mask email addresses
    text = EMAIL_PATTERN.sub('[EMAIL]', text)
    
    # Mask phone numbers
    text = PHONE_PATTERN.sub('[PHONE]', text)
    
    # Mask SSNs
    text = SSN_PATTERN.sub('[SSN]', text)
    
    # Mask credit card numbers
    text = CREDIT_CARD_PATTERN.sub('[CREDIT_CARD]', text)
    
    # Mask addresses (this is a simple pattern, might need refinement)
    text = ADDRESS_PATTERN.sub('[ADDRESS]', text)
    
    # Mask API keys
    text = API_KEY_PATTERN.sub('[API_KEY]', text)
    
    # Mask financial amounts
    for pattern in FINANCIAL_PATTERNS:
        text = pattern.sub('[AMOUNT]', text)
    
    # Mask financial content terms
    for pattern in FINANCIAL_CONTENT_PATTERNS:
        text = pattern.sub('[FINANCIAL_TERM]', text)
    
    return text


def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary by removing or masking PII.
    
    Args:
        data (dict): Dictionary to sanitize
        max_depth (int): Maximum recursion depth to prevent infinite loops
        
    Returns:
        dict: Sanitized dictionary
    """
    if max_depth <= 0:
        return data
    
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        # Check if the key itself contains sensitive information
        key_lower = str(key).lower()
        is_sensitive_key = any(sensitive in key_lower for sensitive in SENSITIVE_FIELD_NAMES)
        
        # Enhanced check for financial document content
        is_financial_content = ('financial' in key_lower or 'document' in key_lower or 
                               'content' in key_lower or 'data' in key_lower or
                               'consolidated' in key_lower or 'raw' in key_lower)
        
        if is_sensitive_key or is_financial_content:
            # Mask the entire value for sensitive keys
            sanitized[key] = '[FILTERED]'
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            # Recursively sanitize list items
            sanitized[key] = [sanitize_dict(item, max_depth - 1) if isinstance(item, dict) else 
                             sanitize_text(str(item)) if isinstance(item, (str, int, float)) else 
                             item for item in value]
        elif isinstance(value, (str, int, float)):
            # Sanitize string values, with special handling for financial content
            if is_financial_content and len(str(value)) > 100:
                # For large financial content, just mark it as filtered
                sanitized[key] = '[LARGE_FINANCIAL_CONTENT_FILTERED]'
            else:
                sanitized[key] = sanitize_text(str(value))
        else:
            # Keep other values as is
            sanitized[key] = value
    
    return sanitized

def sanitize_data(data: Any) -> Any:
    """
    Sanitize data of any type by removing or masking PII.
    
    Args:
        data: Data to sanitize (any type)
        
    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        return sanitize_dict(data)
    elif isinstance(data, list):
        return [sanitize_dict(item) if isinstance(item, dict) else 
                sanitize_text(str(item)) if isinstance(item, (str, int, float)) else 
                item for item in data]
    elif isinstance(data, (str, int, float)):
        return sanitize_text(str(data))
    else:
        return data

def is_sensitive_content(text: str) -> bool:
    """
    Check if text contains sensitive information.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if sensitive content is detected
    """
    if not isinstance(text, str):
        return False
    
    # Check for sensitive patterns
    patterns = [EMAIL_PATTERN, PHONE_PATTERN, SSN_PATTERN, CREDIT_CARD_PATTERN, ADDRESS_PATTERN, API_KEY_PATTERN]
    return any(pattern.search(text) for pattern in patterns)

# Export the main functions
__all__ = ['sanitize_text', 'sanitize_dict', 'sanitize_data', 'is_sensitive_content']