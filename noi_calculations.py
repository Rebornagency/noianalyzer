import logging
from typing import Dict, Any, List, Optional
import json
import time
from functools import lru_cache
import re # Added for regex in enhanced safe_float

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_calculations')

@lru_cache(maxsize=128)
def safe_float(value: Any, default: float = 0.0) -> float: # Added default parameter to match common.py
    """Safely convert value to float with caching for performance and robust handling."""
    if value is None:
        return default
    
    # Handle numpy types if numpy is an expected dependency, otherwise remove this block
    # For now, assuming it might be encountered from pandas dataframes if they are used upstream.
    if hasattr(value, 'item'):
        try:
            return float(value.item())
        except (ValueError, TypeError):
            # Fall through to string/numeric conversion if item() fails or isn't float-convertible
            pass 
            
    # Handle string values
    if isinstance(value, str):
        # Remove currency symbols, commas, and whitespace. Keep decimal point and minus sign.
        clean_value = re.sub(r'[^\d.-]', '', value.strip())
        if not clean_value or clean_value == '.': # Handle empty or just a dot
            return default
        try:
            return float(clean_value)
        except ValueError:
            return default
    
    # Handle numeric values (int, float, etc.)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

@lru_cache(maxsize=256)
def safe_percent_change(current: float, previous: float) -> float:
    """Calculate percentage change with caching for frequently used calculations"""
    if abs(previous) < 0.0001:  # Avoid division by near-zero
        return 0.0 if abs(current) < 0.0001 else 100.0
    return ((current - previous) / previous) * 100

@lru_cache(maxsize=128)
def calculate_egi(gpr: float, vacancy_loss: float, concessions: float, bad_debt: float, other_income: float) -> float:
    """Calculate EGI with caching for repeated calculations"""
    return gpr - vacancy_loss - concessions - bad_debt + other_income

@lru_cache(maxsize=128)
def calculate_noi(egi: float, opex: float) -> float:
    """Calculate NOI with caching for repeated calculations"""
    return egi - opex

@lru_cache(maxsize=64)
def calculate_opex_sum(property_taxes: float, insurance: float, repairs_maintenance: float, utilities: float, management_fees: float) -> float:
    """Calculate sum of OpEx components with caching"""
    return property_taxes + insurance + repairs_maintenance + utilities + management_fees

def calculate_noi_comparisons(consolidated_data: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Always returns a dict with keys: month_vs_prior, actual_vs_budget, year_vs_year.
    Each value is a dict with keys like gpr_current, gpr_prior, etc.
    """
    start_time = time.time()
    
    # If already transformed, return as-is
    if all(
        k in consolidated_data
        for k in ["month_vs_prior", "actual_vs_budget", "year_vs_year"]
    ):
        logger.info(f"NOI comparisons already calculated, returning cached result in {time.time() - start_time:.3f}s")
        return consolidated_data

    # Log input structure to help troubleshoot
    logger.info(f"calculate_noi_comparisons: Input data keys: {list(consolidated_data.keys())}")
    for key, data_item in consolidated_data.items():
        if isinstance(data_item, dict):
            logger.info(f"calculate_noi_comparisons: Input '{key}' (keys): {list(data_item.keys())}")
            try:
                # Log only a few key metrics to avoid overly verbose logs if the dict is huge
                log_snippet = {k: data_item[k] for k in ['period', 'gpr', 'noi', 'opex'] if k in data_item}
                logger.info(f"calculate_noi_comparisons: Input '{key}' (snippet): {json.dumps(log_snippet, default=str)}")
            except Exception as e:
                logger.error(f"Error logging input snippet for {key}: {e}")
        elif data_item is not None:
            logger.info(f"calculate_noi_comparisons: Input '{key}' is not a dict, type: {type(data_item)}")

    # Defensive: check for raw keys
    current = consolidated_data.get("current_month")
    prior = consolidated_data.get("prior_month")
    budget = consolidated_data.get("budget")
    prior_year = consolidated_data.get("prior_year")

    # Log availability of each data type
    logger.info(f"Data available: current={current is not None}, prior={prior is not None}, budget={budget is not None}, prior_year={prior_year is not None}")
    
    # If current data exists, log its structure
    if current:
        logger.info(f"Current data keys: {list(current.keys())}")
        logger.info(f"Current data NOI: {current.get('noi')}")

    def build_comparison(current, compare, compare_suffix):
        """
        Build comparison data structure with proper suffixes.
        This handles the transformation from flat format to the expected display format.
        """
        comp_start_time = time.time()
        logger.info(f"Building comparison for '{compare_suffix}'")
        if not current:
            logger.warning(f"Build_comparison for '{compare_suffix}': Current data is missing or None.")
        else:
            try:
                logger.info(f"Build_comparison for '{compare_suffix}' - Current data (snippet): {json.dumps({k: current[k] for k in ['period', 'gpr', 'noi'] if k in current}, default=str)}")
            except Exception as e:
                logger.error(f"Error logging current data snippet for {compare_suffix}: {e}")
        if not compare:
            logger.warning(f"Build_comparison for '{compare_suffix}': Compare data is missing or None.")
        else:
            try:
                logger.info(f"Build_comparison for '{compare_suffix}' - Compare data (snippet): {json.dumps({k: compare[k] for k in ['period', 'gpr', 'noi'] if k in compare}, default=str)}")
            except Exception as e:
                logger.error(f"Error logging compare data snippet for {compare_suffix}: {e}")

        if not current or not compare:
            logger.warning(f"Missing data for {compare_suffix} comparison: current={current is not None}, compare={compare is not None}")
            return {}
            
        result = {}
        metrics = [
            "gpr", "vacancy_loss", "concessions", "bad_debt", "other_income", "egi", "opex", "noi",
            "property_taxes", "insurance", "repairs_and_maintenance", "utilities", "management_fees",
            "parking", "laundry", "late_fees", "pet_fees", "application_fees", "storage_fees",
            "amenity_fees", "utility_reimbursements", "cleaning_fees", "cancellation_fees", "miscellaneous"
        ]
        
        # Log metric availability in both datasets
        metrics_present_current = [m for m in metrics if m in current]
        metrics_present_compare = [m for m in metrics if m in compare]
        logger.info(f"Metrics in current: {len(metrics_present_current)}/{len(metrics)}, in {compare_suffix}: {len(metrics_present_compare)}/{len(metrics)}")
        
        for m in metrics:
            current_val = safe_float(current.get(m, 0))
            compare_val = safe_float(compare.get(m, 0))
            
            # Store values with proper suffixes
            result[f"{m}_current"] = current_val
            result[f"{m}_{compare_suffix}"] = compare_val
            
            # Calculate changes using memoized function
            change = current_val - compare_val
            
            # Determine which suffix to use based on comparison type
            change_suffix = "variance" if compare_suffix == "budget" else "change"
            pct_change_suffix = "percent_variance" if compare_suffix == "budget" else "percent_change"
            
            # Store change values
            result[f"{m}_{change_suffix}"] = change
            
            # Calculate and store percent change using cached function
            if compare_val != 0:
                result[f"{m}_{pct_change_suffix}"] = safe_percent_change(current_val, compare_val)
            else:
                # Handle zero division - if current is positive, treat as 100% increase
                # Ensure current_val is treated as float for this logic
                current_val_float = float(current_val) # Explicit cast for safety
                if current_val_float > 0:
                    result[f"{m}_{pct_change_suffix}"] = 100.0
                # If current is negative, treat as -100% decrease
                elif current_val_float < 0:
                    result[f"{m}_{pct_change_suffix}"] = -100.0
                else:
                    # Both zero, no change
                    result[f"{m}_{pct_change_suffix}"] = 0.0
        
        comp_time = time.time() - comp_start_time
        logger.info(f"Built {compare_suffix} comparison with {len(result)} metric fields in {comp_time:.3f}s")
        try:
            logger.info(f"Full result for {compare_suffix} comparison: {json.dumps(result, default=str, indent=2)}")
        except Exception as e:
            logger.error(f"Error logging full result for {compare_suffix}: {e}")
        return result

    # Build the comparison data structures with timing
    comparison_start = time.time()
    month_vs_prior = build_comparison(current, prior, "prior")
    actual_vs_budget = build_comparison(current, budget, "budget")
    year_vs_year = build_comparison(current, prior_year, "prior_year")
    comparison_time = time.time() - comparison_start
    
    result = {
        "month_vs_prior": month_vs_prior,
        "actual_vs_budget": actual_vs_budget,
        "year_vs_year": year_vs_year,
        "current": current or {},
        "prior": prior or {},
        "budget": budget or {},
        "prior_year": prior_year or {},
    }
    
    # Log the output structure with performance metrics
    total_time = time.time() - start_time
    logger.info(f"calculate_noi_comparisons: Final Output data (top-level keys): {list(result.keys())}")
    logger.info(f"Performance: Total calculation time: {total_time:.3f}s, Comparison calculations: {comparison_time:.3f}s")
    
    for key, data_item in result.items():
        if isinstance(data_item, dict):
            logger.info(f"calculate_noi_comparisons: Output section '{key}' (keys): {list(data_item.keys())}")
            try:
                # Log snippet for comparison sections, full for raw data sections
                if "_vs_" in key: # Heuristic for comparison sections
                    log_snippet = {k: data_item[k] for k in list(data_item.keys())[:5]} # Log first 5 key-value pairs
                    logger.info(f"calculate_noi_comparisons: Output section '{key}' (snippet): {json.dumps(log_snippet, default=str)}")
                else: # For 'current', 'prior', etc.
                    logger.info(f"calculate_noi_comparisons: Output section '{key}' (full): {json.dumps(data_item, default=str, indent=2)}")
            except Exception as e:
                logger.error(f"Error logging output section {key}: {e}")
        elif data_item is not None:
             logger.info(f"calculate_noi_comparisons: Output section '{key}' is not a dict, type: {type(data_item)}")

    logger.info(f"month_vs_prior has {len(result.get('month_vs_prior', {}))} fields")
    logger.info(f"actual_vs_budget has {len(result.get('actual_vs_budget', {}))} fields")
    logger.info(f"year_vs_year has {len(result.get('year_vs_year', {}))} fields")
    
    return result

def validate_comparison_results(comparison_results: Dict[str, Any]) -> None:
    """
    Enhanced validation of comparison results
    """
    if "current" not in comparison_results:
        logger.warning("No current month data available for validation")
        return
    
    current = comparison_results["current"]
    
    # Validate EGI calculation
    calculated_egi = calculate_egi(
        safe_float(current.get("gpr")),
        safe_float(current.get("vacancy_loss")),
        safe_float(current.get("concessions")),
        safe_float(current.get("bad_debt")),
        safe_float(current.get("other_income"))
    )
    
    reported_egi = safe_float(current.get("egi"))
    
    if abs(calculated_egi - reported_egi) > 0.01:
        logger.warning(
            f"EGI calculation mismatch: reported={reported_egi:.2f}, "
            f"calculated={calculated_egi:.2f}"
        )
    
    # Validate NOI calculation
    calculated_noi = calculate_noi(calculated_egi, safe_float(current.get("opex")))
    reported_noi = safe_float(current.get("noi"))
    
    if abs(calculated_noi - reported_noi) > 0.01:
        logger.warning(
            f"NOI calculation mismatch: reported={reported_noi:.2f}, "
            f"calculated={calculated_noi:.2f}"
        )
    
    # Validate OpEx breakdown summing to total OpEx
    total_opex = safe_float(current.get("opex"))
    sum_components = calculate_opex_sum(
        safe_float(current.get("property_taxes")),
        safe_float(current.get("insurance")),
        safe_float(current.get("repairs_and_maintenance")),
        safe_float(current.get("utilities")),
        safe_float(current.get("management_fees"))
    )
    
    # Allow some tolerance for rounding errors
    if abs(total_opex - sum_components) > 0.1 and total_opex > 0:
        logger.warning(
            f"OpEx components sum mismatch: total={total_opex:.2f}, "
            f"component sum={sum_components:.2f}"
        )
