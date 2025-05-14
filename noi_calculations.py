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
    Always returns a dict with keys: month_vs_prior, actual_vs_budget, year_vs_year.
    Each value is a dict with keys like gpr_current, gpr_prior, etc.
    """
    # If already transformed, return as-is
    if all(
        k in consolidated_data
        for k in ["month_vs_prior", "actual_vs_budget", "year_vs_year"]
    ):
        return consolidated_data

    # Log input structure to help troubleshoot
    logger.info(f"calculate_noi_comparisons: Input data keys: {list(consolidated_data.keys())}")
    
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
            
            # Calculate changes
            change = current_val - compare_val
            
            # Determine which suffix to use based on comparison type
            change_suffix = "variance" if compare_suffix == "budget" else "change"
            pct_change_suffix = "percent_variance" if compare_suffix == "budget" else "percent_change"
            
            # Store change values
            result[f"{m}_{change_suffix}"] = change
            
            # Calculate and store percent change, avoiding division by zero
            if compare_val != 0:
                result[f"{m}_{pct_change_suffix}"] = (change / compare_val * 100)
            else:
                # Handle zero division - if current is positive, treat as 100% increase
                if current_val > 0:
                    result[f"{m}_{pct_change_suffix}"] = 100.0
                # If current is negative, treat as -100% decrease
                elif current_val < 0:
                    result[f"{m}_{pct_change_suffix}"] = -100.0
                else:
                    # Both zero, no change
                    result[f"{m}_{pct_change_suffix}"] = 0.0
        
        logger.info(f"Built {compare_suffix} comparison with {len(result)} metric fields")
        return result

    # Build the comparison data structures
    month_vs_prior = build_comparison(current, prior, "prior")
    actual_vs_budget = build_comparison(current, budget, "budget")
    year_vs_year = build_comparison(current, prior_year, "prior_year")
    
    result = {
        "month_vs_prior": month_vs_prior,
        "actual_vs_budget": actual_vs_budget,
        "year_vs_year": year_vs_year,
        "current": current or {},
        "prior": prior or {},
        "budget": budget or {},
        "prior_year": prior_year or {},
    }
    
    # Log the output structure
    logger.info(f"calculate_noi_comparisons: Output data keys: {list(result.keys())}")
    logger.info(f"month_vs_prior has {len(result['month_vs_prior'])} fields")
    logger.info(f"actual_vs_budget has {len(result['actual_vs_budget'])} fields")
    logger.info(f"year_vs_year has {len(result['year_vs_year'])} fields")
    
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
