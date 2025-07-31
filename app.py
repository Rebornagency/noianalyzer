# Core imports
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import logging
import copy
from typing import Dict, Any, Tuple, List

# Custom imports
from noi_calculations import calculate_noi_metrics, calculate_comparison_metrics
from noi_tool_batch_integration import process_batch_files
from insights_display import display_insights
from storyteller_display import display_storyteller_narrative
from reborn_logo import display_reborn_logo

# Set up logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration --- #
# Set page config at the very beginning
st.set_page_config(
    page_title="NOI Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session State Initialization --- #
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "consolidated_data" not in st.session_state:
    st.session_state.consolidated_data = {}
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = {}
if "insights" not in st.session_state:
    st.session_state.insights = []
if "generated_narrative" not in st.session_state:
    st.session_state.generated_narrative = ""
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {
        "current_month": [],
        "prior_month": [],
        "budget": [],
        "prior_year": []
    }
if "property_name" not in st.session_state:
    st.session_state.property_name = ""
if "testing_mode" not in st.session_state:
    st.session_state.testing_mode = False
if "run_diagnostics" not in st.session_state:
    st.session_state.run_diagnostics = False

# --- Helper Functions --- #
def next_step():
    st.session_state.current_step += 1

def prev_step():
    st.session_state.current_step -= 1

def reset_app():
    st.session_state.current_step = 0
    st.session_state.consolidated_data = {}
    st.session_state.comparison_results = {}
    st.session_state.insights = []
    st.session_state.generated_narrative = ""
    st.session_state.uploaded_files = {
        "current_month": [],
        "prior_month": [],
        "budget": [],
        "prior_year": []
    }
    st.session_state.property_name = ""
    st.session_state.testing_mode = False
    st.session_state.run_diagnostics = False
    st.experimental_rerun()

def is_testing_mode_active():
    return st.session_state.testing_mode

def generate_mock_data():
    """Generates mock data for testing purposes."""
    logger.info("Generating mock data...")
    st.session_state.property_name = "Mock Property"
    st.session_state.consolidated_data = {
        "property_name": "Mock Property",
        "current_month": {
            "document_type": "Current Month", "document_date": "2024-06-30",
            "gpr": 100000, "vacancy_loss": 5000, "other_income": 2000,
            "egi": 97000, "opex": 40000, "noi": 57000,
            "repairs_maintenance": 5000, "utilities": 7000, "property_management": 4000,
            "taxes": 6000, "insurance": 3000, "administrative": 2000,
            "payroll": 8000, "marketing": 3000, "other_expenses": 2000,
            "parking": 500, "laundry": 300, "late_fees": 200, "pet_fees": 100,
            "application_fees": 50, "storage_fees": 50, "amenity_fees": 50, 
            "utility_reimbursements": 500, "cleaning_fees": 100, 
            "cancellation_fees": 50, "miscellaneous": 100
        },
        "prior_month": {
            "document_type": "Prior Month", "document_date": "2024-05-31",
            "gpr": 98000, "vacancy_loss": 4800, "other_income": 1900,
            "egi": 95100, "opex": 39000, "noi": 56100,
            "repairs_maintenance": 4800, "utilities": 6800, "property_management": 3900,
            "taxes": 5800, "insurance": 2900, "administrative": 1900,
            "payroll": 7800, "marketing": 2900, "other_expenses": 2000,
            "parking": 480, "laundry": 290, "late_fees": 190, "pet_fees": 90,
            "application_fees": 45, "storage_fees": 45, "amenity_fees": 45, 
            "utility_reimbursements": 480, "cleaning_fees": 90, 
            "cancellation_fees": 45, "miscellaneous": 90
        },
        "budget": {
            "document_type": "Budget", "document_date": "2024-01-01",
            "gpr": 102000, "vacancy_loss": 5100, "other_income": 2100,
            "egi": 99000, "opex": 41000, "noi": 58000,
            "repairs_maintenance": 5100, "utilities": 7100, "property_management": 4100,
            "taxes": 6100, "insurance": 3100, "administrative": 2100,
            "payroll": 8100, "marketing": 3100, "other_expenses": 2100,
            "parking": 510, "laundry": 310, "late_fees": 210, "pet_fees": 110,
            "application_fees": 55, "storage_fees": 55, "amenity_fees": 55, 
            "utility_reimbursements": 510, "cleaning_fees": 110, 
            "cancellation_fees": 55, "miscellaneous": 110
        },
        "prior_year": {
            "document_type": "Prior Year", "document_date": "2023-06-30",
            "gpr": 95000, "vacancy_loss": 4500, "other_income": 1800,
            "egi": 92300, "opex": 38000, "noi": 54300,
            "repairs_maintenance": 4500, "utilities": 6500, "property_management": 3800,
            "taxes": 5500, "insurance": 2800, "administrative": 1800,
            "payroll": 7500, "marketing": 2800, "other_expenses": 1800,
            "parking": 450, "laundry": 280, "late_fees": 180, "pet_fees": 80,
            "application_fees": 40, "storage_fees": 40, "amenity_fees": 40, 
            "utility_reimbursements": 450, "cleaning_fees": 80, 
            "cancellation_fees": 40, "miscellaneous": 80
        }
    }
    st.session_state.run_diagnostics = True
    logger.info("Mock data generated.")

def run_calculations_and_insights():
    """Runs NOI calculations, comparisons, and generates insights/narrative."""
    logger.info("Running calculations and insights...")
    if st.session_state.consolidated_data:
        # Calculate NOI metrics
        st.session_state.consolidated_data = calculate_noi_metrics(st.session_state.consolidated_data)
        logger.info("NOI metrics calculated.")

        # Calculate comparison metrics
        st.session_state.comparison_results = calculate_comparison_metrics(st.session_state.consolidated_data)
        logger.info("Comparison metrics calculated.")

        # Generate insights (mock for now)
        st.session_state.insights = [
            {"title": "Strong NOI Growth", "description": "Current month NOI shows a significant increase compared to prior month and budget, indicating strong operational performance.", "type": "positive"},
            {"title": "Utility Costs Under Budget", "description": "Utilities expenses are lower than budgeted, contributing positively to overall profitability.", "type": "positive"},
            {"title": "Increased Vacancy Loss", "description": "Vacancy loss has slightly increased compared to the prior month, which warrants further investigation.", "type": "negative"},
            {"title": "Other Income Diversification", "description": "Growth in parking and laundry income streams indicates successful diversification efforts.", "type": "positive"}
        ]
        logger.info("Insights generated.")

        # Generate narrative (mock for now)
        st.session_state.generated_narrative = """
        ## Executive Summary

        The **Mock Property** demonstrated robust financial performance in the current month, with a notable **increase in Net Operating Income (NOI)** compared to both the prior month and the annual budget. This positive trend is primarily driven by effective expense management and diversified income streams.

        ## Key Performance Insights

        1.  **NOI Growth**: The property's NOI for the current month stands at **$57,000**, representing a **1.6% increase** from the prior month's $56,100 and a **-1.7% variance** against the budget of $58,000. Year-over-year, NOI has seen a substantial **5.0% growth** from $54,300.

        2.  **Revenue Performance**: Gross Potential Rent (GPR) was **$100,000**, a **2.0% increase** from the prior month. Effective Gross Income (EGI) reached **$97,000**, showing a **2.0% improvement** month-over-month.

        3.  **Expense Management**: Total Operating Expenses (OpEx) were **$40,000**, a **2.6% increase** from the prior month. Notably, **Utilities** were **$7,000**, which is **-0.0% under budget**, contributing positively to the bottom line.

        4.  **Vacancy and Other Income**: Vacancy Loss was **$5,000**, a **4.2% increase** from the prior month, indicating a slight uptick in unoccupied units. Conversely, Other Income streams, particularly **Parking ($500)** and **Laundry ($300)**, showed healthy contributions.

        ## Recommendations

        *   **Investigate Vacancy Trends**: Analyze the reasons behind the slight increase in vacancy loss and implement strategies to optimize occupancy rates.
        *   **Continue Expense Monitoring**: Maintain rigorous oversight on operating expenses, especially utilities, to sustain cost efficiencies.
        *   **Explore Income Diversification**: Continue to identify and capitalize on additional ancillary income opportunities to further boost EGI.
        *   **Strategic Capital Planning**: Based on strong NOI, consider reinvesting in property enhancements that can command higher rents or reduce future operating costs.
        """
        logger.info("Narrative generated.")
    else:
        logger.warning("No consolidated data available for calculations and insights.")
    st.session_state.run_diagnostics = True

def run_diagnostics():
    """Runs diagnostics after mock data generation or calculations."""
    logger.info("Running diagnostics...")
    # Check if mock data was generated correctly
    if "consolidated_data" not in st.session_state:
        logger.error("Diagnostics: consolidated_data not found in session state")
        st.sidebar.error("Diagnostics: Mock data generation failed")
    else:
        logger.info("Diagnostics: consolidated_data present in session state")
        st.sidebar.success("Diagnostics: Mock data generated successfully")
    
    # Check if comparisons were calculated
    if "comparison_results" not in st.session_state:
        logger.error("Diagnostics: comparison_results not found in session state")
        st.sidebar.error("Diagnostics: Comparison calculation failed")
    else:
        logger.info("Diagnostics: comparison_results present in session state")
        st.sidebar.success("Diagnostics: Comparisons calculated successfully")
    
    # Check if insights were generated
    if "insights" not in st.session_state:
        logger.error("Diagnostics: insights not found in session state")
        st.sidebar.error("Diagnostics: Mock insights generation failed")
    else:
        logger.info("Diagnostics: insights present in session state")
        st.sidebar.success("Diagnostics: Mock insights generated successfully")
    
    # Check if narrative was generated
    if "generated_narrative" not in st.session_state:
        logger.error("Diagnostics: generated_narrative not found in session state")
        st.sidebar.error("Diagnostics: Mock narrative generation failed")
    else:
        logger.info("Diagnostics: generated_narrative present in session state")
        st.sidebar.success("Diagnostics: Mock narrative generated successfully")
    
    # Reset diagnostic flag
    st.session_state.run_diagnostics = False

def debug_testing_mode_data():
    """Debug function to inspect testing mode data structure"""
    if not is_testing_mode_active():
        return
    
    logger.info("=== TESTING MODE DATA DEBUG ===")
    
    # Debug consolidated_data
    if "consolidated_data" in st.session_state:
        consolidated_data = st.session_state.consolidated_data
        logger.info(f"Consolidated data keys: {list(consolidated_data.keys())}")
        
        for key, data in consolidated_data.items():
            if isinstance(data, dict) and key in ["current_month", "prior_month", "budget", "prior_year"]:
                logger.info(f"{key} data sample: gpr={data.get("gpr")}, noi={data.get("noi")}, egi={data.get("egi")}")
            elif key == "property_name":
                logger.info(f"Property name: {data}")
    else:
        logger.error("No consolidated_data found in session state")
    
    # Debug comparison_results
    if "comparison_results" in st.session_state:
        comparison_results = st.session_state.comparison_results
        logger.info(f"Comparison results keys: {list(comparison_results.keys())}")
        
        # Check each comparison section
        for section in ["month_vs_prior", "actual_vs_budget", "year_vs_year"]:
            if section in comparison_results:
                section_data = comparison_results[section]
                logger.info(f"{section} has {len(section_data)} fields")
                # Log a few sample fields
                sample_keys = [k for k in section_data.keys() if 'gpr' in k or 'noi' in k][:5]
                for key in sample_keys:
                    logger.info(f"  {key}: {section_data.get(key)}")
            else:
                logger.error(f"Missing {section} in comparison_results")
        
        # Check raw data sections
        for section in ["current", "prior", "budget", "prior_year"]:
            if section in comparison_results:
                section_data = comparison_results[section]
                if isinstance(section_data, dict):
                    logger.info(f"{section} raw data: gpr={section_data.get("gpr")}, noi={section_data.get("noi")}")
                else:
                    logger.error(f"{section} is not a dict: {type(section_data)}")
            else:
                logger.warning(f"Missing {section} raw data in comparison_results")
    else:
        logger.error("No comparison_results found in session state")
    
    logger.info("=== END TESTING MODE DATA DEBUG ===")

def validate_financial_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate financial data for consistency.
    
    Args:
        data: Dictionary containing financial data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if EGI = GPR - Vacancy Loss + Other Income
    expected_egi = data.get("gpr", 0) - data.get("vacancy_loss", 0) + data.get("other_income", 0)
    actual_egi = data.get("egi", 0)
    
    # Allow for small floating point differences
    if abs(expected_egi - actual_egi) > 1.0:
        return False, f"EGI inconsistency: Expected {expected_egi:.2f}, got {actual_egi:.2f}"
    
    # Check if NOI = EGI - OpEx
    expected_noi = data.get("egi", 0) - data.get("opex", 0)
    actual_noi = data.get("noi", 0)
    
    # Allow for small floating point differences
    if abs(expected_noi - actual_noi) > 1.0:
        return False, f"NOI inconsistency: Expected {expected_noi:.2f}, got {actual_noi:.2f}"
    
    # Check if OpEx components sum up to total OpEx
    # Align component keys with those used in data extraction
    opex_components = [
        "repairs_maintenance", "utilities", 
        "management_fees",  # preferred key
        "property_management",  # legacy key kept for compatibility
        "property_taxes",  # preferred key
        "taxes",           # legacy key kept for compatibility
        "insurance", "administrative", 
        "payroll", "marketing", "other_expenses"
    ]

    # Use dict.fromkeys to preserve order while de-duplicating aliases
    unique_opex_components = list(dict.fromkeys(opex_components))

    opex_sum = sum(data.get(comp, 0) for comp in unique_opex_components)
    total_opex = data.get("opex", 0)
    
    # Allow for small floating point differences
    if abs(opex_sum - total_opex) > 1.0:
        return False, f"OpEx inconsistency: Components sum to {opex_sum:.2f}, but total is {total_opex:.2f}"
    
    # Check if Other Income components sum up to total Other Income
    income_components = [
        "parking", "laundry", "late_fees", "pet_fees", 
        "application_fees", "storage_fees", "amenity_fees", 
        "utility_reimbursements", "cleaning_fees", 
        "cancellation_fees", "miscellaneous"
    ]
    
    income_sum = sum(data.get(component, 0) for component in income_components)
    total_income = data.get("other_income", 0)
    
    # Allow for small floating point differences
    if abs(income_sum - total_income) > 1.0:
        return False, f"Other Income inconsistency: Components sum to {income_sum:.2f}, but total is {total_income:.2f}"
    
    # All checks passed
    return True, ""

def display_document_data(doc_type: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Display and allow editing of data for a specific document type.
    
    Args:
        doc_type: Document type (current_month, prior_month, budget, prior_year)
        doc_data: Dictionary containing document data
        
    Returns:
        Dictionary containing the edited document data
    """
    # Create a deep copy to avoid modifying the original
    edited_doc_data = copy.deepcopy(doc_data)
    
    # Display document metadata
    st.markdown("### Document Information")
    with st.expander("Document Metadata", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Document Type", value=doc_data.get("document_type", ""), disabled=True, key=f"doc_type_display_{doc_type}")
        with col2:
            st.text_input("Document Date", value=doc_data.get("document_date", ""), disabled=True, key=f"doc_date_display_{doc_type}")
    
    # Auto-calculation option
    auto_calculate = st.checkbox("Auto-calculate dependent values", value=True, key=f"auto_calc_{doc_type}")
    
    # Display main financial metrics
    st.markdown("### Key Financial Metrics")
    
    # Create a form for the main metrics
    with st.form(key=f"main_metrics_form_{doc_type}"):
        # GPR
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Gross Potential Rent (GPR)**")
        with col2:
            gpr = st.number_input(
                "GPR Value",
                value=float(doc_data.get("gpr", 0.0)),
                format="%.2f",
                step=100.0,
                key=f"gpr_{doc_type}"
            )
            edited_doc_data["gpr"] = gpr
        
        # Vacancy Loss
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Vacancy Loss**")
        with col2:
            vacancy_loss = st.number_input(
                "Vacancy Loss Value",
                value=float(doc_data.get("vacancy_loss", 0.0)),
                format="%.2f",
                step=100.0,
                key=f"vacancy_loss_{doc_type}"
            )
            edited_doc_data["vacancy_loss"] = vacancy_loss
        
        # Other Income
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Other Income**")
        with col2:
            other_income = st.number_input(
                "Other Income Value",
                value=float(doc_data.get("other_income", 0.0)),
                format="%.2f",
                step=100.0,
                key=f"other_income_{doc_type}"
            )
            edited_doc_data["other_income"] = other_income
        
        # EGI
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Effective Gross Income (EGI)**")
        with col2:
            if auto_calculate:
                calculated_egi = edited_doc_data["gpr"] - edited_doc_data["vacancy_loss"] + edited_doc_data["other_income"]
                edited_doc_data["egi"] = calculated_egi
                st.number_input(
                    "EGI Value (Auto-calculated)",
                    value=float(calculated_egi),
                    format="%.2f",
                    step=100.0,
                    key=f"egi_{doc_type}",
                    disabled=True
                )
            else:
                egi = st.number_input(
                    "EGI Value",
                    value=float(doc_data.get("egi", 0.0)),
                    format="%.2f",
                    step=100.0,
                    key=f"egi_{doc_type}"
                )
                edited_doc_data["egi"] = egi
        
        # OpEx
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Operating Expenses (OpEx)**")
        with col2:
            opex = st.number_input(
                "OpEx Value",
                value=float(doc_data.get("opex", 0.0)),
                format="%.2f",
                step=100.0,
                key=f"opex_{doc_type}"
            )
            edited_doc_data["opex"] = opex
        
        # NOI
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Net Operating Income (NOI)**")
        with col2:
            if auto_calculate:
                calculated_noi = edited_doc_data["egi"] - edited_doc_data["opex"]
                edited_doc_data["noi"] = calculated_noi
                st.number_input(
                    "NOI Value (Auto-calculated)",
                    value=float(calculated_noi),
                    format="%.2f",
                    step=100.0,
                    key=f"noi_{doc_type}",
                    disabled=True
                )
            else:
                noi = st.number_input(
                    "NOI Value",
                    value=float(doc_data.get("noi", 0.0)),
                    format="%.2f",
                    step=100.0,
                    key=f"noi_{doc_type}"
                )
                edited_doc_data["noi"] = noi
        
        # Submit button for the form
        st.form_submit_button("Update Main Metrics")
    
    # Display Operating Expenses breakdown
    st.markdown("### Operating Expenses Breakdown")
    
    # Create a form for OpEx breakdown
    with st.form(key=f"opex_form_{doc_type}"):
        opex_components = [
            ("repairs_maintenance", "Repairs & Maintenance"),
            ("utilities", "Utilities"),
            ("property_management", "Property Management"),
            ("taxes", "Property Taxes"),
            ("insurance", "Insurance"),
            ("administrative", "Administrative"),
            ("payroll", "Payroll"),
            ("marketing", "Marketing"),
            ("other_expenses", "Other Expenses")
        ]
        
        # Create two columns for better layout
        col1, col2 = st.columns(2)
        
        # Distribute OpEx components between columns
        for i, (key, label) in enumerate(opex_components):
            with col1 if i % 2 == 0 else col2:
                value = st.number_input(
                    label,
                    value=float(doc_data.get(key, 0.0)),
                    format="%.2f",
                    step=100.0,
                    key=f"{key}_{doc_type}"
                )
                edited_doc_data[key] = value
        
        # Submit button for the form
        st.form_submit_button("Update OpEx Breakdown")
    
    # Display Other Income breakdown
    st.markdown("### Other Income Breakdown")
    
    # Create a form for Other Income breakdown
    with st.form(key=f"other_income_form_{doc_type}"):
        income_components = [
            ("parking", "Parking"),
            ("laundry", "Laundry"),
            ("late_fees", "Late Fees"),
            ("pet_fees", "Pet Fees"),
            ("application_fees", "Application Fees"),
            ("storage_fees", "Storage Fees"),
            ("amenity_fees", "Amenity Fees"),
            ("utility_reimbursements", "Utility Reimbursements"),
            ("cleaning_fees", "Cleaning Fees"),
            ("cancellation_fees", "Cancellation Fees"),
            ("miscellaneous", "Miscellaneous")
        ]
        
        # Create two columns for better layout
        col1, col2 = st.columns(2)
        
        # Distribute income components between columns
        for i, (key, label) in enumerate(income_components):
            with col1 if i % 2 == 0 else col2:
                value = st.number_input(
                    label,
                    value=float(doc_data.get(key, 0.0)),
                    format="%.2f",
                    step=100.0,
                    key=f"{key}_{doc_type}"
                )
                edited_doc_data[key] = value
        
        # Submit button for the form
        st.form_submit_button("Update Other Income Breakdown")
    
    # Validate data and show warnings if needed
    is_valid, error_message = validate_financial_data(edited_doc_data)
    if not is_valid:
        st.warning(f"Data inconsistency detected: {error_message}")
        st.info("You can still proceed, but consider fixing the inconsistency for more accurate analysis.")
    
    # Return the edited document data
    return edited_doc_data

def display_data_template(consolidated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Display extracted financial data in an editable template format.
    
    Args:
        consolidated_data: Dictionary containing extracted financial data
        
    Returns:
        Dictionary containing the verified/edited financial data
    """
    st.markdown("## Data Extraction Template")
    st.markdown("Review and edit the extracted financial data below. Make any necessary corrections before proceeding with analysis.")
    
    # Create a deep copy of the data to avoid modifying the original
    edited_data = copy.deepcopy(consolidated_data)
    
    # Create tabs for each document type
    doc_tabs = st.tabs(["Current Month", "Prior Month", "Budget", "Prior Year"])
    
    # Process each document type
    for i, doc_type in enumerate(["current_month", "prior_month", "budget", "prior_year"]):
        with doc_tabs[i]:
            if doc_type in consolidated_data:
                edited_data[doc_type] = display_document_data(doc_type, consolidated_data[doc_type])
            else:
                st.info(f"No {doc_type.replace("_", " ")} data available.")
    
    # Add confirmation button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Confirm Data and Proceed with Analysis", type="primary", use_container_width=True):
            return edited_data
    
    # Return None if not confirmed
    return None

# Helper function to inject custom CSS
def inject_custom_css():
    """Inject custom CSS to ensure font consistency and enhanced styling across the application"""
    st.markdown("""
    <style>
    /* Reborn Theme CSS for NOI Analyzer */

    /* Import Inter font from Google Fonts */
    @import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\');

    :root {
        /* Color palette based on design specs */
        --reborn-bg-primary: #0A0F1E;
        --reborn-bg-secondary: #10172A;
        --reborn-bg-tertiary: #1E293B;
        --reborn-text-primary: #FFFFFF;  /* Use pure white for maximum readability */
        --reborn-text-secondary: #A0A0A0;
        --reborn-accent-blue: #3B82F6;
        --reborn-accent-green: #10B981;
        --reborn-accent-orange: #F59E0B;
        --reborn-success: #10B981;
        --reborn-warning: #F87171;
        --reborn-border: rgba(255, 255, 255, 0.1);
        
        /* Spacing */
        --reborn-spacing-xs: 8px;
        --reborn-spacing-sm: 16px;
        --reborn-spacing-md: 24px;
        --reborn-spacing-lg: 32px;
        
        /* Border radius */
        --reborn-radius-sm: 6px;
        --reborn-radius-md: 8px;
        --reborn-radius-lg: 12px;
        --reborn-radius-pill: 999px;
        
        /* Shadows */
        --reborn-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
        --reborn-shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
        
        /* Add explicit font family variables */
        --reborn-font-primary: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, \'Open Sans\', \'Helvetica Neue\', sans-serif;
        --reborn-font-heading: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, \'Open Sans\', \'Helvetica Neue\', sans-serif;
        --reborn-font-mono: \'SFMono-Regular\', Consolas, \'Liberation Mono\', Menlo, Courier, monospace;
    }
    
    .reborn-logo {
        height: 64px !important;
        max-width: 100%;
    }

    /* Existing font styles - keep these */
    body, .stApp, .stMarkdown, .stText, .stTextInput, .stTextArea, 
    .stSelectbox, .stMultiselect, .stDateInput, .stTimeInput, .stNumberInput,
    .stButton > button, .stDataFrame, .stTable, .stExpander, .stTabs {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, \'Open Sans\', \'Helvetica Neue\', sans-serif !important;
    }
    
    /* Ensure markdown content uses Inter and has appropriate sizing */
    .stMarkdown p, .stMarkdown li { /* Target p and li specifically for content text */
        font-family: \'Inter\', -apple-system, BlinkMacMacFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, \'Open Sans\', \'Helvetica Neue\', sans-serif !important;
        font-size: 1rem !important; /* e.g., 16px base for content */
        line-height: 1.6 !important;
        color: #FFFFFF !important; /* Bright white for maximum readability */
    }

    .stMarkdown div { /* General divs in markdown, only font-family */
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, \'Open Sans\', \'Helvetica Neue\', sans-serif !important;
    }
    
    /* Base layout styling - improved spacing and background */
    body {
        background-color: #111827 !important;
        color: #ffffff !important;
    }
    
    /* Full-width layout for better space utilization */
    .stApp {
        background-color: #111827 !important;
        max-width: 100% !important;
        margin: 0 auto !important;
        padding: 0 !important;
    }
    
    /* Expand main content area and reduce unnecessary spacing */
    .main .block-container {
        max-width: 95% !important;
        padding-top: 1rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        margin-top: 0 !important;
    }
    
    /* Adjust sidebar width for better proportions */
    [data-testid="stSidebar"] {
        width: 18rem !important;
    }
    
    /* Make sure content sections use the available space */
    .stTabs [data-baseweb="tab-panel"] {
        padding-left: 0px !important;
        padding-right: 0px !important;
    }
    
    /* Remove extra padding from containers */
    .stMarkdown, .stText {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    /* Enhanced section titles (used for Executive Summary, Key Perf. Insights etc.) */
    .reborn-section-title {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, \'Open Sans\', \'Helvetica Neue\', sans-serif !important;
        font-size: 1.8rem !important; /* Increased from 1.5rem */
        font-weight: 600 !important;
        color: #FFFFFF !important; /* Changed to white */
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        padding: 0.5rem 0.75rem !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-radius: 8px !important;
        border-left: 4px solid var(--reborn-accent-blue) !important;
        line-height: 1.4 !important;
        display: block; /* Ensure it takes full width if needed */
    }

    /* NEW STYLES FOR RESULTS UI */
    /* Main title for Analysis and Recommendations */
    .results-main-title {
        font-size: 2.5rem !important;
        font-weight: 500 !important;
        color: #79b8f3 !important;
        margin-bottom: 2rem !important;
        padding: 0 !important;
        background: none !important;
        border: none !important;
        line-height: 1.3 !important;
    }

    /* Section headers (Executive Summary, Key Performance Insights, etc.) */
    .results-section-header {
        font-size: 1.8rem !important;
        font-weight: 500 !important;
        color: #FFFFFF !important; /* Changed to white */
        margin-top: 2rem !important;
        margin-bottom: 1.5rem !important;
        padding: 0 !important;
        background: none !important;
        border: none !important;
        line-height: 1.3 !important;
    }

    /* Content cards with better styling */
    .results-card {
        background-color: rgba(22, 27, 34, 0.8) !important;
        border: 1px solid rgba(56, 68, 77, 0.5) !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
        margin-bottom: 2rem !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
    }

    /* Text styling within results */
    .results-text {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        color: #e6edf3 !important;
        margin-bottom: 1rem !important;
    }

    /* Number prefix for summary */
    .results-summary-number {
        font-weight: 500 !important;
        margin-right: 0.5rem !important;
        color: #79b8f3 !important;
    }

    /* Bullet list styling */
    .results-bullet-list {
        list-style-type: none !important;
        padding-left: 0 !important;
        margin-bottom: 1.5rem !important;
    }

    .results-bullet-item {
        display: flex !important;
        align-items: flex-start !important;
        margin-bottom: 1rem !important;
        line-height: 1.6 !important;
    }

    .results-bullet-marker {
        color: #79b8f3 !important;
        margin-right: 0.75rem !important;
        font-size: 1.5rem !important;
        line-height: 1 !important;
        flex-shrink: 0 !important;
    }

    .results-bullet-text {
        flex: 1 !important;
        color: #e6edf3 !important;
    }
    /* END NEW STYLES */

    /* Enhanced Upload Card Styling */
    .upload-card {
        background-color: rgba(17, 17, 34, 0.8);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 32px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    .upload-card-header {
        display: flex;
        align-items: center;
        justify-content: center; /* Center align the title and badge */
        margin-top: 2.5rem !important; /* Added to create space between upload cards */
        margin-bottom: 20px !important; /* Add more spacing between upload card header and content */
    }
    
    .upload-card-header h3 {
        font-size: 20px;
        font-weight: 600;
        color: #EAEAEA;
        margin: 0;
    }
    
    .required-badge {
        background-color: rgba(59, 130, 246, 0.2);
        color: #3B82F6;
        font-size: 12px;
        font-weight: 500;
        padding: 2px 8px;
        border-radius: 4px;
        margin-left: 8px;
    }
    
    .upload-area {
        background-color: rgba(13, 13, 13, 0.8);
        border: 1px solid #222;
        border-radius: 8px;
        padding: 32px;
        text-align: center;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.4);
    }
    
    .upload-icon {
        font-size: 32px;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .upload-text {
        color: #ffffff;
        font-size: 14px;
        margin-bottom: 4px;
    }

    .upload-subtext {
        color: #ffffff;
        font-size: 12px;
        margin-bottom: 16px;
    }
    
    /* Enhanced Instructions Card */
    .instructions-card {
        background-color: transparent !important;
        border-radius: 0;
        padding: 0;
        margin-bottom: 32px;
        box-shadow: none !important;
    }
    
    .instructions-card h3 {
        font-size: 20px;
        font-weight: 600;
        color: #EAEAEA;
        margin-bottom: 16px;
    }
    
    .instructions-card ol {
        padding-left: 24px;
        margin-bottom: 0;
    }
    
    .instructions-card li {
        color: #EAEAEA;
        font-size: 14px;
        margin-bottom: 12px;
        line-height: 1.5;
    }
    
    /* Property Name Input Styling */
    .property-input-container {
        background-color: rgba(17, 17, 34, 0.8);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 32px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    .property-input-container label {
        font-size: 16px;
        font-weight: 500;
        color: #FFFFFF;
        margin-bottom: 8px;
    }
    
    /* File info styling */
    .file-info {
        display: flex;
        align-items: center;
        background-color: rgba(30, 41, 59, 0.7);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .file-icon {
        font-size: 24px;
        margin-right: 12px;
    }
    
    .file-details {
        flex-grow: 1;
    }
    
    .file-name {
        color: #E0E0E0;
        font-weight: 500;
        font-size: 14px;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 250px;
    }
    
    .file-meta {
        color: #94A3B8;
        font-size: 12px;
    }
    
    .file-status {
        color: #22C55E;
        font-size: 12px;
        font-weight: 500;
        background-color: rgba(30, 41, 59, 0.5);
        padding: 4px 8px;
        border-radius: 4px;
    }

    /* Feature list styling */
    .feature-list {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        margin-bottom: 2rem;
    }

    .feature-item {
        display: flex;
        margin-bottom: 24px;
    }

    .feature-number {
        background-color: rgba(34, 34, 51, 0.8);
        color: #EAEAEA;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        margin-right: 16px;
        flex-shrink: 0;
    }

    .feature-content {
        flex: 1;
    }

    .feature-content h4 {
        font-size: 16px;
        font-weight: 500;
        color: #EAEAEA;
        margin-top: 0;
        margin-bottom: 4px;
    }

    .feature-content p {
        font-size: 14px;
        color: #ffffff;
        margin: 0;
    }

    .feature-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #e6edf3;
        margin-bottom: 0.5rem;
    }

    .feature-description {
        font-size: 1rem;
        color: #d1d5db;
        line-height: 1.5;
    }

    /* Section header styling */
    .section-header {
        font-size: 1.8rem;
        font-weight: 500;
        color: #FFFFFF !important; /* Changed to white */
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }

    /* Enhanced Button Styling */
    .primary-button {
        background-color: #3B82F6 !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 16px !important;
        margin-bottom: 24px !important;
    }
    
    .primary-button:hover {
        background-color: #2563EB !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* Styling for Streamlit Expander Headers (e.g., Full Financial Narrative) */
    .streamlit-expanderHeader { /* General expander header style */
        background-color: rgba(30, 41, 59, 0.7) !important; /* From load_css fallback, good to have consistently */
        border-radius: 8px !important;
        margin-bottom: 0.5rem !important;
        transition: background-color 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: rgba(30, 41, 59, 0.9) !important;
    }

    .streamlit-expanderHeader p { /* Specifically target the text within the expander header */
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, \'Open Sans\', \'Helvetica Neue\', sans-serif !important;
        font-size: 1.6rem !important; /* Larger than content text */
        font-weight: 700 !important;
        color: #FFFFFF !important; /* Light color for header text */
        text-align: center;
    }
    
    /* Ensure header has no extra spacing */
    .stApp header {
        background-color: transparent !important;
        text-align: center;
    }
    
    /* Remove default Streamlit margins */
    .stApp > header {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Ensure logo container has no extra spacing */
    .stMarkdown:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Enhanced styling for narrative text */
    .narrative-text {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif !important;
        color: #E0E0E0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        padding: 1.25rem !important;
        border-radius: 8px !important;
        margin-bottom: 1.25rem !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Force consistent styling for all elements within narrative text */
    .narrative-text * {
        color: #E0E0E0 !important;
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif !important;
        font-size: 1rem !important;
    }
    
    /* Override any potential color styling in the narrative */
    .narrative-text span, 
    .narrative-text p, 
    .narrative-text div,
    .narrative-text b,
    .narrative-text strong,
    .narrative-text i,
    .narrative-text em {
        color: #E0E0E0 !important;
    }
    
    /* Fix for currency values to ensure they\'re consistently formatted */
    .narrative-text .currency,
    .narrative-text .number {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif !important;
        color: #E0E0E0 !important;
    }
    
    /* Hide redundant expander title when not needed */
    .financial-narrative + .streamlit-expanderHeader {
        display: none !important;
    }
    
    /* Styling for narrative container */
    .narrative-container {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif !important;
        color: #E0E0E0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        padding: 1.25rem !important;
        border-radius: 8px !important;
        margin-bottom: 1.25rem !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Ensure consistent styling for all elements within the narrative */
    .narrative-container p, 
    .narrative-container span, 
    .narrative-container div {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif !important;
        color: #E0E0E0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        margin-bottom: 0.75rem !important;
    }
    
    .opex-chart-title {
        font-family: \'Inter\', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 1.5rem !important; /* Increased font size */
        font-weight: 500;
        color: #FFFFFF !important; /* Changed to white */
        margin-bottom: 1rem;
        text-align: center;
    }
    
    [data-testid="stRadio"] > label {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }

    /* Card-style elements */
    .card-container {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
        margin-bottom: 1.25rem !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }
    
    .card-container:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Info, warning, error messages styling */
    .stInfo, .element-container .alert-info {
        background-color: rgba(96, 165, 250, 0.25) !important;
        border-left: 4px solid #60A5FA !important;
        color: #FFFFFF !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin: 1rem 0 !important;
    }
    
    .stWarning, .element-container .alert-warning {
        background-color: rgba(251, 191, 36, 0.1) !important;
        border-left: 4px solid #FBBF24 !important;
        color: #E0E0E0 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin: 1rem 0 !important;
    }
    
    .stError, .element-container .alert-danger {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border-left: 4px solid #EF4444 !important;
        color: #E0E0E0 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin: 1rem 0 !important;
    }
    
    .stSuccess, .element-container .alert-success {
        background-color: rgba(34, 197, 94, 0.1) !important;
        border-left: 4px solid #22C55E !important;
        color: #E0E0E0 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin: 1rem 0 !important;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 2px dashed rgba(148, 163, 184, 0.4) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"]:hover {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-color: rgba(148, 163, 184, 0.6) !important;
    }

    [data-testid="stFileUploader"] label p {
        color: black !important;
        background-color: black !important;
        width: 50px !important;
        height: 50px !important;
        border-radius: 5px !important;
        float: right !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-top: -30px !important; /* Adjust as needed to position correctly */
        margin-right: 10px !important; /* Adjust as needed to position correctly */
    }
    </style>
    """, unsafe_allow_html=True)

# --- Main Application --- #
def main():
    inject_custom_css()
    display_reborn_logo()

    st.sidebar.title("Navigation")
    if st.sidebar.button("Home", use_container_width=True):
        st.session_state.current_step = 0
    if st.sidebar.button("Data Input", use_container_width=True):
        st.session_state.current_step = 1
    if st.sidebar.button("Data Review & Edit", use_container_width=True):
        st.session_state.current_step = 2
    if st.sidebar.button("Analysis & Insights", use_container_width=True):
        st.session_state.current_step = 3
    if st.sidebar.button("Full Report", use_container_width=True):
        st.session_state.current_step = 4
    if st.sidebar.button("Reset App", use_container_width=True):
        reset_app()

    st.sidebar.markdown("--- ")
    st.sidebar.toggle("Testing Mode", value=st.session_state.testing_mode, key="testing_mode_toggle", on_change=lambda: setattr(st.session_state, "testing_mode", not st.session_state.testing_mode))

    if is_testing_mode_active():
        st.sidebar.button("Generate Mock Data", on_click=generate_mock_data, use_container_width=True)
        st.sidebar.button("Run Calculations & Insights", on_click=run_calculations_and_insights, use_container_width=True)
        if st.session_state.run_diagnostics:
            run_diagnostics()
        st.sidebar.button("Debug Testing Mode Data", on_click=debug_testing_mode_data, use_container_width=True)

    # --- Step 0: Home Page --- #
    if st.session_state.current_step == 0:
        st.title("Welcome to NOI Analyzer")
        st.markdown("""
        <div class="instructions-card">
            <h3>Get Started</h3>
            <ol>
                <li>Upload your financial documents (Current Month Actuals, Prior Month Actuals, Budget, Prior Year Actuals).</li>
                <li>Review and edit the extracted data.</li>
                <li>Generate and analyze key NOI metrics, comparisons, and insights.</li>
                <li>Access a comprehensive financial narrative and detailed reports.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-list">
            <div class="feature-item">
                <div class="feature-number">1</div>
                <div class="feature-content">
                    <h4>AI-Powered Data Extraction</h4>
                    <p>Automatically extract key financial data from various document formats (PDF, XLSX, CSV).</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-number">2</div>
                <div class="feature-content">
                    <h4>Comprehensive NOI Analysis</h4>
                    <p>Calculate Gross Potential Rent (GPR), Effective Gross Income (EGI), Operating Expenses (OpEx), and Net Operating Income (NOI).</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-number">3</div>
                <div class="feature-content">
                    <h4>Comparative Insights</h4>
                    <p>Compare current performance against prior month, budget, and prior year to identify trends and anomalies.</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-number">4</div>
                <div class="feature-content">
                    <h4>Actionable Recommendations</h4>
                    <p>Receive AI-generated insights and a detailed financial narrative to guide your decision-making.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.button("Start Analysis", on_click=next_step, type="primary", use_container_width=True)

    # --- Step 1: Data Input --- #
    elif st.session_state.current_step == 1:
        st.title("Data Input")
        st.markdown("Upload your financial documents below. Supported formats: XLSX, XLS, CSV, PDF.")

        file_types = {
            "Current Month Actuals": {"key": "current_month", "required": True},
            "Prior Month Actuals": {"key": "prior_month", "required": False},
            "Budget": {"key": "budget", "required": False},
            "Prior Year Actuals": {"key": "prior_year", "required": False}
        }

        # Property Name Input
        st.markdown("""
        <div class="property-input-container">
            <label>Property Name</label>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.property_name = st.text_input("", value=st.session_state.property_name, placeholder="Enter Property Name (e.g., 'Maplewood Apartments')", label_visibility="collapsed")

        uploaded_data = {}

        for display_name, info in file_types.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div class="upload-card-header">
                    <h3>{display_name}</h3>
                    {f'<span class="required-badge">Required</span>' if info['required'] else ''}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if display_name == "Current Month Actuals":
                    st.markdown("""
                    <div class="upload-card-header">
                        <span class="required-badge">Required</span>
                    </div>
                    """, unsafe_allow_html=True)

            with st.container():
                uploaded_file = st.file_uploader(
                    f"Upload {display_name} Document",
                    type=["xlsx", "xls", "csv", "pdf"],
                    key=f"file_uploader_{info['key']}",
                    label_visibility="collapsed",
                    help="Drag and drop your financial document here. Max 200MB."
                )
                if uploaded_file:
                    st.session_state.uploaded_files[info['key']] = [uploaded_file]
                else:
                    st.session_state.uploaded_files[info['key']] = []

                # Display uploaded file info
                if st.session_state.uploaded_files[info['key']]:
                    for file in st.session_state.uploaded_files[info['key']]:
                        st.markdown(f"""
                        <div class="file-info">
                            <span class="file-icon">📄</span>
                            <div class="file-details">
                                <div class="file-name">{file.name}</div>
                                <div class="file-meta">{file.size / 1024:.2f} KB</div>
                            </div>
                            <span class="file-status">Uploaded</span>
                        </div>
                        """, unsafe_allow_html=True)


        if st.button("Process Documents", type="primary", use_container_width=True):
            if not st.session_state.property_name:
                st.error("Please enter a Property Name before processing documents.")
            elif not st.session_state.uploaded_files["current_month"]:
                st.error("Please upload the Current Month Actuals document.")
            else:
                with st.spinner("Processing documents..."):
                    try:
                        st.session_state.consolidated_data = process_batch_files(st.session_state.uploaded_files)
                        st.session_state.consolidated_data["property_name"] = st.session_state.property_name
                        st.success("Documents processed successfully!")
                        next_step()
                    except Exception as e:
                        st.error(f"Error processing documents: {e}")
                        logger.error(f"Document processing error: {e}", exc_info=True)

    # --- Step 2: Data Review & Edit --- #
    elif st.session_state.current_step == 2:
        st.title("Data Review & Edit")
        st.markdown("Review the extracted data and make any necessary corrections.")

        if st.session_state.consolidated_data:
            edited_data = display_data_template(st.session_state.consolidated_data)
            if edited_data:
                st.session_state.consolidated_data = edited_data
                run_calculations_and_insights()
                next_step()
        else:
            st.warning("No data available for review. Please go back to Data Input.")
            if st.button("Go to Data Input", use_container_width=True):
                st.session_state.current_step = 1
                st.experimental_rerun()

    # --- Step 3: Analysis & Insights --- #
    elif st.session_state.current_step == 3:
        st.title("Analysis & Insights")

        if st.session_state.comparison_results and st.session_state.insights and st.session_state.generated_narrative:
            st.markdown(f"<h1 class=\"results-main-title\">Financial Analysis for {st.session_state.property_name}</h1>", unsafe_allow_html=True)

            # Display Storyteller Narrative
            st.markdown("<h2 class=\"results-section-header\">Executive Summary & Financial Narrative</h2>", unsafe_allow_html=True)
            display_storyteller_narrative(st.session_state.generated_narrative)

            # Display Key Performance Insights
            st.markdown("<h2 class=\"results-section-header\">Key Performance Insights</h2>", unsafe_allow_html=True)
            display_insights(st.session_state.insights)

            # Display Comparison Charts
            st.markdown("<h2 class=\"results-section-header\">Comparative Analysis</h2>", unsafe_allow_html=True)

            comparison_options = [
                "Current Month vs. Prior Month",
                "Actual vs. Budget",
                "Year-over-Year (Current vs. Prior Year)"
            ]
            selected_comparison = st.selectbox("Select Comparison View", comparison_options)

            comparison_data = st.session_state.comparison_results

            if selected_comparison == "Current Month vs. Prior Month":
                st.subheader("Current Month vs. Prior Month Performance")
                plot_comparison_chart(comparison_data["current"], comparison_data["prior"], "Current Month", "Prior Month")
                plot_opex_comparison_chart(comparison_data["current"], comparison_data["prior"], "Current Month", "Prior Month")
                plot_other_income_comparison_chart(comparison_data["current"], comparison_data["prior"], "Current Month", "Prior Month")

            elif selected_comparison == "Actual vs. Budget":
                st.subheader("Actual vs. Budget Performance")
                plot_comparison_chart(comparison_data["current"], comparison_data["budget"], "Actual", "Budget")
                plot_opex_comparison_chart(comparison_data["current"], comparison_data["budget"], "Actual", "Budget")
                plot_other_income_comparison_chart(comparison_data["current"], comparison_data["budget"], "Actual", "Budget")

            elif selected_comparison == "Year-over-Year (Current vs. Prior Year)":
                st.subheader("Year-over-Year Performance")
                plot_comparison_chart(comparison_data["current"], comparison_data["prior_year"], "Current Year", "Prior Year")
                plot_opex_comparison_chart(comparison_data["current"], comparison_data["prior_year"], "Current Year", "Prior Year")
                plot_other_income_comparison_chart(comparison_data["current"], comparison_data["prior_year"], "Current Year", "Prior Year")

            st.button("Generate Full Report", on_click=next_step, type="primary", use_container_width=True)

        else:
            st.warning("No analysis data available. Please go back to Data Input and Data Review & Edit.")
            if st.button("Go to Data Input", use_container_width=True):
                st.session_state.current_step = 1
                st.experimental_rerun()

    # --- Step 4: Full Report --- #
    elif st.session_state.current_step == 4:
        st.title("Full Financial Report")
        st.markdown("Here is the comprehensive financial report for your property.")

        if st.session_state.consolidated_data and st.session_state.comparison_results and st.session_state.generated_narrative:
            # Placeholder for report generation logic
            st.success("Report generation feature coming soon!")
            st.info("For now, you can review the analysis and insights in the previous section.")

            # Example of how you might display parts of the report
            st.markdown("### Consolidated Data")
            st.json(st.session_state.consolidated_data)

            st.markdown("### Comparison Results")
            st.json(st.session_state.comparison_results)

            st.markdown("### Generated Narrative")
            st.markdown(st.session_state.generated_narrative)

            if st.button("Back to Analysis & Insights", use_container_width=True):
                st.session_state.current_step = 3
                st.experimental_rerun()

        else:
            st.warning("No report data available. Please complete previous steps.")
            if st.button("Go to Data Input", use_container_width=True):
                st.session_state.current_step = 1
                st.experimental_rerun()

# --- Plotting Functions --- #
def plot_comparison_chart(data1: Dict[str, Any], data2: Dict[str, Any], label1: str, label2: str):
    categories = ["GPR", "Vacancy Loss", "Other Income", "EGI", "OpEx", "NOI"]
    values1 = [data1.get("gpr", 0), data1.get("vacancy_loss", 0), data1.get("other_income", 0),
               data1.get("egi", 0), data1.get("opex", 0), data1.get("noi", 0)]
    values2 = [data2.get("gpr", 0), data2.get("vacancy_loss", 0), data2.get("other_income", 0),
               data2.get("egi", 0), data2.get("opex", 0), data2.get("noi", 0)]

    df = pd.DataFrame({
        "Category": categories,
        label1: values1,
        label2: values2
    })

    fig = go.Figure(data=[
        go.Bar(name=label1, x=df["Category"], y=df[label1], marker_color=\"#3B82F6\"),
        go.Bar(name=label2, x=df["Category"], y=df[label2], marker_color=\"#10B981\")
    ])

    fig.update_layout(
        barmode=\"group\",

