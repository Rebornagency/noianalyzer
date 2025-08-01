import logging
import json
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI

from constants import SUCCESS_MESSAGES, ERROR_MESSAGES, MAIN_METRICS, OPEX_COMPONENTS, INCOME_COMPONENTS
from utils.error_handler import setup_logger, handle_errors, graceful_degradation, APIError
from utils.common import safe_float, safe_string, format_currency, format_percent, summarize_dict_for_logging
from config import get_openai_api_key

# Setup logger
logger = setup_logger(__name__)


@graceful_degradation(
    fallback_value="Unable to generate financial narrative due to an error. You can still view all financial metrics and insights.",
    operation_name="financial narrative generation"
)
@handle_errors(default_return="Error generating financial narrative. Please try again.")
def create_narrative(comparison_results: Dict[str, Any], property_name: str = "") -> str:
    """
    Generate a comprehensive financial narrative based on detailed NOI comparison results.
    
    This function analyzes financial data and creates a well-structured narrative that explains
    key drivers of changes in financial performance, significant variances, budget adherence,
    and notable trends. Uses graceful degradation to ensure the application remains functional
    even if narrative generation fails.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        property_name: Name of the property for the analysis
        
    Returns:
        A comprehensive financial narrative as a string
        
    Raises:
        APIError: If OpenAI API key is invalid or API call fails
    """
    logger.info(
        f"Generating financial narrative for property: {property_name}",
        extra={
            "property_name": property_name,
            "has_comparison_results": bool(comparison_results)
        }
    )
    
    # Validate inputs
    if not comparison_results or not isinstance(comparison_results, dict):
        logger.error(f"Invalid comparison results: {type(comparison_results)}")
        raise APIError(ERROR_MESSAGES["INVALID_API_RESPONSE"])

    # Get API key from config
    api_key = get_openai_api_key()
    
    # Validate API key
    if not api_key or len(api_key) < 10:
        logger.error("Invalid or missing OpenAI API key")
        raise APIError(ERROR_MESSAGES["API_KEY_MISSING"])
    
    # Log API key status (masked for security)
    logger.info(
        f"Using OpenAI API key: {'*' * (len(api_key) - 5)}{api_key[-5:]}",
        extra={"api_key_length": len(api_key)}
    )

    # Format the financial data for the prompt
    formatted_data = format_financial_data_for_prompt(comparison_results)

    # Create the detailed prompt for the storyteller
    prompt = create_storyteller_prompt(formatted_data, property_name)
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Call OpenAI API
        logger.info(
            f"Sending prompt to OpenAI API",
            extra={
                "prompt_length": len(prompt),
                "model": "gpt-3.5-turbo"
            }
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional financial analyst specializing in real estate property performance analysis. You write clear, insightful narratives explaining financial performance."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,  # Lower temperature for more factual responses
            max_tokens=1500   # Allow for a detailed narrative
        )
        
        # Extract the generated narrative
        narrative = response.choices[0].message.content
        logger.info(
            f"Generated narrative successfully",
            extra={
                "narrative_length": len(narrative),
                "property_name": property_name
            }
        )
        
        # Post-process the narrative to ensure consistent formatting
        processed_narrative = format_narrative_for_display(narrative)
        
        return processed_narrative
        
    except Exception as e:
        logger.error(
            f"Error calling OpenAI API: {str(e)}",
            exc_info=True,
            extra={
                "property_name": property_name,
                "api_key_length": len(api_key) if api_key else 0
            }
        )
        raise APIError(f"OpenAI API error: {str(e)}")


@handle_errors(default_return="")
def format_narrative_for_display(narrative: str) -> str:
    """
    Post-process the narrative to ensure consistent formatting for display.
    
    Args:
        narrative: The raw narrative text generated by the API
        
    Returns:
        Formatted narrative with consistent style
    """
    if not narrative:
        return ""
    
    # Remove any HTML tags
    narrative = re.sub(r'<[^>]*>', '', narrative)
    
    # Normalize paragraph breaks
    narrative = re.sub(r'\n\s*\n', '\n\n', narrative)
    
    # Ensure dollar amounts are consistently formatted
    # Find patterns like: $1.2 million or $1,200,000 or 1.2 million dollars
    narrative = re.sub(
        r'(\$?)(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m)\s*(?:dollars)?', 
        lambda m: f"${safe_float(m.group(2).replace(',', '')) * 1000000:,.2f}", 
        narrative
    )
    
    # Find patterns like: $1.2k or $1,200 or 1,200 dollars
    narrative = re.sub(
        r'(\$?)(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:thousand|k)\s*(?:dollars)?', 
        lambda m: f"${safe_float(m.group(2).replace(',', '')) * 1000:,.2f}", 
        narrative
    )
    
    # Find any remaining number with dollar sign
    narrative = re.sub(
        r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)', 
        lambda m: f"${safe_float(m.group(1).replace(',', '')):,.2f}", 
        narrative
    )
    
    # Find any percentages and format consistently
    narrative = re.sub(
        r'(\d+(?:\.\d+)?)(?:\s*)?(%|percent|percentage points?)',
        lambda m: f"{safe_float(m.group(1)):.1f}%",
        narrative
    )
    
    # Remove any special formatting like colors (might come from API)
    narrative = re.sub(r'\*\*|\*|__|_', '', narrative)
    
    return narrative.strip()


@handle_errors(default_return="No financial data available.")
def format_financial_data_for_prompt(comparison_results: Dict[str, Any]) -> str:
    """
    Formats the financial data into a structured text representation for the prompt.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        
    Returns:
        Formatted string with detailed financial data
    """
    logger.info("Formatting financial data for prompt")
    
    # Validate input
    if not comparison_results or not isinstance(comparison_results, dict):
        logger.warning("Invalid comparison results provided")
        return "No valid financial data available."
    
    # Log structure safely
    try:
        summary = summarize_dict_for_logging(comparison_results)
        logger.info(f"Comparison results structure: {json.dumps(summary, default=str)}")
    except Exception as e:
        logger.warning(f"Could not log comparison results structure: {str(e)}")
    
    formatted_text = ""
    
    # Get current period data
    current = comparison_results.get("current", {})
    if not current:
        logger.warning("No current period data found in comparison results")
        return "No current period financial data available."

    # --- Current Period Data ---
    formatted_text += "CURRENT PERIOD FINANCIAL DATA:\n"
    
    # Income components
    formatted_text += "INCOME:\n"
    formatted_text += f"- Gross Potential Rent (GPR): {format_currency(current.get('gpr'))}\n"
    formatted_text += f"- Vacancy Loss: {format_currency(current.get('vacancy_loss'))}\n"
    formatted_text += f"- Concessions: {format_currency(current.get('concessions'))}\n"
    formatted_text += f"- Bad Debt: {format_currency(current.get('bad_debt'))}\n"
    formatted_text += f"- Other Income: {format_currency(current.get('other_income'))}\n"
    
    # Other income breakdown if available
    other_income_components = [
        ('parking', 'Parking'),
        ('laundry', 'Laundry'), 
        ('late_fees', 'Late Fees'),
        ('pet_fees', 'Pet Fees'),
        ('application_fees', 'Application Fees'),
        ('storage_fees', 'Storage Fees'),
        ('amenity_fees', 'Amenity Fees'),
        ('utility_reimbursements', 'Utility Reimbursements'),
        ('cleaning_fees', 'Cleaning Fees'),
        ('cancellation_fees', 'Cancellation Fees'),
        ('miscellaneous', 'Miscellaneous')
    ]
    
    for key, label in other_income_components:
        value = current.get(key)
        if value and safe_float(value) > 0:
            formatted_text += f"  • {label}: {format_currency(value)}\n"
    
    formatted_text += f"- Effective Gross Income (EGI): {format_currency(current.get('egi'))}\n\n"
    
    # Expense components
    formatted_text += "EXPENSES:\n"
    formatted_text += f"- Total Operating Expenses (OpEx): {format_currency(current.get('opex'))}\n"
    
    # OpEx breakdown
    opex_components = [
        ('property_taxes', 'Property Taxes'),
        ('insurance', 'Insurance'),
        ('repairs_maintenance', 'Repairs & Maintenance'),
        ('utilities', 'Utilities'),
        ('management_fees', 'Management Fees')
    ]
    
    for key, label in opex_components:
        value = current.get(key)
        if value and safe_float(value) > 0:
            formatted_text += f"  • {label}: {format_currency(value)}\n"
    
    formatted_text += f"\nNET OPERATING INCOME (NOI): {format_currency(current.get('noi'))}\n\n"
    
    # Add comparison data if available
    formatted_text += _format_comparison_data(comparison_results)
    
    logger.info(f"Formatted financial data ({len(formatted_text)} chars)")
    return formatted_text


@handle_errors(default_return="")
def _format_comparison_data(comparison_results: Dict[str, Any]) -> str:
    """
    Format comparison data sections for the prompt.
    
    Args:
        comparison_results: Comparison results dictionary
        
    Returns:
        Formatted comparison data string
    """
    formatted_text = ""
    
    # Actual vs Budget comparison
    if "actual_vs_budget" in comparison_results:
        avb = comparison_results["actual_vs_budget"]
        formatted_text += "ACTUAL VS BUDGET COMPARISON:\n"
        
        for metric in MAIN_METRICS:
            budget_key = f"{metric}_budget"
            variance_key = f"{metric}_variance"
            percent_key = f"{metric}_percent_variance"
            
            if budget_key in avb:
                budget_val = format_currency(avb.get(budget_key))
                variance_val = format_currency(avb.get(variance_key))
                percent_val = format_percent(avb.get(percent_key, 0) / 100) if avb.get(percent_key) else "0.0%"
                
                formatted_text += f"- {metric.upper()}: Budget {budget_val}, Variance {variance_val} ({percent_val})\n"
        
        formatted_text += "\n"
    
    # Month vs Prior comparison
    if "month_vs_prior" in comparison_results:
        mvp = comparison_results["month_vs_prior"]
        formatted_text += "MONTH VS PRIOR MONTH COMPARISON:\n"
        
        for metric in MAIN_METRICS:
            prior_key = f"{metric}_prior"
            change_key = f"{metric}_change"
            percent_key = f"{metric}_percent_change"
            
            if prior_key in mvp:
                prior_val = format_currency(mvp.get(prior_key))
                change_val = format_currency(mvp.get(change_key))
                percent_val = format_percent(mvp.get(percent_key, 0) / 100) if mvp.get(percent_key) else "0.0%"
                
                formatted_text += f"- {metric.upper()}: Prior {prior_val}, Change {change_val} ({percent_val})\n"
        
        formatted_text += "\n"
    
    # Year vs Year comparison  
    if "year_vs_year" in comparison_results:
        yoy = comparison_results["year_vs_year"]
        formatted_text += "YEAR OVER YEAR COMPARISON:\n"
        
        for metric in MAIN_METRICS:
            prior_key = f"{metric}_prior_year"
            change_key = f"{metric}_change"
            percent_key = f"{metric}_percent_change"
            
            if prior_key in yoy:
                prior_val = format_currency(yoy.get(prior_key))
                change_val = format_currency(yoy.get(change_key))
                percent_val = format_percent(yoy.get(percent_key, 0) / 100) if yoy.get(percent_key) else "0.0%"
                
                formatted_text += f"- {metric.upper()}: Prior Year {prior_val}, Change {change_val} ({percent_val})\n"
        
        formatted_text += "\n"
    
    return formatted_text


@handle_errors(default_return="")
def create_storyteller_prompt(formatted_data: str, property_name: str) -> str:
    """
    Creates a comprehensive prompt for the financial storyteller with improved structure.
    
    Args:
        formatted_data: Formatted financial data string
        property_name: Name of the property
        
    Returns:
        Complete prompt for the AI model
    """
    property_name_clean = safe_string(property_name) or "the property"
    
    prompt = f"""
Please analyze the following financial data for {property_name_clean} and create a comprehensive, professional narrative that explains the financial performance. 

**Financial Data:**
{formatted_data}

**Analysis Requirements:**
1. **Executive Summary**: Provide a brief overview of overall financial performance
2. **Key Performance Drivers**: Identify and explain the main factors driving financial performance
3. **Notable Variances**: Highlight significant variances from budget, prior month, or prior year
4. **Trend Analysis**: Discuss any notable trends or patterns in the data
5. **Operational Insights**: Provide insights into operational efficiency and areas for improvement

**Style Guidelines:**
- Write in a professional, analytical tone
- Use specific dollar amounts and percentages from the data
- Focus on actionable insights
- Organize information logically with clear sections
- Avoid technical jargon; write for property management stakeholders
- Keep the narrative concise but comprehensive (aim for 800-1200 words)

**Format:**
Structure the narrative with clear sections and use bullet points where appropriate for readability.

Generate the financial narrative now:
"""
    
    return prompt


@handle_errors(default_return={})
def identify_key_drivers(
    comparison_results: Dict[str, Any], 
    threshold_percent: float = 5.0, 
    threshold_amount: float = 1000.0
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identify key drivers of financial performance with improved error handling.
    
    Args:
        comparison_results: Results from NOI comparisons
        threshold_percent: Minimum percentage change to be considered significant
        threshold_amount: Minimum dollar amount change to be considered significant
        
    Returns:
        Dictionary containing key drivers by comparison type
    """
    logger.info(f"Identifying key drivers with thresholds: {threshold_percent}%, ${threshold_amount}")
    
    if not comparison_results or not isinstance(comparison_results, dict):
        logger.warning("Invalid comparison results for key driver analysis")
        return {}
    
    key_drivers = {}
    
    # Analyze each comparison type
    for comparison_type in ["actual_vs_budget", "month_vs_prior", "year_vs_year"]:
        if comparison_type not in comparison_results:
            continue
            
        drivers = []
        comp_data = comparison_results[comparison_type]
        
        for metric in MAIN_METRICS:
            # Determine the appropriate keys based on comparison type
            if comparison_type == "actual_vs_budget":
                change_key = f"{metric}_variance"
                percent_key = f"{metric}_percent_variance"
            else:
                change_key = f"{metric}_change"
                percent_key = f"{metric}_percent_change"
            
            change_amount = safe_float(comp_data.get(change_key, 0))
            change_percent = safe_float(comp_data.get(percent_key, 0))
            
            # Check if change meets thresholds
            if (abs(change_amount) >= threshold_amount or 
                abs(change_percent) >= threshold_percent):
                
                is_positive = _is_positive_change(metric, change_amount)
                
                drivers.append({
                    "metric": metric,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "is_positive": is_positive,
                    "significance": "high" if abs(change_percent) >= threshold_percent * 2 else "medium"
                })
        
        if drivers:
            key_drivers[comparison_type] = sorted(
                drivers, 
                key=lambda x: abs(x["change_percent"]), 
                reverse=True
            )
    
    logger.info(f"Identified key drivers: {summarize_dict_for_logging(key_drivers)}")
    return key_drivers


def _is_positive_change(metric: str, change_val: float) -> bool:
    """
    Determine if a change in a specific metric is positive for the business.
    
    Args:
        metric: The financial metric name
        change_val: The change value
        
    Returns:
        True if the change is positive for business performance
    """
    # For expenses (OpEx, vacancy loss), decreases are positive
    # For income (GPR, EGI, NOI, other income), increases are positive
    negative_metrics = ["opex", "vacancy_loss", "concessions", "bad_debt"]
    
    if metric in negative_metrics:
        return change_val < 0  # Decrease in expenses is positive
    else:
        return change_val > 0  # Increase in income is positive 