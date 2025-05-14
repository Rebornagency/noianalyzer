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

    # Defensive: check for raw keys
    current = consolidated_data.get("current_month")
    prior = consolidated_data.get("prior_month")
    budget = consolidated_data.get("budget")
    prior_year = consolidated_data.get("prior_year")

    def build_comparison(current, compare, compare_suffix):
        result = {}
        metrics = [
            "gpr", "vacancy_loss", "concessions", "bad_debt", "other_income", "egi", "opex", "noi",
            "property_taxes", "insurance", "repairs_and_maintenance", "utilities", "management_fees",
            "parking", "laundry", "late_fees", "pet_fees", "application_fees", "storage_fees",
            "amenity_fees", "utility_reimbursements", "cleaning_fees", "cancellation_fees", "miscellaneous"
        ]
        for m in metrics:
            result[f"{m}_current"] = current.get(m, 0) if current else 0
            result[f"{m}_{compare_suffix}"] = compare.get(m, 0) if compare else 0
            change = (current.get(m, 0) if current else 0) - (compare.get(m, 0) if compare else 0)
            result[f"{m}_change"] = change
            result[f"{m}_percent_change"] = (change / result[f"{m}_{compare_suffix}"] * 100) if result[f"{m}_{compare_suffix}"] else 0
        return result

    return {
        "month_vs_prior": build_comparison(current, prior, "prior"),
        "actual_vs_budget": build_comparison(current, budget, "budget"),
        "year_vs_year": build_comparison(current, prior_year, "prior_year"),
        "current": current or {},
        "prior": prior or {},
        "budget": budget or {},
        "prior_year": prior_year or {},
    }

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
