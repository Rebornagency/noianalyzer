import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_calculations')

def calculate_noi_comparisons(consolidated_data: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate detailed NOI comparisons with improved data handling and validation
    """
    comparison_results = {}
    
    def normalize_data(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize input data structure"""
        if not data:
            return {}
        return data.get('financials', data)
    
    def safe_float(value: Any) -> float:
        """Safely convert value to float"""
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0
    
    def safe_percent_change(current: float, previous: float) -> float:
        """Calculate percentage change with improved handling of edge cases"""
        if abs(previous) < 0.0001:  # Avoid division by near-zero
            return 0.0 if abs(current) < 0.0001 else 100.0
        return ((current - previous) / previous) * 100
    
    # Normalize all input data
    normalized_data = {
        period: normalize_data(data)
        for period, data in consolidated_data.items()
    }
    
    # Get current period data
    current_data = normalized_data.get("current_month", {})
    if not current_data:
        logger.error("No current month data available")
        return {"error": "No current month data available"}
    
    # Store current data
    comparison_results["current"] = current_data
    
    # Define metrics to compare
    metrics = [
        "gpr", "vacancy_loss", "concessions", "bad_debt",
        "other_income", "egi", "opex", "noi"
    ]
    
    # Calculate comparisons for each period type
    period_types = {
        "month_vs_prior": "prior_month",
        "actual_vs_budget": "budget",
        "year_vs_year": "prior_year"
    }
    
    for comparison_type, period_key in period_types.items():
        comparison_data = normalized_data.get(period_key, {})
        if comparison_data:
            results = {}
            
            for metric in metrics:
                current_val = safe_float(current_data.get(metric))
                compare_val = safe_float(comparison_data.get(metric))
                
                results[f"{metric}_current"] = current_val
                results[f"{metric}_compare"] = compare_val
                results[f"{metric}_change"] = current_val - compare_val
                results[f"{metric}_percent_change"] = safe_percent_change(
                    current_val, compare_val
                )
            
            comparison_results[comparison_type] = results
            logger.info(f"Calculated {comparison_type} with {len(results)} metrics")
    
    # Validate results
    validate_comparison_results(comparison_results)
    
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
