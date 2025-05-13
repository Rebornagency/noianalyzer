import logging
import json
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('helpers')

def format_for_noi_comparison(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format API response for NOI comparison.
    
    Args:
        api_response: Response from extraction API
        
    Returns:
        Formatted data for NOI comparison
    """
    logger.info("Formatting API response for NOI comparison")
    logger.info(f"API response keys: {list(api_response.keys() if isinstance(api_response, dict) else [])}")
    
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
        'repairs_and_maintenance': 0.0,
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
    
    # Return empty result if API response is invalid
    if not api_response or not isinstance(api_response, dict):
        logger.error(f"Invalid API response: {api_response}")
        return result
    
    # Extract property_id and period
    result['property_id'] = api_response.get('property_id')
    result['period'] = api_response.get('period')
    
    # If metadata exists, try to extract property_id and period from it
    if 'metadata' in api_response and isinstance(api_response['metadata'], dict):
        metadata = api_response['metadata']
        logger.info(f"Found metadata: {metadata}")
        if not result['property_id'] and 'property_id' in metadata:
            result['property_id'] = metadata['property_id']
            logger.info(f"Using property_id from metadata: {result['property_id']}")
        if not result['period'] and 'period' in metadata:
            result['period'] = metadata['period']
            logger.info(f"Using period from metadata: {result['period']}")
    
    # Helper function to safely extract numeric values
    def safe_float(value):
        if value is None:
            return 0.0
        
        # Handle numpy types
        if hasattr(value, 'item'):
            try:
                return float(value.item())
            except:
                return 0.0
        
        # Handle string values
        if isinstance(value, str):
            # Remove currency symbols and commas
            clean_value = value.replace('$', '').replace(',', '').strip()
            try:
                return float(clean_value)
            except ValueError:
                return 0.0
        
        # Handle numeric values
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
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
        'repairs_and_maintenance': 'repairs_and_maintenance',
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
            for field in ['property_taxes', 'insurance', 'repairs_and_maintenance', 'utilities', 'management_fees']:
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
                            logger.info(f"Adding to miscellaneous: {safe_float(item['amount'])}")
        else:
            # If other_income is not a dict, assume it's a direct value
            result['other_income'] = safe_float(other_income)
            logger.info(f"Using flat other_income: {result['other_income']}")
    
    # Map remaining fields from API response to result
    for api_field, result_field in field_mapping.items():
        if api_field in financials and api_field not in ['operating_expenses', 'other_income']:
            result[result_field] = safe_float(financials[api_field])
    
    # Calculate EGI if not provided
    if result['egi'] == 0.0 and result['gpr'] > 0.0:
        egi = result['gpr']
        egi -= result['vacancy_loss']
        egi -= result['concessions']
        egi -= result['bad_debt']
        egi += result['other_income']
        result['egi'] = egi
        logger.info(f"Calculated EGI: {result['egi']}")
    
    # Calculate NOI if not provided
    if result['noi'] == 0.0 and result['egi'] > 0.0 and result['opex'] > 0.0:
        result['noi'] = result['egi'] - result['opex']
        logger.info(f"Calculated NOI: {result['noi']}")
    
    # Log the formatted result
    logger.info(f"Formatted result: property_id={result['property_id']}, period={result['period']}")
    logger.info(f"Financial values: gpr={result['gpr']}, vacancy_loss={result['vacancy_loss']}, egi={result['egi']}, opex={result['opex']}, noi={result['noi']}")
    
    return result

def calculate_noi_comparisons(
    current_data: Dict[str, Any],
    budget_data: Optional[Dict[str, Any]] = None,
    prior_month_data: Optional[Dict[str, Any]] = None,
    prior_year_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate NOI comparisons between current data and other periods.
    
    Args:
        current_data: Current period data
        budget_data: Budget data (optional)
        prior_month_data: Prior month data (optional)
        prior_year_data: Prior year data (optional)
        
    Returns:
        Dictionary with comparison results
    """
    logger.info("Calculating NOI comparisons")
    
    # Initialize result
    result = {
        'current': current_data,
        'actual_vs_budget': None,
        'month_vs_prior': None,
        'year_vs_year': None
    }
    
    # Calculate actual vs budget comparison
    if budget_data:
        logger.info("Calculating actual vs budget comparison")
        avb = {}
        
        for key in ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 'egi', 'opex', 'noi']:
            current_value = current_data.get(key)
            budget_value = budget_data.get(key)
            
            # Skip if either value is None
            if current_value is None or budget_value is None:
                avb[f'{key}_budget'] = budget_value
                avb[f'{key}_variance'] = None
                avb[f'{key}_percent_variance'] = None
                continue
            
            # Calculate variance
            variance = current_value - budget_value
            
            # Calculate percent variance
            if budget_value != 0:
                percent_variance = (variance / abs(budget_value)) * 100
            else:
                percent_variance = 0 if variance == 0 else float('inf')
            
            # Store results
            avb[f'{key}_budget'] = budget_value
            avb[f'{key}_variance'] = variance
            avb[f'{key}_percent_variance'] = percent_variance
        
        result['actual_vs_budget'] = avb
    
    # Calculate month vs prior month comparison
    if prior_month_data:
        logger.info("Calculating month vs prior month comparison")
        mom = {}
        
        for key in ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 'egi', 'opex', 'noi']:
            current_value = current_data.get(key)
            prior_value = prior_month_data.get(key)
            
            # Skip if either value is None
            if current_value is None or prior_value is None:
                mom[f'{key}_prior'] = prior_value
                mom[f'{key}_change'] = None
                mom[f'{key}_percent_change'] = None
                continue
            
            # Calculate change
            change = current_value - prior_value
            
            # Calculate percent change
            if prior_value != 0:
                percent_change = (change / abs(prior_value)) * 100
            else:
                percent_change = 0 if change == 0 else float('inf')
            
            # Store results
            mom[f'{key}_prior'] = prior_value
            mom[f'{key}_change'] = change
            mom[f'{key}_percent_change'] = percent_change
        
        result['month_vs_prior'] = mom
    
    # Calculate year vs prior year comparison
    if prior_year_data:
        logger.info("Calculating year vs prior year comparison")
        yoy = {}
        
        for key in ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 'egi', 'opex', 'noi']:
            current_value = current_data.get(key)
            prior_value = prior_year_data.get(key)
            
            # Skip if either value is None
            if current_value is None or prior_value is None:
                yoy[f'{key}_prior_year'] = prior_value
                yoy[f'{key}_change'] = None
                yoy[f'{key}_percent_change'] = None
                continue
            
            # Calculate change
            change = current_value - prior_value
            
            # Calculate percent change
            if prior_value != 0:
                percent_change = (change / abs(prior_value)) * 100
            else:
                percent_change = 0 if change == 0 else float('inf')
            
            # Store results
            yoy[f'{key}_prior_year'] = prior_value
            yoy[f'{key}_change'] = change
            yoy[f'{key}_percent_change'] = percent_change
        
        result['year_vs_year'] = yoy
    
    return result

def format_currency(value: Optional[float]) -> str:
    """
    Format value as currency.
    
    Args:
        value: Value to format
        
    Returns:
        Formatted currency string
    """
    if value is None:
        return "N/A"
    return f"${value:,.2f}"

def format_percent(value: Optional[float]) -> str:
    """
    Format value as percentage.
    
    Args:
        value: Value to format
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"
    return f"{value:.1f}%"

def format_change(value: Optional[float], is_favorable: bool = True) -> str:
    """
    Format change value with color indicator.
    
    Args:
        value: Value to format
        is_favorable: Whether positive change is favorable
        
    Returns:
        Formatted change string with color indicator
    """
    if value is None:
        return "N/A"
    
    if value > 0:
        color = "green" if is_favorable else "red"
        return f"<span style='color:{color}'>+{format_currency(value)}</span>"
    elif value < 0:
        color = "red" if is_favorable else "green"
        return f"<span style='color:{color}'>{format_currency(value)}</span>"
    else:
        return f"{format_currency(value)}"

def format_percent_change(value: Optional[float], is_favorable: bool = True) -> str:
    """
    Format percentage change with color indicator.
    
    Args:
        value: Value to format
        is_favorable: Whether positive change is favorable
        
    Returns:
        Formatted percentage change string with color indicator
    """
    if value is None:
        return "N/A"
    
    if value > 0:
        color = "green" if is_favorable else "red"
        return f"<span style='color:{color}'>+{format_percent(value)}</span>"
    elif value < 0:
        color = "red" if is_favorable else "green"
        return f"<span style='color:{color}'>{format_percent(value)}</span>"
    else:
        return f"{format_percent(value)}"

def create_comparison_dataframe(comparison_data: Dict[str, Any], comparison_type: str) -> pd.DataFrame:
    """
    Create DataFrame for comparison visualization.
    
    Args:
        comparison_data: Comparison data
        comparison_type: Type of comparison (actual_vs_budget, month_vs_prior, year_vs_year)
        
    Returns:
        DataFrame with comparison data
    """
    logger.info(f"Creating comparison DataFrame for {comparison_type}")
    
    # Get current data
    current = comparison_data.get('current', {})
    
    # Get comparison data based on type
    if comparison_type == 'actual_vs_budget':
        comp = comparison_data.get('actual_vs_budget', {})
        if not comp:
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
    
    elif comparison_type == 'month_vs_prior':
        comp = comparison_data.get('month_vs_prior', {})
        if not comp:
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
            # Determine if positive change is favorable (different for expenses)
            is_favorable = key not in ['vacancy_loss', 'opex']
            
            # Get values
            current_value = current.get(key)
            prior = comp.get(f'{key}_prior')
            change = comp.get(f'{key}_change')
            percent_change = comp.get(f'{key}_percent_change')
            
            # Format values
            current_fmt = format_currency(current_value)
            prior_fmt = format_currency(prior)
            change_fmt = format_change(change, is_favorable)
            percent_change_fmt = format_percent_change(percent_change, is_favorable)
            
            # Add to data
            data.append({
                'Category': label,
                'Current': current_fmt,
                'Prior': prior_fmt,
                'Change': change_fmt,
                'Change %': percent_change_fmt,
                'Current_raw': current_value,
                'Prior_raw': prior,
                'Change_raw': change,
                'Change_%_raw': percent_change
            })
        
        return pd.DataFrame(data)
    
    elif comparison_type == 'year_vs_year':
        comp = comparison_data.get('year_vs_year', {})
        if not comp:
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
            # Determine if positive change is favorable (different for expenses)
            is_favorable = key not in ['vacancy_loss', 'opex']
            
            # Get values
            current_value = current.get(key)
            prior = comp.get(f'{key}_prior_year')
            change = comp.get(f'{key}_change')
            percent_change = comp.get(f'{key}_percent_change')
            
            # Format values
            current_fmt = format_currency(current_value)
            prior_fmt = format_currency(prior)
            change_fmt = format_change(change, is_favorable)
            percent_change_fmt = format_percent_change(percent_change, is_favorable)
            
            # Add to data
            data.append({
                'Category': label,
                'Current': current_fmt,
                'Prior Year': prior_fmt,
                'Change': change_fmt,
                'Change %': percent_change_fmt,
                'Current_raw': current_value,
                'Prior_Year_raw': prior,
                'Change_raw': change,
                'Change_%_raw': percent_change
            })
        
        return pd.DataFrame(data)
    
    # Return empty DataFrame if comparison type is not recognized
    return pd.DataFrame()

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
