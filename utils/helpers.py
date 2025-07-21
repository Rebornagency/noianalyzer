import logging
import json
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

from constants import MAIN_METRICS, OPEX_COMPONENTS, INCOME_COMPONENTS, ERROR_MESSAGES
from utils.error_handler import setup_logger, handle_errors, DataValidationError, create_error_response
from utils.common import (
    safe_float, safe_string, format_currency, format_percent, format_change,
    clean_financial_data, summarize_dict_for_logging, compare_with_tolerance
)

# Setup logger
logger = setup_logger(__name__)


@handle_errors(default_return={})
def format_for_noi_comparison(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format API response for NOI comparison with improved error handling.
    
    Args:
        api_response: Response from extraction API
        
    Returns:
        Formatted data for NOI comparison
        
    Raises:
        DataValidationError: If API response is invalid
    """
    logger.info("Formatting API response for NOI comparison")
    
    if not api_response or not isinstance(api_response, dict):
        logger.error(f"Invalid API response: {type(api_response)}")
        raise DataValidationError(ERROR_MESSAGES["INVALID_API_RESPONSE"])
    
    # Log structure for debugging (safely)
    try:
        response_summary = summarize_dict_for_logging(api_response)
        logger.info(f"API response structure: {json.dumps(response_summary, default=str)}")
    except Exception as e:
        logger.warning(f"Could not log API response structure: {str(e)}")
    
    # Initialize result with default values
    result = {
        'property_id': None,
        'period': None,
        'gpr': 0.0,
        'vacancy_loss': 0.0,
        'concessions': 0.0,
        'bad_debt': 0.0,
        'other_income': 0.0,
        'egi': 0.0,
        'opex': 0.0,
        'noi': 0.0,
        # Add OpEx breakdown components
        'property_taxes': 0.0,
        'insurance': 0.0,
        'repairs_maintenance': 0.0,
        'utilities': 0.0,
        'management_fees': 0.0,
        # Add Other Income breakdown components
        'parking': 0.0,
        'laundry': 0.0,
        'late_fees': 0.0,
        'pet_fees': 0.0,
        'application_fees': 0.0,
        'storage_fees': 0.0,
        'amenity_fees': 0.0,
        'utility_reimbursements': 0.0,
        'cleaning_fees': 0.0,
        'cancellation_fees': 0.0,
        'miscellaneous': 0.0
    }
    
    # Extract property_id and period
    result['property_id'] = safe_string(api_response.get('property_id'))
    result['period'] = safe_string(api_response.get('period'))
    
    # If metadata exists, try to extract property_id and period from it
    if 'metadata' in api_response and isinstance(api_response['metadata'], dict):
        metadata = api_response['metadata']
        logger.info(f"Found metadata: {summarize_dict_for_logging(metadata)}")
        if not result['property_id'] and 'property_id' in metadata:
            result['property_id'] = safe_string(metadata['property_id'])
            logger.info(f"Using property_id from metadata: {result['property_id']}")
        if not result['period'] and 'period' in metadata:
            result['period'] = safe_string(metadata['period'])
            logger.info(f"Using period from metadata: {result['period']}")
    
    # Map the flat structure to our expected format
    field_mapping = {
        'gross_potential_rent': 'gpr',
        'vacancy_loss': 'vacancy_loss',
        'concessions': 'concessions',
        'bad_debt': 'bad_debt',
        'effective_gross_income': 'egi',
        'net_operating_income': 'noi',
        'property_taxes': 'property_taxes',
        'insurance': 'insurance',
        'repairs_and_maintenance': 'repairs_maintenance',
        'utilities': 'utilities',
        'management_fees': 'management_fees',
        'parking': 'parking',
        'laundry': 'laundry',
        'late_fees': 'late_fees',
        'pet_fees': 'pet_fees',
        'application_fees': 'application_fees',
        'storage_fees': 'storage_fees',
        'amenity_fees': 'amenity_fees',
        'utility_reimbursements': 'utility_reimbursements',
        'cleaning_fees': 'cleaning_fees',
        'cancellation_fees': 'cancellation_fees',
        'miscellaneous': 'miscellaneous'
    }
    
    # Handle both nested and flat structures
    # First, check if we're working with an extraction v2 API response that might have 'financials'
    financials = api_response
    if 'financials' in api_response and isinstance(api_response['financials'], dict):
        logger.info("Found nested 'financials' object in API response")
        financials = api_response['financials']
    
    # Handle operating_expenses (could be nested or flat)
    operating_expenses = financials.get('operating_expenses')
    if operating_expenses is not None:
        logger.info(f"Found operating_expenses: {type(operating_expenses)}")
        if isinstance(operating_expenses, dict):
            # Extract the total operating expenses from the nested structure
            if 'total_operating_expenses' in operating_expenses:
                result['opex'] = safe_float(operating_expenses['total_operating_expenses'])
                logger.info(f"Using nested total_operating_expenses: {result['opex']}")
            
            # Extract OpEx breakdown components if available
            for field in ['property_taxes', 'insurance', 'repairs_maintenance', 'utilities', 'management_fees']:
                if field in operating_expenses:
                    result[field] = safe_float(operating_expenses[field])
                    logger.info(f"Using nested {field}: {result[field]}")
        else:
            # If operating_expenses is not a dict, assume it's a direct value
            result['opex'] = safe_float(operating_expenses)
            logger.info(f"Using flat operating_expenses: {result['opex']}")
    
    # Also check for operating_expenses_total (flat API format)
    if result['opex'] == 0.0 and 'operating_expenses_total' in financials:
        result['opex'] = safe_float(financials['operating_expenses_total'])
        logger.info(f"Using operating_expenses_total: {result['opex']}")
    
    # Handle other_income (could be nested or flat)
    other_income = financials.get('other_income')
    if other_income is not None:
        logger.info(f"Found other_income: {type(other_income)}")
        if isinstance(other_income, dict):
            # Extract the total other income from the nested structure
            if 'total' in other_income:
                result['other_income'] = safe_float(other_income['total'])
                logger.info(f"Using nested other_income.total: {result['other_income']}")
            
            # Extract other income breakdown components if available
            for field in ['parking', 'laundry', 'late_fees', 'pet_fees', 'application_fees', 
                         'storage_fees', 'amenity_fees', 'utility_reimbursements', 
                         'cleaning_fees', 'cancellation_fees', 'miscellaneous']:
                if field in other_income:
                    result[field] = safe_float(other_income[field])
                    logger.info(f"Using nested {field}: {result[field]}")
            
            # Check for additional_items array (like in the example)
            if 'additional_items' in other_income and isinstance(other_income['additional_items'], list):
                for item in other_income['additional_items']:
                    if isinstance(item, dict) and 'name' in item and 'amount' in item:
                        name = item['name'].lower().replace(' ', '_')
                        # If we have a field for this item, update it
                        if name in result:
                            result[name] = safe_float(item['amount'])
                            logger.info(f"Using additional_item {name}: {result[name]}")
                        # Otherwise, add to miscellaneous
                        else:
                            result['miscellaneous'] += safe_float(item['amount'])
        else:
            # If other_income is not a dict, assume it's a direct value
            result['other_income'] = safe_float(other_income)
            logger.info(f"Using flat other_income: {result['other_income']}")
    
    # Process direct mappings from field_mapping
    for api_field, result_field in field_mapping.items():
        if api_field in financials:
            result[result_field] = safe_float(financials[api_field])
            logger.info(f"Mapped {api_field} -> {result_field}: {result[result_field]}")
    
    # Clean and validate the final result
    result = clean_financial_data(result)
    logger.info(f"Formatted NOI comparison data: {summarize_dict_for_logging(result)}")
    
    return result


@handle_errors(default_return={})
def calculate_noi_comparisons(
    current_data: Dict[str, Any],
    budget_data: Optional[Dict[str, Any]] = None,
    prior_month_data: Optional[Dict[str, Any]] = None,
    prior_year_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate NOI comparisons with improved error handling.
    
    Args:
        current_data: Current period financial data
        budget_data: Budget financial data
        prior_month_data: Prior month financial data
        prior_year_data: Prior year financial data
        
    Returns:
        Dictionary containing all comparison results
    """
    logger.info("Calculating NOI comparisons")
    
    # Clean input data
    current_data = clean_financial_data(current_data)
    
    result = {
        'current': current_data
    }
    
    # Actual vs Budget comparison
    if budget_data:
        budget_data = clean_financial_data(budget_data)
        logger.info("Calculating actual vs budget comparison")
        
        avb = {}
        for key in MAIN_METRICS:
            current_value = current_data.get(key, 0.0)
            budget_value = budget_data.get(key, 0.0)
            
            variance = current_value - budget_value
            percent_variance = ((current_value - budget_value) / budget_value * 100) if budget_value != 0 else 0
            
            # Store budget values and variances
            avb[f'{key}_budget'] = budget_value
            avb[f'{key}_variance'] = variance
            avb[f'{key}_percent_variance'] = percent_variance
        
        result['actual_vs_budget'] = avb
    
    # Month vs Prior comparison
    if prior_month_data:
        prior_month_data = clean_financial_data(prior_month_data)
        logger.info("Calculating month vs prior comparison")
        
        mvp = {}
        for key in MAIN_METRICS:
            current_value = current_data.get(key, 0.0)
            prior_value = prior_month_data.get(key, 0.0)
            
            change = current_value - prior_value
            percent_change = ((current_value - prior_value) / abs(prior_value) * 100) if prior_value != 0 else 0
            
            # Store prior values and changes
            mvp[f'{key}_prior'] = prior_value
            mvp[f'{key}_change'] = change
            mvp[f'{key}_percent_change'] = percent_change
        
        result['month_vs_prior'] = mvp
    
    # Year vs Year comparison
    if prior_year_data:
        prior_year_data = clean_financial_data(prior_year_data)
        logger.info("Calculating year vs year comparison")
        
        yoy = {}
        for key in MAIN_METRICS:
            current_value = current_data.get(key, 0.0)
            prior_value = prior_year_data.get(key, 0.0)
            
            change = current_value - prior_value
            percent_change = ((current_value - prior_value) / abs(prior_value) * 100) if prior_value != 0 else 0
            
            # Store results
            yoy[f'{key}_prior_year'] = prior_value
            yoy[f'{key}_change'] = change
            yoy[f'{key}_percent_change'] = percent_change
        
        result['year_vs_year'] = yoy
    
    logger.info("NOI comparisons calculated successfully")
    return result


# Legacy format functions - keeping for backward compatibility but redirecting to common utilities
# Removing these as they are no longer directly called and redirect to utils.common
# def format_currency(value: Optional[float]) -> str:
#     """Legacy format_currency function"""
#     from utils.common import format_currency as common_format_currency
#     return common_format_currency(value)
#
#
# def format_percent(value: Optional[float]) -> str:
#     """Legacy format_percent function"""
#     from utils.common import format_percent as common_format_percent
#     return common_format_percent(value)


# def format_change(value: Optional[float]) -> str:
#     """Legacy format_change function - ensure this is not needed or also redirects/is handled by common"""
#     # Assuming this might have existed, if it does and needs removal, add its definition here commented out
#     # For now, this is a placeholder based on typical financial apps
#     from utils.common import format_change as common_format_change # If it existed and redirected
#     return common_format_change(value)


@handle_errors(default_return="N/A")
def format_percent_change(value: Optional[float], is_favorable: bool = True) -> str:
    """
    Format percentage change with color indicator (legacy version with HTML).
    
    Args:
        value: Value to format
        is_favorable: Whether positive change is favorable
        
    Returns:
        Formatted percentage change string with color indicator
    """
    if value is None:
        return "N/A"
    
    try:
        if value > 0:
            color = "green" if is_favorable else "red"
            return f"<span style='color:{color}'>+{value:.1f}%</span>"
        elif value < 0:
            color = "red" if is_favorable else "green"
            return f"<span style='color:{color}'>{value:.1f}%</span>"
        else:
            return f"{value:.1f}%"
    except (ValueError, TypeError):
        return "N/A"


@handle_errors(default_return=pd.DataFrame())
def create_comparison_dataframe(comparison_data: Dict[str, Any], comparison_type: str) -> pd.DataFrame:
    """
    Create DataFrame for comparison visualization with improved error handling.
    
    Args:
        comparison_data: Comparison data
        comparison_type: Type of comparison (actual_vs_budget, month_vs_prior, year_vs_year)
        
    Returns:
        DataFrame with comparison data
    """
    logger.info(f"Creating comparison DataFrame for {comparison_type}")
    
    if not comparison_data or not isinstance(comparison_data, dict):
        logger.warning(f"Invalid comparison data for {comparison_type}")
        return pd.DataFrame()
    
    # Get current data
    current = comparison_data.get('current', {})
    
    # Get comparison data based on type
    if comparison_type == 'actual_vs_budget':
        comp = comparison_data.get('actual_vs_budget', {})
        if not comp:
            logger.warning("No actual_vs_budget data found")
            return pd.DataFrame()
        
        # Create DataFrame
        data = []
        for key, label in [
            ('gpr', 'Gross Potential Rent'),
            ('vacancy_loss', 'Vacancy Loss'),
            ('other_income', 'Other Income'),
            ('egi', 'Effective Gross Income'),
            ('opex', 'Operating Expenses'),
            ('noi', 'Net Operating Income')
        ]:
            # Determine if positive variance is favorable (different for expenses)
            is_favorable = key not in ['vacancy_loss', 'opex']
            
            # Get values
            actual = current.get(key)
            budget = comp.get(f'{key}_budget')
            variance = comp.get(f'{key}_variance')
            percent_variance = comp.get(f'{key}_percent_variance')
            
            # Format values
            actual_fmt = format_currency(actual)
            budget_fmt = format_currency(budget)
            variance_fmt = format_change(variance, is_favorable)
            percent_variance_fmt = format_percent_change(percent_variance, is_favorable)
            
            # Add to data
            data.append({
                'Category': label,
                'Actual': actual_fmt,
                'Budget': budget_fmt,
                'Variance': variance_fmt,
                'Variance %': percent_variance_fmt,
                'Actual_raw': actual,
                'Budget_raw': budget,
                'Variance_raw': variance,
                'Variance_%_raw': percent_variance
            })
        
        return pd.DataFrame(data)
    
    # Add other comparison types (month_vs_prior, year_vs_year) with similar structure
    # ... (implementing similar logic for other comparison types)
    
    logger.warning(f"Unsupported comparison type: {comparison_type}")
    return pd.DataFrame()


@handle_errors(default_return="unknown")
def determine_document_type(filename: str, result: Dict[str, Any]) -> str:
    """
    Determine document type based on filename and content with improved error handling.
    
    Args:
        filename: Name of the file
        result: Extraction result
        
    Returns:
        Document type string
    """
    logger.info(f"Determining document type for file: {filename}")
    
    if not filename:
        logger.warning("Empty filename provided")
        return "unknown"
    
    filename_lower = filename.lower()
    
    # Check filename patterns
    if any(word in filename_lower for word in ['budget', 'budgeted', 'forecast']):
        return 'budget'
    elif any(word in filename_lower for word in ['prior', 'previous', 'last']):
        if any(word in filename_lower for word in ['year', 'annual']):
            return 'prior_year'
        else:
            return 'prior_month'
    elif any(word in filename_lower for word in ['current', 'actual', 'present']):
        return 'current_month'
    
    # Check if result contains document type metadata
    if isinstance(result, dict):
        doc_type = result.get('document_type') or result.get('type')
        if doc_type:
            return safe_string(doc_type).lower()
        
        # Check metadata
        metadata = result.get('metadata', {})
        if isinstance(metadata, dict):
            doc_type = metadata.get('document_type') or metadata.get('type')
            if doc_type:
                return safe_string(doc_type).lower()
    
    logger.info(f"Could not determine document type for {filename}, defaulting to current_month")
    return 'current_month'
