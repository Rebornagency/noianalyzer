import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import logging
import os
import json
import copy
from typing import Dict, Any, List, Optional, Tuple
import base64
from datetime import datetime
import io
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import tempfile
import jinja2
import streamlit.components.v1 as components

from utils.helpers import format_for_noi_comparison
from noi_calculations import calculate_noi_comparisons
from noi_tool_batch_integration import process_all_documents
from ai_extraction import extract_noi_data
from ai_insights_gpt import generate_insights_with_gpt

# Try to import specific functions that might be missing in minimal setups
try:
    from financial_storyteller import create_narrative
    from storyteller_display import display_financial_narrative, display_narrative_in_tabs
except ImportError:
    # Create dummy functions if not available
    def create_narrative(*args, **kwargs):
        return "Narrative generation not available - module not found."
    def display_financial_narrative(*args, **kwargs):
        pass
    def display_narrative_in_tabs(*args, **kwargs):
        pass

from config import get_openai_api_key, get_extraction_api_url, get_api_key, save_api_settings
from insights_display import display_insights
from reborn_logo import get_reborn_logo_base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("noi_analyzer_enhanced.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('noi_analyzer')

def safe_text(value):
    """Convert any value to a safe string, avoiding 'undefined' text."""
    if value is None or value == "undefined" or value == "null" or str(value).lower() == "nan":
        return ""
    return str(value)

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
    opex_components = [
        "repairs_maintenance", "utilities", "property_management", 
        "taxes", "insurance", "administrative", 
        "payroll", "marketing", "other_expenses"
    ]
    
    opex_sum = sum(data.get(component, 0) for component in opex_components)
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
                st.info(f"No {doc_type.replace('_', ' ')} data available.")
    
    # Add confirmation button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Confirm Data and Proceed with Analysis", type="primary", use_container_width=True):
            return edited_data
    
    # Return None if not confirmed
    return None

# Helper function to inject custom CSS
def inject_custom_css():
    """Inject custom CSS to ensure font consistency across the application"""
    st.markdown("""
    <style>
    /* Force Inter font on all elements */
    body, .stApp, .stMarkdown, .stText, .stTextInput, .stTextArea, 
    .stSelectbox, .stMultiselect, .stDateInput, .stTimeInput, .stNumberInput,
    .stButton > button, .stDataFrame, .stTable, .stExpander, .stTabs {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Ensure markdown content uses Inter and has appropriate sizing */
    .stMarkdown p, .stMarkdown li { /* Target p and li specifically for content text */
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-size: 1rem !important; /* e.g., 16px base for content */
        line-height: 1.6 !important;
        color: #D1D5DB !important; /* Light gray for readability */
    }

    .stMarkdown div { /* General divs in markdown, only font-family */
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Base layout styling - improved spacing and background */
    body {
        background-color: #111827 !important;
        color: #E5E7EB !important;
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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-size: 1.6rem !important; /* Increased from 1.5rem */
        font-weight: 600 !important;
        color: var(--reborn-accent-blue) !important;
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
        color: #79b8f3 !important;
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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
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

    /* Feature list styling */
    .feature-list {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        margin-bottom: 2rem;
    }

    .feature-item {
        display: flex;
        align-items: flex-start;
        background-color: rgba(22, 27, 34, 0.8);
        border: 1px solid rgba(56, 68, 77, 0.5);
        border-radius: 8px;
        padding: 1.25rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .feature-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    .feature-number {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 2.5rem;
        height: 2.5rem;
        background-color: rgba(59, 130, 246, 0.2);
        color: #79b8f3;
        font-size: 1.25rem;
        font-weight: 600;
        border-radius: 50%;
        margin-right: 1rem;
        flex-shrink: 0;
    }

    .feature-content {
        flex: 1;
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
        color: #79b8f3;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-size: 1.25rem !important; /* Larger than content text */
        font-weight: 600 !important;
        color: #E0E0E0 !important; /* Light color for header text */
    }
    
    /* Ensure header has no extra spacing */
    .stApp header {
        background-color: transparent !important;
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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
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
    
    /* Fix for currency values to ensure they're consistently formatted */
    .narrative-text .currency,
    .narrative-text .number {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #E0E0E0 !important;
    }
    
    /* Hide redundant expander title when not needed */
    .financial-narrative + .streamlit-expanderHeader {
        display: none !important;
    }
    
    /* Styling for narrative container */
    .narrative-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
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
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #E0E0E0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        margin-bottom: 0.75rem !important;
    }
    
    /* Ensure consistent styling for numbers and currency values */
    .narrative-container .currency,
    .narrative-container .number {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #E0E0E0 !important;
    }
    
    /* Enhanced button styling */
    .stButton > button {
        background-color: #1E40AF !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.25rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton > button:hover {
        background-color: #2563EB !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
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
        background-color: rgba(56, 189, 248, 0.1) !important;
        border-left: 4px solid #38BDF8 !important;
        color: #E0E0E0 !important;
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
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border-radius: 8px !important;
        padding: 0.25rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px !important;
        margin: 0.25rem !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1E40AF !important;
        color: white !important;
    }
    
    /* OpEx Table Styling */
    .opex-table-container {
        margin: 1rem 0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        background-color: rgba(22, 27, 34, 0.8) !important;
        border: 1px solid rgba(56, 68, 77, 0.5) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    .opex-table {
        width: 100% !important;
        border-collapse: collapse !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #e6edf3 !important;
        background-color: transparent !important;
    }
    
    .opex-table th, .opex-table td {
        padding: 0.75rem 1rem !important;
        text-align: left !important;
        border-bottom: 1px solid rgba(56, 68, 77, 0.3) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #e6edf3 !important;
    }
    
    .opex-table th {
        background-color: rgba(30, 41, 59, 0.8) !important;
        font-weight: 600 !important;
        color: #79b8f3 !important;
        font-size: 0.95rem !important;
    }
    
    .opex-table tr:hover {
        background-color: rgba(30, 41, 59, 0.4) !important;
    }
    
    .opex-table tr:last-child td {
        border-bottom: none !important;
    }
    
    .opex-category-cell {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
    }
    
    .opex-category-indicator {
        width: 12px !important;
        height: 12px !important;
        border-radius: 50% !important;
        flex-shrink: 0 !important;
    }
    
    .opex-positive-value {
        color: #22c55e !important; /* Green for favorable changes */
        font-weight: 500 !important;
    }
    
    .opex-negative-value {
        color: #ef4444 !important; /* Red for unfavorable changes */
        font-weight: 500 !important;
    }
    
    .opex-neutral-value {
        color: #e6edf3 !important; /* Default text color */
    }
    
    .opex-chart-container {
        margin: 1rem 0 !important;
        background-color: rgba(22, 27, 34, 0.8) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        border: 1px solid rgba(56, 68, 77, 0.5) !important;
    }
    
    .opex-chart-title {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #79b8f3 !important;
        margin-bottom: 1rem !important;
        text-align: center !important;
    }

    /* Options Container Styling */
    .options-container {
        background-color: var(--reborn-bg-secondary);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid var(--reborn-accent-blue);
    }

    .options-header {
        color: var(--reborn-text-primary);
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }

    /* NOI Coach Context Styling */
    .noi-coach-context-container {
        background-color: var(--reborn-bg-secondary);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid var(--reborn-accent-teal);
    }

    .noi-coach-context-header {
        color: var(--reborn-text-primary);
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }

    .noi-coach-interface {
        background-color: var(--reborn-bg-secondary);
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    .noi-coach-response {
        background-color: var(--reborn-bg-tertiary);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        border-left: 4px solid var(--reborn-accent-blue);
    }

    </style>
    """, unsafe_allow_html=True)

# Helper function to summarize data structures for logging
def summarize_data_for_log(data_dict, max_items=3):
    """Summarize a data structure for more concise logging"""
    if not isinstance(data_dict, dict):
        return str(data_dict)
    keys = list(data_dict.keys())
    summary = {k: data_dict[k] for k in keys[:max_items]}
    if len(keys) > max_items:
        summary[f"...and {len(keys) - max_items} more keys"] = "..."
    return summary

# --- Initialize Jinja2 Environment and Load Template Globally ---
report_template = None  # Initialize to None to prevent NameError if loading fails
env = None              # Initialize to None

# Define a fallback template as a string in case the file is missing
FALLBACK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NOI Analysis Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; 
            margin: 20px; 
            line-height: 1.6;
        }
        h1, h2 { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            color: #333; 
            font-weight: 600;
        }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-family: 'Inter', sans-serif; }
        th { background-color: #f2f2f2; }
        .positive-change { color: green; }
        .negative-change { color: red; }
        p { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body>
    <h1>NOI Analysis Report - {{ property_name }}</h1>
    <p>Generated on {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
    
    <h2>Executive Summary</h2>
    {% if performance_data.executive_summary %}
    <p>{{ performance_data.executive_summary }}</p>
    {% else %}
    <p>No executive summary available.</p>
    {% endif %}
    
    <h2>Key Financial Metrics</h2>
    <p><strong>Current NOI:</strong> ${{ performance_data.noi|default(0)|round|int }}</p>
    
    {% if performance_data.get('financial_narrative') %}
    <h2>Financial Narrative</h2>
    <p>{{ performance_data.financial_narrative }}</p>
    {% endif %}
    
    <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #777;">
        <p>Generated by NOI Analyzer | © {{ datetime.now().year }} Reborn</p>
    </div>
</body>
</html>"""

try:
    # Define the path to your templates directory (assumes 'templates' is alongside app.py)
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    
    if not os.path.isdir(template_dir):
        logger.error(f"Templates directory not found at: {template_dir}. Using fallback template.")
        # Create a template from the string
        env = jinja2.Environment(autoescape=True)
        # Add custom filters for number formatting
        env.filters['format_number'] = lambda value: "{:,}".format(value) if value is not None else "0"
        report_template = env.from_string(FALLBACK_TEMPLATE)
        logger.info("Using fallback inline template for PDF generation.")
    else:
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        # Add custom filters for number formatting
        env.filters['format_number'] = lambda value: "{:,}".format(value) if value is not None else "0"
        
        # Try to load the report template file
        template_filename = 'report_template.html'  # Name from the existing code
        if os.path.exists(os.path.join(template_dir, template_filename)):
            report_template = env.get_template(template_filename)
            logger.info(f"Successfully loaded Jinja2 environment and '{template_filename}' template.")
        else:
            logger.error(f"'{template_filename}' not found in {template_dir}. Using fallback template.")
            # Create a template from the string
            env = jinja2.Environment(autoescape=True)
            # Add custom filters for number formatting
            env.filters['format_number'] = lambda value: "{:,}".format(value) if value is not None else "0"
            report_template = env.from_string(FALLBACK_TEMPLATE)
            logger.info("Using fallback inline template for PDF generation.")
except Exception as e:
    logger.error(f"Failed to initialize Jinja2 environment or load template: {e}", exc_info=True)
    # Create a template from the string as a last resort
    try:
        env = jinja2.Environment(autoescape=True)
        # Add custom filters for number formatting
        env.filters['format_number'] = lambda value: "{:,}".format(value) if value is not None else "0"
        report_template = env.from_string(FALLBACK_TEMPLATE)
        logger.info("Using fallback inline template after exception in template loading.")
    except Exception as e2:
        logger.error(f"Failed to create fallback template: {e2}", exc_info=True)
# --- End of Jinja2 initialization ---

# Import the logo function
from reborn_logo import get_reborn_logo_base64

# Logo display function - updated to use direct embedding with better error handling
def display_logo():
    """Display the Reborn logo in the Streamlit app"""
    try:
        logo_base64 = get_reborn_logo_base64()
        
        # Direct embedding of the logo with proper sizing, alignment, and no extra spacing
        logo_html = f"""
        <div style="
            display: flex; 
            justify-content: center; 
            align-items: center; 
            margin-bottom: 15px; 
            margin-top: 0; 
            padding: 5px 0;
        ">
            <img 
                src="data:image/png;base64,{logo_base64}" 
                width="180px" 
                alt="Reborn Logo" 
                style="
                    object-fit: contain;
                    filter: drop-shadow(0px 4px 6px rgba(0, 0, 0, 0.25)); 
                    -webkit-filter: drop-shadow(0px 4px 6px rgba(0, 0, 0, 0.25));
                    max-width: 100%;
                    background: transparent;
                "
            >
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        logger.info("Successfully displayed logo")
    except Exception as e:
        logger.error(f"Error displaying logo: {str(e)}")
        # Fallback to text with better styling
        st.markdown("""
        <h2 style='
            text-align: center; 
            color: #4DB6AC; 
            margin-top: 0; 
            padding: 15px 0; 
            font-size: 2rem;
            font-weight: 600;
            text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2);
        '>
            REBORN NOI ANALYZER
        </h2>
        """, unsafe_allow_html=True)

# New function for small logo display
def display_logo_small():
    """Display the Reborn logo (small, transparent PNG) aligned to the left."""
    try:
        logo_b64 = get_reborn_logo_base64()
        
        # Inline logo with proper sizing, alignment and subtle enhancement
        logo_html = f"""
        <div style="
            display: flex; 
            align-items: center; 
            margin: 0; 
            padding: 5px 0;
        ">
            <img 
                src="data:image/png;base64,{logo_b64}"
                height="36px"
                style="
                    background: transparent; 
                    object-fit: contain; 
                    margin-right: 10px;
                    filter: drop-shadow(0px 2px 3px rgba(0, 0, 0, 0.2));
                    -webkit-filter: drop-shadow(0px 2px 3px rgba(0, 0, 0, 0.2));
                "
                alt="Reborn Logo" 
            />
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        logger.info("Successfully displayed small logo")
    except Exception as e:
        logger.error(f"Error displaying small logo: {str(e)}")
        # Don't show any fallback as this is used inline with the title

# Show instructions to the user
def show_instructions():
    """Display instructions for using the NOI Analyzer"""
    instructions_html = """
    <div style="background-color: rgba(30, 41, 59, 0.8); padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; border-left: 4px solid #4DB6AC; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #4DB6AC; font-size: 1.3rem; margin-bottom: 1rem; font-weight: 600;">Instructions:</h3>
        <ol style="color: #F0F0F0; padding-left: 1.5rem; margin-bottom: 1.25rem;">
            <li style="margin-bottom: 0.5rem; line-height: 1.5;">Upload your financial documents using the file uploaders</li>
            <li style="margin-bottom: 0.5rem; line-height: 1.5;">At minimum, upload a <b style="color: #4DB6AC;">Current Month Actuals</b> file</li>
            <li style="margin-bottom: 0.5rem; line-height: 1.5;">For comparative analysis, upload additional files (Prior Month, Budget, Prior Year)</li>
            <li style="margin-bottom: 0.5rem; line-height: 1.5;">Click "<b style="color: #4DB6AC;">Process Documents</b>" to analyze the data</li>
            <li style="margin-bottom: 0.5rem; line-height: 1.5;">View the results in the analysis tabs</li>
            <li style="margin-bottom: 0.5rem; line-height: 1.5;">Export your results as PDF or Excel using the export options</li>
        </ol>
        <p style="color: #E0E0E0; font-style: italic; font-size: 0.9rem; background-color: rgba(77, 182, 172, 0.1); padding: 0.75rem; border-radius: 4px; display: inline-block;">Note: Supported file formats include Excel (.xlsx, .xls), CSV, and PDF</p>
    </div>
    """
    st.markdown(instructions_html, unsafe_allow_html=True)

# Function to show processing status with better visual indicators
def show_processing_status(message, is_running=False, status_type="info"):
    """
    Display a processing status message with enhanced visual styling.
    
    Parameters:
    - message (str): The status message to display
    - is_running (bool): Whether the process is currently running (adds an animation)
    - status_type (str): Type of status - "info", "success", "warning", or "error"
    """
    # Define colors based on status type
    colors = {
        "info": "#38BDF8",      # Blue
        "success": "#22C55E",   # Green
        "warning": "#FBBF24",   # Yellow
        "error": "#EF4444"      # Red
    }
    
    color = colors.get(status_type, colors["info"])
    
    # Define the animation for running status
    if is_running:
        animation = f"""
        <style>
        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        .status-dot {{
            animation: pulse 1.5s infinite ease-in-out;
        }}
        </style>
        """
    else:
        animation = ""
    
    # Create the HTML for the status indicator
    status_html = f"""
    {animation}
    <div style="
        display: flex;
        align-items: center;
        background-color: rgba(30, 41, 59, 0.8);
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <div class="status-dot" style="
            background-color: {color};
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 12px;
            flex-shrink: 0;
        "></div>
        <div style="
            color: #E0E0E0;
            font-size: 1rem;
            line-height: 1.5;
        ">
            {message}
        </div>
    </div>
    """
    
    # Display the status
    st.markdown(status_html, unsafe_allow_html=True)

# Function to display file information with enhanced styling
def show_file_info(file_name, file_size=None, file_type=None, uploaded=False):
    """
    Display uploaded file information with enhanced visual styling.
    
    Parameters:
    - file_name (str): Name of the file
    - file_size (str, optional): Size of the file (e.g., "2.5 MB")
    - file_type (str, optional): Type of file (e.g., "Excel", "PDF", "CSV")
    - uploaded (bool): Whether the file has been successfully uploaded
    """
    # Set icon based on file type
    icon = "📄"  # Default
    if file_type:
        if "excel" in file_type.lower() or "xlsx" in file_type.lower() or "xls" in file_type.lower():
            icon = "📊"
        elif "pdf" in file_type.lower():
            icon = "📑"
        elif "csv" in file_type.lower():
            icon = "📋"
    
    # Set status color based on uploaded status
    status_color = "#22C55E" if uploaded else "#94A3B8"  # Green if uploaded, gray if not
    status_text = "Uploaded" if uploaded else "Ready"
    
    # Create the HTML for the file info
    file_info_html = f"""
    <div style="
        display: flex;
        align-items: center;
        background-color: rgba(30, 41, 59, 0.7);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    ">
        <div style="
            font-size: 1.5rem;
            margin-right: 12px;
            flex-shrink: 0;
        ">
            {icon}
        </div>
        <div style="flex-grow: 1;">
            <div style="
                color: #E0E0E0;
                font-weight: 500;
                font-size: 0.95rem;
                margin-bottom: 0.25rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 250px;
            ">
                {file_name}
            </div>
            <div style="
                color: #94A3B8;
                font-size: 0.8rem;
            ">
                {file_size if file_size else ""}
                {" • " if file_size and file_type else ""}
                {file_type if file_type else ""}
            </div>
        </div>
        <div style="
            color: {status_color};
            font-size: 0.8rem;
            font-weight: 500;
            background-color: rgba(30, 41, 59, 0.5);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        ">
            {status_text}
        </div>
    </div>
    """
    
    # Display the file info
    st.markdown(file_info_html, unsafe_allow_html=True)

# Debug helper function to diagnose comparison structure issues
def debug_comparison_structure(comparison_results: Dict[str, Any]) -> None:
    """
    Debug function to analyze and log the structure of comparison results.
    
    This function uses INFO level for its logs by design. If these logs are too verbose,
    you have two options:
    1. Temporarily comment out calls to this function when not actively debugging
    2. Modify the log levels inside this function from INFO to DEBUG if you want 
       to retain the ability to see these logs when setting the logger to DEBUG level
    """
    if not comparison_results:
        logger.error("No comparison results available for debugging")
        return
        
    logger.info("=== COMPARISON RESULTS STRUCTURE DEBUG ===")
    logger.info(f"Top level keys: {list(comparison_results.keys())}")
    
    # Check for current data
    if "current" in comparison_results and isinstance(comparison_results["current"], dict):
        logger.info(f"Current data keys: {list(comparison_results['current'].keys())}")
        
        # Check for financial metrics in current data
        financial_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]
        for key in financial_keys:
            if key in comparison_results["current"]:
                logger.info(f"Current.{key} = {comparison_results['current'][key]}")
            else:
                logger.info(f"[Debug] Missing key in current data: {key}. This is expected if this metric was not provided or extracted.")
    else:
        logger.warning("No 'current' key in comparison results or it's not a dictionary")
    
    # Check comparison data sections
    for section_key_name in ["month_vs_prior", "actual_vs_budget", "year_vs_year"]:
        if section_key_name in comparison_results and isinstance(comparison_results[section_key_name], dict):
            section_data = comparison_results[section_key_name]
            logger.info(f"{section_key_name} keys: {list(section_data.keys())}")
            
            # Define patterns based on section type
            if section_key_name == "actual_vs_budget":
                # Suffix for the comparison period's actual value (e.g., gpr_budget)
                compare_suffix_pattern = "_budget" 
                # Suffix for the difference amount (e.g., gpr_variance)
                change_suffix_pattern = "_variance" 
                # Suffix for the percentage difference (e.g., gpr_percent_variance)
                percent_change_suffix_pattern = "_percent_variance" 
            elif section_key_name == "month_vs_prior":
                compare_suffix_pattern = "_prior"
                change_suffix_pattern = "_change"
                percent_change_suffix_pattern = "_percent_change"
            elif section_key_name == "year_vs_year":
                compare_suffix_pattern = "_prior_year"
                change_suffix_pattern = "_change"
                percent_change_suffix_pattern = "_percent_change"
            else:
                # Fallback for any other unexpected section, though unlikely
                compare_suffix_pattern = "_compare" # Generic fallback
                change_suffix_pattern = "_change"
                percent_change_suffix_pattern = "_percent_change"

            patterns_to_check = {
                "_current": "_current",
                "compare_values": compare_suffix_pattern,
                "change_values": change_suffix_pattern,
                "percent_change_values": percent_change_suffix_pattern
            }
            
            for pattern_name, pattern_suffix in patterns_to_check.items():
                matches = [key for key in section_data.keys() if key.endswith(pattern_suffix)]
                if matches:
                    logger.info(f"  Found {len(matches)} keys with pattern '{pattern_suffix}' for {pattern_name} in {section_key_name}: {matches[:3]}...")
                    # Show sample values from the first match
                    logger.info(f"    Sample value ({matches[0]}): {section_data[matches[0]]}")
                else:
                    # MODIFIED LINE: Changed from WARNING to INFO with more context
                    logger.info(f"  [Debug] In section '{section_key_name}', no keys found with pattern '{pattern_suffix}' for {pattern_name}. This may be expected if comparison data is incomplete or not applicable.")
        else:
            # MODIFIED LINE: Changed from WARNING to INFO with more context
            logger.info(f"[Debug] Comparison section '{section_key_name}' not found in results. This is expected if data for this comparison was not uploaded or processed.")
    
    logger.info("=== END COMPARISON RESULTS STRUCTURE DEBUG ===")

# Set page configuration
st.set_page_config(
    page_title="NOI Analyzer Enhanced",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Call load_css to apply custom styles
inject_custom_css()

# Initialize session state variables
if 'current_month_actuals' not in st.session_state:
    st.session_state.current_month_actuals = None
if 'prior_month_actuals' not in st.session_state:
    st.session_state.prior_month_actuals = None
if 'current_month_budget' not in st.session_state:
    st.session_state.current_month_budget = None
if 'prior_year_actuals' not in st.session_state:
    st.session_state.prior_year_actuals = None
if 'consolidated_data' not in st.session_state:
    st.session_state.consolidated_data = None
if 'processing_completed' not in st.session_state:
    st.session_state.processing_completed = False
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None
if 'insights' not in st.session_state:
    st.session_state.insights = None
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None
if 'show_zero_values' not in st.session_state:
    st.session_state.show_zero_values = False
if 'property_name' not in st.session_state:
    st.session_state.property_name = ""
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""
if 'extraction_api_url' not in st.session_state:
    st.session_state.extraction_api_url = ""
if 'extraction_api_key' not in st.session_state:
    st.session_state.extraction_api_key = ""
if 'noi_coach_history' not in st.session_state:
    st.session_state.noi_coach_history = []
if 'current_comparison_view' not in st.session_state:
    st.session_state.current_comparison_view = "budget"  # Default to budget view
if 'edited_narrative' not in st.session_state:
    st.session_state.edited_narrative = None
if 'generated_narrative' not in st.session_state:
    st.session_state.generated_narrative = None
if 'show_narrative_editor' not in st.session_state:
    st.session_state.show_narrative_editor = False
# Theme selection
if 'theme' not in st.session_state:
    st.session_state.theme = "dark"  # Default to dark theme
if 'user_initiated_processing' not in st.session_state:
    st.session_state.user_initiated_processing = False

# Display comparison tab
def display_comparison_tab(tab_data: Dict[str, Any], prior_key_suffix: str, name_suffix: str):
    """
    Display a comparison tab with KPI cards and detailed metrics.
    
    Args:
        tab_data: Comparison data for the tab
        prior_key_suffix: Suffix for prior period keys (e.g., 'prior', 'budget', 'prior_year')
        name_suffix: Display name for the prior period (e.g., 'Prior Month', 'Budget', 'Prior Year')
    """
    logger.info(f"--- display_comparison_tab START for {name_suffix} ---")
    
    # Ensure all text values are strings and safely handled
    name_suffix = safe_text(name_suffix) or "Prior Period"
    prior_key_suffix = safe_text(prior_key_suffix) or "prior"
    
    try:
        logger.info(f"display_comparison_tab for {name_suffix}: Received tab_data (keys): {list(tab_data.keys())}")
        # Move full JSON dumps to DEBUG level
        logger.debug(f"display_comparison_tab for {name_suffix}: Full tab_data: {json.dumps(tab_data, default=str, indent=2)}")
    except Exception as e:
        logger.error(f"Error logging incoming tab_data in display_comparison_tab for {name_suffix}: {e}")

    # Check if we're receiving raw data instead of properly transformed data
    if any(key in ['current_month', 'prior_month', 'budget', 'prior_year'] for key in tab_data.keys()):
        logger.error(f"Raw data format detected in display_comparison_tab for {name_suffix}. Keys: {list(tab_data.keys())}")
        st.error(f"Internal error: Data format mismatch for {name_suffix} comparison. Please reload the application.")
        return
    
    # Check for basic metrics that should be in any properly transformed data
    expected_current_keys = [key for key in tab_data.keys() if key.endswith('_current')]
    if not expected_current_keys:
        logger.error(f"No '_current' keys found in tab_data for {name_suffix}. Keys: {list(tab_data.keys())}")
        st.error(f"No data available for {name_suffix} comparison.")
        return
    
    # Extract current values from the tab_data
    current_values = {}
    for key in tab_data.keys():
        if key.endswith('_current'):
            base_metric = key.replace('_current', '')
            current_values[base_metric] = tab_data[key]
    logger.info(f"display_comparison_tab for {name_suffix}: Extracted current_values (keys): {list(current_values.keys())}")
    try:
        # Move full JSON dumps to DEBUG level
        logger.debug(f"display_comparison_tab for {name_suffix}: Full current_values: {json.dumps(current_values, default=str, indent=2)}")
    except Exception as e:
        logger.error(f"Error logging full current_values for {name_suffix}: {e}")
    
    # Extract prior values from the tab_data
    prior_values = {}
    for key in tab_data.keys():
        if key.endswith(f'_{prior_key_suffix}'):
            base_metric = key.replace(f'_{prior_key_suffix}', '')
            prior_values[base_metric] = tab_data[key]
        elif key.endswith('_compare'):  # Alternative format
            base_metric = key.replace('_compare', '')
            prior_values[base_metric] = tab_data[key]
    logger.info(f"display_comparison_tab for {name_suffix}: Extracted prior_values (keys): {list(prior_values.keys())}")
    try:
        # Move full JSON dumps to DEBUG level
        logger.debug(f"display_comparison_tab for {name_suffix}: Full prior_values: {json.dumps(prior_values, default=str, indent=2)}")
    except Exception as e:
        logger.error(f"Error logging full prior_values for {name_suffix}: {e}")
    
    # Log the extracted values for key metrics
    logger.info(f"Current NOI: {current_values.get('noi')}, Prior NOI: {prior_values.get('noi')}")
    
    # Create columns for KPI cards
    col1, col2, col3 = st.columns(3)
    
    # Display KPI cards using Streamlit's metric component instead of custom HTML
    with col1:
        # Current value
        current_noi = current_values.get("noi", 0.0)
        st.metric(label="Current", value=f"${current_noi:,.0f}")
        
    with col2:
        # Prior period value
        prior_noi = prior_values.get("noi", 0.0)
        st.metric(label=f"{name_suffix}", value=f"${prior_noi:,.0f}")
        
    with col3:
        # Change - get directly from tab_data or calculate
        change_val = tab_data.get("noi_change", tab_data.get("noi_variance", current_noi - prior_noi))
        percent_change = tab_data.get("noi_percent_change", tab_data.get("noi_percent_variance", 
                                      (change_val / prior_noi * 100) if prior_noi != 0 else 0))
        
        # Format the percentage value with sign
        percent_display = f"{percent_change:.1f}%"
        if percent_change > 0:
            percent_display = f"+{percent_display}"
        
        # NOI is a positive business impact when it increases (green for increase, red for decrease)
        st.metric(
            label="Change",
            value=percent_display,
            delta=f"${change_val:,.0f}",
            delta_color="normal" if change_val >= 0 else "inverse"
        )

    # Log additional information before creating DataFrame
    logger.info(f"Creating DataFrame for {name_suffix} comparison")
    
    # Create DataFrame for data
    metrics = ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"]
    data_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]

    df_data = []
    for key, name in zip(data_keys, metrics):
        # Handle both formats for current, prior, and change values
        current_val = current_values.get(key, tab_data.get(f"{key}_current", 0.0))
        prior_val = prior_values.get(key, tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_compare", 0.0)))
        change_val = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance", 0.0))
        percent_change = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance", 0.0))
        
        # Debug logging for data extraction
        logger.debug(f"Metric: {name}, Current: {current_val}, Prior: {prior_val}, Change: {change_val}, %Change: {percent_change}")
        
        # Skip zero values if show_zero_values is False
        if not st.session_state.show_zero_values and current_val == 0 and prior_val == 0:
            continue
            
        df_row = {
            "Metric": name,
            "Current": current_val,
            name_suffix: prior_val,
            "Change ($)": change_val,
            "Change (%)": percent_change,
            # Add business impact direction for proper color coding
            "Direction": "inverse" if name in ["Vacancy Loss", "Total OpEx"] else "normal"
        }
        df_data.append(df_row)
        logger.debug(f"display_comparison_tab for {name_suffix}: Appended to df_data: {json.dumps(df_row, default=str)}")

    # Create DataFrame for display
    if not df_data:
        logger.warning(f"No data available for {name_suffix} display")
        st.info("No data available for display. Try enabling 'Show Zero Values' in the sidebar.")
        return
        
    logger.info(f"Created df_data with {len(df_data)} rows for {name_suffix} comparison")
    
    try:
        # Create the DataFrame
        df = pd.DataFrame(df_data)
        logger.info(f"Created DataFrame with columns: {list(df.columns)}")
        
        # Check if the DataFrame has the expected columns
        required_columns = ["Metric", "Current", name_suffix, "Change ($)", "Change (%)"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"DataFrame is missing columns: {missing_columns}")
            st.error(f"Error: DataFrame is missing required columns: {', '.join(missing_columns)}")
            # Display the raw DataFrame as a fallback
            st.dataframe(df, use_container_width=True)
            return

        # Format DataFrame for display
        df_display = df.copy()
        df_display["Current"] = df_display["Current"].apply(lambda x: f"${x:,.2f}")
        df_display[name_suffix] = df_display[name_suffix].apply(lambda x: f"${x:,.2f}")
        df_display["Change ($)"] = df_display["Change ($)"].apply(lambda x: f"${x:,.2f}")
        df_display["Change (%)"] = df_display["Change (%)"].apply(lambda x: f"{x:.1f}%")
        
        # Remove the Direction column from display
        display_columns = ["Metric", "Current", name_suffix, "Change ($)", "Change (%)"]
        df_styled = df_display[display_columns]
        
        # Apply conditional formatting based on business impact
        def style_df(row):
            styles = [''] * len(row)
            
            # Get indices of the columns to style
            pct_change_idx = list(row.index).index("Change (%)")
            dollar_change_idx = list(row.index).index("Change ($)")
            metric_idx = list(row.index).index("Metric")
            
            metric = row["Metric"]
            
            try:
                change_pct_str = row["Change (%)"].strip('%') if isinstance(row["Change (%)"], str) else str(row["Change (%)"])
                change_pct = float(change_pct_str)
                
                # Determine color and impact label based on metric type and change direction
                if metric in ["Vacancy Loss", "Total OpEx"]:
                    # For these metrics (expenses/losses), a decrease (negative change) is FAVORABLE
                    if change_pct < 0:
                        color = "color: green"  # Negative change is favorable for expenses
                        impact = "Favorable"
                    elif change_pct > 0:
                        color = "color: red"    # Positive change is unfavorable for expenses
                        impact = "Unfavorable"
                    else:
                        color = ""              # No change, neutral impact
                        impact = "Neutral"
                else:
                    # For income metrics (NOI, GPR), an increase (positive change) is FAVORABLE
                    if change_pct > 0:
                        color = "color: green"  # Positive change is favorable for income
                        impact = "Favorable"
                    elif change_pct < 0:
                        color = "color: red"    # Negative change is unfavorable for income
                        impact = "Unfavorable"
                    else:
                        color = ""              # No change, neutral impact
                        impact = "Neutral"
                
                # Apply to both dollar and percentage columns
                styles[pct_change_idx] = color
                styles[dollar_change_idx] = color
                
                # Store the impact label if we want to add an Impact column
                row["Impact"] = impact
                
            except (ValueError, TypeError):
                # If there's an error parsing the percentage, don't apply styling
                pass
            
            return styles
        
        # Apply styling and display
        styled_df = df_styled.style.apply(style_df, axis=1)
        
        # Add Impact column if desired
        if "add_impact_column" not in st.session_state:
            st.session_state.add_impact_column = False
            
        impact_toggle = st.checkbox("Show Impact Column", value=st.session_state.add_impact_column, key=f"impact_toggle_{name_suffix}")
        if impact_toggle != st.session_state.add_impact_column:
            st.session_state.add_impact_column = impact_toggle
            st.rerun()
            
        if st.session_state.add_impact_column:
            # Add Impact column
            impacts = []
            for _, row in df.iterrows():
                metric = row["Metric"]
                change_pct = row["Change (%)"]
                
                # Determine impact based on metric and change
                if metric in ["Vacancy Loss", "Total OpEx"]:
                    # For expenses, decrease is favorable
                    impact = "Favorable" if change_pct < 0 else ("Unfavorable" if change_pct > 0 else "Neutral")
                else:
                    # For income, increase is favorable
                    impact = "Favorable" if change_pct > 0 else ("Unfavorable" if change_pct < 0 else "Neutral")
                    
                impacts.append(impact)
                
            df_styled["Impact"] = impacts
            styled_df = df_styled.style.apply(style_df, axis=1)
            
        st.dataframe(styled_df, use_container_width=True)
        
        # Add OpEx Breakdown expander section
        with st.expander("Operating Expense Breakdown"):
            # Check if we have OpEx component data
            opex_components = ["property_taxes", "insurance", "repairs_and_maintenance", "utilities", "management_fees"]
            
            # Check if any opex components exist in the data
            if any(component in current_values for component in opex_components):
                # Apply modern container styling
                st.markdown('<div class="opex-container">', unsafe_allow_html=True)
                
                # Modern header styling
                st.markdown('<div class="opex-header">Operating Expense Breakdown</div>', unsafe_allow_html=True)
                
                # Create DataFrame for OpEx components
                opex_df_data = []
                opex_metrics = ["Property Taxes", "Insurance", "Repairs & Maintenance", "Utilities", "Management Fees"]
                
                # Define color map for categories (will be used for both table indicators and charts)
                category_colors = {
                    "Property Taxes": "#4ecdc4",
                    "Insurance": "#1e88e5",
                    "Repairs & Maintenance": "#8ed1fc",
                    "Utilities": "#ff6b6b",
                    "Management Fees": "#ba68c8"
                }
                
                for key, name in zip(opex_components, opex_metrics):
                    # Handle both formats for current, prior, and change values
                    current_val = current_values.get(key, tab_data.get(f"{key}_current", 0.0))
                    prior_val = prior_values.get(key, tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_compare", 0.0)))
                    change_val = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance", 0.0))
                    percent_change = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance", 0.0))
                    
                    # Skip zero values if show_zero_values is False
                    if not st.session_state.show_zero_values and current_val == 0 and prior_val == 0:
                        continue
                        
                    opex_df_data.append({
                        "Expense Category": name,
                        "Current": current_val,
                        name_suffix: prior_val,
                        "Change ($)": change_val,
                        "Change (%)": percent_change,
                        # Add color for the category
                        "Color": category_colors.get(name, "#a9a9a9")  # Default gray if not in map
                    })
                
                # Check if we have data to display after filtering
                if opex_df_data:
                    opex_df = pd.DataFrame(opex_df_data)
                    
                    # Format DataFrame for display
                    opex_df_display = opex_df.copy()
                    opex_df_display["Current"] = opex_df_display["Current"].apply(lambda x: f"${x:,.2f}")
                    opex_df_display[name_suffix] = opex_df_display[name_suffix].apply(lambda x: f"${x:,.2f}")
                    opex_df_display["Change ($)"] = opex_df_display["Change ($)"].apply(lambda x: f"${x:,.2f}")
                    opex_df_display["Change (%)"] = opex_df_display["Change (%)"].apply(lambda x: f"{x:.1f}%")
                    
                    # Instead of using Streamlit's dataframe with styling,
                    # we'll create a custom HTML table with our modern design
                    html_table = """
                    <div class="opex-table-container">
                        <table class="opex-table">
                            <thead>
                                <tr>
                                    <th>Expense Category</th>
                                    <th>Current</th>
                                    <th>""" + safe_text(name_suffix) + """</th>
                                    <th>Change ($)</th>
                                    <th>Change (%)</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                    
                    # Add rows to the table
                    for _, row in opex_df_display.iterrows():
                        # Determine CSS class for values based on change direction
                        try:
                            change_pct_str = row["Change (%)"].strip('%') if isinstance(row["Change (%)"], str) else str(row["Change (%)"])
                            change_pct = float(change_pct_str)
                            if change_pct < 0:
                                value_class = "opex-positive-value"  # Green for decrease in expenses (favorable)
                            elif change_pct > 0:
                                value_class = "opex-negative-value"   # Red for increase in expenses (unfavorable)
                            else:
                                value_class = "opex-neutral-value"    # Neutral if no change
                        except (ValueError, TypeError):
                            value_class = "opex-neutral-value"        # Default to neutral if error
                        
                        # Get category color and ensure safe text
                        color = safe_text(row["Color"]) or "#a9a9a9"
                        category = safe_text(row["Expense Category"])
                        current_val = safe_text(row["Current"])
                        prior_val = safe_text(row[name_suffix])
                        change_dollar = safe_text(row["Change ($)"])
                        change_percent = safe_text(row["Change (%)"])
                        
                        # Add the row with color indicator
                        html_table += f"""
                        <tr>
                            <td>
                                <div class="opex-category-cell">
                                    <span class="opex-category-indicator" style="background-color: {color};"></span>
                                    {category}
                                </div>
                            </td>
                            <td class="opex-neutral-value">{current_val}</td>
                            <td class="opex-neutral-value">{prior_val}</td>
                            <td class="{value_class}">{change_dollar}</td>
                            <td class="{value_class}">{change_percent}</td>
                        </tr>
                        """
                    
                    # Close the table
                    html_table += """
                            </tbody>
                        </table>
                    </div>
                    """
                    
                    # Display the custom HTML table using st.markdown instead of components.html
                    st.markdown(html_table, unsafe_allow_html=True)
                    
                    # Create columns for charts with enhanced styling
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Wrap the chart in a container with our custom styling
                        chart_container_html = '<div class="opex-chart-container"><div class="opex-chart-title">Current Operating Expenses Breakdown</div></div>'
                        components.html(chart_container_html, height=50)
                        
                        # Filter out zero values for the pie chart
                        pie_data = opex_df[opex_df["Current"] > 0]
                        if not pie_data.empty:
                            # Create a custom color map based on our category colors
                            color_map = {row["Expense Category"]: row["Color"] for _, row in pie_data.iterrows()}
                            
                            fig = px.pie(
                                pie_data, 
                                values="Current", 
                                names="Expense Category",
                                color="Expense Category",
                                color_discrete_map=color_map,
                                hole=0.4
                            )
                            fig.update_layout(
                                template="plotly_dark",
                                plot_bgcolor='rgba(13, 17, 23, 0)',
                                paper_bgcolor='rgba(13, 17, 23, 0)',
                                font=dict(
                                    family="Inter, sans-serif",
                                    size=14,
                                    color="#e6edf3"
                                ),
                                margin=dict(l=20, r=20, t=20, b=20),
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.2,
                                    xanchor="center",
                                    x=0.5,
                                    font=dict(size=12, color="#e6edf3")
                                ),
                                showlegend=False  # Hide legend as we have colored indicators in the table
                            )
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Close the chart container
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        # Wrap the chart in a container with our custom styling
                        chart_container_html = f'<div class="opex-chart-container"><div class="opex-chart-title">OpEx Components: Current vs {name_suffix}</div></div>'
                        components.html(chart_container_html, height=50)
                        
                        # Create a horizontal bar chart for comparison
                        if not opex_df.empty:
                            # Prepare the data in a format suitable for the horizontal bar chart
                            bar_data = []
                            for _, row in opex_df.iterrows():
                                bar_data.append({
                                    "Expense Category": row["Expense Category"],
                                    "Amount": row["Current"],
                                    "Period": "Current",
                                    "Color": row["Color"]
                                })
                                bar_data.append({
                                    "Expense Category": row["Expense Category"],
                                    "Amount": opex_df[opex_df["Expense Category"] == row["Expense Category"]][name_suffix].values[0],
                                    "Period": name_suffix,
                                    "Color": row["Color"]
                                })
                            
                            bar_df = pd.DataFrame(bar_data)
                            
                            # Create the bar chart with improved styling
                            comp_fig = px.bar(
                                bar_df,
                                x="Amount",
                                y="Expense Category",
                                color="Period",
                                barmode="group",
                                orientation="h",
                                color_discrete_map={
                                    "Current": "#1e88e5",
                                    name_suffix: "#4ecdc4"
                                },
                                labels={"Amount": "Amount ($)", "Expense Category": ""}
                            )
                            
                            # Update layout for modern appearance
                            comp_fig.update_layout(
                                template="plotly_dark",
                                plot_bgcolor='rgba(13, 17, 23, 0)',
                                paper_bgcolor='rgba(13, 17, 23, 0)',
                                margin=dict(l=20, r=20, t=20, b=50),
                                font=dict(
                                    family="Inter, sans-serif",
                                    size=14,
                                    color="#e6edf3"
                                ),
                                xaxis=dict(
                                    showgrid=True,
                                    gridcolor='rgba(255, 255, 255, 0.1)',
                                    tickprefix="$",
                                    tickformat=',',
                                    title=dict(text="Amount ($)", font=dict(size=14))
                                ),
                                yaxis=dict(
                                    showgrid=False
                                ),
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.25,
                                    xanchor="right",
                                    x=1,
                                    font=dict(size=12, color="#e6edf3")
                                )
                            )
                            
                            st.plotly_chart(comp_fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Close the chart container
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Close the main container
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # We have components but no data to display
                    st.info("No operating expense details available for this period.")
            else:
                # No operating expense components in the data
                st.info("Operating expense breakdown is not available for this comparison.")
                
        # Add Other Income Breakdown expander section
        with st.expander("Other Income Breakdown"):
            # Check if we have Other Income component data
            other_income_components = [
                "parking", "laundry", "late_fees", "pet_fees", "application_fees",
                "storage_fees", "amenity_fees", "utility_reimbursements", 
                "cleaning_fees", "cancellation_fees", "miscellaneous"
            ]
            
            income_metrics = [
                "Parking", "Laundry", "Late Fees", "Pet Fees", "Application Fees",
                "Storage Fees", "Amenity Fees", "Utility Reimbursements", 
                "Cleaning Fees", "Cancellation Fees", "Miscellaneous"
            ]
            
            # MODIFIED: Check if any component exists with _current suffix in tab_data
            if any(f"{component}_current" in tab_data for component in other_income_components):
                logger.info(f"Found other income components in tab_data for {name_suffix}. Preparing breakdown.")
                # Create DataFrame for Other Income components
                income_df_data = []
                
                for key, name in zip(other_income_components, income_metrics):
                    # Handle both formats for current, prior, and change values
                    current_val = current_values.get(key, tab_data.get(f"{key}_current", 0.0))
                    prior_val = prior_values.get(key, tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_compare", 0.0)))
                    change_val = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance", 0.0))
                    percent_change = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance", 0.0))
                    
                    # Skip zero values if show_zero_values is False
                    if not st.session_state.show_zero_values and current_val == 0 and prior_val == 0:
                        continue
                        
                    income_df_data.append({
                        "Income Category": name,
                        "Current": current_val,
                        name_suffix: prior_val,
                        "Change ($)": change_val,
                        "Change (%)": percent_change,
                        # Other Income is positive when it increases
                        "Direction": "Favorable" if change_val > 0 else ("Unfavorable" if change_val < 0 else "Neutral")
                    })
                
                if income_df_data:
                    # Sort by current value (descending) to show most significant components first
                    income_df_data = sorted(income_df_data, key=lambda x: x["Current"], reverse=True)
                    
                    # Add a total row
                    total_current = sum(item["Current"] for item in income_df_data)
                    total_prior = sum(item[name_suffix] for item in income_df_data)
                    total_change = total_current - total_prior
                    total_percent = (total_change / total_prior * 100) if total_prior else 0
                    
                    income_df_data.append({
                        "Income Category": "Total Other Income",
                        "Current": total_current,
                        name_suffix: total_prior,
                        "Change ($)": total_change,
                        "Change (%)": total_percent,
                        "Direction": "Favorable" if total_change > 0 else ("Unfavorable" if total_change < 0 else "Neutral")
                    })
                    
                    income_df = pd.DataFrame(income_df_data)
                    
                    # Format DataFrame for display
                    income_df_display = income_df.copy()
                    income_df_display["Current"] = income_df_display["Current"].apply(lambda x: f"${x:,.2f}")
                    income_df_display[name_suffix] = income_df_display[name_suffix].apply(lambda x: f"${x:,.2f}")
                    income_df_display["Change ($)"] = income_df_display["Change ($)"].apply(lambda x: f"${x:,.2f}")
                    income_df_display["Change (%)"] = income_df_display["Change (%)"].apply(lambda x: f"{x:.1f}%")
                    
                    # Add percentage of total column
                    income_percents = []
                    for item in income_df_data:
                        if item["Income Category"] == "Total Other Income":
                            income_percents.append("100.0%")
                        else:
                            pct = (item["Current"] / total_current * 100) if total_current > 0 else 0
                            income_percents.append(f"{pct:.1f}%")
                    
                    income_df_display["% of Total"] = income_percents
                    
                    # Rename Direction to Impact for display
                    income_df_display["Impact"] = income_df_display["Direction"]
                    income_df_display = income_df_display.drop(columns=["Direction"])
                    
                    # Create a function to apply styling
                    def style_income_df(row):
                        styles = [''] * len(row)
                        
                        # Get indices of the columns to style
                        pct_change_idx = list(row.index).index("Change (%)")
                        dollar_change_idx = list(row.index).index("Change ($)")
                        
                        # Get total row styling
                        if row["Income Category"] == "Total Other Income":
                            return ['font-weight: bold'] * len(row)
                        
                        try:
                            direction = row.get("Direction", "")
                            
                            # Apply colors based on business impact
                            if direction == "Favorable":
                                color = "color: green"  # Positive impact on NOI
                            elif direction == "Unfavorable":
                                color = "color: red"    # Negative impact on NOI
                            else:
                                color = ""              # Neutral impact
                            
                            # Apply to both dollar and percentage columns
                            styles[pct_change_idx] = color
                            styles[dollar_change_idx] = color
                        except (ValueError, TypeError, KeyError):
                            # If there's an error, don't apply styling
                            pass
                        
                        return styles
                    
                    # Apply styling and display
                    income_styled = income_df_display.style.apply(style_income_df, axis=1)
                    st.dataframe(income_styled, use_container_width=True)
                    
                    # Display a pie chart to visualize the breakdown
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Filter out zero values and total row for the pie chart
                        pie_data = income_df[
                            (income_df["Current"] > 0) & 
                            (income_df["Income Category"] != "Total Other Income")
                        ]
                        if not pie_data.empty:
                            fig = px.pie(
                                pie_data, 
                                values="Current", 
                                names="Income Category",
                                title="Current Other Income Breakdown",
                                color_discrete_sequence=px.colors.qualitative.Pastel,
                                hole=0.4
                            )
                            fig.update_layout(
                                template="plotly_dark",
                                plot_bgcolor='rgba(30, 41, 59, 0.8)',
                                paper_bgcolor='rgba(16, 23, 42, 0)',
                                font=dict(
                                    family="Inter, sans-serif",
                                    size=12,
                                    color="#F0F0F0"
                                ),
                                title_font=dict(size=16, color="#F0F0F0", family="Inter, sans-serif"),
                                legend=dict(font=dict(size=10, color="#F0F0F0"))
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Create horizontal bar chart for comparing current vs prior
                        comp_data = income_df.copy()
                        
                        # Sort by current value
                        comp_data = comp_data[comp_data["Income Category"] != "Total Other Income"]
                        comp_data = comp_data.sort_values(by="Current", ascending=True)
                        
                        # Only show top 6 categories to avoid chart getting too crowded
                        if len(comp_data) > 6:
                            comp_data = comp_data.tail(6)  # Get the 6 largest categories
                        
                        # Create horizontal bar chart for comparing current vs prior
                        comp_fig = go.Figure()
                        
                        # Add bars for current and prior values
                        comp_fig.add_trace(go.Bar(
                            y=comp_data["Income Category"],
                            x=comp_data["Current"],
                            name="Current",
                            orientation='h',
                            marker=dict(color="#4DB6AC")
                        ))
                        
                        comp_fig.add_trace(go.Bar(
                            y=comp_data["Income Category"],
                            x=comp_data[name_suffix],
                            name=name_suffix,
                            orientation='h',
                            marker=dict(color="#BA68C8")
                        ))
                        
                        # Update layout
                        comp_fig.update_layout(
                            title=f"Top Other Income Components: Current vs {name_suffix}",
                            barmode='group',
                            xaxis_title="Amount ($)",
                            xaxis=dict(tickprefix="$"),
                            template="plotly_dark",
                            plot_bgcolor='rgba(30, 41, 59, 0.8)',
                            paper_bgcolor='rgba(16, 23, 42, 0)',
                            margin=dict(l=20, r=20, t=60, b=80),
                            font=dict(
                                family="Inter, sans-serif",
                                size=12,
                                color="#F0F0F0"
                            ),
                            title_font=dict(size=16, color="#F0F0F0", family="Inter, sans-serif"),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.2,
                                xanchor="center",
                                x=0.5,
                                font=dict(size=10, color="#F0F0F0")
                            )
                        )
                        
                        st.plotly_chart(comp_fig, use_container_width=True)
                    
                    # Add a section with key insights about other income
                    st.subheader("Other Income Insights")
                    
                    # Find the largest income component
                    non_total_data = [item for item in income_df_data if item["Income Category"] != "Total Other Income"]
                    if non_total_data:
                        largest_component = max(non_total_data, key=lambda x: x["Current"])
                        largest_pct = (largest_component["Current"] / total_current * 100) if total_current > 0 else 0
                        
                        st.markdown(f"- **{largest_component['Income Category']}** is the largest source of other income at **${largest_component['Current']:,.2f}** ({largest_pct:.1f}% of total)")
                    
                    # Find the component with largest growth
                    growth_components = [item for item in non_total_data if item["Change (%)"] > 0]
                    if growth_components:
                        fastest_growth = max(growth_components, key=lambda x: x["Change (%)"])
                        st.markdown(f"- **{fastest_growth['Income Category']}** has the highest growth at **{fastest_growth['Change (%)']}%** (${fastest_growth['Change ($)']:,.2f})")
                    
                    # Find declining components
                    declining_components = [item for item in non_total_data if item["Change (%)"] < 0]
                    if declining_components:
                        most_decline = min(declining_components, key=lambda x: x["Change (%)"])
                        st.markdown(f"- **{most_decline['Income Category']}** has decreased by **{abs(most_decline['Change (%)']):,.1f}%** (${abs(most_decline['Change ($)']):,.2f})")
                    
                    # Overall trend
                    if total_change > 0:
                        st.markdown(f"- Overall other income has **increased** by **${total_change:,.2f}** ({total_percent:.1f}%)")
                    elif total_change < 0:
                        st.markdown(f"- Overall other income has **decreased** by **${abs(total_change):,.2f}** ({abs(total_percent):.1f}%)")
                        
                    # Opportunity analysis
                    low_components = [item for item in non_total_data if item["Current"] == 0 and item[name_suffix] > 0]
                    if low_components:
                        st.markdown("- **Opportunity alert:** The following income sources had values previously but are now at zero:")
                        for item in low_components:
                            st.markdown(f"  - **{item['Income Category']}** (previously ${item[name_suffix]:,.2f})")
                    else:
                        st.info("No other income details available for this period.")
                        logger.info(f"No other income component keys (e.g., parking_current) found in tab_data for {name_suffix}. Displaying 'no details' message.")
                else:
                    st.info("Other income components were identified, but all had zero values for both current and prior periods (and 'Show Zero Values' is off).")
                    logger.info(f"Other income components found but resulted in empty df_data for {name_suffix} (likely all zeros and show_zero_values is False).")
            else:
                st.info("No other income details available for this period.")
                logger.info(f"No other income component keys (e.g., parking_current) found in tab_data for {name_suffix}. Displaying 'no details' message.")
        
        try:
            logger.info(f"Creating charts for {name_suffix} comparison")
            # Create bar chart for visual comparison
            
            # Add chart container and title for modern styling
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown(f'<div class="chart-title">Current vs {name_suffix}</div>', unsafe_allow_html=True)

            fig = go.Figure()

            # Calculate change percentages for hover data
            change_pcts = df["Change (%)"].tolist()
            change_vals = df["Change ($)"].tolist()
            directions = df["Direction"].tolist()
            metrics = df["Metric"].tolist()
            
            # Helper function to determine if a change is positive from business perspective
            def is_positive_change(metric, change_val):
                if metric in ["Vacancy Loss", "Total OpEx"]:
                    # For these metrics, a decrease (negative change) is good
                    return change_val < 0
                else:
                    # For other metrics (NOI, GPR, EGI, etc.), an increase (positive change) is good
                    return change_val > 0
            
            # Use consistent vibrant colors instead of gradients
            current_color = '#1e88e5'  # Vibrant blue
            compare_color = '#00bfa5'  # Teal green

            # Add current period bars with enhanced styling
            fig.add_trace(go.Bar(
                x=df["Metric"],
                y=df["Current"],
                name="Current",
                marker=dict(
                    color=current_color,
                    line=dict(width=0)  # Remove bar borders
                ),
                opacity=0.9,
                customdata=list(zip(change_vals, change_pcts, directions)),
                hovertemplate='<b>%{x}</b><br>Current: $%{y:,.0f}<br>Change: $%{customdata[0]:,.0f} (%{customdata[1]:.1f}%)<extra></extra>'
            ))

            # Add prior period bars with enhanced styling
            fig.add_trace(go.Bar(
                x=df["Metric"],
                y=df[name_suffix],
                name=name_suffix,
                marker=dict(
                    color=compare_color,
                    line=dict(width=0)  # Remove bar borders
                ),
                opacity=0.9,
                customdata=list(zip(df["Metric"])),
                hovertemplate='<b>%{x}</b><br>' + f'{name_suffix}: $' + '%{y:,.0f}<extra></extra>'
            ))

            # Identify peak NOI for annotation
            if 'NOI' in df['Metric'].values:
                current_noi = df.loc[df['Metric'] == 'NOI', 'Current'].values[0]
                prior_noi = df.loc[df['Metric'] == 'NOI', name_suffix].values[0]
                
                # Calculate the difference and percentage change with safe handling
                noi_diff = current_noi - prior_noi if current_noi is not None and prior_noi is not None else 0
                noi_pct = (noi_diff / prior_noi * 100) if prior_noi != 0 and prior_noi is not None else 0
                
                # Ensure safe text for annotation
                noi_diff_safe = safe_text(noi_diff) or "0"
                noi_pct_safe = safe_text(f"{noi_pct:.1f}") or "0.0"
                
                # Create annotation text based on whether NOI increased or decreased
                # For NOI, an increase is positive (green), decrease is negative (red)
                if noi_diff > 0:
                    annotation_text = safe_text(f"NOI increased by<br>${noi_diff:,.0f}<br>({noi_pct:.1f}%)")
                    arrow_color = "#00bfa5"  # Teal green for positive
                elif noi_diff < 0:
                    annotation_text = safe_text(f"NOI decreased by<br>${abs(noi_diff):,.0f}<br>({noi_pct:.1f}%)")
                    arrow_color = "#f44336"  # Red for negative
                else:
                    annotation_text = safe_text("NOI unchanged")
                    arrow_color = "#78909c"  # Gray for neutral
                    
                # Add annotation for NOI with improved styling
                fig.add_annotation(
                    x='NOI', 
                    y=max(current_noi, prior_noi) * 1.15,  # Position higher above the bar
                    text=annotation_text,
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=arrow_color,
                    bgcolor="rgba(13, 17, 23, 0.8)",
                    bordercolor=arrow_color,
                    borderwidth=1,
                    borderpad=8,  # Increased padding
                    font=dict(
                        family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                        color="#e6edf3",
                        size=14
                    ),
                    align="center"
                )

            # Update layout with modern theme styling
            fig.update_layout(
                barmode='group',
                title=None,  # Remove title as we use custom title above
                template="plotly_dark",
                plot_bgcolor='rgba(13, 17, 23, 0)',  # Transparent background
                paper_bgcolor='rgba(13, 17, 23, 0)',  # Transparent paper
                font=dict(
                    family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                    size=14,
                    color="#e6edf3"
                ),
                margin=dict(l=40, r=40, t=20, b=100),  # Increased bottom margin for legend
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.25,  # Moved further down to avoid overlap
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(13, 17, 23, 0.5)",  # Semi-transparent background
                    bordercolor="rgba(56, 139, 253, 0.15)",
                    borderwidth=1,
                    font=dict(
                        size=14,
                        color="#e6edf3"
                    )
                ),
                xaxis=dict(
                    title=None,
                    tickfont=dict(
                        family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                        size=14,
                        color="#e6edf3"
                    ),
                    showgrid=False,
                    zeroline=False,
                    showline=False
                ),
                yaxis=dict(
                    title=dict(
                        text="Amount ($)",
                        font=dict(
                            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                            size=14,
                            color="#e6edf3"
                        )
                    ),
                    showgrid=True,
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    gridwidth=0.5,
                    zeroline=False,
                    showline=False,
                    tickfont=dict(
                        family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                        size=14,
                        color="#e6edf3"
                    )
                ),
                hoverlabel=dict(
                    bgcolor="rgba(13, 17, 23, 0.8)",
                    font_size=14,
                    font_family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                    font_color="#e6edf3",
                    bordercolor="rgba(56, 139, 253, 0.15)"
                ),
                bargap=0.15,  # Adjust bar gap
                bargroupgap=0.05  # Adjust gap between grouped bars
            )

            # Add dollar sign to y-axis labels
            fig.update_yaxes(tickprefix="$", tickformat=",.0f")
            
            # Wrap the chart display in the container div
            st.plotly_chart(fig, use_container_width=True)
            
            # Close the chart container div
            st.markdown('</div>', unsafe_allow_html=True)
            
            logger.info(f"Successfully displayed chart for {name_suffix} comparison")

            # --- Consolidated Insights, Executive Summary, and Recommendations Section ---
            st.markdown("---")
            st.markdown("""
                <div class="results-main-title">Analysis and Recommendations</div>
            """, unsafe_allow_html=True)

            insights_data = st.session_state.get("insights")
            # narrative_data = st.session_state.get("edited_narrative") or st.session_state.get("generated_narrative") # narrative_data is not directly used here for insights

            # Use the unified insights display function
            if insights_data and isinstance(insights_data, dict):
                # We might want to pass a filtered version of insights_data specific to this tab 
                # or the full one if display_unified_insights handles context appropriately.
                # For now, passing the full insights_data as per instruction.
                display_unified_insights(insights_data)
            else:
                st.info(f"No overall insights data available to display for {name_suffix} context.")

            # The old detailed breakdown of insights per comparison type within this tab is now handled by display_unified_insights.
            # The recommendations and narrative sections (if they were part of the old structure here) are also covered 
            # by display_unified_insights or by the main Financial Narrative tab.

            # Display OpEx breakdown if available
            if 'opex_components' in tab_data and tab_data['opex_components']:
                display_opex_breakdown(tab_data['opex_components'], name_suffix)
            else:
                logger.info(f"No OpEx components found for {name_suffix} comparison")

        except Exception as e:
            logger.error(f"Error displaying comparison tab {name_suffix}: {str(e)}", exc_info=True)
        
        # Removed PDF Generation Block from display_comparison_tab function
        # The comprehensive PDF generator at the bottom of the app now handles all PDF export needs

    # THIS IS THE END OF THE display_comparison_tab function's main try block
    except Exception as e_main_display: # Catch-all for the entire display_comparison_tab function
        logger.error(f"An unexpected error occurred in display_comparison_tab for {name_suffix}: {str(e_main_display)}", exc_info=True)
        st.error(f"An error occurred while displaying the comparison tab for {name_suffix}: {name_suffix}.")
    # Return for display_comparison_tab, ensuring it's at the same indent level as the try/except
    logger.info(f"--- display_comparison_tab END for {name_suffix} ---")
    return

# Function to handle user questions about NOI data
def ask_noi_coach(question: str, comparison_results: Dict[str, Any], context: str) -> str:
    """
    Process user questions about NOI data and generate responses.
    
    Args:
        question: The user's question
        comparison_results: The comparison results dictionary
        context: The selected comparison context (budget, prior_month, prior_year)
    
    Returns:
        A string response to the user's question
    """
    logger.info(f"NOI Coach question received: {question}")
    logger.info(f"Context: {context}")
    
    # Safety check for comparison results
    if not comparison_results or "current" not in comparison_results:
        return "I don't have enough financial data to answer that question. Please make sure you've uploaded your financial documents."
    
    try:
        # Prepare the data for the selected context
        context_data = {}
        context_data["current"] = comparison_results.get("current", {})
        
        if context == "budget" and "budget" in comparison_results:
            context_data["compare"] = comparison_results.get("budget", {})
            comparison_type = "budget"
        elif context == "prior_month" and "prior" in comparison_results:
            context_data["compare"] = comparison_results.get("prior", {})
            comparison_type = "prior month"
        elif context == "prior_year" and "prior_year" in comparison_results:
            context_data["compare"] = comparison_results.get("prior_year", {})
            comparison_type = "prior year"
        else:
            # Default to budget if available
            if "budget" in comparison_results:
                context_data["compare"] = comparison_results.get("budget", {})
                comparison_type = "budget"
            else:
                return "I don't have the comparison data you're asking about. Please select a different context or upload the relevant document."
        
        # Format the data into a structured message
        data_summary = f"""
        Current period NOI: ${context_data['current'].get('noi', 0):,.2f}
        Comparison period ({comparison_type}) NOI: ${context_data['compare'].get('noi', 0):,.2f}
        
        Key metrics comparison:
        - GPR: ${context_data['current'].get('gpr', 0):,.2f} vs ${context_data['compare'].get('gpr', 0):,.2f}
        - Vacancy Loss: ${context_data['current'].get('vacancy_loss', 0):,.2f} vs ${context_data['compare'].get('vacancy_loss', 0):,.2f}
        - Other Income: ${context_data['current'].get('other_income', 0):,.2f} vs ${context_data['compare'].get('other_income', 0):,.2f}
        - EGI: ${context_data['current'].get('egi', 0):,.2f} vs ${context_data['compare'].get('egi', 0):,.2f}
        - OpEx: ${context_data['current'].get('opex', 0):,.2f} vs ${context_data['compare'].get('opex', 0):,.2f}
        """
        
        # Check if we have insights already generated
        insights_text = ""
        if hasattr(st.session_state, "insights") and st.session_state.insights:
            insights = st.session_state.insights
            if "summary" in insights:
                insights_text += f"Summary: {insights['summary']}\n\n"
            if context in insights:
                insights_text += f"Analysis: {insights[context]}\n\n"
        
        # Simple analytics to answer basic questions
        if "driving" in question.lower() or "factor" in question.lower():
            # Identify main drivers for changes in NOI
            current_noi = context_data['current'].get('noi', 0)
            compare_noi = context_data['compare'].get('noi', 0)
            noi_change = current_noi - compare_noi
            
            # Calculate percent contributions to NOI change
            factors = []
            
            # Revenue factors
            current_gpr = context_data['current'].get('gpr', 0)
            compare_gpr = context_data['compare'].get('gpr', 0)
            gpr_change = current_gpr - compare_gpr
            if abs(gpr_change) > 0.01 * abs(compare_gpr):
                factors.append({
                    "factor": "Gross Potential Rent",
                    "change": gpr_change,
                    "percent": gpr_change / abs(compare_gpr) * 100 if compare_gpr else 0
                })
            
            # Vacancy factors
            current_vacancy = context_data['current'].get('vacancy_loss', 0)
            compare_vacancy = context_data['compare'].get('vacancy_loss', 0)
            vacancy_change = current_vacancy - compare_vacancy
            if abs(vacancy_change) > 0.01 * abs(compare_noi):
                factors.append({
                    "factor": "Vacancy Loss",
                    "change": vacancy_change,
                    "percent": vacancy_change / abs(compare_noi) * 100 if compare_noi else 0
                })
            
            # Other income factors
            current_other = context_data['current'].get('other_income', 0)
            compare_other = context_data['compare'].get('other_income', 0)
            other_change = current_other - compare_other
            if abs(other_change) > 0.01 * abs(compare_noi):
                factors.append({
                    "factor": "Other Income",
                    "change": other_change,
                    "percent": other_change / abs(compare_noi) * 100 if compare_noi else 0
                })
            
            # Operating expense factors
            current_opex = context_data['current'].get('opex', 0)
            compare_opex = context_data['compare'].get('opex', 0)
            opex_change = current_opex - compare_opex
            if abs(opex_change) > 0.01 * abs(compare_noi):
                factors.append({
                    "factor": "Operating Expenses",
                    "change": opex_change,
                    "percent": opex_change / abs(compare_noi) * 100 if compare_noi else 0
                })
            
            # Sort factors by absolute impact
            factors.sort(key=lambda x: abs(x["change"]), reverse=True)
            
            # Generate response
            response = f"Based on your {comparison_type} comparison data, the main factors driving NOI change are:\n\n"
            
            for factor in factors:
                change_str = f"${abs(factor['change']):,.2f}"
                direction = "increase" if factor["change"] > 0 else "decrease"
                impact = "positive" if (factor["change"] > 0 and factor["factor"] != "Vacancy Loss" and factor["factor"] != "Operating Expenses") or \
                                      (factor["change"] < 0 and (factor["factor"] == "Vacancy Loss" or factor["factor"] == "Operating Expenses")) else "negative"
                
                response += f"- {factor['factor']}: {change_str} {direction} ({abs(factor['percent']):.1f}% of NOI), {impact} impact\n"
            
            return response
        
        elif "vacancy" in question.lower() or "occupancy" in question.lower():
            # Provide vacancy analysis
            current_vacancy = context_data['current'].get('vacancy_loss', 0)
            compare_vacancy = context_data['compare'].get('vacancy_loss', 0)
            vacancy_change = current_vacancy - compare_vacancy
            
            current_gpr = context_data['current'].get('gpr', 0)
            compare_gpr = context_data['compare'].get('gpr', 0)
            
            current_vacancy_rate = (current_vacancy / current_gpr * 100) if current_gpr else 0
            compare_vacancy_rate = (compare_vacancy / compare_gpr * 100) if compare_gpr else 0
            
            response = f"Vacancy analysis compared to {comparison_type}:\n\n"
            response += f"- Current vacancy loss: ${current_vacancy:,.2f} ({current_vacancy_rate:.1f}% of GPR)\n"
            response += f"- Comparison vacancy loss: ${compare_vacancy:,.2f} ({compare_vacancy_rate:.1f}% of GPR)\n"
            
            if current_vacancy > compare_vacancy:
                response += f"\nVacancy has increased by ${vacancy_change:,.2f}, which is a negative trend. "
                response += "This suggests occupancy rates have decreased, reducing potential rental income."
            else:
                response += f"\nVacancy has decreased by ${abs(vacancy_change):,.2f}, which is a positive trend. "
                response += "This suggests improved occupancy rates, increasing your rental income."
            
            return response
            
        else:
            # For other questions, provide a general analysis
            current_noi = context_data['current'].get('noi', 0)
            compare_noi = context_data['compare'].get('noi', 0)
            noi_change = current_noi - compare_noi
            noi_pct_change = (noi_change / compare_noi * 100) if compare_noi else 0
            
            response = f"Based on your {comparison_type} comparison data:\n\n"
            
            if noi_change > 0:
                response += f"Your NOI has increased by ${noi_change:,.2f} ({noi_pct_change:.1f}%) compared to the {comparison_type}. "
                response += "This is a positive trend indicating improved property performance.\n\n"
            else:
                response += f"Your NOI has decreased by ${abs(noi_change):,.2f} ({abs(noi_pct_change):.1f}%) compared to the {comparison_type}. "
                response += "This suggests challenges that may need to be addressed.\n\n"
            
            # Add insight on revenue
            current_egi = context_data['current'].get('egi', 0)
            compare_egi = context_data['compare'].get('egi', 0)
            egi_change = current_egi - compare_egi
            egi_pct_change = (egi_change / compare_egi * 100) if compare_egi else 0
            
            if egi_change > 0:
                response += f"Revenue (EGI) is up by ${egi_change:,.2f} ({egi_pct_change:.1f}%). "
            else:
                response += f"Revenue (EGI) is down by ${abs(egi_change):,.2f} ({abs(egi_pct_change):.1f}%). "
            
            # Add insight on expenses
            current_opex = context_data['current'].get('opex', 0)
            compare_opex = context_data['compare'].get('opex', 0)
            opex_change = current_opex - compare_opex
            opex_pct_change = (opex_change / compare_opex * 100) if compare_opex else 0
            
            if opex_change > 0:
                response += f"Operating expenses have increased by ${opex_change:,.2f} ({opex_pct_change:.1f}%)."
            else:
                response += f"Operating expenses have decreased by ${abs(opex_change):,.2f} ({abs(opex_pct_change):.1f}%)."
            
            return response
        
    except Exception as e:
        logger.error(f"Error in ask_noi_coach: {str(e)}")
        return f"I encountered an error while analyzing your data: {str(e)}"

# Function to display NOI Coach interface
def display_noi_coach():
    """Display the NOI Coach interface with chat input and response area."""
    st.markdown("<h2 class='reborn-section-title'>NOI Coach</h2>", unsafe_allow_html=True)
    
    # Initialize session state for chat history if not exists
    if 'noi_coach_history' not in st.session_state:
        st.session_state.noi_coach_history = []
    
    # Add CSS for chat interface
    st.markdown("""
    <style>
        /* Chat message styling */
        .chat-message {
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0.5rem;
            max-width: 80%;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .user-message {
            background-color: #1e88e5;
            color: white;
            margin-left: auto;
            margin-right: 0;
        }
        
        .assistant-message {
            background-color: rgba(22, 27, 34, 0.8);
            color: #e6edf3;
            margin-right: auto;
            margin-left: 0;
            border: 1px solid rgba(56, 68, 77, 0.5);
        }
        
        .chat-message-content {
            word-wrap: break-word;
            line-height: 1.5;
        }
        
        .chat-input-label {
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #e6edf3;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.noi_coach_history:
        role = message["role"]
        content = safe_text(message["content"])
        
        if role == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="chat-message-content">{content}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div class="chat-message-content">{content}</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    with st.form(key="noi_coach_form", clear_on_submit=True):
        st.markdown("<div class='chat-input-label'>Ask a question about your financial data:</div>", unsafe_allow_html=True)
        user_question = st.text_input("", placeholder="e.g., What's driving the change in NOI?", label_visibility="collapsed")
        
        col1, col2 = st.columns([4, 1])
        with col2:
            submit_button = st.form_submit_button("Ask NOI Coach")
    
    # Process the question when submitted
    if submit_button and user_question:
        # Log the question
        logger.info(f"NOI Coach question received: {user_question}")
        
        # Add user message to history
        st.session_state.noi_coach_history.append({
            "role": "user",
            "content": user_question
        })
        
        # Check if we have financial data to analyze
        if 'comparison_results' not in st.session_state or not st.session_state.comparison_results:
            response = "Please process financial documents first so I can analyze your data."
        else:
            try:
                # Check if we have ai_insights_gpt module for NOI Coach functionality
                if generate_noi_coach_response is not None:
                    # Get the current context selection from session state
                    current_view = getattr(st.session_state, 'current_comparison_view', 'budget')
                    response = generate_noi_coach_response(user_question, st.session_state.comparison_results, current_view)
                else:
                    # Fallback response if ai_insights_gpt is not available
                    logger.warning("ai_insights_gpt module not available for NOI Coach")
                    comparison_data = st.session_state.comparison_results
                    current_data = comparison_data.get('current', {})
                    
                    # Generate a basic response based on available data
                    if 'noi' in current_data:
                        current_noi = current_data.get('noi', 0)
                        response = f"Based on your financial data, your current NOI is ${current_noi:,.2f}. "
                        
                        # Add context based on comparison data
                        if 'budget' in comparison_data:
                            budget_noi = comparison_data['budget'].get('noi', 0)
                            noi_diff = current_noi - budget_noi
                            if noi_diff > 0:
                                response += f"This is ${noi_diff:,.2f} above your budget target. "
                            elif noi_diff < 0:
                                response += f"This is ${abs(noi_diff):,.2f} below your budget target. "
                        
                        response += "For more detailed analysis, please ensure all financial documents are properly processed."
                    else:
                        response = "I can see your financial data, but I need more information to provide a detailed analysis. Please ensure all documents are properly processed."
                
            except Exception as e:
                logger.error(f"Error generating NOI Coach response: {str(e)}")
                response = "I'm sorry, I encountered an error while analyzing your data. Please try again later."
        
        # Add assistant response to history
        st.session_state.noi_coach_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Rerun to display the updated chat
        st.rerun()

def display_unified_insights_no_html(insights_data):
    """
    Display unified insights using pure Streamlit components without HTML.
    
    Args:
        insights_data: Dictionary containing 'summary', 'performance', and 'recommendations' keys
    """
    if not insights_data or not isinstance(insights_data, dict):
        st.warning("No insights data available to display.")
        return
    
    # Display Executive Summary
    if 'summary' in insights_data:
        st.markdown("## Executive Summary")
        
        summary_text = insights_data['summary']
        # Remove redundant "Executive Summary:" prefix if it exists
        if summary_text.startswith("Executive Summary:"):
            summary_text = summary_text[len("Executive Summary:"):].strip()
            
        st.markdown(summary_text)
    
    # Display Key Performance Insights
    if 'performance' in insights_data and insights_data['performance']:
        st.markdown("## Key Performance Insights")
        
        for insight in insights_data['performance']:
            col1, col2 = st.columns([1, 20])
            with col1:
                st.markdown("•")
            with col2:
                st.markdown(insight)
    
    # Display Recommendations
    if 'recommendations' in insights_data and insights_data['recommendations']:
        st.markdown("## Recommendations")
        
        for recommendation in insights_data['recommendations']:
            col1, col2 = st.columns([1, 20])
            with col1:
                st.markdown("•")
            with col2:
                st.markdown(recommendation)

# Define the generate_comprehensive_pdf function before it's called in main()
def generate_comprehensive_pdf():
    """
    Generate a comprehensive PDF report that includes all available data,
    insights, and visualizations from the NOI analysis.
    
    Returns:
        bytes: PDF file as bytes if successful, None otherwise
    """
    logger.info("PDF EXPORT: Generating comprehensive PDF with all available data")
    
    try:
        # Verify we have the necessary data
        if not report_template:
            logger.error("PDF EXPORT: Global report_template is None. PDF generation will fail.")
            return None
            
        if not hasattr(st.session_state, 'comparison_results') or not st.session_state.comparison_results:
            logger.error("PDF EXPORT: No comparison results found in session state")
            return None
            
        # Get property name
        property_name = st.session_state.property_name if hasattr(st.session_state, 'property_name') and st.session_state.property_name else "Property"
        
        # Prepare context for the template
        context = {
            'datetime': datetime,
            'property_name': property_name,
            'performance_data': {}
        }
        
        # Add current period data
        if 'current' in st.session_state.comparison_results:
            current_data = st.session_state.comparison_results['current']
            context['performance_data'].update(current_data)
            
            # Format key metrics for display
            for key in ['gpr', 'vacancy_loss', 'other_income', 'egi', 'opex', 'noi']:
                if key in current_data:
                    context['performance_data'][f'{key}_formatted'] = f"${current_data[key]:,.2f}" if current_data[key] is not None else "N/A"
        
        # Add comparison data
        comparison_sections = ['month_vs_prior', 'actual_vs_budget', 'year_vs_year']
        for section in comparison_sections:
            if section in st.session_state.comparison_results:
                context['performance_data'][section] = st.session_state.comparison_results[section]
                
                # Format key metrics for display
                section_data = st.session_state.comparison_results[section]
                for key in list(section_data.keys()):
                    if isinstance(section_data[key], (int, float)):
                        context['performance_data'][section][f'{key}_formatted'] = f"${section_data[key]:,.2f}"
        
        # Add insights if available
        if hasattr(st.session_state, 'insights') and st.session_state.insights:
            context['performance_data']['insights'] = st.session_state.insights
            
            # Ensure all expected keys exist
            for key in ['summary', 'performance', 'recommendations']:
                if key not in context['performance_data']['insights']:
                    context['performance_data']['insights'][key] = []
        
        # Add narrative if available
        if hasattr(st.session_state, 'generated_narrative') and st.session_state.generated_narrative:
            context['performance_data']['financial_narrative'] = st.session_state.generated_narrative
        elif hasattr(st.session_state, 'edited_narrative') and st.session_state.edited_narrative:
            context['performance_data']['financial_narrative'] = st.session_state.edited_narrative
        
        # Add executive summary if available
        if hasattr(st.session_state, 'insights') and st.session_state.insights and 'summary' in st.session_state.insights:
            context['performance_data']['executive_summary'] = st.session_state.insights['summary']
        
        # Render the template to HTML
        html_content = report_template.render(**context)
        logger.info("PDF EXPORT: Comprehensive HTML content rendered from template")
        
        # Write HTML to temporary file for debugging if needed
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix='.html').name
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"PDF EXPORT: HTML content written to temporary file: {tmp_path}")
        
        # Remove font-display property to prevent WeasyPrint warnings
        html_content = html_content.replace('font-display: swap;', '/* font-display: swap; */')
        
        # Generate PDF from HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        logger.info("PDF EXPORT: Comprehensive PDF bytes generated successfully")
        
        # Clean up temporary file
        try:
            os.remove(tmp_path)
        except Exception as e:
            logger.warning(f"PDF EXPORT: Could not remove temporary file {tmp_path}: {str(e)}")
            
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"PDF EXPORT: Error generating comprehensive PDF: {str(e)}", exc_info=True)
        return None

# Main function for the NOI Analyzer application
def main():
    """
    Main function for the NOI Analyzer Enhanced application.
    Sets up the UI and coordinates all functionality.
    """
    # Inject custom CSS to ensure font consistency
    inject_custom_css()
    
    # Load custom CSS
    inject_custom_css()
    
    # JavaScript function for theme toggling
    st.markdown("""
    <script>
    function toggleTheme() {
        const root = document.documentElement;
        const currentTheme = root.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        root.setAttribute('data-theme', newTheme);
        
        // Store theme preference in localStorage
        localStorage.setItem('preferred-theme', newTheme);
    }

    function initTheme() {
        const root = document.documentElement;
        const savedTheme = localStorage.getItem('preferred-theme') || 'dark';
        root.setAttribute('data-theme', savedTheme);
    }

    // Initialize theme on page load
    document.addEventListener('DOMContentLoaded', initTheme);
    
    // Also initialize if DOM is already ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Display logo at the very top of the app
    display_logo()
    
    # Log session state at the beginning of a run for debugging narrative
    logger.info(f"APP.PY (main start): st.session_state.generated_narrative is: {st.session_state.get('generated_narrative')}")
    logger.info(f"APP.PY (main start): st.session_state.edited_narrative is: {st.session_state.get('edited_narrative')}")
    
    # Display initial UI or results based on processing_completed
    if not st.session_state.get('processing_completed', False) and not st.session_state.get('template_viewed', False) and not st.session_state.get('consolidated_data'):
        # Show welcome content when no data has been processed and template is not active
        # Modern title with accent color
        st.markdown(
        '''
        <h1 class="noi-title">
            <span class="noi-title-accent">NOI</span> Analyzer
        </h1>
        '''
        , unsafe_allow_html=True)
        
        # Two-column layout for better space utilization
        col1, col2 = st.columns([1, 1.2])
        
        with col1:
            # Modern Upload Documents section
            st.markdown('<h2 class="section-header">Upload Documents</h2>', unsafe_allow_html=True)
            
            # Create modern file upload cards
            st.markdown('<div class="upload-container">', unsafe_allow_html=True)
            
            # Current Month Actuals (Required)
            st.markdown(
            '''
            <div class="upload-card">
                <div class="upload-card-header">Current Month Actuals <span class="required-badge">Required</span></div>
            '''
            , unsafe_allow_html=True)
            current_month_file_main = st.file_uploader(
                "Upload Current Month Actuals ",  # Added space for unique label component
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_current_month_upload_functional", # Unique key
                label_visibility="collapsed",
                help="Upload your current month's financial data here or in the sidebar"
            )
            if current_month_file_main is not None:
                st.session_state.current_month_actuals = current_month_file_main
            # Display file info regardless of where it was uploaded
            if st.session_state.get('current_month_actuals'):
                 show_file_info(st.session_state.current_month_actuals.name, 
                                file_size=f"{st.session_state.current_month_actuals.size / 1024:.1f}KB" if st.session_state.current_month_actuals.size else None,
                                file_type=st.session_state.current_month_actuals.type,
                                uploaded=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Prior Month Actuals
            st.markdown(
            '''
            <div class="upload-card">
                <div class="upload-card-header">Prior Month Actuals</div>
            '''
            , unsafe_allow_html=True)
            prior_month_file_main = st.file_uploader(
                "Upload Prior Month Actuals ", 
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_prior_month_upload_functional", 
                label_visibility="collapsed",
                help="Upload your prior month's financial data here or in the sidebar"
            )
            if prior_month_file_main is not None:
                st.session_state.prior_month_actuals = prior_month_file_main
            if st.session_state.get('prior_month_actuals'):
                show_file_info(st.session_state.prior_month_actuals.name,
                               file_size=f"{st.session_state.prior_month_actuals.size / 1024:.1f}KB" if st.session_state.prior_month_actuals.size else None,
                               file_type=st.session_state.prior_month_actuals.type,
                               uploaded=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Current Month Budget
            st.markdown(
            '''
            <div class="upload-card">
                <div class="upload-card-header">Current Month Budget</div>
            '''
            , unsafe_allow_html=True)
            budget_file_main = st.file_uploader(
                "Upload Current Month Budget ", 
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_budget_upload_functional", 
                label_visibility="collapsed",
                help="Upload your budget data here or in the sidebar"
            )
            if budget_file_main is not None:
                st.session_state.current_month_budget = budget_file_main
            if st.session_state.get('current_month_budget'):
                show_file_info(st.session_state.current_month_budget.name,
                               file_size=f"{st.session_state.current_month_budget.size / 1024:.1f}KB" if st.session_state.current_month_budget.size else None,
                               file_type=st.session_state.current_month_budget.type,
                               uploaded=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Prior Year Same Month
            st.markdown(
            '''
            <div class="upload-card">
                <div class="upload-card-header">Prior Year Same Month</div>
            '''
            , unsafe_allow_html=True)
            prior_year_file_main = st.file_uploader(
                "Upload Prior Year Same Month ", 
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_prior_year_upload_functional",
                label_visibility="collapsed",
                help="Upload the same month from prior year here or in the sidebar"
            )
            if prior_year_file_main is not None:
                st.session_state.prior_year_actuals = prior_year_file_main
            if st.session_state.get('prior_year_actuals'):
                show_file_info(st.session_state.prior_year_actuals.name,
                               file_size=f"{st.session_state.prior_year_actuals.size / 1024:.1f}KB" if st.session_state.prior_year_actuals.size else None,
                               file_type=st.session_state.prior_year_actuals.type,
                               uploaded=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Property name input with modern styling
            st.markdown('<div class="upload-card">', unsafe_allow_html=True)
            st.markdown('<div class="upload-card-header">Property Information</div>', unsafe_allow_html=True)
            # Property name input that updates session state
            main_page_property_name_input = st.text_input(
                "Property Name", # Clearer label
                value=st.session_state.property_name,
                help="Enter the name of the property being analyzed. Updates sidebar as well.",
                key="main_property_name_input" # Unique key for this input field
            )
            if main_page_property_name_input != st.session_state.property_name:
                st.session_state.property_name = main_page_property_name_input
                # No st.rerun() here is generally fine as other components 
                # should read the updated st.session_state.property_name in the next interaction.
                # If immediate update of a disabled field elsewhere is needed, a rerun might be considered.
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Add options container after file uploaders
            st.markdown('<div class="options-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="options-header">Display Options</h3>', unsafe_allow_html=True)

            # Create a row for the options
            options_col1, options_col2 = st.columns(2)

            # Show Zero Values toggle in first column
            with options_col1:
                show_zero_values = st.checkbox(
                    "Show Zero Values", 
                    value=st.session_state.show_zero_values,
                    help="Show metrics with zero values in the comparison tables"
                )
                
                if show_zero_values != st.session_state.show_zero_values:
                    st.session_state.show_zero_values = show_zero_values
                    st.rerun()

            # Theme toggle in second column
            with options_col2:
                current_theme = st.session_state.theme
                theme_button_text = "☀️ Light Mode" if current_theme == "dark" else "🌙 Dark Mode"
                
                # Create theme toggle button
                if st.button(theme_button_text, key="theme_toggle"):
                    # Toggle theme in session state
                    new_theme = "light" if current_theme == "dark" else "dark"
                    st.session_state.theme = new_theme
                    
                    # Apply theme change via JavaScript
                    st.markdown(f"""
                    <script>
                    const root = document.documentElement;
                    root.setAttribute('data-theme', '{new_theme}');
                    localStorage.setItem('preferred-theme', '{new_theme}');
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            
            # Main page 'Process Documents' button
            # This button's click also sets user_initiated_processing to True
            st.markdown(
            '''
            <style>
            /* Override button styling for process button */
            .stButton > button[kind="primary"] {
                background-color: #3B82F6 !important;
                color: white !important;
                font-size: 1.1rem !important;
                font-weight: 500 !important;
                padding: 0.75rem 1.5rem !important;
                border-radius: 8px !important;
                border: none !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
                transition: all 0.3s ease !important;
                margin-top: 1rem !important;
                margin-bottom: 1.5rem !important;
                width: 100% !important;
            }
            
            .stButton > button[kind="primary"]:hover {
                background-color: #2563EB !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
                transform: translateY(-2px) !important;
            }
            </style>
            '''
            , unsafe_allow_html=True)
            
            if st.button(
                "Process Documents", 
                type="primary",
                use_container_width=True,
                help="Process the uploaded documents to generate NOI analysis",
                key="main_process_button"
            ):
                st.session_state.user_initiated_processing = True
                # Reset states for a fresh processing cycle
                st.session_state.template_viewed = False
                st.session_state.processing_completed = False
                if 'consolidated_data' in st.session_state: del st.session_state.consolidated_data
                if 'comparison_results' in st.session_state: del st.session_state.comparison_results
                if 'insights' in st.session_state: del st.session_state.insights
                if 'generated_narrative' in st.session_state: del st.session_state.generated_narrative
                if 'edited_narrative' in st.session_state: del st.session_state.edited_narrative
                logger.info("Main page 'Process Documents' clicked. Initiating processing cycle.")
                st.rerun() # Rerun to start the processing logic below

        with col2:
            # Enhanced Instructions section
            st.markdown(
            '''
            <div class="info-card">
                <h3 class="info-card-header">Instructions:</h3>
                <ol class="info-list">
                    <li>Upload your financial documents using the file uploaders in the sidebar</li>
                    <li>At minimum, upload a <span class="highlight">Current Month Actuals</span> file</li>
                    <li>For comparative analysis, upload additional files (Prior Month, Budget, Prior Year)</li>
                    <li>Click "<span class="highlight">Process Documents</span>" (here or in sidebar) to analyze the data</li>
                    <li>Review and edit extracted data in the template that appears</li>
                    <li>Confirm data to view the analysis results</li>
                    <li>Export your results as PDF or Excel using the export options</li>
                </ol>
                <p style="color: #e6edf3; font-style: italic; font-size: 0.9rem; background-color: rgba(59, 130, 246, 0.1); padding: 0.75rem; border-radius: 6px;">Note: Supported file formats include Excel (.xlsx, .xls), CSV, and PDF</p>
            </div>
            '''
            , unsafe_allow_html=True)
            
            # Enhanced Features section
            st.markdown("<h2 class='section-header'>Features</h2>", unsafe_allow_html=True)
            display_features_section_no_html() # Call the new function
    
    # --- Stage 1: Document Extraction (if user initiated processing and no data yet) ---
    if st.session_state.user_initiated_processing and 'consolidated_data' not in st.session_state:
        try:
            show_processing_status("Processing documents. This may take a minute...", is_running=True)
            logger.info("APP.PY: --- User Initiated Document Processing START ---")

            # Ensure current_month_file is from session state, as button click clears local vars
            if not st.session_state.current_month_actuals:
                show_processing_status("Current Month Actuals file is required. Please upload it to proceed.", status_type="error")
                st.session_state.user_initiated_processing = False # Reset flag as processing cannot continue
                st.rerun() # Rerun to show the error and stop
                return # Explicitly return

            # Pass file objects from session state to process_all_documents
            # process_all_documents internally uses st.session_state to get file objects
            raw_consolidated_data = process_all_documents()
            logger.info(f"APP.PY: raw_consolidated_data received. Type: {type(raw_consolidated_data)}. Keys: {list(raw_consolidated_data.keys()) if isinstance(raw_consolidated_data, dict) else 'Not a dict'}. Has error: {raw_consolidated_data.get('error') if isinstance(raw_consolidated_data, dict) else 'N/A'}")

            if isinstance(raw_consolidated_data, dict) and "error" not in raw_consolidated_data and raw_consolidated_data:
                st.session_state.consolidated_data = raw_consolidated_data
                st.session_state.template_viewed = False # Ensure template is shown
                logger.info("Document extraction successful. Data stored. Proceeding to template display.")
            elif isinstance(raw_consolidated_data, dict) and "error" in raw_consolidated_data:
                error_message = raw_consolidated_data["error"]
                logger.error(f"Error during document processing: {error_message}")
                st.error(f"An error occurred during document processing: {error_message}")
                st.session_state.user_initiated_processing = False # Reset flag
            elif not raw_consolidated_data:
                logger.warning("No data was extracted from the documents or data is empty.")
                st.warning("No data was extracted from the documents or the extracted data is empty. Please check the files or try again.")
                st.session_state.user_initiated_processing = False # Reset flag
            else:
                logger.error(f"Unknown error or invalid data structure after document processing. Data: {raw_consolidated_data}")
                st.error("An unknown error occurred or the data structure is invalid after processing.")
                st.session_state.user_initiated_processing = False # Reset flag
            
            st.rerun() # Rerun to move to template display or show error

        except Exception as e_extract:
            logger.error(f"Exception during document extraction stage: {str(e_extract)}", exc_info=True)
            st.error(f"An unexpected error occurred during document extraction: {str(e_extract)}")
            st.session_state.user_initiated_processing = False # Reset flag
            st.rerun()
        return # Stop further execution in this run, let rerun handle next step

    # --- Stage 2: Data Template Display and Confirmation ---
    # This block executes if consolidated_data exists but template hasn't been viewed/confirmed
    if 'consolidated_data' in st.session_state and \
       st.session_state.consolidated_data and \
       not st.session_state.get('template_viewed', False) and \
       not st.session_state.get('processing_completed', False): # Ensure analysis hasn't already run
        
        logger.info("Displaying data template for user review.")
        show_processing_status("Documents processed. Please review the extracted data.", status_type="info")
        
        # Ensure consolidated_data is not an error message from a previous step
        if isinstance(st.session_state.consolidated_data, dict) and "error" not in st.session_state.consolidated_data:
            verified_data = display_data_template(st.session_state.consolidated_data)
            
            if verified_data is not None:
                st.session_state.consolidated_data = verified_data # Update with (potentially) edited data
                st.session_state.template_viewed = True
                st.session_state.user_initiated_processing = False # Reset, as next step is auto analysis
                logger.info("Data confirmed by user via template. Proceeding to analysis preparation.")
                st.rerun() # Rerun to trigger analysis stage
            else:
                # Template is displayed, waiting for user confirmation. Nothing else to do in this run.
                logger.info("Data template is active. Waiting for user confirmation.")
        else:
            # If consolidated_data holds an error or is invalid, don't show template.
            # This case should ideally be caught earlier.
            logger.error("Attempted to display template with invalid consolidated_data.")
            st.error("Cannot display data template due to an issue with extracted data. Please try processing again.")
            # Clear problematic data and reset flags
            if 'consolidated_data' in st.session_state: del st.session_state.consolidated_data
            st.session_state.user_initiated_processing = False
            st.session_state.template_viewed = False
            st.rerun()
        return # Stop further execution in this run

    # --- Stage 3: Financial Analysis (if data confirmed and not yet processed) ---
    if st.session_state.get('template_viewed', False) and \
       not st.session_state.get('processing_completed', False) and \
       'consolidated_data' in st.session_state and \
       st.session_state.consolidated_data:

        logger.info("APP.PY: --- Financial Analysis START ---")
        show_processing_status("Processing verified data for analysis...", is_running=True)
        try:
            # Ensure consolidated_data is valid before analysis
            if not isinstance(st.session_state.consolidated_data, dict) or "error" in st.session_state.consolidated_data:
                logger.error("Analysis cannot proceed: consolidated_data is invalid or contains an error.")
                st.error("Analysis cannot proceed due to an issue with the prepared data. Please re-process documents.")
                # Reset states to allow user to restart
                st.session_state.processing_completed = False
                st.session_state.template_viewed = False
                st.session_state.user_initiated_processing = False
                if 'consolidated_data' in st.session_state: del st.session_state.consolidated_data
                st.rerun()
                return

            # Validate consolidated data structure before processing
            if not st.session_state.consolidated_data or not isinstance(st.session_state.consolidated_data, dict):
                logger.error("consolidated_data is missing or invalid")
                st.error("Error: Invalid data structure. Please try processing the documents again.")
                return
            
            # The data in st.session_state.consolidated_data is already formatted 
            # by process_single_document_core (via process_all_documents).
            # It's ready for calculate_noi_comparisons.
            consolidated_data_for_analysis = st.session_state.consolidated_data
            
            # Validate that consolidated_data_for_analysis (which is st.session_state.consolidated_data) is valid
            if not consolidated_data_for_analysis or not isinstance(consolidated_data_for_analysis, dict):
                logger.error("Formatted data for analysis is invalid or not a dict (expected from session state)")
                st.error("Error: Failed to prepare financial data for analysis. Please check your documents and try again.")
                return
            
            # Check that we have at least some valid financial data
            required_keys = ['current_month', 'prior_month', 'budget', 'prior_year']
            available_keys = [key for key in required_keys if key in consolidated_data_for_analysis and consolidated_data_for_analysis[key]]
            logger.info(f"Available data types for analysis: {available_keys}")
            
            if not available_keys:
                # If 'current_month_actuals' (or similar raw key) exists and is non-empty, it implies a formatting or key mapping issue.
                # However, process_all_documents should already map to 'current_month', etc.
                # This check primarily ensures that at least one period has data.
                raw_current_key_exists = any(k in consolidated_data_for_analysis for k in ['current_month_actuals', 'current_month']) # Example check
                if raw_current_key_exists and consolidated_data_for_analysis.get(list(consolidated_data_for_analysis.keys())[0]): # if first key has data
                     logger.warning("Data seems to exist in consolidated_data_for_analysis but not with standard keys or is empty.")
                st.error("Error: No valid financial data found for key periods (current_month, prior_month, etc.). Please ensure your documents contain the required financial information.")
                return
            
            st.session_state.comparison_results = calculate_noi_comparisons(consolidated_data_for_analysis)
            
            if st.session_state.comparison_results and not st.session_state.comparison_results.get("error"):
                insights = generate_insights_with_gpt(st.session_state.comparison_results, get_openai_api_key())
                st.session_state.insights = {
                    "summary": insights.get("summary", "No summary available."),
                    "performance": insights.get("performance", []),
                    "recommendations": insights.get("recommendations", [])
                }
                narrative = create_narrative(st.session_state.comparison_results, st.session_state.property_name)
                st.session_state.generated_narrative = narrative
                st.session_state.edited_narrative = narrative # Initialize edited with generated

                st.session_state.processing_completed = True
                st.session_state.user_initiated_processing = False # Processing is done
                show_processing_status("Analysis complete!", status_type="success")
                logger.info("Financial analysis, insights, and narrative generated successfully.")
            else:
                error_msg = st.session_state.comparison_results.get("error", "Unknown error during analysis.") if st.session_state.comparison_results else "Comparison results are empty."
                logger.error(f"Error during financial analysis: {error_msg}")
                st.error(f"An error occurred during analysis: {error_msg}")
                st.session_state.processing_completed = False # Ensure it's marked as not completed
                # Don't delete consolidated_data here, user might want to re-run analysis if it was a transient issue
            
            st.rerun() # Rerun to display results or updated status
        except Exception as e_analysis:
            logger.error(f"Exception during financial analysis stage: {str(e_analysis)}", exc_info=True)
            st.error(f"An unexpected error occurred during analysis: {str(e_analysis)}")
            st.session_state.processing_completed = False
            st.rerun()
        return # Stop further execution

    # --- Stage 4: Display Results or Welcome Page ---
    if st.session_state.get('processing_completed', False):
        # Show results after processing is fully completed
        # Modern styled title
        st.markdown(f"""
        <h1 class="noi-title">
            <span class="noi-title-accent">NOI</span> Analysis Results
            {' - <span class="noi-title-property">' + st.session_state.property_name + '</span>' if st.session_state.property_name else ''}
        </h1>
        """, unsafe_allow_html=True)
        
        # Add styling for property name
        st.markdown("""
        <style>
        .noi-title-property {
            color: #e6edf3;
            font-weight: 400;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Get the comparison results from session state
        # The st.session_state.comparison_results should be populated by calculate_noi_comparisons
        # and is expected to have keys like 'month_vs_prior', 'actual_vs_budget', 'year_vs_year', 
        # and 'current', 'prior', 'budget', 'prior_year' for raw data.

        if not hasattr(st.session_state, 'comparison_results') or not st.session_state.comparison_results:
            st.error("Error: Comparison results are not available. Please try processing the documents again.")
            logger.error("st.session_state.comparison_results is missing or empty when trying to display tabs.")
            return

        comparison_data_for_tabs = st.session_state.comparison_results
        logger.info(f"Using comparison_results from session state for tabs. Top-level keys: {list(comparison_data_for_tabs.keys())}")
        try:
            # Use structure summary for INFO level instead of full structure
            logger.info(f"comparison_data_for_tabs summary: {len(comparison_data_for_tabs)} top-level keys, data types: {set(type(v).__name__ for v in comparison_data_for_tabs.values())}")
            # Full structure details moved to DEBUG level
            logger.debug(f"Full comparison_data_for_tabs structure: {json.dumps({k: list(v.keys()) if isinstance(v, dict) else type(v).__name__ for k, v in comparison_data_for_tabs.items()}, default=str, indent=2)}")
        except Exception as e:
            logger.error(f"Error logging comparison_data_for_tabs structure: {e}")

        # Create tabs for each comparison type with modern styling
        st.markdown("""
        <style>
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(16, 23, 42, 0.5) !important;
            border-radius: 10px 10px 0 0 !important;
            padding: 0.25rem 0.25rem 0 0.25rem !important;
            gap: 0 !important;
            border-bottom: none !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0 !important;
            padding: 0.75rem 1.25rem !important;
            margin: 0 0.125rem !important;
            background-color: rgba(16, 23, 42, 0.3) !important;
            border: none !important;
            color: rgba(230, 237, 243, 0.7) !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #3B82F6 !important;
            color: white !important;
        }
        
        .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
            background-color: rgba(16, 23, 42, 0.5) !important;
            color: #e6edf3 !important;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            background-color: rgba(16, 23, 42, 0.2) !important;
            border-radius: 0 0 10px 10px !important;
            padding: 1.5rem !important;
            border: 1px solid rgba(59, 130, 246, 0.1) !important;
            border-top: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        tabs = st.tabs(["Prior Month", "Budget", "Prior Year", "Summary", "NOI Coach"])
        
        with tabs[0]:
            st.header("Current Month vs. Prior Month")
            # Ensure 'month_vs_prior' data exists and is not empty
            month_vs_prior_data = comparison_data_for_tabs.get('month_vs_prior', {})
            if month_vs_prior_data:
                logger.info(f"APP.PY: Preparing to display Prior Month tab with data: {list(month_vs_prior_data.keys())}")
                try:
                    # Move full JSON dumps to DEBUG level
                    logger.debug(f"APP.PY: Full data for Prior Month tab: {json.dumps(month_vs_prior_data, default=str, indent=2)}")
                except Exception as e_log_json:
                    logger.error(f"APP.PY: Error logging JSON for Prior Month tab data: {e_log_json}")
                display_comparison_tab(month_vs_prior_data, "prior", "Prior Month")
            else:
                st.warning("Not enough data for Prior Month comparison.")
                logger.warning("APP.PY: 'month_vs_prior' data is missing or empty in comparison_data_for_tabs.")
                # Optionally, display current month summary if available
                current_data_summary = comparison_data_for_tabs.get('current', {})
                if current_data_summary:
                    st.write("Current Month Data Summary:")
                    current_summary_to_display = {k: v for k, v in current_data_summary.items() if v is not None and v != 0}
                    if current_summary_to_display:
                        st.json(current_summary_to_display)
                    else:
                        st.info("No current month data values to display.")
                
        with tabs[1]:
            st.header("Actual vs. Budget")
            # Ensure 'actual_vs_budget' data exists and is not empty
            actual_vs_budget_data = comparison_data_for_tabs.get('actual_vs_budget', {})
            if actual_vs_budget_data:
                logger.info(f"APP.PY: Preparing to display Budget tab with data: {list(actual_vs_budget_data.keys())}")
                try:
                    # Move full JSON dumps to DEBUG level
                    logger.debug(f"APP.PY: Full data for Budget tab: {json.dumps(actual_vs_budget_data, default=str, indent=2)}")
                except Exception as e_log_json:
                    logger.error(f"APP.PY: Error logging JSON for Budget tab data: {e_log_json}")
                display_comparison_tab(actual_vs_budget_data, "budget", "Budget")
            else:
                st.warning("Not enough data for Budget comparison.")
                logger.warning("APP.PY: 'actual_vs_budget' data is missing or empty in comparison_data_for_tabs.")

        with tabs[2]:
            st.header("Current Year vs. Prior Year")
            # Ensure 'year_vs_year' data exists and is not empty
            year_vs_year_data = comparison_data_for_tabs.get('year_vs_year', {})
            if year_vs_year_data:
                logger.info(f"APP.PY: Preparing to display Prior Year tab with data: {list(year_vs_year_data.keys())}")
                try:
                    # Move full JSON dumps to DEBUG level
                    logger.debug(f"APP.PY: Full data for Prior Year tab: {json.dumps(year_vs_year_data, default=str, indent=2)}")
                except Exception as e_log_json:
                    logger.error(f"APP.PY: Error logging JSON for Prior Year tab data: {e_log_json}")
                display_comparison_tab(year_vs_year_data, "prior_year", "Prior Year")
            else:
                st.warning("Not enough data for Prior Year comparison.")
                logger.warning("APP.PY: 'year_vs_year' data is missing or empty in comparison_data_for_tabs.")
        
        with tabs[3]: # Summary Tab (formerly Financial Narrative & Insights)
            st.header("Overall Summary & Insights")
            
            # Display the narrative text and editor
            display_narrative_in_tabs()
            
            # Display the consolidated insights (summary, performance, recommendations)
            if "insights" in st.session_state and st.session_state.insights:
                try:
                    display_unified_insights_no_html(st.session_state.insights)
                except Exception as e:
                    logger.error(f"Error displaying insights: {e}")
                    st.error("An error occurred while displaying insights. Please try processing documents again.")
            else:
                logger.info("No insights data found in session state for Financial Narrative & Insights tab.")
                st.info("Insights (including summary and recommendations) will be displayed here once generated.")

        # Display NOI Coach section
        with tabs[4]: # NOI Coach tab
            display_noi_coach()
    
    # Process documents when button is clicked
    if process_clicked:
        try:
            # Display enhanced status message instead of spinner
            show_processing_status("Processing documents. This may take a minute...", is_running=True)
            
            logger.info("APP.PY: --- Document Processing START ---")
            if not current_month_file_sb:
                show_processing_status("Current Month Actuals file is required. Please upload it to proceed.", status_type="error")
                st.session_state.processing_completed = False # Ensure it's false if we exit early
                return
                
            st.session_state.current_month_actuals = current_month_file_sb
            st.session_state.prior_month_actuals = prior_month_file_sb
            st.session_state.current_month_budget = budget_file_sb
            st.session_state.prior_year_actuals = prior_year_file_sb

            # Process the documents
            raw_consolidated_data = process_all_documents()
            logger.info(f"APP.PY: raw_consolidated_data received. Type: {type(raw_consolidated_data)}. Keys: {list(raw_consolidated_data.keys()) if isinstance(raw_consolidated_data, dict) else 'Not a dict'}. Has error: {raw_consolidated_data.get('error') if isinstance(raw_consolidated_data, dict) else 'N/A'}")
            
            # Log the details of raw_consolidated_data if available
            if isinstance(raw_consolidated_data, dict) and isinstance(raw_consolidated_data.get('current_month'), dict):
                try:
                    logger.info(f"APP.PY: Snippet of raw_consolidated_data['current_month']: {summarize_data_for_log(raw_consolidated_data['current_month'])}")
                    logger.debug(f"APP.PY: Full raw_consolidated_data['current_month']: {json.dumps(raw_consolidated_data['current_month'], default=str, indent=2)}")
                except Exception as e_log_snippet:
                    logger.error(f"APP.PY: Error logging raw_consolidated_data snippet: {e_log_snippet}")

            # Store raw consolidated data in session state
            st.session_state.consolidated_data = raw_consolidated_data
            
            # Check if we have valid data to display in the template
            if isinstance(raw_consolidated_data, dict) and "error" not in raw_consolidated_data and raw_consolidated_data: # Added check for non-empty dict
                show_processing_status("Documents processed. Please review the extracted data.", status_type="info")

                if 'template_viewed' not in st.session_state:
                    st.session_state.template_viewed = False
                
                if not st.session_state.template_viewed:
                    verified_data = display_data_template(raw_consolidated_data)
                    
                    if verified_data is not None:
                        st.session_state.consolidated_data = verified_data
                        st.session_state.template_viewed = True
                        # Analysis will be triggered in the next block if template_viewed is True
                        logger.info("Data confirmed by user. Proceeding to analysis preparation.")
                        st.rerun() # Rerun to proceed to analysis part
                    else:
                        logger.info("User has not confirmed data yet. Waiting for confirmation.")
                        return # Stop further execution until data is confirmed
                
                # This block will run if template_viewed is True (either just confirmed or previously confirmed)
                if st.session_state.template_viewed:
                    show_processing_status("Processing verified data...", is_running=True)
                    logger.info("Proceeding with analysis using verified/previously verified data.")
                    
                    try:
                        # Validate consolidated data before processing
                        if not st.session_state.consolidated_data or not isinstance(st.session_state.consolidated_data, dict):
                            logger.error("consolidated_data is missing or invalid for verified data processing")
                            st.error("Error: Invalid data structure. Please try processing the documents again.")
                            st.session_state.processing_completed = False
                            st.rerun()
                            return
                        
                        # Perform financial analysis with verified data
                        # The data in st.session_state.consolidated_data is already formatted.
                        consolidated_data_for_analysis = st.session_state.consolidated_data
                        
                        # Validate that consolidated_data_for_analysis is valid
                        if not consolidated_data_for_analysis or not isinstance(consolidated_data_for_analysis, dict):
                            logger.error("Formatted data for analysis is invalid or not a dict (expected from session state)")
                            st.error("Error: Failed to format financial data for analysis. Please check your documents and try again.")
                            st.session_state.processing_completed = False
                            st.rerun()
                            return
                        
                        # Check that we have at least some valid financial data
                        required_keys = ['current_month', 'prior_month', 'budget', 'prior_year']
                        available_keys = [key for key in required_keys if key in consolidated_data_for_analysis and consolidated_data_for_analysis[key]]
                        logger.info(f"Available data types for verified analysis: {available_keys}")
                        
                        if not available_keys:
                            logger.error("No valid financial data found after formatting for verified data")
                            st.error("Error: No valid financial data found. Please ensure your documents contain the required financial information.")
                            st.session_state.processing_completed = False
                            st.rerun()
                            return
                        
                        st.session_state.comparison_results = calculate_noi_comparisons(consolidated_data_for_analysis)
                        
                        if not st.session_state.comparison_results.get("error"):
                            insights = generate_insights_with_gpt(st.session_state.comparison_results, get_openai_api_key())
                            st.session_state.insights = {
                                "summary": insights.get("summary", "No summary available."),
                                "performance": insights.get("performance", []),
                                "recommendations": insights.get("recommendations", [])
                            }
                            narrative = create_narrative(st.session_state.comparison_results, st.session_state.property_name)
                            st.session_state.generated_narrative = narrative
                            st.session_state.edited_narrative = narrative # Initialize edited with generated

                            st.session_state.processing_completed = True
                            show_processing_status("Analysis complete!", status_type="success")
                            logger.info("Financial analysis, insights, and narrative generated successfully.")
                        else:
                            error_msg = st.session_state.comparison_results.get("error", "Unknown error during analysis.")
                            logger.error(f"Error during financial analysis: {error_msg}")
                            st.error(f"An error occurred during analysis: {error_msg}")
                            st.session_state.processing_completed = False
                            
                    except Exception as e_analysis:
                        logger.error(f"Exception during financial analysis: {str(e_analysis)}", exc_info=True)
                        st.error(f"An unexpected error occurred during analysis: {str(e_analysis)}")
                        st.session_state.processing_completed = False
                    
                    st.rerun() # Rerun to display results or updated status

            elif isinstance(raw_consolidated_data, dict) and "error" in raw_consolidated_data:
                error_message = raw_consolidated_data["error"]
                logger.error(f"Error during document processing: {error_message}")
                st.error(f"An error occurred during document processing: {error_message}")
                st.session_state.error_message = error_message
                st.session_state.processing_completed = False
            elif not raw_consolidated_data : # Handles empty dict or None
                logger.warning("No data was extracted from the documents or data is empty.")
                st.warning("No data was extracted from the documents or the extracted data is empty. Please check the files or try again.")
                st.session_state.error_message = "No data extracted or data is empty."
                st.session_state.processing_completed = False
            else: # Catch any other unexpected raw_consolidated_data states
                logger.error(f"Unknown error or invalid data structure after document processing. Data: {raw_consolidated_data}")
                st.error("An unknown error occurred or the data structure is invalid after processing.")
                st.session_state.error_message = "Unknown processing error."
                st.session_state.processing_completed = False
            
            logger.info(f"APP.PY: --- Document Processing END --- processing_completed: {st.session_state.processing_completed}")
            # Force rerun to refresh UI
            st.rerun()
        except Exception as e:
            # Main exception handler for the entire process_clicked block
            logger.error(f"Error processing documents: {e}", exc_info=True)
            show_processing_status(f"Error: {str(e)}", status_type="error")
            st.session_state.processing_completed = False

    # Add this code in the main UI section after displaying all tabs
    # (after the st.tabs() section in the main function)
    if st.session_state.processing_completed:
        # Add a separator
        st.markdown("---")

        # Add export options in a container at the bottom with modern styling
        st.markdown("""
        <div class="export-container">
            <h2 class="export-title">Export Options</h2>
            <div class="export-description">Download your analysis as PDF or Excel for sharing and reporting.</div>
        </div>
        
        <style>
        .export-container {
            margin-bottom: 1.5rem;
        }
        
        .export-title {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1.75rem;
            font-weight: 500;
            color: #3B82F6;
            margin-bottom: 0.5rem;
        }
        
        .export-description {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1rem;
            color: #e6edf3;
            margin-bottom: 1.5rem;
        }
        
        /* Export button styling */
        .export-button {
            background-color: rgba(16, 23, 42, 0.7) !important;
            border: 1px solid rgba(59, 130, 246, 0.3) !important;
            border-radius: 8px !important;
            padding: 1.5rem !important;
            transition: all 0.3s ease !important;
            margin-bottom: 1rem !important;
        }
        
        .export-button:hover {
            background-color: rgba(16, 23, 42, 0.9) !important;
            border-color: rgba(59, 130, 246, 0.5) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # PDF Export button with modern styling
            st.markdown('<div class="export-button">', unsafe_allow_html=True)
            if st.button("Generate Complete PDF Report", key="global_pdf_export"):
                # Use our custom status indicator instead of spinner
                show_processing_status("Generating comprehensive PDF report...", is_running=True)
                try:
                    pdf_bytes = generate_comprehensive_pdf() 
                    
                    if pdf_bytes:
                        # Create a unique filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        property_part = st.session_state.property_name.replace(" ", "_") if hasattr(st.session_state, 'property_name') and st.session_state.property_name else "Property"
                        pdf_filename = f"NOI_Analysis_{property_part}_{timestamp}.pdf"
                        
                        # Display download button
                        st.download_button(
                            label="Download Complete PDF Report",
                            data=pdf_bytes,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            key=f"download_comprehensive_pdf_{timestamp}"  # Ensure unique key
                        )
                        # Show success message
                        show_processing_status("PDF report generated successfully!", status_type="success")
                    else:
                        # Show error message
                        show_processing_status("Failed to generate PDF report. Please check the logs for details.", status_type="error")
                except Exception as e:
                    logger.error(f"Error in PDF generation process: {str(e)}", exc_info=True)
                    # Show error message
                    show_processing_status(f"Error generating PDF report: {str(e)}", status_type="error")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Excel Export button (if implemented) with modern styling
            st.markdown('<div class="export-button">', unsafe_allow_html=True)
            if st.button("Export to Excel", key="global_excel_export"):
                # Use our custom status indicator
                show_processing_status("Generating Excel export...", is_running=True)
                # Excel export logic here
                show_processing_status("Excel export functionality coming soon!", status_type="info")
            st.markdown('</div>', unsafe_allow_html=True)

def display_features_section():
    """Display the features section using pure Streamlit components without HTML"""
    st.markdown("## Features")
    
    # Feature 1: Comparative Analysis
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown("**1**")
        with col2:
            st.markdown("### Comparative Analysis")
            st.markdown("Compare current performance against budget, prior month, and prior year")
    
    st.markdown("---")
    
    # Feature 2: Financial Insights
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown("**2**")
        with col2:
            st.markdown("### Financial Insights")
            st.markdown("AI-generated analysis of key metrics and trends")
    
    st.markdown("---")
    
    # Feature 3: NOI Coach
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown("**3**")
        with col2:
            st.markdown("### NOI Coach")
            st.markdown("Ask questions about your financial data and get AI-powered insights")
    
    st.markdown("---")
    
    # Feature 4: Export Options
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown("**4**")
        with col2:
            st.markdown("### Export Options")
            st.markdown("Save results as PDF or Excel for sharing and reporting")

def display_features_section_enhanced():
    """Display the features section using pure Streamlit components with enhanced styling"""
    st.markdown("## Features")
    
    # Custom CSS for the number circles - minimal and safe
    st.markdown("""
    <style>
    .number-circle {
        background-color: rgba(59, 130, 246, 0.2);
        color: #79b8f3;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 20px;
        margin: 10px auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Feature 1: Comparative Analysis
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown('<div class="number-circle">1</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("### Comparative Analysis")
            st.markdown("Compare current performance against budget, prior month, and prior year")
    
    st.markdown("---")
    
    # Feature 2: Financial Insights
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown('<div class="number-circle">2</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("### Financial Insights")
            st.markdown("AI-generated analysis of key metrics and trends")
    
    st.markdown("---")
    
    # Feature 3: NOI Coach
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown('<div class="number-circle">3</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("### NOI Coach")
            st.markdown("Ask questions about your financial data and get AI-powered insights")
    
    st.markdown("---")
    
    # Feature 4: Export Options
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown('<div class="number-circle">4</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("### Export Options")
            st.markdown("Save results as PDF or Excel for sharing and reporting")

def display_features_section_no_html():
    """Display the features section using pure Streamlit components with NO HTML at all"""
    st.markdown("## Features")
    
    # Feature 1: Comparative Analysis
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            # Use emoji or text for the number
            st.markdown("🔵")
            st.markdown("1")
        with col2:
            st.markdown("### Comparative Analysis")
            st.markdown("Compare current performance against budget, prior month, and prior year")
    
    st.markdown("---")
    
    # Feature 2: Financial Insights
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown("🔵")
            st.markdown("2")
        with col2:
            st.markdown("### Financial Insights")
            st.markdown("AI-generated analysis of key metrics and trends")
    
    st.markdown("---")
    
    # Feature 3: NOI Coach
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown("🔵")
            st.markdown("3")
        with col2:
            st.markdown("### NOI Coach")
            st.markdown("Ask questions about your financial data and get AI-powered insights")
    
    st.markdown("---")
    
    # Feature 4: Export Options
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            st.markdown("🔵")
            st.markdown("4")
        with col2:
            st.markdown("### Export Options")
            st.markdown("Save results as PDF or Excel for sharing and reporting")

def display_unified_insights(insights_data):
    """
    Display unified insights using native Streamlit components.
    
    Args:
        insights_data: Dictionary containing 'summary', 'performance', and 'recommendations' keys
    """
    logger.info("Displaying unified insights")
    
    if not insights_data or not isinstance(insights_data, dict):
        st.warning("No insights data available to display.")
        return
    
    logger.info(f"Insights data keys: {list(insights_data.keys())}")
    
    # Display Executive Summary
    if 'summary' in insights_data:
        st.markdown("## Executive Summary")
        
        summary_text = insights_data['summary']
        # Remove redundant "Executive Summary:" prefix if it exists
        if summary_text.startswith("Executive Summary:"):
            summary_text = summary_text[len("Executive Summary:")          :].strip()
            
        with st.container():
            st.markdown(f"{summary_text}")
    
    # Display Key Performance Insights
    if 'performance' in insights_data and insights_data['performance']:
        st.markdown("## Key Performance Insights")
        
        for insight in insights_data['performance']:
            with st.container():
                col1, col2 = st.columns([1, 20])
                with col1:
                    st.markdown("•")
                with col2:
                    st.markdown(insight)
    
    # Display Recommendations
    if 'recommendations' in insights_data and insights_data['recommendations']:
        st.markdown("## Recommendations")
        
        for recommendation in insights_data['recommendations']:
            with st.container():
                col1, col2 = st.columns([1, 20])
                with col1:
                    st.markdown("•")
                with col2:
                    st.markdown(recommendation)

def display_opex_breakdown(opex_components, comparison_type):
    """
    Display Operating Expenses breakdown using native Streamlit components.
    
    Args:
        opex_components: Dictionary of OpEx components
        comparison_type: Type of comparison (budget, prior_month, prior_year)
    """
    if not opex_components or not isinstance(opex_components, dict) or len(opex_components) == 0:
        st.info("No detailed Operating Expenses breakdown available.")
        return
    
    st.markdown("### Operating Expenses Breakdown")
    
    # Create a container for the OpEx breakdown
    with st.container():
        # Header row
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            st.markdown("**Expense Category**")
        with col2:
            st.markdown("**Current**")
        with col3:
            st.markdown(f"**{comparison_type.title()}**")
        with col4:
            st.markdown("**Variance**")
        
        # Add a separator
        st.markdown("---")
        
        # Display each OpEx component
        for category, values in opex_components.items():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            # Format the category name for display
            display_name = category.replace('_', ' ').title()
            
            # Get values with defaults
            current_value = values.get('current', 0)
            compare_value = values.get('compare', 0)
            variance = current_value - compare_value
            
            # Display the row
            with col1:
                st.markdown(f"**{display_name}**")
            with col2:
                st.markdown(f"${current_value:,.2f}")
            with col3:
                st.markdown(f"${compare_value:,.2f}")
            with col4:
                # Color-code the variance
                color = "#22C55E" if variance < 0 else "#EF4444"  # Green if expense decreased, red if increased
                st.markdown(f"<span style='color:{color}'>${variance:,.2f}</span>", unsafe_allow_html=True)
            
            # Add a light separator between rows
            st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)

def display_card_container(title, content):
    """
    Display content in a consistently styled card container.
    
    Args:
        title: Card title
        content: Function to render card content
    """
    st.markdown(f"### {title}")
    
    with st.container():
        # Create a visual container with styling
        st.markdown("""        <div style="background-color: rgba(22, 27, 34, 0.8); 
                    border: 1px solid rgba(56, 68, 77, 0.5); 
                    border-radius: 8px; 
                    padding: 16px; 
                    margin-bottom: 20px;">
        </div>
        """, unsafe_allow_html=True)
        
        # This is a trick - we're creating an empty styled container above,
        # then putting the actual content below it in a Streamlit container
        content()

# Run the main function when the script is executed directly
if __name__ == "__main__":
    main()

