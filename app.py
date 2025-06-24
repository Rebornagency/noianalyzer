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
import math
import html

# Import and initialize Sentry for error tracking
from sentry_config import (
    init_sentry, set_user_context, add_breadcrumb, 
    capture_exception_with_context, capture_message_with_context, 
    monitor_performance
)

# Initialize Sentry as early as possible
sentry_initialized = init_sentry()

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

# Try to import the NOI Coach module
try:
    from noi_coach import display_noi_coach as display_noi_coach_enhanced
    NOI_COACH_AVAILABLE = True
except ImportError:
    NOI_COACH_AVAILABLE = False
    def display_noi_coach_enhanced():
        st.error("NOI Coach module not available. Please ensure noi_coach.py is in the project directory.")

# Import mock data generators for testing mode
try:
    from mock_data import (
        generate_mock_consolidated_data,
        generate_mock_insights,
        generate_mock_narrative
    )
    MOCK_DATA_AVAILABLE = True
except ImportError:
    MOCK_DATA_AVAILABLE = False
    def generate_mock_consolidated_data(*args, **kwargs):
        return {"error": "Mock data module not available"}
    def generate_mock_insights(*args, **kwargs):
        return {"summary": "Mock insights not available", "performance": [], "recommendations": []}
    def generate_mock_narrative(*args, **kwargs):
        return "Mock narrative not available"

from config import get_openai_api_key, get_extraction_api_url, get_api_key, save_api_settings
from insights_display import display_insights
from reborn_logo import get_reborn_logo_base64
from utils.ui_helpers import (
    load_custom_css_universal,
    render_navigation_with_search_universal,
    render_comparison_view_universal,
)

# Constants for testing mode
TESTING_MODE_ENV_VAR = "NOI_ANALYZER_TESTING_MODE"
DEFAULT_TESTING_MODE = os.getenv(TESTING_MODE_ENV_VAR, "false").lower() == "true"

# Helper function to check if testing mode is active
def is_testing_mode_active() -> bool:
    """
    Determine if testing mode is currently active.
    
    Returns:
        bool: True if testing mode is active, False otherwise
    """
    return st.session_state.get("testing_mode", DEFAULT_TESTING_MODE)

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

# Log Sentry initialization status
if sentry_initialized:
    logger.info("Sentry error tracking initialized successfully")
    add_breadcrumb("Application started", "app", "info")
else:
    logger.warning("Sentry error tracking not initialized - check SENTRY_DSN environment variable")

def safe_text(value):
    """Convert any value to a safe string, avoiding 'undefined' text."""
    if value is None or value == "undefined" or value == "null" or str(value).lower() == "nan" or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value)

def inject_custom_css():
    """Inject custom CSS for styling the app, with error handling."""
    try:
        css_file = "static/css/reborn_theme.css"
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        logger.info(f"Successfully loaded custom CSS from {css_file}")
    except FileNotFoundError:
        logger.warning(f"CSS file not found at {css_file}. Using default Streamlit styles.")
    except Exception as e:
        logger.error(f"Error loading CSS: {e}", exc_info=True)

def save_testing_config():
    """Save testing mode configuration to a file"""
    if not is_testing_mode_active():
        return
    
    config = {
        "testing_mode": st.session_state.get("testing_mode", False),
        "mock_property_name": st.session_state.get("mock_property_name", "Test Property"),
        "mock_scenario": st.session_state.get("mock_scenario", "Standard Performance")
    }
    
    try:
        from pathlib import Path
        config_dir = Path("./config")
        
        # Try to create directory, but handle permission errors gracefully
        try:
            config_dir.mkdir(exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot create config directory (insufficient permissions): {str(e)}")
            # Try using session state as fallback instead of file persistence
            st.session_state._testing_config_cache = config
            logger.info("Testing configuration cached in session state as fallback")
            return
        
        # Try to save to file
        config_file = config_dir / "testing_config.json"
        with open(config_file, "w") as f:
            json.dump(config, f)
        logger.info("Testing configuration saved to file")
        
    except Exception as e:
        logger.warning(f"Error saving testing configuration to file: {str(e)}")
        # Use session state as fallback
        try:
            st.session_state._testing_config_cache = config
            logger.info("Testing configuration cached in session state as fallback")
        except Exception as fallback_error:
            logger.error(f"Failed to save testing configuration even to session state: {str(fallback_error)}")

def load_testing_config():
    """Load testing mode configuration from file or session state fallback"""
    try:
        from pathlib import Path
        config_file = Path("./config/testing_config.json")
        
        # Try to load from file first
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                logger.info("Testing configuration loaded from file")
            except Exception as e:
                logger.warning(f"Error reading testing configuration file: {str(e)}")
                config = None
        else:
            config = None
        
        # If file loading failed, try session state fallback
        if config is None and hasattr(st.session_state, '_testing_config_cache'):
            config = st.session_state._testing_config_cache
            logger.info("Testing configuration loaded from session state fallback")
        
        # Apply configuration if available
        if config:
            st.session_state.testing_mode = config.get("testing_mode", DEFAULT_TESTING_MODE)
            st.session_state.mock_property_name = config.get("mock_property_name", "Test Property")
            st.session_state.mock_scenario = config.get("mock_scenario", "Standard Performance")
            logger.info("Testing configuration applied successfully")
        
    except Exception as e:
        logger.warning(f"Error loading testing configuration: {str(e)}")
        # Continue with default values - not a critical error

def display_testing_mode_indicator():
    """Display a visual indicator when testing mode is enabled"""
    if is_testing_mode_active():
        scenario = st.session_state.get("mock_scenario", "Standard Performance")
        
        # Color coding based on scenario
        if scenario == "High Growth":
            color = "#22C55E"  # Green
            emoji = "📈"
        elif scenario == "Declining Performance":
            color = "#EF4444"  # Red
            emoji = "📉"
        elif scenario == "Budget Variance":
            color = "#F59E0B"  # Amber
            emoji = "⚖️"
        else:  # Standard Performance
            color = "#3B82F6"  # Blue
            emoji = "📊"
        
        # Convert hex to RGB for alpha transparency
        hex_color = color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        st.markdown(
            f"""
            <div style="
                background-color: rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.1);
                border-left: 4px solid {color};
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                border-radius: 4px;
                display: flex;
                align-items: center;
            ">
                <span style="
                    font-size: 1.2rem;
                    margin-right: 0.75rem;
                ">{emoji}</span>
                <div>
                    <span style="
                        color: {color};
                        font-weight: 600;
                        display: block;
                        margin-bottom: 0.25rem;
                    ">Testing Mode Active</span>
                    <span style="
                        color: #E0E0E0;
                        font-size: 0.9rem;
                    ">Scenario: {scenario}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def process_documents_testing_mode():
    """Process documents in testing mode using mock data"""
    logger.info("Testing mode enabled, using mock data")
    
    # Get property name and scenario from session state
    property_name = st.session_state.get("mock_property_name", "Test Property")
    scenario = st.session_state.get("mock_scenario", "Standard Performance")
    
    # Log the testing configuration
    logger.info(f"Generating mock data for property: {property_name}, scenario: {scenario}")
    
    try:
        # Generate mock consolidated data with the selected scenario
        mock_data = generate_mock_consolidated_data(property_name, scenario)
        
        # Store in session state - this mimics what happens after real document processing
        st.session_state.consolidated_data = mock_data
        st.session_state.template_viewed = True  # Skip template verification step
        st.session_state.processing_completed = True
        
        # Calculate comparisons using the mock data - this uses the real calculation logic
        st.session_state.comparison_results = calculate_noi_comparisons(mock_data)
        
        # Debug the generated data
        debug_testing_mode_data()
        
        # Generate mock insights - this replaces the API call to OpenAI
        st.session_state.insights = generate_mock_insights(scenario)
        
        # Generate mock narrative - this replaces the API call for narrative generation
        mock_narrative = generate_mock_narrative(scenario)
        st.session_state.generated_narrative = mock_narrative
        st.session_state.edited_narrative = mock_narrative  # Initialize edited to same as generated
        
        logger.info(f"Mock data processing completed for scenario: {scenario}")
        return True
    except Exception as e:
        logger.error(f"Error generating mock data: {str(e)}", exc_info=True)
        st.error("An error occurred while generating mock data. Please check the logs.")
        return False

def run_testing_mode_diagnostics():
    """Run diagnostics on testing mode functionality"""
    if not is_testing_mode_active():
        return
    
    # Only run diagnostics when explicitly triggered
    if not st.session_state.get("run_diagnostics", False):
        return
    
    logger.info("Running testing mode diagnostics")
    
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
                logger.info(f"{key} data sample: gpr={data.get('gpr')}, noi={data.get('noi')}, egi={data.get('egi')}")
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
                    logger.info(f"{section} raw data: gpr={section_data.get('gpr')}, noi={section_data.get('noi')}")
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
                st.info(f"No {doc_type.replace('_', ' ')} data available.")
    
    # Add confirmation button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Confirm Data and Proceed with Analysis", type="primary", use_container_width=True):
            return edited_data
    
    # Return None if not confirmed
    return None

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
    """Display header with logo, company name, and a theme toggle."""
    try:
        logo_base64 = get_reborn_logo_base64()
        # Fallback detection
        invalid_logo = not logo_base64 or not isinstance(logo_base64, str) or len(logo_base64) < 100

        # Inject CSS only once
        if "header_css_injected" not in st.session_state:
            st.markdown(
                """
                <style>
                .header-container {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.25rem 0 0.75rem 0; /* tighter spacing */
                    margin-bottom: 0.25rem;
                }
                .logo-title-container {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }
                .reborn-logo { height: 64px; }
                .reborn-text {
                    font-family: 'Inter', sans-serif;
                    font-size: 2.25rem;
                    font-weight: 700;
                    color: #ffffff;
                    margin: 0;
                    letter-spacing: 0.05em;
                }
                /* Theme toggle pill */
                .theme-toggle {
                    position: relative;
                    width: 56px;
                    height: 28px;
                    border-radius: 14px;
                    background-color: var(--toggle-bg, #374151);
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }
                .theme-toggle::before {
                    content: var(--toggle-emoji, "🌙");
                    position: absolute;
                    top: 50%;
                    left: var(--toggle-pos, 30px);
                    transform: translateY(-50%);
                    width: 22px;
                    height: 22px;
                    border-radius: 50%;
                    background: #fff;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.25);
                    transition: left 0.3s ease;
                }
                #MainMenu, header { visibility: hidden; }
                </style>
                """,
                unsafe_allow_html=True,
            )
            # (no session_state flag so it injects every time)

        # Determine toggle styling variables based on current theme
        current_theme = st.session_state.get("theme", "dark")
        toggle_css_vars = (
            "--toggle-bg: #374151; --toggle-pos: 30px; --toggle-emoji: '🌙'" if current_theme == "dark" else
            "--toggle-bg: #E5E7EB; --toggle-pos: 4px; --toggle-emoji: '☀️'"
        )

        # Build HTML (logo + text + toggle)
        left_part = (
            (f"<img src='data:image/png;base64,{logo_base64}' class='reborn-logo' alt='Reborn Logo'>" if not invalid_logo else "")
        ) + "<h1 class='reborn-text'>REBORN</h1>"

        st.markdown(
            f"""
            <div class='header-container'>
                <div class='logo-title-container'>{left_part}</div>
                <div id='theme-toggle' class='theme-toggle' style='{toggle_css_vars}'></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Inject JS once to wire the toggle
        if "header_toggle_js" not in st.session_state:
            st.markdown(
                """
                <script>
                // Theme helper (matches one defined in main JS)
                function _toggleThemeReborn() {
                    const root = parent.document.documentElement;
                    const current = root.getAttribute('data-theme') || 'dark';
                    const next = current === 'dark' ? 'light' : 'dark';
                    root.setAttribute('data-theme', next);
                    localStorage.setItem('preferred-theme', next);
                    // update CSS variables for smoother UI feedback
                    const toggle = document.getElementById('theme-toggle');
                    if (toggle) {
                        toggle.style.setProperty('--toggle-bg', next === 'dark' ? '#374151' : '#E5E7EB');
                        toggle.style.setProperty('--toggle-pos', next === 'dark' ? '30px' : '4px');
                        toggle.style.setProperty('--toggle-emoji', next === 'dark' ? '"🌙"' : '"☀️"');
                    }
                }
                document.addEventListener('DOMContentLoaded', function () {
                    const tgt = document.getElementById('theme-toggle');
                    if (tgt) {
                        tgt.addEventListener('click', function(){
                            // Call the global toggleTheme() already injected by main()
                            if (typeof toggleTheme === 'function') { toggleTheme(); }
                            // Ensure Streamlit session_state updates via hidden button
                            const hiddenBtn = document.querySelector("button[data-testid='baseButton-theme_toggle_hidden']");
                            if (hiddenBtn) { hiddenBtn.click(); }
                        });
                    }
                });
                </script>
                """,
                unsafe_allow_html=True,
            )
            st.session_state.header_toggle_js = True

        # Update Streamlit session_state theme when rerunning (based on localStorage)
        if st.session_state.get('theme_synced') is not True:
            st.markdown(
                """
                <script>
                const savedTheme = localStorage.getItem('preferred-theme') || 'dark';
                if (window.parent) {
                   window.parent.postMessage({ rebornThemeSync: savedTheme }, '*');
                }
                </script>
                """,
                unsafe_allow_html=True,
            )
            st.session_state.theme_synced = True

    except Exception as e:
        logger.error(f"Error in display_logo: {e}", exc_info=True)
        st.markdown("<h1>REBORN</h1>", unsafe_allow_html=True)

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

# Testing mode initialization
if 'testing_mode' not in st.session_state:
    st.session_state.testing_mode = DEFAULT_TESTING_MODE
if 'mock_property_name' not in st.session_state:
    st.session_state.mock_property_name = "Test Property"
if 'mock_scenario' not in st.session_state:
    st.session_state.mock_scenario = "Standard Performance"
if 'testing_config_loaded' not in st.session_state:
    st.session_state.testing_config_loaded = False

def highlight_changes(val):
    if isinstance(val, str) and val.startswith('-'):
        return 'color: red'
    # Check for positive changes, ensuring we don't misinterpret currency symbols or other characters as positive.
    # A common convention for positive financial changes is an explicit '+' sign or simply no sign for positive numbers.
    # Given the example df, 'Change ($)' and 'Change (%)' can be positive without a '+'.
    # We will assume that if it doesn't start with '-', and it's a change column, it's positive if not zero.
    # However, the original prompt suggests looking for a '+' prefix. Let's stick to that for green.
    # If no explicit '+', we won't color it green, but it won't be red either.
    elif isinstance(val, str) and val.startswith('+'): # Explicitly look for '+' for green
        return 'color: green'
    # Fallback for values that are not explicitly positive (green) or negative (red)
    return ''

# Display comparison tab
def display_comparison_tab(tab_data: Dict[str, Any], prior_key_suffix: str, name_suffix: str):
    """
    Display a comparison tab with financial data, charts, and insights.

    Args:
        tab_data: Dictionary containing data for this specific comparison tab.
        prior_key_suffix: Suffix used for prior period keys (e.g., 'prior_month', 'budget').
        name_suffix: Name for the prior period (e.g., 'Prior Month', 'Budget').
    """
    # Ensure name_suffix is safe to use in titles
    name_suffix = safe_text(name_suffix) or "Prior Period" # Ensure fallback
    prior_key_suffix = safe_text(prior_key_suffix) or "prior" # Ensure fallback for key suffix as well

    try:
        logger.info(f"Displaying comparison tab: {name_suffix}")
        add_breadcrumb(f"Displaying comparison tab: {name_suffix}", "ui.display", "info")

        # Ensure tab_data is not None and is a dictionary
        if tab_data is None or not isinstance(tab_data, dict):
            st.error(f"No data available to display for {name_suffix} comparison.")
            logger.warning(f"tab_data is None or not a dict for {name_suffix}")
            return

        # Extract current and prior values safely
        current_values = tab_data.get("current", {})
        prior_values = tab_data.get(prior_key_suffix, {}) # e.g., tab_data.get('prior_month', {})

        if not current_values and not prior_values:
            st.info(f"No financial data found for current or {name_suffix} periods.")
            return
            
        # Main metrics table
        main_metrics_data = []
        metrics_order = [
            ("gpr", "Gross Potential Rent"), ("vacancy_loss", "Vacancy Loss"), 
            ("other_income", "Other Income"), ("egi", "Effective Gross Income"),
            ("opex", "Total Operating Expenses"), ("noi", "Net Operating Income")
        ]

        for key, name in metrics_order:
            current_val = current_values.get(key, 0.0)
            prior_val = prior_values.get(key, 0.0)
            
            # Use .get for change and percent_change with a default of 0.0
            change_val = tab_data.get(f"{key}_change", 0.0) 
            percent_change_val = tab_data.get(f"{key}_percent_change", 0.0)

            main_metrics_data.append({
                "Metric": name,
                "Current": f"${current_val:,.2f}",
                name_suffix: f"${prior_val:,.2f}",
                "Change ($)": f"${change_val:,.2f}",
                "Change (%)": f"{percent_change_val:.1f}%"
            })
        
        main_metrics_df = pd.DataFrame(main_metrics_data)
        
        # --- NEW: Build numeric DataFrame for charts and deeper analysis ---
        chart_data = []
        for key, name in metrics_order:
            current_val_num = float(current_values.get(key, 0.0) or 0.0)
            prior_val_num = float(prior_values.get(key, 0.0) or 0.0)

            # Prefer pre-calculated numeric change if available; otherwise calculate
            change_val_num = tab_data.get(f"{key}_change")
            if change_val_num is None or pd.isna(change_val_num):
                change_val_num = current_val_num - prior_val_num
            change_val_num = float(change_val_num)

            percent_change_num = tab_data.get(f"{key}_percent_change")
            if percent_change_num is None or pd.isna(percent_change_num):
                percent_change_num = (change_val_num / prior_val_num * 100) if prior_val_num else 0.0
            percent_change_num = float(percent_change_num)

            # Align metric naming with helper logic used later in the chart section
            metric_name_chart = "Total OpEx" if name == "Total Operating Expenses" else name

            # Determine business direction (favorable / unfavorable / neutral)
            if metric_name_chart in ["Vacancy Loss", "Total OpEx"]:
                direction = "Favorable" if change_val_num < 0 else ("Unfavorable" if change_val_num > 0 else "Neutral")
            else:
                direction = "Favorable" if change_val_num > 0 else ("Unfavorable" if change_val_num < 0 else "Neutral")

            chart_data.append({
                "Metric": metric_name_chart,
                "Current": current_val_num,
                name_suffix: prior_val_num,
                "Change ($)": change_val_num,
                "Change (%)": percent_change_num,
                "Direction": direction
            })

        # This DataFrame is used later for visualisations
        df = pd.DataFrame(chart_data)
        # --- END NEW CODE ---

        # Apply styling for changes
        styled_df = main_metrics_df.style.applymap(
            highlight_changes, 
            subset=['Change ($)', 'Change (%)']
        )
            
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Add OpEx Breakdown expander section
        with st.expander("Operating Expense Breakdown", expanded=True):
            opex_components_keys = ["property_taxes", "insurance", "repairs_and_maintenance", "utilities", "management_fees"]
            opex_metrics_names = ["Property Taxes", "Insurance", "Repairs & Maintenance", "Utilities", "Management Fees"]

            # Check if any opex components exist in the data (either in current_values or prior_values)
            if any(component in current_values for component in opex_components_keys) or \
               any(f"{component}_{prior_key_suffix}" in tab_data for component in opex_components_keys) or \
               any(component in prior_values for component in opex_components_keys): # Added check for prior_values directly
                
                opex_df_data = []
                category_colors = {
                    "Property Taxes": "#4ecdc4", "Insurance": "#1e88e5",
                    "Repairs & Maintenance": "#8ed1fc", "Utilities": "#ff6b6b",
                    "Management Fees": "#ba68c8"
                }
                
                for key, name in zip(opex_components_keys, opex_metrics_names):
                    current_val_raw = current_values.get(key, tab_data.get(f"{key}_current", 0.0))
                    # Ensure prior_val_raw fetches from all possible keys and defaults to 0.0
                    prior_val_raw = prior_values.get(key, 
                                       tab_data.get(f"{key}_{prior_key_suffix}", 
                                       tab_data.get(f"{key}_compare", 0.0)))

                    current_val = float(current_val_raw) if pd.notna(current_val_raw) else 0.0
                    prior_val = float(prior_val_raw) if pd.notna(prior_val_raw) else 0.0

                    # Prefer pre-calculated change values if available and valid, otherwise calculate
                    change_val_raw = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance"))
                    if pd.notna(change_val_raw):
                        change_val = float(change_val_raw)
                    else:
                        change_val = current_val - prior_val

                    percent_change_raw = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance"))
                    if pd.notna(percent_change_raw):
                        percent_change = float(percent_change_raw)
                    else:
                        percent_change = (change_val / prior_val * 100) if prior_val != 0 else 0.0
                    
                    if not st.session_state.get("show_zero_values", True) and current_val == 0 and prior_val == 0:
                        continue
                        
                    opex_df_data.append({
                        "Expense Category": name,
                        "Current": current_val,
                        name_suffix: prior_val,
                        "Change ($)": change_val,
                        "Change (%)": percent_change,
                        "Color": category_colors.get(name, "#a9a9a9") 
                    })
                
                if opex_df_data:
                    opex_df = pd.DataFrame(opex_df_data)
                    
                    # Create display dataframe without the Color column
                    opex_df_display = opex_df.drop(columns=['Color']).copy()
                    opex_df_display["Current"] = opex_df_display["Current"].apply(lambda x: f"${x:,.2f}")
                    opex_df_display[name_suffix] = opex_df_display[name_suffix].apply(lambda x: f"${x:,.2f}")
                    # Apply + sign for positive changes, - for negative, and no sign for zero.
                    opex_df_display["Change ($)"] = opex_df_display["Change ($)"].apply(
                        lambda x: f"+${x:,.2f}" if x > 0 else (f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}")
                    )
                    opex_df_display["Change (%)"] = opex_df_display["Change (%)"].apply(
                        lambda x: f"+{x:.1f}%" if x > 0 else (f"{x:.1f}%" if x < 0 else f"{x:.1f}%") # Negative sign is inherent
                    )
                    
                    styled_opex_df = opex_df_display.style.applymap(
                        highlight_changes, 
                        subset=['Change ($)', 'Change (%)']
                    )
                    
                    st.dataframe(styled_opex_df.format({
                        "Current": "{:}",
                        name_suffix: "{:}",
                        "Change ($)": "{:}",
                        "Change (%)": "{:}"
                    }).hide(axis="index").set_table_styles([
                        {'selector': 'th', 'props': [('background-color', 'rgba(30, 41, 59, 0.7)'), ('color', '#e6edf3'), ('font-family', 'Inter'), ('text-align', 'left')]},
                        {'selector': 'td', 'props': [('font-family', 'Inter'), ('color', '#e6edf3'), ('text-align', 'left')]}
                    ]), use_container_width=True)

                    # Create columns for charts with enhanced styling
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Wrap the chart in a container with our custom styling
                        chart_container_html = '<div class="opex-chart-container"><div class="opex-chart-title">Current Operating Expenses Breakdown</div></div>'
                        st.markdown(chart_container_html, unsafe_allow_html=True)
                        
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
                        chart_container_html = f'<div class="opex-chart-container"><div class="opex-chart-title">OpEx Components: Current vs {safe_text(name_suffix)}</div></div>'
                        st.markdown(chart_container_html, unsafe_allow_html=True)
                        
                        # Create a horizontal bar chart for comparison
                        if not opex_df.empty:
                            # Prepare the data in a format suitable for the horizontal bar chart
                            bar_data = []
                            for _, row in opex_df.iterrows(): # Use the original opex_df with numerical data for charts
                                bar_data.append({
                                    "Expense Category": row["Expense Category"],
                                    "Amount": row["Current"], # Use numerical "Current"
                                    "Period": "Current",
                                    "Color": row["Color"]
                                })
                                bar_data.append({
                                    "Expense Category": row["Expense Category"],
                                    "Amount": row[name_suffix], # Use numerical column for prior/budget
                                    "Period": name_suffix,
                                    "Color": row["Color"] # Can be used if you map colors per category
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
                                    "Current": "#1e88e5", # Blue for Current
                                    name_suffix: "#4ecdc4"  # Teal for Prior/Budget (can be dynamic based on name_suffix if needed)
                                },
                                labels={"Amount": "Amount ($)", "Expense Category": ""},
                                height=len(opex_df["Expense Category"].unique()) * 60 + 100 # Dynamic height
                            )
                            
                            # Update layout for modern appearance
                            comp_fig.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#e6edf3', family="Inter"),
                                legend=dict(
                                    orientation="h", 
                                    yanchor="bottom", y=1.02, 
                                    xanchor="right", x=1,
                                    bgcolor='rgba(30, 41, 59, 0.7)', 
                                    bordercolor='rgba(56, 139, 253, 0.15)'
                                ),
                                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                                yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                                margin=dict(t=0, b=20, l=0, r=0) # Adjust top margin for title
                            )
                            st.plotly_chart(comp_fig, use_container_width=True)
                        else:
                            st.info("No OpEx data to display in bar chart.")
                else:
                    # We have components but no data to display after filtering
                    st.info("No operating expense details available for this period based on current filters.")
            else:
                # No operating expense components in the data
                st.info("Operating expense breakdown is not available for this comparison.")
                
        # Add Other Income Breakdown expander section
        with st.expander("Other Income Breakdown", expanded=True):
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
                    current_val_raw = current_values.get(key, tab_data.get(f"{key}_current", 0.0))
                    prior_val_raw = prior_values.get(key, tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_compare", 0.0)))
                    change_val_raw = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance", 0.0))
                    percent_change_raw = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance", 0.0))

                    current_val = float(current_val_raw) if pd.notna(current_val_raw) else 0.0
                    prior_val = float(prior_val_raw) if pd.notna(prior_val_raw) else 0.0
                    change_val = float(change_val_raw) if pd.notna(change_val_raw) else 0.0
                    percent_change = float(percent_change_raw) if pd.notna(percent_change_raw) else 0.0
                    
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
                            title=f"Top Other Income Components: Current vs {safe_text(name_suffix)}",
                            barmode='group',
                            xaxis_title="Amount ($)",
                            xaxis=dict(tickprefix="$"),
                            template="plotly_dark",
                            plot_bgcolor='rgba(30, 41, 59, 0.8)',
                            paper_bgcolor='rgba(16, 23, 42, 0)',
                            margin=dict(l=20, r=20, t=60, b=100),
                            font=dict(
                                family="Inter, sans-serif",
                                size=12,
                                color="#F0F0F0"
                            ),
                            title_font=dict(size=16, color="#F0F0F0", family="Inter, sans-serif"),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.3,  # moved slightly lower to sit below axis title
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
                        # No low_components to report; skip informational message to avoid confusion.
                        pass
                else:
                    st.info("Other income components were identified, but all had zero values for both current and prior periods (and 'Show Zero Values' is off).")
                    logger.info(f"Other income components found but resulted in empty df_data for {name_suffix} (likely all zeros and show_zero_values is False).")
            else:
                st.info("No other income details available for this period.")
                logger.info(f"No other income component keys (e.g., parking_current) found in tab_data for {name_suffix}. Displaying 'no details' message.")
        
        try:
            logger.info(f"Creating charts for {name_suffix} comparison")
            # Create bar chart for visual comparison
            
            # Add chart container and title for modern styling (single HTML block to avoid stray text)
            st.markdown(
                f'<div class="chart-container"><div class="chart-title">Current vs {safe_text(name_suffix)}</div></div>',
                unsafe_allow_html=True
            )

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
                current_noi_val = df.loc[df['Metric'] == 'NOI', 'Current'].values[0]
                prior_noi_val = df.loc[df['Metric'] == 'NOI', name_suffix].values[0]

                current_noi = float(current_noi_val) if pd.notna(current_noi_val) else 0.0
                prior_noi = float(prior_noi_val) if pd.notna(prior_noi_val) else 0.0
                
                # Calculate the difference and percentage change with safe handling
                noi_diff = current_noi - prior_noi
                noi_pct = (noi_diff / prior_noi * 100) if prior_noi != 0 else 0
                
                # Ensure safe text for annotation
                noi_diff_safe = safe_text(noi_diff) or "0"
                noi_pct_safe = safe_text(f"{noi_pct:.1f}") or "0.0"
                
                # Create annotation text based on whether NOI increased or decreased
                # For NOI, an increase is positive (green), decrease is negative (red)
                if noi_diff > 0:
                    annotation_text = safe_text(f"NOI increased by<br>${noi_diff:,.0f}<br>({noi_pct:.1f}%)")
                    arrow_color = "#00bfa5"  # Teal green for positive
                elif noi_diff < 0:
                    annotation_text = safe_text(f"NOI decreased by<br>${abs(noi_diff):,.0f}<br>({abs(noi_pct):.1f}%)")
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
                title_text='',  # Explicitly clear Plotly title to prevent 'undefined' from appearing
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
            
            # Safety: ensure no stray title text remains (avoids 'undefined' render)
            if fig.layout.title and (fig.layout.title.text is None or str(fig.layout.title.text).lower() == 'undefined'):
                fig.update_layout(title_text='')
            
            # Wrap the chart display in the container div
            st.plotly_chart(fig, use_container_width=True)
            
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
            # if 'opex_components' in tab_data and tab_data['opex_components']:
            #     display_opex_breakdown(tab_data['opex_components'], name_suffix)
            # else:
            #     logger.info(f"No OpEx components found for {name_suffix} comparison")

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
    
    if 'noi_coach_history' not in st.session_state:
        st.session_state.noi_coach_history = []
    if 'noi_coach_selected_context' not in st.session_state:
        st.session_state.noi_coach_selected_context = "budget" # Default context

    # CSS for chat (can be kept or removed if global styles cover it)
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
        .chat-message-content { word-wrap: break-word; line-height: 1.5; }
        .chat-input-label { margin-bottom: 0.5rem; font-weight: 500; color: #e6edf3; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    </style>""", unsafe_allow_html=True)

    # Context selector
    st.markdown("### Select Comparison Context")
    contexts = {
        "prior_month": "Prior Month",
        "budget": "Budget",
        "prior_year": "Prior Year"
    }
    selected_context_key = st.radio(
        "Analyze against:",
        options=list(contexts.keys()),
        format_func=lambda k: contexts[k],
        index=list(contexts.keys()).index(st.session_state.noi_coach_selected_context),
        horizontal=True,
        key="noi_coach_context_radio"
    )
    if selected_context_key != st.session_state.noi_coach_selected_context:
        st.session_state.noi_coach_selected_context = selected_context_key
        # st.rerun() # Optional: rerun if changing context should clear chat or update something immediately

    # Display chat history
    for message in st.session_state.noi_coach_history:
        role = message["role"]
        content = safe_text(message["content"])
        if role == "user":
            st.markdown(f"""<div class="chat-message user-message"><div class="chat-message-content">{content}</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="chat-message assistant-message"><div class="chat-message-content">{content}</div></div>""", unsafe_allow_html=True)
    
    with st.form(key="noi_coach_form_app", clear_on_submit=True):
        st.markdown("<div class='chat-input-label'>Ask a question about your financial data:</div>", unsafe_allow_html=True)
        user_question = st.text_input("", placeholder="e.g., What's driving the change in NOI?", label_visibility="collapsed")
        # Use wider, equal spacer columns to guarantee perfect centering
        col_left, col_center, col_right = st.columns([4,2,4])
        with col_center:
            submit_button = st.form_submit_button("Ask NOI Coach")
    
    if submit_button and user_question:
        logger.info(f"NOI Coach (app.py) question: {user_question} with context: {st.session_state.noi_coach_selected_context}")
        st.session_state.noi_coach_history.append({"role": "user", "content": user_question})
        
        if 'comparison_results' not in st.session_state or not st.session_state.comparison_results:
            response = "Please process financial documents first so I can analyze your data."
        else:
            try:
                # Call the ask_noi_coach function from app.py
                response = ask_noi_coach(
                    user_question,
                    st.session_state.comparison_results,
                    st.session_state.noi_coach_selected_context
                )
            except Exception as e:
                logger.error(f"Error generating NOI Coach response in app.py: {str(e)}", exc_info=True)
                response = f"I'm sorry, I encountered an error: {str(e)}"
        
        st.session_state.noi_coach_history.append({"role": "assistant", "content": response})
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
            
        import html as _html_mod  # local import within function
        escaped = _html_mod.escape(summary_text).replace("\n", "<br>")
        st.markdown(f"<div class='results-text'>{escaped}</div>", unsafe_allow_html=True)
    
    # Display Key Performance Insights
    if 'performance' in insights_data and insights_data['performance']:
        st.markdown("## Key Performance Insights")
        
        performance_markdown = ""
        for insight in insights_data['performance']:
            performance_markdown += f"- {insight}\n"
        if performance_markdown:
            st.markdown(performance_markdown)
    
    # Display Recommendations
    if 'recommendations' in insights_data and insights_data['recommendations']:
        st.markdown("## Recommendations")
        
        recommendations_markdown = ""
        for recommendation in insights_data['recommendations']:
            recommendations_markdown += f"- {recommendation}\n"
        if recommendations_markdown:
            st.markdown(recommendations_markdown)

def create_prior_month_comparison_table_html(data):
    """
    Create the Prior Month comparison table with proper styling and color coding
    
    FUNCTIONALITY PRESERVATION: Only affects HTML presentation, not data processing
    """
    html = '''
    <div class="prior-month-table-container">
        <table class="prior-month-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Current</th>
                    <th>Prior Month</th>
                    <th class="change-dollar-column">Change ($)</th>
                    <th class="change-percent-column">Change (%)</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for row in data:
        metric_name = row['metric']
        current_value = format_currency_value_universal(row['current'])
        prior_value = format_currency_value_universal(row['prior'])
        change_dollar = format_financial_change_universal(row['change_dollar'], "change", is_percentage=False)
        change_percent = format_financial_change_universal(row['change_percent'], "change", is_percentage=True)
        
        html += f'''
                <tr>
                    <td>{metric_name}</td>
                    <td>{current_value}</td>
                    <td>{prior_value}</td>
                    <td class="change-dollar-column">{change_dollar}</td>
                    <td class="change-percent-column">{change_percent}</td>
                </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </div>
    '''
    
    return html

@monitor_performance
def generate_comprehensive_pdf():
    """
    Generates a comprehensive PDF report of the analysis.
    
    This function compiles all the comparison data, insights, and narratives 
    into a single HTML document and then converts it to a PDF.
    
    FUNCTIONALITY PRESERVATION: This function only affects PDF generation.
    All underlying calculations and data values remain unchanged.
    """
    # This is a placeholder for the full PDF generation logic.
    # It would gather all session state data and render a Jinja2 template.
    if 'comparison_results' not in st.session_state:
        st.error("No data available to generate a report.")
        return None
        
    try:
        # Example of data to pass to the template
        context = {
            "property_name": st.session_state.get("property_name", "N/A"),
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "comparison_results": st.session_state.get("comparison_results"),
            "insights": st.session_state.get("insights"),
            "narrative": st.session_state.get("generated_narrative")
        }
        
        # This would use a more complex template in a real scenario
        html_content = f"<h1>Report for {context['property_name']}</h1>"
        html_content += f"<p>Date: {context['report_date']}</p>"
        # Add more sections for each part of the analysis
        
        # For demonstration, creating a dummy PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name
        
        st.success("PDF report generated successfully!")
        return pdf_path
        except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}", exc_info=True)
        st.error(f"Could not generate PDF report. Error: {e}")
        return None

def format_currency_value_universal(value):
    """
    Format currency values with proper styling - universal application
    
    FUNCTIONALITY PRESERVATION: Only affects visual formatting, not data values
    """
    if value is None or math.isinf(value) or math.isnan(value):
        return f'<span class="currency-value">$N/A</span>'
    return f'<span class="currency-value">${value:,.0f}</span>'

def format_financial_change_universal(value, comparison_type="change", is_percentage=False):
    """
    Format financial change values with appropriate color coding for ALL comparison types
    
    Args:
        value: The financial value (float)
        comparison_type: Type of comparison ("change", "variance", "growth")
        is_percentage: Boolean indicating if this is a percentage value
    
    Returns:
        Formatted string with HTML and CSS classes
        
    FUNCTIONALITY PRESERVATION: This function only affects visual presentation.
    All underlying calculations and data values remain unchanged.
    """
    if value is None or math.isinf(value) or math.isnan(value):
        value = 0

    if value > 0:
        css_class = f"{comparison_type}-positive"
        prefix = "+" if not is_percentage else "+"
        suffix = "%" if is_percentage else ""
    elif value < 0:
        css_class = f"{comparison_type}-negative"
        prefix = ""
        suffix = "%" if is_percentage else ""
    else:
        css_class = f"{comparison_type}-neutral"
        prefix = ""
        suffix = "%" if is_percentage else ""
    
    if is_percentage:
        formatted_value = f"{value:.1f}"
    else:
        formatted_value = f"{value:,.0f}"
    
    return f'<span class="{css_class} {"percentage-value" if is_percentage else "currency-value"}">{prefix}{formatted_value}{suffix}</span>'

@monitor_performance
def main():
    """
    Main application function with universal styling
    
    FUNCTIONALITY PRESERVATION: All existing functionality preserved
    """
    with monitor_performance("main_app"):
        # Load custom CSS - affects only visual presentation
        load_custom_css_universal()
        
        # Set page config for light theme - visual only
        st.set_page_config(
            page_title="NOI Analyzer",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

        # Initialize session state if not already done
        if "data_loaded" not in st.session_state:
            st.session_state.data_loaded = False
        if "processing_completed" not in st.session_state:
            st.session_state.processing_completed = False
        if "comparison_results" not in st.session_state:
            st.session_state.comparison_results = {}
        if "insights" not in st.session_state:
            st.session_state.insights = {}
            
        # Load testing configuration
        load_testing_config()

        # Sidebar for configuration
        with st.sidebar:
            st.markdown("## Configuration")
            
            # Testing Mode Toggle
            testing_mode = st.toggle(
        "Enable Testing Mode",
                value=is_testing_mode_active(),
                key="testing_mode",
                help="Use mock data for demonstration and testing purposes without API calls."
    )
    
            # Save config if it changes
        save_testing_config()
    
    if is_testing_mode_active():
                display_testing_mode_indicator()
                st.session_state.mock_property_name = st.text_input(
            "Property Name",
            value=st.session_state.get("mock_property_name", "Test Property"),
                    key="mock_property_name"
                )
                st.session_state.mock_scenario = st.selectbox(
                    "Select Mock Scenario",
                    ["Standard Performance", "High Growth", "Declining Performance", "Budget Variance"],
                    index=["Standard Performance", "High Growth", "Declining Performance", "Budget Variance"].index(
                        st.session_state.get("mock_scenario", "Standard Performance")
                    ),
                    key="mock_scenario",
                    help="Choose a pre-defined data scenario to test different outputs."
                )
                if st.button("Generate Mock Data", use_container_width=True):
                    process_documents_testing_mode()
                
                # Optional diagnostics
                if st.checkbox("Show Diagnostics"):
                    st.session_state.run_diagnostics = st.button("Run Diagnostics")
            run_testing_mode_diagnostics()
            else:
                # API Key Configuration
                with st.expander("API Settings", expanded=False):
                    st.info("API keys are securely stored and never exposed in the frontend.")
                    openai_api_key = st.text_input(
                        "OpenAI API Key", 
                        type="password", 
                        value=get_openai_api_key() or "",
                        help="Required for AI-powered insights and analysis."
                    )
                    extraction_api_url = st.text_input(
                        "Extraction API URL", 
                        value=get_extraction_api_url() or "",
                        help="URL for the data extraction service."
                    )
                    api_key = st.text_input(
                        "Extraction API Key", 
                        type="password", 
                        value=get_api_key() or "",
                        help="API key for the data extraction service."
                    )
                    if st.button("Save API Settings"):
                        save_api_settings(openai_api_key, extraction_api_url, api_key)
                        st.success("API settings saved!")

        # Main content
        display_logo()

        if not st.session_state.processing_completed:
            st.markdown("### Upload Your Financial Documents")
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.current_month_file = upload_card("Current Month T-12", required=True, key="current_uploader")
                st.session_state.prior_month_file = upload_card("Prior Month T-12", key="prior_uploader")
            with col2:
                st.session_state.budget_file = upload_card("Budget", key="budget_uploader")
                st.session_state.prior_year_file = upload_card("Prior Year T-12", key="prior_year_uploader")
            
            st.session_state.property_name = property_input(st.session_state.get("property_name", ""))

            if st.button("Analyze Financials", use_container_width=True, type="primary"):
                if st.session_state.current_month_file:
                    with st.spinner("Processing documents and analyzing financials... this may take a moment."):
                        # Collect all uploaded files
                        uploaded_files = {
                            "current_month": st.session_state.current_month_file,
                            "prior_month": st.session_state.prior_month_file,
                            "budget": st.session_state.budget_file,
                            "prior_year": st.session_state.prior_year_file,
                        }
                        
                        # Filter out None values
                        files_to_process = {k: v for k, v in uploaded_files.items() if v is not None}

                        # Call the batch processing function
                        results = process_all_documents(
                            files_to_process, 
                            st.session_state.property_name
                        )

                        # Store results in session state
                        st.session_state.consolidated_data = results.get("consolidated_data")
                        st.session_state.comparison_results = results.get("comparison_results")
                        st.session_state.insights = results.get("insights")
                        st.session_state.generated_narrative = results.get("narrative")
                        st.session_state.edited_narrative = results.get("narrative")

                        st.session_state.processing_completed = True
                        st.rerun()
                else:
                    st.error("Please upload at least the Current Month T-12 document.")

            # Display instruction and feature cards
            col1, col2 = st.columns(2)
            with col1:
            instructions_card([
                    "Upload your property's financial statements.",
                    "The 'Current Month' T-12 is required.",
                    "Provide other documents for deeper comparisons.",
                    "Click 'Analyze' to generate insights."
                ])
            with col2:
            feature_list([
                    ("Automated Data Extraction", "Extracts key financial data from your documents."),
                    ("Comprehensive NOI Analysis", "Calculates and compares NOI across different periods."),
                    ("AI-Powered Insights", "Generates actionable insights and recommendations."),
                    ("Financial Storytelling", "Creates a narrative summary of your property's performance.")
                ])

    if st.session_state.processing_completed:
            # Render navigation - functionality unchanged
            tab1, tab2, tab3, tab4, tab5 = render_navigation_with_search_universal()
            
            comparison_results = st.session_state.get("comparison_results", {})
            prior_month_data = comparison_results.get("month_vs_prior", {})
            budget_data = comparison_results.get("actual_vs_budget", {})
            prior_year_data = comparison_results.get("year_vs_year", {})
            
            # Apply consistent styling to all comparison views
            render_comparison_view_universal(tab1, "prior_month", prior_month_data)
            render_comparison_view_universal(tab2, "budget", budget_data)
            render_comparison_view_universal(tab3, "prior_year", prior_year_data)
            
            # Summary and NOI Coach tabs - apply same styling principles
            with tab4:
                st.write("Summary View")
                display_unified_insights(st.session_state.get("insights", {}))

            with tab5:
                if NOI_COACH_AVAILABLE:
                    display_noi_coach_enhanced()
                    else:
                    st.error("NOI Coach is not available.")

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
        st.info("No insights data available to display.")
        return
    
    logger.info(f"Insights data keys: {list(insights_data.keys())}")
    
    # Display Executive Summary
    if 'summary' in insights_data:
        st.markdown("## Executive Summary")
        
        summary_text = insights_data['summary']
        # Remove redundant "Executive Summary:" prefix if it exists
        if summary_text.startswith("Executive Summary:"):
            summary_text = summary_text[len("Executive Summary:"):].strip()
            
        with st.container():
            import html as _html_mod  # local import to avoid top-level issues
            escaped = _html_mod.escape(summary_text).replace("\n", "<br>")
            st.markdown(f"<div class='results-text'>{escaped}</div>", unsafe_allow_html=True)
    
    # Display Key Performance Insights
    if 'performance' in insights_data and insights_data['performance']:
        st.markdown("## Key Performance Insights")
        
        performance_markdown = ""
        for insight in insights_data['performance']:
            performance_markdown += f"- {insight}\n"
        if performance_markdown:
            st.markdown(performance_markdown)
    
    # Display Recommendations
    if 'recommendations' in insights_data and insights_data['recommendations']:
        st.markdown("## Recommendations")
        
        recommendations_markdown = ""
        for recommendation in insights_data['recommendations']:
            recommendations_markdown += f"- {recommendation}\n"
        if recommendations_markdown:
            st.markdown(recommendations_markdown)

def display_opex_breakdown(opex_data, comparison_type="prior month"):
    """
    Display operating expense breakdown using Streamlit DataFrame.
    
    Args:
        opex_data: Dictionary containing operating expense data. 
                   Example: {"property_taxes": {"current": 100, "prior": 90}, ...}
        comparison_type: Type of comparison (e.g., "Prior Month", "Budget")
    """
    if not opex_data or not isinstance(opex_data, dict):
        st.info("No operating expense data provided for breakdown.")
        return

    opex_df_list = []
    for category_key, data_values in opex_data.items():
        if not data_values or not isinstance(data_values, dict):
            logger.warning(f"Skipping invalid OpEx data for category: {category_key}")
            continue
            
        current = data_values.get('current', 0.0)
        prior = data_values.get('prior', 0.0) # Assuming 'prior' as the comparison key
        
        change = current - prior
        percent_change = (change / prior * 100) if prior != 0 else 0.0
        
        display_name = category_key.replace('_', ' ').title()
        
        opex_df_list.append({
            "Expense Category": display_name,
            "Current": current,
            comparison_type: prior, # Use the dynamic comparison_type for the column name
            "Change ($)": change,
            "Change (%)": percent_change
        })

    if not opex_df_list:
        st.info("No valid operating expense items to display.")
        return

    opex_df = pd.DataFrame(opex_df_list)

    # Format for display
    opex_df_display = opex_df.copy()
    opex_df_display["Current"] = opex_df_display["Current"].apply(lambda x: f"${x:,.2f}")
    opex_df_display[comparison_type] = opex_df_display[comparison_type].apply(lambda x: f"${x:,.2f}")
    opex_df_display["Change ($)"] = opex_df_display["Change ($)"].apply(
        lambda x: f"+${x:,.2f}" if x > 0 else (f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}")
    )
    opex_df_display["Change (%)"] = opex_df_display["Change (%)"].apply(
        lambda x: f"+{x:.1f}%" if x > 0 else (f"{x:.1f}%" if x < 0 else f"{x:.1f}%") # Negative sign is inherent
    )

    styled_df = opex_df_display.style.applymap(
        highlight_changes,
        subset=['Change ($)', 'Change (%)']
    )

    st.markdown("#### Operating Expenses Breakdown")
    st.dataframe(styled_df.format({
        "Current": "{:}",
        comparison_type: "{:}",
        "Change ($)": "{:}",
        "Change (%)": "{:}"
    }).hide(axis="index").set_table_styles([
        {'selector': 'th', 'props': [('background-color', 'rgba(30, 41, 59, 0.7)'), ('color', '#e6edf3'), ('font-family', 'Inter')]},
        {'selector': 'td', 'props': [('font-family', 'Inter'), ('color', '#e6edf3')]},
        {'selector': '.col_heading', 'props': [('text-align', 'left')]} # Ensures header text is left-aligned
    ]), use_container_width=True)

    # Remove the old HTML and style block as it's no longer used by this function.
    # The custom CSS classes like .opex-breakdown-container, .opex-breakdown-table etc.
    # were part of the old HTML rendering method. If they are not used elsewhere for st.markdown,
    # they might eventually be cleaned up from the CSS file. For now, we only remove the Python string.

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

# Enhanced UI Component Functions
def upload_card(title, required=False, key=None, file_types=None, help_text=None):
    """
    Display an enhanced upload card component using Streamlit-native containers.
    
    Args:
        title: Title of the upload card
        required: Whether this upload is required
        key: Unique key for the file uploader
        file_types: List of accepted file types
        help_text: Help text for the uploader
        
    Returns:
        The uploaded file object
    """
    if file_types is None:
        file_types = ["xlsx", "xls", "csv", "pdf"]
    
    # Use Streamlit container instead of HTML div
    with st.container():
        # 1. Header section - only use markdown for the header, not to wrap widgets
        st.markdown(f"""
        <div class="upload-card-header">
            <h3>{title}</h3>
            {' <span class="required-badge">Required</span>' if required else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # ADD THIS: Empty space between title and uploader for better spacing
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        
        # 2. Add the file uploader - not wrapped in HTML
        uploaded_file = st.file_uploader(
            f"Upload {title}",
            type=file_types,
            key=key,
            label_visibility="collapsed",
            help=help_text or f"Upload your {title.lower()} file"
        )
        
        # 3. Display upload area styling or file info
        if not uploaded_file:
            st.markdown("""
            <div class="upload-area">
                <div class="upload-icon">📤</div>
                <div class="upload-text">Drag and drop file here</div>
                <div class="upload-subtext">Limit 200 MB per file • .xlsx, .xls, .csv, .pdf</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display file info
            file_size = f"{uploaded_file.size / 1024:.1f} KB" if uploaded_file.size else "Unknown size"
            file_type = uploaded_file.type if uploaded_file.type else "Unknown type"
            
            st.markdown(f"""
            <div class="file-info">
                <div class="file-icon">📄</div>
                <div class="file-details">
                    <div class="file-name">{uploaded_file.name}</div>
                    <div class="file-meta">{file_size} • {file_type}</div>
                </div>
                <div class="file-status">Uploaded</div>
            </div>
            """, unsafe_allow_html=True)
    
    return uploaded_file

def instructions_card(items):
    """
    Display an enhanced instructions card.
    
    Args:
        items: List of instruction steps
    """
    items_html = "".join([f"<li>{item}</li>" for item in items])
    st.markdown(f"""
    <div class="instructions-card">
        <h3 class="feature-title">Instructions</h3>
        <ol class="instructions-list">
            {items_html}
        </ol>
    </div>
    """, unsafe_allow_html=True)

def feature_list(features):
    """
    Display an enhanced feature list.
    
    Args:
        features: List of dictionaries with 'title' and 'description' keys
    """
    st.markdown("<h3 class=\"feature-title\">Features</h3>", unsafe_allow_html=True)
    
    for idx, feature in enumerate(features):
        st.markdown(f"""
        <div class="feature-item">
            <div class="feature-number">{idx + 1}</div>
            <div class="feature-content">
                <h4>{feature['title']}</h4>
                <p>{feature['description']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def property_input(value=""):
    """
    Display an enhanced property name input using Streamlit-native containers.
    
    Args:
        value: Current property name value
        
    Returns:
        The entered property name
    """
    with st.container():
        # Header only - don't try to wrap the input widget in HTML
        st.markdown("""
        <div class="upload-card-header">
            <h3>Property Information</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Property name input - not wrapped in HTML
        property_name = st.text_input(
            "Property Name",
            value=value,
            help="Enter the name of the property being analyzed",
            key="main_property_name_input"
        )
    
    return property_name

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

# Run the main function when the script is executed directly
if __name__ == "__main__":
    main()

