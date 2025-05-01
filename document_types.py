"""
Compatibility layer for document type handling between extraction API and NOI analyzer
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger('document_types')

# Standard document types
STANDARD_DOCUMENT_TYPES = {
    'profit_loss': ['p&l', 'income_statement', 'profit and loss', 'income statement'],
    'balance_sheet': ['balance sheet', 'balancesheet', 'bs'],
    'rent_roll': ['rent roll', 'rentroll', 'rr'],
    'operating_statement': ['operating statement', 'operations', 'op_statement'],
    'budget': ['budget', 'forecast', 'projection', 'plan'],
    'trailing_12': ['t12', 't12m', 'trailing 12', 'trailing twelve', 'ttm']
}

# Period type mapping
PERIOD_TYPE_MAPPING = {
    'current': ['current', 'actual', 'this month', 'current month'],
    'prior_month': ['prior month', 'previous month', 'last month', 'mom'],
    'budget': ['budget', 'budgeted', 'forecast', 'plan', 'projected'],
    'prior_year': ['prior year', 'previous year', 'last year', 'yoy']
}

def standardize_document_type(doc_type: Optional[str]) -> Optional[str]:
    """
    Standardize document type string to a common format
    """
    if not doc_type:
        return None
    
    doc_type_lower = doc_type.lower().strip()
    
    for standard_type, variations in STANDARD_DOCUMENT_TYPES.items():
        if doc_type_lower == standard_type or any(v in doc_type_lower for v in variations):
            return standard_type
    
    # If we can't determine, log and return original
    logger.warning(f"Unknown document type: {doc_type}")
    return doc_type

def standardize_period_type(period_type: Optional[str]) -> str:
    """
    Standardize period type string to a common format
    """
    if not period_type:
        return 'current'
    
    period_type_lower = period_type.lower().strip()
    
    for standard_type, variations in PERIOD_TYPE_MAPPING.items():
        if period_type_lower == standard_type or any(v in period_type_lower for v in variations):
            return standard_type
    
    # Default to current if unknown
    logger.warning(f"Unknown period type: {period_type}, defaulting to 'current'")
    return 'current'

def detect_document_properties(filename: Optional[str], text_content: Optional[str]) -> Dict[str, Any]:
    """
    Detect document properties from filename and content
    """
    result = {
        'document_type': None,
        'period_type': 'current',
        'period': None
    }
    
    # Try to detect from filename
    if filename:
        import re
        
        # Try to detect document type
        for doc_type, patterns in STANDARD_DOCUMENT_TYPES.items():
            if any(pattern in filename.lower() for pattern in patterns):
                result['document_type'] = doc_type
                break
        
        # Try to detect period
        # Format: YYYY-MM or MM-YYYY
        date_patterns = [
            r'(\d{4})[_-](\d{2})',  # YYYY-MM
            r'(\d{2})[_-](\d{4})',  # MM-YYYY
            r'(\d{2})[_-](\d{2})[_-](\d{4})'  # MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    if len(groups[0]) == 4:  # YYYY-MM
                        result['period'] = f"{groups[0]}-{groups[1]}"
                    else:  # MM-YYYY
                        result['period'] = f"{groups[1]}-{groups[0]}"
                elif len(groups) == 3:  # MM-DD-YYYY
                    result['period'] = f"{groups[2]}-{groups[0]}"
                break
    
    # Try to detect from content if available
    if text_content and not result['document_type']:
        # Simple keyword matching
        first_page = text_content.split('\n\n')[0] if '\n\n' in text_content else text_content
        first_page = first_page.lower()
        
        for doc_type, patterns in STANDARD_DOCUMENT_TYPES.items():
            if any(pattern in first_page for pattern in patterns):
                result['document_type'] = doc_type
                break
    
    return result 