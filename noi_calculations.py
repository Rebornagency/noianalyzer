import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_calculations')

def safe_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0

def calculate_noi_comparisons(consolidated_data: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate detailed NOI comparisons with improved data handling and validation
    """
    comparison_results = {}
    
    logger.info(f"calculate_noi_comparisons received data with keys: {list(consolidated_data.keys())}")
    
    # Check if we've already transformed the data to avoid double transformation
    if any(key in ['month_vs_prior', 'actual_vs_budget', 'year_vs_year', 'current'] for key in consolidated_data.keys()):
        logger.warning("calculate_noi_comparisons was called with data that appears to be already transformed")
        # If any key has _current suffix, this is already transformed data
        sample_keys = list(consolidated_data.get('month_vs_prior', {}).keys())[:5] if 'month_vs_prior' in consolidated_data else []
        if sample_keys and any(key.endswith('_current') for key in sample_keys):
            logger.info("Returning already transformed data to avoid double transformation")
            return consolidated_data
        
    # Handle the legacy format of consolidated_data from utils/helpers.py calculate_noi_comparisons
    if all(key in ['current', 'actual_vs_budget', 'month_vs_prior', 'year_vs_year'] for key in consolidated_data.keys() if key != 'error'):
        logger.info("Received data in legacy format - already has transformed structure")
        # Reformat if needed (e.g., backfill missing keys)
        # But generally just pass it through
        return consolidated_data
    
    # Handle the new format from process_all_documents (keys like current_month, prior_month, etc.)
    mapped_keys = {
        'current_month': 'current', 
        'prior_month': 'prior_month',
        'budget': 'budget',
        'prior_year': 'prior_year'
    }
    
    # Map the consolidated data to our working format
    working_data = {}
    for source_key, target_key in mapped_keys.items():
        if source_key in consolidated_data:
            if consolidated_data[source_key]:  # Check if not None
                working_data[target_key] = consolidated_data[source_key]
                logger.info(f"Mapped {source_key} to {target_key}")
                if target_key == 'current':
                    logger.info(f"Current data keys: {list(working_data[target_key].keys())}")
            else:
                logger.warning(f"Skipping None value for {source_key}")
    
    # If no current data found under current_month, look for it under "current"
    if 'current' not in working_data and 'current' in consolidated_data:
        working_data['current'] = consolidated_data['current']
        logger.info("Using 'current' key directly from input data")
        
    # Confirm we have current data
    if 'current' not in working_data:
        logger.error("No current data found in any format - cannot calculate comparisons")
        return {'error': 'No current data found to calculate comparisons'}
    
    def normalize_data(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize input data structure"""
        if not data:
            logger.warning("normalize_data received empty or None data")
            return {}
        
        logger.info(f"Normalizing data with keys: {list(data.keys())}")
        financials = data.get('financials', data)
        normalized = {}
        
        # Define standard key mappings to normalize different naming conventions
        standard_keys = {
            # Standard keys from format_for_noi_comparison
            'gpr': 'gpr',  
            'vacancy_loss': 'vacancy_loss',
            'concessions': 'concessions',
            'bad_debt': 'bad_debt',
            'other_income': 'other_income',
            'egi': 'egi',
            'opex': 'opex',
            'noi': 'noi',
            'property_taxes': 'property_taxes',
            'insurance': 'insurance',
            'repairs_and_maintenance': 'repairs_and_maintenance',
            'utilities': 'utilities',
            'management_fees': 'management_fees',
            
            # Legacy extraction API direct keys
            'gross_potential_rent': 'gpr',
            'operating_expenses': 'opex',  # We'll handle nested case separately
            'net_operating_income': 'noi',
            'effective_gross_income': 'egi',
            'operating_expenses_total': 'opex',
            'repairs_maintenance': 'repairs_and_maintenance'
        }
        
        # Copy known keys with standardized names
        for source_key, target_key in standard_keys.items():
            if source_key in financials and financials[source_key] is not None:
                normalized[target_key] = financials[source_key]
        
        # For any keys not covered, copy them as is
        for key, value in financials.items():
            if key not in standard_keys and value is not None:
                normalized[key] = value
        
        # Extract nested OpEx components if they exist
        if "operating_expenses" in financials and isinstance(financials["operating_expenses"], dict):
            opex_data = financials["operating_expenses"]
            logger.info(f"Found nested operating_expenses with keys: {list(opex_data.keys())}")
            
            # Set total OpEx
            if "total_operating_expenses" in opex_data:
                normalized["opex"] = opex_data["total_operating_expenses"]
                logger.info(f"Extracted opex value: {normalized['opex']}")
            
            # Extract each OpEx component
            component_mapping = {
                "property_taxes": ["property_taxes", "taxes"],
                "insurance": ["insurance"],
                "repairs_and_maintenance": ["repairs_maintenance", "repairs", "maintenance"],
                "utilities": ["utilities"],
                "management_fees": ["management_fees", "management"]
            }
            
            # Try to extract each component using various possible field names
            for normalized_key, possible_fields in component_mapping.items():
                for field in possible_fields:
                    if field in opex_data and opex_data[field] is not None:
                        normalized[normalized_key] = opex_data[field]
                        break
        else:
            logger.info("No nested operating_expenses found or it's not a dictionary")
        
        # If opex is still not set, try the operating_expenses as a direct value
        if "opex" not in normalized and "operating_expenses" in financials and not isinstance(financials["operating_expenses"], dict):
            normalized["opex"] = financials["operating_expenses"]
            logger.info(f"Using flat operating_expenses for opex: {normalized['opex']}")
        
        # Handle nested other_income if it exists
        if "other_income" in financials and isinstance(financials["other_income"], dict):
            other_income_data = financials["other_income"]
            logger.info(f"Found nested other_income with keys: {list(other_income_data.keys())}")
            
            # Extract total other_income
            if "total" in other_income_data:
                normalized["other_income"] = other_income_data["total"]
                logger.info(f"Extracted other_income value: {normalized['other_income']}")
        
        # Ensure all OpEx components exist with default values if missing
        opex_components = ["property_taxes", "insurance", "repairs_and_maintenance", "utilities", "management_fees"]
        for component in opex_components:
            if component not in normalized:
                normalized[component] = 0
        
        # Ensure all standard keys exist with default values
        for key in ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 'egi', 'opex', 'noi']:
            if key not in normalized:
                normalized[key] = 0
                logger.warning(f"Adding missing key with default value: {key}=0")
        
        logger.info(f"Normalized data: gpr={normalized.get('gpr')}, opex={normalized.get('opex')}, noi={normalized.get('noi')}")
        return normalized
    
    def safe_percent_change(current: float, previous: float) -> float:
        """Calculate percentage change with improved handling of edge cases"""
        if abs(previous) < 0.0001:  # Avoid division by near-zero
            return 0.0 if abs(current) < 0.0001 else 100.0
        return ((current - previous) / previous) * 100
    
    # Normalize all input data
    normalized_data = {
        period: normalize_data(data)
        for period, data in working_data.items()
    }
    
    logger.info(f"Normalized data periods: {list(normalized_data.keys())}")
    
    # Get current period data - handle either 'current_month' or 'current'
    current_data = normalized_data.get("current_month", normalized_data.get("current", {}))
    if not current_data:
        logger.error("No current month data available")
        return {"error": "No current month data available"}
    
    # Store current data under the 'current' key for consistency
    comparison_results["current"] = current_data
    
    # Define metrics to compare, now including OpEx components
    metrics = [
        "gpr", "vacancy_loss", "concessions", "bad_debt",
        "other_income", "parking", "laundry", "late_fees", "pet_fees", "application_fees",
        "storage_fees", "amenity_fees", "utility_reimbursements", 
        "cleaning_fees", "cancellation_fees", "miscellaneous",
        "egi", "opex", "property_taxes", "insurance", 
        "repairs_and_maintenance", "utilities", "management_fees", "noi"
    ]
    
    # Calculate comparisons with correct output structure for each period type
    comparison_mapping = {
        "month_vs_prior": "prior_month",
        "actual_vs_budget": "budget",
        "year_vs_year": "prior_year"
    }
    
    for result_key, data_key in comparison_mapping.items():
        comparison_data = normalized_data.get(data_key, {})
        if comparison_data:
            logger.info(f"Calculating {result_key} comparison with {data_key}")
            results = {}
            
            for metric in metrics:
                current_val = safe_float(current_data.get(metric))
                compare_val = safe_float(comparison_data.get(metric))
                
                # Store with the correct field suffixes for the display function
                results[f"{metric}_current"] = current_val
                results[f"{metric}_compare"] = compare_val
                results[f"{metric}_change"] = current_val - compare_val
                results[f"{metric}_percent_change"] = safe_percent_change(
                    current_val, compare_val
                )
            
            comparison_results[result_key] = results
            logger.info(f"Calculated {result_key} with {len(results)} metrics")
            
            # Add a debug check to verify some key metrics were properly calculated
            if "noi_current" in results and "noi_compare" in results:
                logger.info(f"{result_key} - NOI current: {results['noi_current']}, compare: {results['noi_compare']}")
            else:
                logger.warning(f"{result_key} - Missing expected NOI fields")
        else:
            logger.warning(f"No {data_key} data available for {result_key} comparison")
    
    # Validate results
    validate_comparison_results(comparison_results)
    
    # Add backward compatibility for display_comparison_tab function
    # The function expects certain keys with specific suffixes
    if "month_vs_prior" in comparison_results:
        for metric in metrics:
            if f"{metric}_current" in comparison_results["month_vs_prior"]:
                comparison_results["month_vs_prior"][f"{metric}_prior"] = comparison_results["month_vs_prior"][f"{metric}_compare"]
    
    if "actual_vs_budget" in comparison_results:
        for metric in metrics:
            if f"{metric}_current" in comparison_results["actual_vs_budget"]:
                comparison_results["actual_vs_budget"][f"{metric}_budget"] = comparison_results["actual_vs_budget"][f"{metric}_compare"]
    
    if "year_vs_year" in comparison_results:
        for metric in metrics:
            if f"{metric}_current" in comparison_results["year_vs_year"]:
                comparison_results["year_vs_year"][f"{metric}_prior_year"] = comparison_results["year_vs_year"][f"{metric}_compare"]
    
    # Final structure validation before returning
    result_keys = list(comparison_results.keys())
    logger.info(f"Final comparison results keys: {result_keys}")
    
    # Verify the expected structure is present
    if "month_vs_prior" in comparison_results:
        sample_keys = list(comparison_results["month_vs_prior"].keys())[:5]
        logger.info(f"Sample keys in month_vs_prior: {sample_keys}")
        
        # Perform additional compatibility checks
        expected_key_formats = ['_current', '_prior', '_change', '_percent_change']
        for metric in metrics[:3]:  # Check just a few key metrics
            for suffix in expected_key_formats:
                key = f"{metric}{suffix}"
                if key not in comparison_results["month_vs_prior"]:
                    logger.warning(f"Expected key {key} missing from month_vs_prior")
    
    return comparison_results

def validate_comparison_results(comparison_results: Dict[str, Any]) -> None:
    """
    Enhanced validation of comparison results
    """
    if "current" not in comparison_results:
        logger.warning("No current month data available for validation")
        return
    
    current = comparison_results["current"]
    
    # Validate EGI calculation
    calculated_egi = (
        safe_float(current.get("gpr")) -
        safe_float(current.get("vacancy_loss")) -
        safe_float(current.get("concessions")) -
        safe_float(current.get("bad_debt")) +
        safe_float(current.get("other_income"))
    )
    
    reported_egi = safe_float(current.get("egi"))
    
    if abs(calculated_egi - reported_egi) > 0.01:
        logger.warning(
            f"EGI calculation mismatch: reported={reported_egi:.2f}, "
            f"calculated={calculated_egi:.2f}"
        )
    
    # Validate NOI calculation
    calculated_noi = calculated_egi - safe_float(current.get("opex"))
    reported_noi = safe_float(current.get("noi"))
    
    if abs(calculated_noi - reported_noi) > 0.01:
        logger.warning(
            f"NOI calculation mismatch: reported={reported_noi:.2f}, "
            f"calculated={calculated_noi:.2f}"
        )
    
    # Validate OpEx breakdown summing to total OpEx
    total_opex = safe_float(current.get("opex"))
    sum_components = (
        safe_float(current.get("property_taxes")) +
        safe_float(current.get("insurance")) +
        safe_float(current.get("repairs_and_maintenance")) +
        safe_float(current.get("utilities")) +
        safe_float(current.get("management_fees"))
    )
    
    # Allow some tolerance for rounding errors
    if abs(total_opex - sum_components) > 0.1 and total_opex > 0:
        logger.warning(
            f"OpEx components sum mismatch: total={total_opex:.2f}, "
            f"component sum={sum_components:.2f}"
        )
