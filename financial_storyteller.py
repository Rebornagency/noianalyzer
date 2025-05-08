import logging
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from config import get_openai_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('financial_storyteller')

def create_narrative(comparison_results: Dict[str, Any], property_name: str = "") -> str:
    """
    Generate a comprehensive financial narrative based on detailed NOI comparison results.
    
    This function analyzes financial data and creates a well-structured narrative that explains
    key drivers of changes in financial performance, significant variances, budget adherence,
    and notable trends.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        property_name: Name of the property for the analysis
        
    Returns:
        A comprehensive financial narrative as a string
    """
    logger.info(f"Generating financial narrative for property: {property_name}")
    
    # Get API key from config
    api_key = get_openai_api_key()
    
    # Log API key status (masked)
    if api_key and len(api_key) > 10:
        logger.info(f"Using OpenAI API key: {'*' * (len(api_key) - 5)}{api_key[-5:]}")
    else:
        logger.error("Invalid or missing OpenAI API key. Cannot generate narrative.")
        return "Error: OpenAI API key is not configured correctly. Please add your API key in the settings."

    # Check if comparison_results is empty or invalid
    if not comparison_results or not isinstance(comparison_results, dict):
        logger.error(f"Invalid comparison results: {comparison_results}")
        return "Error: Invalid comparison data received. Unable to generate narrative."

    # Format the financial data for the prompt
    formatted_data = format_financial_data_for_prompt(comparison_results)

    # Create the detailed prompt for the storyteller
    prompt = create_storyteller_prompt(formatted_data, property_name)
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Call OpenAI API
        logger.info(f"Sending prompt to OpenAI API (length: {len(prompt)} chars)...")
        response = client.chat.completions.create(
            model="gpt-4", # or "gpt-4-turbo"
            messages=[
                {"role": "system", "content": "You are a professional financial analyst specializing in real estate property performance analysis. You write clear, insightful narratives explaining financial performance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4, # Lower temperature for more factual responses
            max_tokens=1500  # Allow for a detailed narrative
        )
        
        # Extract the generated narrative
        narrative = response.choices[0].message.content
        logger.info(f"Generated narrative of {len(narrative)} chars")
        
        return narrative
    except Exception as e:
        logger.error(f"Error generating narrative: {str(e)}")
        return f"Error generating financial narrative: {str(e)}. Please try again or contact support."

def format_financial_data_for_prompt(comparison_results: Dict[str, Any]) -> str:
    """
    Formats the financial data into a structured text representation for the prompt.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        
    Returns:
        Formatted string with detailed financial data
    """
    formatted_text = ""
    
    # Log the structure of comparison_results for debugging
    logger.info(f"Formatting comparison results with keys: {list(comparison_results.keys())}")
    
    # Handle case where comparison_results might be empty
    if not comparison_results:
        return "No financial data available."
    
    # Get current period data
    current = comparison_results.get("current", {})
    if not current:
        logger.warning("No current period data found in comparison results")
        current = {}

    def format_value(value):
        """Formats numeric values with dollar signs and commas."""
        if value is None:
            return "N/A"
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return "N/A"

    # --- Current Period Data ---
    if current:
        formatted_text += "CURRENT PERIOD FINANCIAL DATA:\n"
        
        # Income components
        formatted_text += "INCOME:\n"
        formatted_text += f"- Gross Potential Rent (GPR): {format_value(current.get('gpr'))}\n"
        formatted_text += f"- Vacancy Loss: {format_value(current.get('vacancy_loss'))}\n"
        formatted_text += f"- Concessions: {format_value(current.get('concessions'))}\n"
        formatted_text += f"- Bad Debt: {format_value(current.get('bad_debt'))}\n"
        formatted_text += f"- Other Income: {format_value(current.get('other_income'))}\n"
        
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
            if key in current and current[key]:
                formatted_text += f"  • {label}: {format_value(current.get(key))}\n"
        
        formatted_text += f"- Effective Gross Income (EGI): {format_value(current.get('egi'))}\n\n"
        
        # Expense components
        formatted_text += "EXPENSES:\n"
        formatted_text += f"- Total Operating Expenses (OpEx): {format_value(current.get('opex'))}\n"
        
        # OpEx breakdown
        opex_components = [
            ('property_taxes', 'Property Taxes'),
            ('insurance', 'Insurance'),
            ('repairs_and_maintenance', 'Repairs & Maintenance'),
            ('utilities', 'Utilities'),
            ('management_fees', 'Management Fees')
        ]
        
        for key, label in opex_components:
            if key in current:
                formatted_text += f"  • {label}: {format_value(current.get(key))}\n"
        
        formatted_text += f"- Net Operating Income (NOI): {format_value(current.get('noi'))}\n\n"

    # --- Budget Comparison ---
    avb = comparison_results.get("actual_vs_budget", {})
    if avb:
        formatted_text += "ACTUAL VS BUDGET COMPARISON:\n"
        formatted_text += "Metric | Actual | Budget | Variance ($) | Variance (%)\n"
        formatted_text += "-------|--------|--------|--------------|------------\n"
        
        metrics = [
            ("gpr", "GPR"), 
            ("vacancy_loss", "Vacancy Loss"),
            ("other_income", "Other Income"),
            ("egi", "EGI"),
            ("opex", "Total OpEx")
        ]
        
        # Add OpEx components to metrics list
        for key, label in opex_components:
            if key in current:
                metrics.append((key, label))
        
        # Add NOI as the last item
        metrics.append(("noi", "NOI"))
        
        for key, name in metrics:
            current_val = avb.get(f"{key}_current", 0)
            compare_val = avb.get(f"{key}_compare", 0)
            change_val = avb.get(f"{key}_change", 0)
            percent_change = avb.get(f"{key}_percent_change", 0)
            
            # Handle potential None values
            current_val = 0 if current_val is None else current_val
            compare_val = 0 if compare_val is None else compare_val
            change_val = 0 if change_val is None else change_val
            percent_change = 0 if percent_change is None else percent_change
            
            formatted_text += f"{name} | {format_value(current_val)} | {format_value(compare_val)} | "
            formatted_text += f"{format_value(change_val)} | {percent_change:.1f}%\n"
        
        formatted_text += "\n"

    # --- Prior Month Comparison ---
    mom = comparison_results.get("month_vs_prior", {})
    if mom:
        formatted_text += "MONTH-OVER-MONTH COMPARISON:\n"
        formatted_text += "Metric | Current Month | Prior Month | Change ($) | Change (%)\n"
        formatted_text += "-------|---------------|-------------|------------|----------\n"
        
        for key, name in metrics:
            current_val = mom.get(f"{key}_current", 0)
            prior_val = mom.get(f"{key}_compare", 0)
            change_val = mom.get(f"{key}_change", 0)
            percent_change = mom.get(f"{key}_percent_change", 0)
            
            # Handle potential None values
            current_val = 0 if current_val is None else current_val
            prior_val = 0 if prior_val is None else prior_val
            change_val = 0 if change_val is None else change_val
            percent_change = 0 if percent_change is None else percent_change
            
            formatted_text += f"{name} | {format_value(current_val)} | {format_value(prior_val)} | "
            formatted_text += f"{format_value(change_val)} | {percent_change:.1f}%\n"
        
        formatted_text += "\n"

    # --- Year-over-Year Comparison ---
    yoy = comparison_results.get("year_vs_year", {})
    if yoy:
        formatted_text += "YEAR-OVER-YEAR COMPARISON:\n"
        formatted_text += "Metric | Current Year | Prior Year | Change ($) | Change (%)\n"
        formatted_text += "-------|--------------|------------|------------|----------\n"
        
        for key, name in metrics:
            current_val = yoy.get(f"{key}_current", 0)
            prior_val = yoy.get(f"{key}_compare", 0)
            change_val = yoy.get(f"{key}_change", 0)
            percent_change = yoy.get(f"{key}_percent_change", 0)
            
            # Handle potential None values
            current_val = 0 if current_val is None else current_val
            prior_val = 0 if prior_val is None else prior_val
            change_val = 0 if change_val is None else change_val
            percent_change = 0 if percent_change is None else percent_change
            
            formatted_text += f"{name} | {format_value(current_val)} | {format_value(prior_val)} | "
            formatted_text += f"{format_value(change_val)} | {percent_change:.1f}%\n"
        
        formatted_text += "\n"

    return formatted_text

def create_storyteller_prompt(formatted_data: str, property_name: str) -> str:
    """
    Creates a detailed prompt for the storyteller model.
    
    Args:
        formatted_data: Formatted financial data
        property_name: Name of the property
        
    Returns:
        Detailed prompt for the model
    """
    return f"""
    As a senior real estate financial analyst, create a detailed, professional narrative summary of the financial performance for {property_name or "this property"}. The narrative should have the style of a high-quality financial report that a professional property manager would submit to property owners or investors.

    Here is the financial data to analyze:
    ---
    {formatted_data}
    ---

    Create a comprehensive narrative that covers:

    1. **Overall Performance Summary**:
       - Begin with a headline statement about the property's NOI performance
       - Provide context by comparing against budget, prior month, and prior year (if available)
       - Quantify the performance in both dollar and percentage terms

    2. **Revenue Analysis**:
       - Analyze Gross Potential Rent (GPR) performance
       - Explain vacancy and credit loss trends and their impact
       - Highlight any significant changes in Other Income categories
       - Discuss the overall Effective Gross Income (EGI) performance and key drivers

    3. **Expense Analysis**:
       - Review total Operating Expense performance
       - Identify the 2-3 expense categories with the most significant variances (both positive and negative)
       - Explain how these expense categories impacted overall performance

    4. **Notable Variances**:
       - Focus on line items with variances exceeding 5% or $1,000 (whichever is greater)
       - For each significant variance, provide potential business reasons based on the data
       - Connect related trends across different financial categories

    The narrative should:
    - Be factual and objective, based strictly on the data provided
    - Be written in clear, professional language
    - Make logical connections between different metrics
    - Highlight the most important insights rather than mentioning every minor detail
    - Focus on changes and trends rather than just stating absolute values
    - Use precise financial terminology
    - Be approximately 400-600 words in length

    Do not include:
    - Generic statements that could apply to any property
    - Requests for additional information
    - Disclaimers about the analysis

    Write the narrative as one cohesive report with clear paragraph breaks between sections, but without explicit section headers or bullet points.
    """

def identify_key_drivers(comparison_results: Dict[str, Any], threshold_percent: float = 5.0, threshold_amount: float = 1000.0) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identify the key drivers of financial performance changes.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        threshold_percent: Minimum percentage change to be considered significant
        threshold_amount: Minimum dollar amount change to be considered significant
        
    Returns:
        Dictionary with key drivers by comparison type
    """
    key_drivers = {
        "month_vs_prior": [],
        "actual_vs_budget": [],
        "year_vs_year": []
    }
    
    # Metrics to check, in order of importance
    metrics_to_check = [
        ("noi", "NOI"),
        ("egi", "Effective Gross Income"),
        ("gpr", "Gross Potential Rent"),
        ("vacancy_loss", "Vacancy Loss"),
        ("other_income", "Other Income"),
        ("opex", "Operating Expenses"),
        ("property_taxes", "Property Taxes"),
        ("insurance", "Insurance"),
        ("repairs_and_maintenance", "Repairs & Maintenance"),
        ("utilities", "Utilities"),
        ("management_fees", "Management Fees")
    ]
    
    # Check each comparison type
    for comparison_type in key_drivers.keys():
        if comparison_type in comparison_results:
            data = comparison_results[comparison_type]
            
            for metric_key, metric_name in metrics_to_check:
                change_key = f"{metric_key}_change"
                percent_key = f"{metric_key}_percent_change"
                
                if change_key in data and percent_key in data:
                    change = data[change_key]
                    percent = data[percent_key]
                    
                    # Skip if values are None
                    if change is None or percent is None:
                        continue
                    
                    # Check if the change exceeds thresholds
                    if abs(percent) >= threshold_percent or abs(change) >= threshold_amount:
                        key_drivers[comparison_type].append({
                            "metric": metric_key,
                            "name": metric_name,
                            "change": change,
                            "percent_change": percent,
                            "is_positive": is_positive_change(metric_key, change)
                        })
            
            # Sort drivers by absolute impact
            key_drivers[comparison_type].sort(key=lambda x: abs(x["change"]), reverse=True)
    
    return key_drivers

def is_positive_change(metric: str, change_val: float) -> bool:
    """
    Determine if a change is positive or negative based on the metric.
    For most metrics, an increase is positive, but for expense and loss metrics,
    a decrease is positive.
    
    Args:
        metric: The metric key
        change_val: The change value
        
    Returns:
        True if the change is positive, False otherwise
    """
    # For these metrics, a decrease (negative change) is actually positive
    negative_is_positive = [
        "vacancy_loss", "concessions", "bad_debt", "opex",
        "property_taxes", "insurance", "repairs_and_maintenance",
        "utilities", "management_fees"
    ]
    
    if metric in negative_is_positive:
        return change_val < 0
    else:
        return change_val > 0 