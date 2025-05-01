"""
Helper functions for the NOI Analyzer application
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('helpers')

def format_for_noi_comparison(api_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Enhanced formatting of API results for NOI comparison
    """
    if not api_results:
        return {}
    
    # Get the config for field mappings
    from config import get_config
    config = get_config()
    field_mapping = config['field_mapping']
    
    def normalize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data structure and field names"""
        if not data:
            return {}
            
        # Get financial data
        if 'financials' in data and isinstance(data['financials'], dict):
            financials = data['financials']
        else:
            financials = data
        
        result = {}
        
        # Map fields using the field mapping config
        for standard_key, possible_keys in field_mapping.items():
            for key in possible_keys:
                if key in financials:
                    try:
                        result[standard_key] = float(financials[key] or 0.0)
                        break
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert {key}={financials[key]} to float")
                        result[standard_key] = 0.0
            
            # If key wasn't found, set default
            if standard_key not in result:
                result[standard_key] = 0.0
        
        # Add period and metadata
        result['period'] = data.get('period')
        result['property_id'] = data.get('property_id')
        
        # Categorize the period type
        if 'document_type' in data.get('metadata', {}):
            result['document_type'] = data['metadata']['document_type']
        
        return result
    
    # Organize data by period type
    result = {}
    
    # Default to current month if no type specified
    if 'period_type' not in api_results:
        result['current_month'] = normalize_data(api_results)
    else:
        period_type = api_results['period_type'].lower()
        
        if period_type in ['current', 'actual', 'current_month']:
            result['current_month'] = normalize_data(api_results)
        elif period_type in ['budget', 'budgeted', 'forecast']:
            result['budget'] = normalize_data(api_results)
        elif period_type in ['prior_month', 'previous_month', 'last_month']:
            result['prior_month'] = normalize_data(api_results)
        elif period_type in ['prior_year', 'previous_year', 'last_year']:
            result['prior_year'] = normalize_data(api_results)
        else:
            # Default to current if we can't determine
            logger.warning(f"Unknown period type: {period_type}, defaulting to current_month")
            result['current_month'] = normalize_data(api_results)
    
    return result

def create_comparison_dataframe(comparison_results: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Create a standardized DataFrame from comparison results
    with improved error handling
    """
    if not comparison_results or 'current' not in comparison_results:
        logger.error("No valid comparison results to create DataFrame")
        return None
    
    try:
        # Define standard metrics and their display names
        metrics = [
            ('gpr', 'Gross Potential Rent'),
            ('vacancy_loss', 'Vacancy Loss'),
            ('concessions', 'Concessions'),
            ('bad_debt', 'Bad Debt'),
            ('other_income', 'Other Income'),
            ('egi', 'Effective Gross Income'),
            ('opex', 'Operating Expenses'),
            ('noi', 'Net Operating Income')
        ]
        
        # Create DataFrame
        rows = []
        
        # Current data
        current = comparison_results.get('current', {})
        
        for key, display_name in metrics:
            row = {'Metric': display_name, 'Current': current.get(key, 0.0)}
            
            # Add comparison data
            if 'month_vs_prior' in comparison_results:
                mom = comparison_results['month_vs_prior']
                row['Prior Month'] = mom.get(f"{key}_prior", 0.0)
                row['MoM $'] = mom.get(f"{key}_change", 0.0)
                row['MoM %'] = mom.get(f"{key}_percent_change", 0.0)
            
            if 'actual_vs_budget' in comparison_results:
                avb = comparison_results['actual_vs_budget']
                row['Budget'] = avb.get(f"{key}_budget", 0.0)
                row['Budget $'] = avb.get(f"{key}_variance", 0.0)
                row['Budget %'] = avb.get(f"{key}_percent_variance", 0.0)
            
            if 'year_vs_year' in comparison_results:
                yoy = comparison_results['year_vs_year']
                row['Prior Year'] = yoy.get(f"{key}_prior_year", 0.0)
                row['YoY $'] = yoy.get(f"{key}_change", 0.0)
                row['YoY %'] = yoy.get(f"{key}_percent_change", 0.0)
            
            rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Format percentages and currency values
        for col in df.columns:
            if col.endswith('%'):
                df[col] = df[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
            elif col not in ['Metric'] and not col.endswith('%'):
                df[col] = df[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
        
        return df
        
    except Exception as e:
        logger.error(f"Error creating comparison DataFrame: {str(e)}")
        return None

def determine_document_type(filename: str, result: Dict[str, Any]) -> str:
    """
    Determine the document type based on filename and content
    
    Args:
        filename: Name of the file
        result: Extraction result
        
    Returns:
        Document type (current_month, prior_month, budget, prior_year)
    """
    filename = filename.lower()
    
    # Try to determine from filename first
    if "budget" in filename:
        return "budget"
    elif "prior" in filename or "previous" in filename:
        if "year" in filename:
            return "prior_year"
        else:
            return "prior_month"
    elif "current" in filename or "actual" in filename:
        return "current_month"
    
    # If not determined from filename, try to use document_type from result
    doc_type = result.get("document_type", "").lower()
    if "budget" in doc_type:
        return "budget"
    elif "prior year" in doc_type or "previous year" in doc_type:
        return "prior_year"
    elif "prior" in doc_type or "previous" in doc_type:
        return "prior_month"
    elif "current" in doc_type or "actual" in doc_type:
        return "current_month"
    
    # Default to current_month if can't determine
    return "current_month"

def format_currency(value: float) -> str:
    """
    Format a value as currency
    
    Args:
        value: Numeric value to format
        
    Returns:
        Formatted currency string
    """
    return f"${value:,.2f}"

def format_percent(value: float) -> str:
    """
    Format a value as percentage
    
    Args:
        value: Numeric value to format
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.2f}%"