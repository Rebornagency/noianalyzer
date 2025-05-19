import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import logging
import os
import json
from typing import Dict, Any, List, Optional, Tuple
import base64
from datetime import datetime
import io
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import tempfile
import jinja2

from utils.helpers import format_for_noi_comparison
from noi_calculations import calculate_noi_comparisons
from noi_tool_batch_integration import process_all_documents
from ai_extraction import extract_noi_data
from ai_insights_gpt import generate_insights_with_gpt
from financial_storyteller import create_narrative
from storyteller_display import display_financial_narrative, display_narrative_in_tabs
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
    
    /* Ensure markdown content uses Inter */
    .stMarkdown p, .stMarkdown li, .stMarkdown div {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Remove top margin from main container */
    .main .block-container {
        padding-top: 1rem !important;
        max-width: 1200px;
    }
    
    /* Enhanced section titles */
    .reborn-section-title {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: var(--reborn-accent-blue) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        padding: 0.5rem 0.75rem !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-radius: 6px !important;
        border-left: 4px solid var(--reborn-accent-blue) !important;
        line-height: 1.4 !important;
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
        
        # Direct embedding of the logo with proper sizing, alignment, and subtle enhancement
        logo_html = f"""
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px; margin-top: 0px; padding: 5px;">
            <img 
                src="data:image/png;base64,{logo_base64}" 
                width="180px" 
                alt="Reborn Logo" 
                style="
                    object-fit: contain;
                    filter: drop-shadow(0px 2px 4px rgba(0, 0, 0, 0.1)); 
                    -webkit-filter: drop-shadow(0px 2px 4px rgba(0, 0, 0, 0.1));
                    max-width: 100%;
                "
            >
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        logger.info("Successfully displayed logo")
    except Exception as e:
        logger.error(f"Error displaying logo: {str(e)}")
        # Fallback to text
        st.markdown("<h2 style='text-align: center; color: #4DB6AC;'>REBORN NOI ANALYZER</h2>", unsafe_allow_html=True)

# New function for small logo display
def display_logo_small():
    """Display the Reborn logo (small, transparent PNG) aligned to the left."""
    try:
        logo_b64 = get_reborn_logo_base64()
        
        # Inline logo with proper sizing, alignment and subtle enhancement
        logo_html = f"""
        <div style="display:flex; align-items:center; margin:0; padding:0;">
            <img src="data:image/png;base64,{logo_b64}"
                 height="32px"
                 style="
                     background:transparent; 
                     object-fit:contain; 
                     margin-right:8px;
                     filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.1));
                     -webkit-filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.1));
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
    <div style="background-color: rgba(30, 41, 59, 0.8); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: #4DB6AC;">Instructions:</h3>
        <ol style="color: #F0F0F0;">
            <li>Upload your financial documents using the file uploaders</li>
            <li>At minimum, upload a <b>Current Month Actuals</b> file</li>
            <li>For comparative analysis, upload additional files (Prior Month, Budget, Prior Year)</li>
            <li>Click "Process Documents" to analyze the data</li>
            <li>View the results in the analysis tabs</li>
            <li>Export your results as PDF or Excel using the export options</li>
        </ol>
        <p style="color: #F0F0F0; font-style: italic;">Note: Supported file formats include Excel (.xlsx, .xls), CSV, and PDF</p>
    </div>
    """
    st.markdown(instructions_html, unsafe_allow_html=True)

# Load custom CSS function (defined here before it's used)
def load_css():
    """Load and apply custom CSS styling"""
    try:
        css_path = os.path.join(os.path.dirname(__file__), "static/css/reborn_theme.css")
        if os.path.exists(css_path):
            with open(css_path) as f:
                css_content = f.read()
                
                # Add CSS to reduce top padding
                css_content += """
                /* Reduce top padding */
                .block-container {
                    padding-top: 1rem !important;
                }
                
                /* Ensure no extra padding in main content area */
                .main .block-container {
                    padding-top: 0.5rem !important;
                    margin-top: 0 !important;
                }
                """
                
                st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
                logger.info(f"Successfully loaded CSS from {css_path} with additional padding reduction")
        else:
            logger.warning(f"CSS file not found at path: {css_path}")
            # Apply fallback comprehensive styling
            st.markdown("""
            <style>
            /* Global theming */
            .stApp {
                background-color: #0A0F1E;
                color: #F0F0F0;
            }
            
            /* Reduce top padding */
            .block-container {
                padding-top: 1rem !important;
            }
            
            /* Ensure no extra padding in main content area */
            .main .block-container {
                padding-top: 0.5rem !important;
                margin-top: 0 !important;
            }
            
            /* Headers */
            h1, h2, h3, h4, h5 {
                color: #4DB6AC !important;
                font-family: 'Inter', sans-serif;
            }
            
            /* Section headers */
            .section-header {
                color: #4DB6AC; 
                font-size: 1.5rem; 
                margin-top: 2rem;
                font-weight: 600;
            }
            
            /* Metric cards */
            .metric-card {
                background-color: #1E293B; 
                border-radius: 10px; 
                padding: 15px; 
                margin: 10px 0;
                border: 1px solid rgba(255,255,255,0.1);
            }
            .metric-title {
                color: #94A3B8; 
                font-size: 0.9rem;
            }
            .metric-value {
                color: white; 
                font-size: 1.5rem; 
                font-weight: bold;
            }
            
            /* Color indicators */
            .positive-change {color: #22C55E !important;}
            .negative-change {color: #EF4444 !important;}
            
            /* Expanders */
            .streamlit-expanderHeader {
                background-color: rgba(30, 41, 59, 0.7);
                border-radius: 5px;
                color: #F0F0F0;
                font-weight: 500;
            }
            
            /* Insights */
            .insights-summary {
                background-color: rgba(30, 41, 59, 0.7);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #4DB6AC;
                margin-bottom: 10px;
            }
            
            /* Button styling */
            .stButton>button {
                background-color: #4DB6AC;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 24px;
                font-weight: 500;
            }
            .stButton>button:hover {
                background-color: #3B9E94;
            }
            
            /* Tables */
            .dataframe {
                font-family: 'Inter', sans-serif;
            }
            .dataframe th {
                background-color: #1E293B;
            }
            .dataframe td {
                background-color: rgba(30, 41, 59, 0.5);
            }
            
            /* Ensure text contrast */
            p, span, div, li {
                color: #F0F0F0;
            }
            </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading CSS: {str(e)}")
        # Apply minimal fallback styling
        st.markdown("""
        <style>
        /* Reduce top padding */
        .block-container {
            padding-top: 1rem !important;
        }
        
        /* Ensure no extra padding in main content area */
        .main .block-container {
            padding-top: 0.5rem !important;
            margin-top: 0 !important;
        }
        
        h1, h2, h3, h4, h5 {color: #4DB6AC !important;}
        .section-header {color: #4DB6AC; font-size: 1.5rem; margin-top: 2rem;}
        .positive-change {color: #22C55E !important;}
        .negative-change {color: #EF4444 !important;}
        </style>
        """, unsafe_allow_html=True)

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
    initial_sidebar_state="expanded"
)

# Call load_css to apply custom styles
load_css()

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
            
            if any(component in current_values for component in opex_components):
                # Create DataFrame for OpEx components
                opex_df_data = []
                opex_metrics = ["Property Taxes", "Insurance", "Repairs & Maintenance", "Utilities", "Management Fees"]
                
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
                        # Operating expenses are positive when they decrease
                        # Removing Direction column as requested
                    })
                
                if opex_df_data:
                    opex_df = pd.DataFrame(opex_df_data)
                    
                    # Format DataFrame for display
                    opex_df_display = opex_df.copy()
                    opex_df_display["Current"] = opex_df_display["Current"].apply(lambda x: f"${x:,.2f}")
                    opex_df_display[name_suffix] = opex_df_display[name_suffix].apply(lambda x: f"${x:,.2f}")
                    opex_df_display["Change ($)"] = opex_df_display["Change ($)"].apply(lambda x: f"${x:,.2f}")
                    opex_df_display["Change (%)"] = opex_df_display["Change (%)"].apply(lambda x: f"{x:.1f}%")
                    
                    # Apply styling and display - no need to drop Direction column as it's no longer added
                    opex_styled_df = opex_df_display
                    
                    # Create a function to apply styling
                    def style_opex_df(row):
                        styles = [''] * len(row)
                        
                        # Get indices of the columns to style
                        pct_change_idx = list(row.index).index("Change (%)")
                        dollar_change_idx = list(row.index).index("Change ($)")
                        
                        try:
                            change_pct_str = row["Change (%)"].strip('%') if isinstance(row["Change (%)"], str) else str(row["Change (%)"])
                            change_pct = float(change_pct_str)
                            
                            # For expenses, a decrease (negative change) is favorable
                            # and an increase (positive change) is unfavorable
                            if change_pct < 0:
                                color = "color: green"  # Negative change (decrease in expenses) is favorable
                                impact = "Favorable"
                            elif change_pct > 0:
                                color = "color: red"    # Positive change (increase in expenses) is unfavorable
                                impact = "Unfavorable"
                            else:
                                color = ""              # No change, neutral impact
                            
                            # Apply to both dollar and percentage columns
                            styles[pct_change_idx] = color
                            styles[dollar_change_idx] = color
                            
                            # If we ever want to add an Impact column to this table too:
                            # row["Impact"] = impact
                            
                        except (ValueError, TypeError):
                            # If there's an error parsing the percentage, don't apply styling
                            pass
                        
                        return styles
                    
                    # Apply styling and display
                    opex_styled = opex_styled_df.style.apply(style_opex_df, axis=1)
                    st.dataframe(opex_styled, use_container_width=True)
                    
                    # Display a pie chart to visualize the breakdown
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Filter out zero values for the pie chart
                        pie_data = opex_df[opex_df["Current"] > 0]
                        if not pie_data.empty:
                            fig = px.pie(
                                pie_data, 
                                values="Current", 
                                names="Expense Category",
                                title="Current Operating Expenses Breakdown",
                                color_discrete_sequence=px.colors.qualitative.Set3,
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
                        # Create a horizontal bar chart for comparison
                        if not opex_df.empty:
                            comp_fig = go.Figure()
                            
                            # Add current period bars
                            comp_fig.add_trace(go.Bar(
                                y=opex_df["Expense Category"],
                                x=opex_df["Current"],
                                name="Current",
                                orientation='h',
                                marker=dict(
                                    color='rgba(13, 110, 253, 0.8)',
                                    line=dict(width=1, color='white')
                                )
                            ))
                            
                            # Add prior period bars
                            comp_fig.add_trace(go.Bar(
                                y=opex_df["Expense Category"],
                                x=opex_df[name_suffix],
                                name=name_suffix,
                                orientation='h',
                                marker=dict(
                                    color='rgba(32, 201, 151, 0.8)',
                                    line=dict(width=1, color='white')
                                )
                            ))
                            
                            # Update layout
                            comp_fig.update_layout(
                                title=f"OpEx Components: Current vs {name_suffix}",
                                barmode='group',
                                xaxis_title="Amount ($)", # This is the value axis for horizontal bars
                                yaxis_title=None, # Categories are on y, no title needed if clear
                                xaxis=dict(tickprefix="$"),
                                template="plotly_dark",
                                plot_bgcolor='rgba(30, 41, 59, 0.8)',
                                paper_bgcolor='rgba(16, 23, 42, 0)',
                                margin=dict(l=120, r=20, t=60, b=100), # Increased left margin for longer y-axis labels, increased bottom margin
                                font=dict(
                                    family="Inter, sans-serif",
                                    size=12,
                                    color="#F0F0F0"
                                ),
                                title_font=dict(size=16, color="#F0F0F0", family="Inter, sans-serif"),
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.25, # Adjusted legend position slightly lower
                                    xanchor="center",
                                    x=0.5,
                                    font=dict(size=10, color="#F0F0F0")
                                )
                            )
                            
                            st.plotly_chart(comp_fig, use_container_width=True)
                else:
                    st.info("No operating expense details available for this period.")
            else:
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
            
            # Create custom color scales based on values to add visual contrast
            current_colors = []
            compare_colors = []
            
            # Use a gradient of blue shades for current values
            current_max = max(df["Current"]) if not df["Current"].empty else 0
            for val in df["Current"]:
                intensity = min(1.0, 0.3 + 0.7 * (val / current_max)) if current_max > 0 else 0.5
                current_colors.append(f'rgba(13, 110, 253, {intensity})')
                
            # Use a gradient of teal shades for comparison values
            compare_max = max(df[name_suffix]) if not df[name_suffix].empty else 0
            for val in df[name_suffix]:
                intensity = min(1.0, 0.3 + 0.7 * (val / compare_max)) if compare_max > 0 else 0.5
                compare_colors.append(f'rgba(32, 201, 151, {intensity})')

            # Add current period bars with enhanced styling
            fig.add_trace(go.Bar(
                x=df["Metric"],
                y=df["Current"],
                name="Current",
                marker=dict(
                    color=current_colors,
                    line=dict(width=1, color='white')
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
                    color=compare_colors,
                    line=dict(width=1, color='white')
                ),
                opacity=0.9,
                customdata=list(zip(df["Metric"])),
                hovertemplate='<b>%{x}</b><br>' + f'{name_suffix}: $' + '%{y:,.0f}<extra></extra>'
            ))

            # Identify peak NOI for annotation
            if 'NOI' in df['Metric'].values:
                current_noi = df.loc[df['Metric'] == 'NOI', 'Current'].values[0]
                prior_noi = df.loc[df['Metric'] == 'NOI', name_suffix].values[0]
                
                # Calculate the difference and percentage change
                noi_diff = current_noi - prior_noi
                noi_pct = (noi_diff / prior_noi * 100) if prior_noi != 0 else 0
                
                # Create annotation text based on whether NOI increased or decreased
                # For NOI, an increase is positive (green), decrease is negative (red)
                if noi_diff > 0:
                    annotation_text = f"NOI increased by ${noi_diff:,.0f}<br>({noi_pct:.1f}%)"
                    arrow_color = "green"
                elif noi_diff < 0:
                    annotation_text = f"NOI decreased by ${abs(noi_diff):,.0f}<br>({noi_pct:.1f}%)"
                    arrow_color = "red"
                else:
                    annotation_text = "NOI unchanged"
                    arrow_color = "gray"
                    
                # Add annotation for NOI
                fig.add_annotation(
                    x='NOI', 
                    y=max(current_noi, prior_noi) * 1.1,
                    text=annotation_text,
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=arrow_color,
                    bgcolor="rgba(30, 41, 59, 0.8)",
                    bordercolor=arrow_color,
                    borderwidth=1,
                    borderpad=4,
                    font=dict(color="#F0F0F0", size=12)
                )

            # Update layout with dark theme styling
            fig.update_layout(
                barmode='group',
                title=f"Current vs {name_suffix}",
                title_font=dict(size=18, color="#F0F0F0", family="Inter, sans-serif"),
                template="plotly_dark",
                plot_bgcolor='rgba(30, 41, 59, 0.8)',
                paper_bgcolor='rgba(16, 23, 42, 0)',
                font=dict(
                    family="Inter, sans-serif",
                    size=14,
                    color="#F0F0F0"
                ),
                margin=dict(l=20, r=20, t=60, b=80),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(10, 15, 30, 0.6)",
                    bordercolor="rgba(255, 255, 255, 0.1)",
                    borderwidth=1,
                    font=dict(
                        color="#F0F0F0"
                    )
                ),
                xaxis=dict(
                    title="",
                    tickfont=dict(size=14),
                    showgrid=False,
                    zeroline=False,
                    color="#F0F0F0"
                ),
                yaxis=dict(
                    title="Amount ($)",
                    titlefont=dict(size=14, color="#F0F0F0"),
                    tickfont=dict(size=12, color="#F0F0F0"),
                    showgrid=True,
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    zeroline=False
                ),
                hoverlabel=dict(
                    bgcolor="#1E293B",
                    font_size=14,
                    font_family="Inter, sans-serif",
                    font_color="#F0F0F0"
                )
            )

            # Add dollar sign to y-axis labels
            fig.update_yaxes(tickprefix="$")
            
            # Add subtle pattern and depth to bars
            for trace in fig.data:
                trace.update(
                    marker_pattern_shape="",
                    marker_line_width=1,
                    marker_line_color="white"
                )

            # Display chart
            st.plotly_chart(fig, use_container_width=True)
            logger.info(f"Successfully displayed chart for {name_suffix} comparison")

            # --- Tab-specific PDF Export --- 
            st.subheader(f"Export {name_suffix} Report")
            try:
                # Prepare context for tab-specific PDF
                pdf_context = {
                    "property_name": current_prop_name,
                    "datetime": datetime,
                    "performance_data": {
                        # Include current values and specific comparison data for this tab
                        "noi": current_values.get("noi", 0),
                        "egi": current_values.get("egi", 0),
                        "opex": current_values.get("opex", 0),
                        "gpr": current_values.get("gpr", 0),
                        # Add other relevant current values as needed
                        
                        # Specific comparison data for this tab
                        f"{prior_key_suffix}_data": tab_data, # Pass the whole tab_data for this comparison
                        
                        # Include narrative and summary if desired for tab-specific reports
                        "financial_narrative": st.session_state.get("edited_narrative") or st.session_state.get("generated_narrative", ""),
                        "executive_summary": st.session_state.get("insights", {}).get("summary", "")
                        # Add more specific insights if needed for tab reports
                    },
                    "logo_base64": get_reborn_logo_base64(),
                    # A flag to indicate this is a tab-specific report for template logic if needed
                    "is_tab_specific_report": True,
                    "tab_name": name_suffix 
                }
                
                # Render the template (you might want a simplified template or logic within the main template for tab reports)
                if report_template:
                    html_content_tab = report_template.render(**pdf_context)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_tab:
                        tmp_tab.write(html_content_tab.encode('utf-8'))
                        tmp_tab_path = tmp_tab.name
                    
                    pdf_bytes_tab = HTML(filename=tmp_tab_path).write_pdf()
                    
                    pdf_filename_tab = f"{current_prop_name.replace(' ', '_')}_{name_suffix.replace(' ', '_')}_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label=f"Download {name_suffix} PDF Report",
                        data=pdf_bytes_tab,
                        file_name=pdf_filename_tab,
                        mime="application/pdf",
                        key=f"download_pdf_{name_suffix.lower().replace(' ', '_')}"  # Unique key based on tab name
                    )
                else:
                    st.warning("PDF template not loaded. Cannot generate tab-specific PDF.")

            except Exception as e_pdf_tab:
                logger.error(f"Error generating PDF for {name_suffix} tab: {e_pdf_tab}", exc_info=True)
                st.error(f"Could not generate PDF for {name_suffix} report.")

            # --- Consolidated Insights, Executive Summary, and Recommendations Section ---
            st.markdown("---")
            st.markdown("""
                <div class="reborn-section-title">Analysis and Recommendations (for {name_suffix})</div>
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

        except Exception as e:
            logger.error(f"Error displaying comparison tab {name_suffix}: {str(e)}", exc_info=True)
        
        # PDF Generation Block - Moved to the bottom
        try:
            # Prepare OpEx breakdown data for PDF context (already done above for UI, can reuse)
            # KPIs for PDF context (already calculated above for UI, can reuse)
            # Executive Summary and Financial Narrative for PDF context (already fetched above for UI, can reuse)

            # Use the globally defined report_template
            if report_template is None:
                logger.error("PDF EXPORT: Global report_template is None. PDF generation will fail.")
                st.error("PDF generation is not available. Please check if the template file exists and is properly loaded.")
                return

            logger.info("PDF EXPORT: Using globally loaded report template.")
            
            # Create context for template (ensure all these variables are defined)
            # executive_summary and financial_narrative are fetched before this try-block now by UI display logic
            # opex_breakdown_data, opex_breakdown_available, kpis, egi, opex, noi, gpr are from UI part
            current_prop_name = st.session_state.property_name if st.session_state.property_name else "N/A"
            
            # Safely extract all required variables from current_values with defaults
            # This prevents NameError exceptions if any variable is undefined
            egi_value = current_values.get("egi", 0)
            opex_value = current_values.get("opex", 0)
            noi_value = current_values.get("noi", 0)
            gpr_value = current_values.get("gpr", 0)
            vacancy_loss_value = current_values.get("vacancy_loss", 0)
            other_income_value = current_values.get("other_income", 0)
            
            # Ensure opex_breakdown_data and opex_breakdown_available are defined
            if 'opex_breakdown_data' not in locals() or opex_breakdown_data is None:
                opex_breakdown_data = []
            
            if 'opex_breakdown_available' not in locals() or opex_breakdown_available is None:
                opex_breakdown_available = False
            
            # Ensure kpis is defined
            if 'kpis' not in locals() or kpis is None:
                kpis = {}
            
            # Create the context dictionary with safely extracted values
            context = {
                "property_name": current_prop_name,
                "datetime": datetime,
                "performance_data": {
                    "egi": egi_value,
                    "opex": opex_value,
                    "noi": noi_value,
                    "gpr": gpr_value,
                    "vacancy_loss": vacancy_loss_value,
                    "other_income": other_income_value,
                    "opex_breakdown_data": opex_breakdown_data,
                    "opex_breakdown_available": opex_breakdown_available,
                    "kpis": kpis,
                    "executive_summary": st.session_state.get("insights", {}).get("summary", ""),
                    "financial_narrative": st.session_state.get("generated_narrative") or st.session_state.get("edited_narrative", ""),
                },
                "comparison_title": name_suffix, 
                "comparison_results": tab_data 
            }
            logger.info("PDF EXPORT: Context for PDF template created successfully.")
            
            html_content = report_template.render(**context)
            logger.info("PDF EXPORT: HTML content rendered from template.")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
                tmp.write(html_content.encode('utf-8'))
                tmp_path = tmp.name
            logger.info(f"PDF EXPORT: HTML content written to temporary file: {tmp_path}")
            
            pdf_bytes = HTML(filename=tmp_path).write_pdf()
            logger.info("PDF EXPORT: PDF bytes generated successfully.")
            
            # Add download button for PDF
            st.subheader("Export Report")
            pdf_filename = f"{current_prop_name.replace(' ', '_')}_NOI_Analysis_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf"
            )
            logger.info(f"PDF EXPORT: Download button displayed for: {pdf_filename}")

        except jinja2.exceptions.TemplateNotFound as e_tnf:
            logger.error(f"PDF EXPORT: Template not found error: {str(e_tnf)}", exc_info=True)
            st.error(f"Error preparing PDF for export: The report template was not found.")
        except NameError as e_name:
            logger.error(f"PDF EXPORT: NameError occurred: {str(e_name)}", exc_info=True)
            st.error(f"Error preparing PDF for export (NameError): {str(e_name)}. This is likely due to missing variable definitions.")
        except Exception as e_pdf_gen:
            logger.error(f"Error in data preparation or PDF generation: {str(e_pdf_gen)}", exc_info=True)
            st.error(f"Error preparing PDF for export: {str(e_pdf_gen)}")
    
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
    """
    Display the NOI Coach interface for asking questions about the financial data.
    This provides an AI-powered assistant to help users understand their NOI analysis.
    """
    st.markdown('<h2 class="section-header">NOI Coach</h2>', unsafe_allow_html=True)
    
    # Create an expander for the NOI Coach
    with st.expander("Ask questions about your NOI data", expanded=False):
        st.markdown("""
        Ask questions about your NOI data and get AI-powered insights. Examples:
        - What factors are driving the change in NOI?
        - How does my vacancy loss compare to industry standards?
        - What actions could improve my NOI?
        """)
        
        # Input for user questions
        user_question = st.text_input(
            "Your question:",
            key="noi_coach_question",
            help="Ask a question about your financial data"
        )
        
        # Get currently selected comparison context
        context = st.session_state.current_comparison_view
        
        # Submit button
        if st.button("Get Answer", key="noi_coach_submit"):
            if user_question:
                with st.spinner("Analyzing your data and generating insights..."):
                    try:
                        # Use the ask_noi_coach function to get AI-powered insights
                        answer = ask_noi_coach(
                            user_question, 
                            st.session_state.comparison_results,
                            context
                        )
                        
                        # Add the Q&A to the history
                        if "noi_coach_history" not in st.session_state:
                            st.session_state.noi_coach_history = []
                        
                        st.session_state.noi_coach_history.append({
                            "question": user_question,
                            "answer": answer,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        # Display the answer
                        st.markdown("### Answer")
                        st.markdown(answer)
                    except Exception as e:
                        logger.error(f"Error in NOI Coach: {str(e)}")
                        st.error(f"Error generating insights: {str(e)}")
            else:
                st.warning("Please enter a question to get insights.")
        
        # Show history of questions and answers
        if "noi_coach_history" in st.session_state and st.session_state.noi_coach_history:
            st.markdown("### Previous Questions")
            
            for i, qa in enumerate(reversed(st.session_state.noi_coach_history)):
                # Only show the 5 most recent Q&As
                if i >= 5:
                    break
                
                with st.container():
                    st.markdown(f"**Q: {qa['question']}**")
                    st.markdown(f"A: {qa['answer']}")
                    st.markdown(f"<small>Asked on {qa['timestamp']}</small>", unsafe_allow_html=True)
                    st.markdown("---")

# Main function for the NOI Analyzer application
def main():
    """
    Main function for the NOI Analyzer Enhanced application.
    Sets up the UI and coordinates all functionality.
    """
    # Inject custom CSS to ensure font consistency
    inject_custom_css()
    
    # Load custom CSS
    load_css()
    
    # Display logo at the very top of the app
    display_logo()
    
    # Log session state at the beginning of a run for debugging narrative
    logger.info(f"APP.PY (main start): st.session_state.generated_narrative is: {st.session_state.get('generated_narrative')}")
    logger.info(f"APP.PY (main start): st.session_state.edited_narrative is: {st.session_state.get('edited_narrative')}")
    
    # Sidebar configuration
    with st.sidebar:
        st.title("NOI Analyzer")
        
        # File uploaders for NOI data
        st.header("Upload Documents")
        
        # Upload current month actuals
        current_month_file = st.file_uploader(
            "Current Month Actuals (Required)", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="current_month_upload",
            help="Upload your current month's financial data"
        )
        
        # Upload prior month actuals
        prior_month_file = st.file_uploader(
            "Prior Month Actuals", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="prior_month_upload",
            help="Upload your prior month's financial data for month-over-month comparison"
        )
        
        # Upload budget
        budget_file = st.file_uploader(
            "Current Month Budget", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="budget_upload",
            help="Upload your budget data for budget vs actuals comparison"
        )
        
        # Upload prior year actuals
        prior_year_file = st.file_uploader(
            "Prior Year Same Month", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="prior_year_upload",
            help="Upload the same month from prior year for year-over-year comparison"
        )
        
        # Property name input
        property_name = st.text_input(
            "Property Name (Optional)",
            value=st.session_state.property_name,
            help="Enter the name of the property being analyzed"
        )
        
        if property_name != st.session_state.property_name:
            st.session_state.property_name = property_name
        
        # Process button
        process_clicked = st.button(
            "Process Documents", 
            type="primary",
            use_container_width=True,
            help="Process the uploaded documents to generate NOI analysis"
        )
        
        # Options
        st.header("Options")
        
        # Show zero values toggle
        show_zero_values = st.checkbox(
            "Show Zero Values", 
            value=st.session_state.show_zero_values,
            help="Show metrics with zero values in the comparison tables"
        )
        
        if show_zero_values != st.session_state.show_zero_values:
            st.session_state.show_zero_values = show_zero_values
            st.rerun()
        
        # NOI Coach context selection
        st.subheader("NOI Coach Context")
        view_options = {
            "budget": "Budget Comparison",
            "prior_year": "Year-over-Year",
            "prior_month": "Month-over-Month"
        }
        selected_view = st.selectbox(
            "Select context for NOI Coach",
            options=list(view_options.keys()),
            format_func=lambda x: view_options[x],
            index=list(view_options.keys()).index(st.session_state.current_comparison_view)
        )
        
        if selected_view != st.session_state.current_comparison_view:
            st.session_state.current_comparison_view = selected_view
            st.success(f"NOI Coach context set to {view_options[selected_view]}")
    
    # Main content area
    if not st.session_state.processing_completed:
        # Show welcome content when no data has been processed
        st.title("NOI Analyzer Enhanced")
        show_instructions()
        
        # Add sample screenshots or overview
        st.subheader("Features")
        st.markdown("""
        - **Comparative Analysis:** Compare current performance against budget, prior month, and prior year
        - **Financial Insights:** AI-generated analysis of key metrics and trends
        - **NOI Coach:** Ask questions about your financial data and get AI-powered insights
        - **Export Options:** Save results as PDF or Excel for sharing and reporting
        """)
        
    else:
        # Show results after processing
        st.title(f"NOI Analysis Results{' - ' + st.session_state.property_name if st.session_state.property_name else ''}")
        
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

        # Create tabs for each comparison type
        tabs = st.tabs(["Prior Month", "Budget", "Prior Year", "Financial Narrative", "NOI Coach"])
        
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
        
        with tabs[3]: # Financial Narrative & Insights Tab
            st.header("Financial Narrative & Insights")
            
            # Display the narrative text and editor
            display_narrative_in_tabs()
            
            # Display the consolidated insights (summary, performance, recommendations)
            if "insights" in st.session_state and st.session_state.insights:
                display_unified_insights(st.session_state.insights)
            else:
                logger.info("No insights data found in session state for Financial Narrative & Insights tab.")
                st.info("Insights (including summary and recommendations) will be displayed here once generated.")

        # Display NOI Coach section
        with tabs[4]: # NOI Coach tab
            display_noi_coach()
    
    # Process documents when button is clicked
    if process_clicked:
        try:
            with st.spinner("Processing documents. This may take a minute..."):
                logger.info("APP.PY: --- Document Processing START ---")
                if not current_month_file:
                    st.error("Current Month Actuals file is required. Please upload it to proceed.")
                    st.session_state.processing_completed = False # Ensure it's false if we exit early
                    return
                st.session_state.current_month_actuals = current_month_file
                st.session_state.prior_month_actuals = prior_month_file
                st.session_state.current_month_budget = budget_file
                st.session_state.prior_year_actuals = prior_year_file

                # Process the documents
                raw_consolidated_data = process_all_documents()
                logger.info(f"APP.PY: raw_consolidated_data received. Type: {type(raw_consolidated_data)}. Keys: {list(raw_consolidated_data.keys()) if isinstance(raw_consolidated_data, dict) else 'Not a dict'}. Has error: {raw_consolidated_data.get('error') if isinstance(raw_consolidated_data, dict) else 'N/A'}")
                if isinstance(raw_consolidated_data, dict) and isinstance(raw_consolidated_data.get('current_month'), dict):
                    try:
                        # Use the summarize function for more concise INFO logging
                        logger.info(f"APP.PY: Snippet of raw_consolidated_data['current_month']: {summarize_data_for_log(raw_consolidated_data['current_month'])}")
                        # Full details moved to DEBUG level
                        logger.debug(f"APP.PY: Full raw_consolidated_data['current_month']: {json.dumps(raw_consolidated_data['current_month'], default=str, indent=2)}")
                    except Exception as e_log_snippet:
                        logger.error(f"APP.PY: Error logging raw_consolidated_data snippet: {e_log_snippet}")


                if raw_consolidated_data and isinstance(raw_consolidated_data, dict) and not raw_consolidated_data.get('error'):
                    logger.info("APP.PY: Condition to transform data met. Calling calculate_noi_comparisons.")
                    try:
                        transformed_data = calculate_noi_comparisons(raw_consolidated_data)
                        logger.info(f"APP.PY: calculate_noi_comparisons returned. Transformed_data type: {type(transformed_data)}. Keys: {list(transformed_data.keys()) if isinstance(transformed_data, dict) else 'Not a dict'}")
                        
                        if isinstance(transformed_data, dict) and "month_vs_prior" in transformed_data:
                            mvp_data = transformed_data["month_vs_prior"]
                            logger.info(f"APP.PY: transformed_data['month_vs_prior'] type: {type(mvp_data)}. Keys: {list(mvp_data.keys()) if isinstance(mvp_data, dict) else 'Not a dict'}")
                            if isinstance(mvp_data, dict):
                                try:
                                    # Use the summarize function for more concise INFO logging
                                    logger.info(f"APP.PY: Snippet of transformed_data['month_vs_prior']: {summarize_data_for_log(mvp_data)}")
                                    # Full details moved to DEBUG level
                                    logger.debug(f"APP.PY: Full transformed_data['month_vs_prior']: {json.dumps(mvp_data, default=str, indent=2)}")
                                except Exception as e_log_snippet_mvp:
                                    logger.error(f"APP.PY: Error logging transformed_data['month_vs_prior'] snippet: {e_log_snippet_mvp}")
                        else:
                            logger.warning("APP.PY: 'month_vs_prior' key missing in transformed_data or transformed_data is not a dict.")

                        st.session_state.comparison_results = transformed_data
                        logger.info(f"APP.PY: st.session_state.comparison_results assigned. Type: {type(st.session_state.comparison_results)}. Keys: {list(st.session_state.comparison_results.keys()) if isinstance(st.session_state.comparison_results, dict) else 'Not a dict'}")
                    except Exception as e_calc:
                        logger.error(f"APP.PY: Error during calculate_noi_comparisons or assignment: {str(e_calc)}", exc_info=True)
                        st.session_state.comparison_results = {"error": f"Calculation error: {str(e_calc)}"}
                elif isinstance(raw_consolidated_data, dict) and raw_consolidated_data.get('error'):
                    logger.error(f"APP.PY: Error reported by process_all_documents: {raw_consolidated_data.get('error')}")
                    st.session_state.comparison_results = raw_consolidated_data
                else:
                    logger.warning(f"APP.PY: Condition to transform data NOT met or raw_consolidated_data is not as expected. raw_consolidated_data type: {type(raw_consolidated_data)}")
                    st.session_state.comparison_results = {"error": "No data from document processing or unexpected data structure."}
                
                # Generate insights and narrative only if comparison results are valid
                if isinstance(st.session_state.comparison_results, dict) and not st.session_state.comparison_results.get("error"):
                    logger.info("APP.PY: comparison_results seem okay. Generating insights and narrative.")
                    
                    # Optional debugging of comparison structure - can be disabled to reduce log volume
                    enable_structure_debug = True  # Set to False to disable detailed structure logging
                    if enable_structure_debug:
                        logger.info(f"APP.PY: Calling debug_comparison_structure with st.session_state.comparison_results. Keys: {list(st.session_state.comparison_results.keys()) if isinstance(st.session_state.comparison_results, dict) else 'Not a dict'}")
                        debug_comparison_structure(st.session_state.comparison_results)
                    
                    insights = generate_insights_with_gpt(st.session_state.comparison_results)
                    # Create a properly structured insights dictionary that matches UI expectations
                    structured_insights = {
                        "summary": insights.get("summary", "")
                    }

                    # Map the performance insights to the comparison-specific keys
                    if "performance" in insights and insights["performance"]:
                        # Convert the performance array to a string for each comparison type
                        performance_text = "\n\n".join([f"• {point}" for point in insights["performance"]])
                        
                        # Add the same insights to all comparison types for now
                        structured_insights["month_vs_prior"] = performance_text
                        structured_insights["actual_vs_budget"] = performance_text
                        structured_insights["year_vs_year"] = performance_text

                    # Add recommendations to the structured insights
                    if "recommendations" in insights and insights["recommendations"]:
                        recommendations_text = "\n\n".join([f"• {rec}" for rec in insights["recommendations"]])
                        structured_insights["recommendations"] = recommendations_text

                    # Store the properly structured insights in session state
                    st.session_state.insights = structured_insights
                    logger.info(f"Structured insights keys: {list(structured_insights.keys())}")
                    
                    narrative = create_narrative(st.session_state.comparison_results, st.session_state.property_name)
                    # Log the raw narrative content and type BEFORE assigning to session state
                    logger.info(f"APP.PY: 'narrative' var from create_narrative. Type: {type(narrative)}. Content snippet: {(str(narrative)[:200] + '...') if narrative else 'None'}")
                    st.session_state.generated_narrative = narrative
                    logger.info("APP.PY: Narrative generated and assigned to st.session_state.generated_narrative.")
                    
                    st.session_state.processing_completed = True
                    st.success("Documents processed successfully!")
                else:
                    error_msg = "Unknown processing error"
                    if isinstance(st.session_state.comparison_results, dict) and st.session_state.comparison_results.get("error"):
                        error_msg = st.session_state.comparison_results.get("error")
                    elif not isinstance(st.session_state.comparison_results, dict) :
                         error_msg = "Comparison results are not in the expected format."

                    logger.error(f"APP.PY: Processing failed or comparison_results has an error or is not a dict. Results: {st.session_state.comparison_results}")
                    st.error(f"Failed to process documents fully. Error: {error_msg}")
                    st.session_state.processing_completed = False
                
                logger.info(f"APP.PY: --- Document Processing END --- processing_completed: {st.session_state.processing_completed}")
                st.rerun()
        except Exception as e:
            logger.error(f"APP.PY: Unhandled error in process_clicked block: {str(e)}", exc_info=True)
            st.error(f"An unexpected error occurred: {str(e)}")
            st.session_state.processing_completed = False
            st.rerun() # Rerun to reflect the error state

    # Add this code in the main UI section after displaying all tabs
    # (after the st.tabs() section in the main function)

    st.markdown("---")
    st.subheader("Export Complete Analysis")

    # Generate PDF button with a unique key
    if st.button("Generate Complete PDF Report", key="global_pdf_export"):
        with st.spinner("Generating comprehensive PDF report..."):
            pdf_bytes = generate_comprehensive_pdf()
            
            if pdf_bytes:
                # Create a unique filename
                current_prop_name = st.session_state.property_name if hasattr(st.session_state, "property_name") else "Property"
                pdf_filename = f"{current_prop_name.replace(' ', '_')}_Complete_NOI_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Display download button with a unique key
                st.download_button(
                    label="Download Complete PDF Report",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key="global_pdf_download"
                )
                st.success("PDF report generated successfully!")
            else:
                st.error("Failed to generate PDF report. Please check the logs for details.")

# Run the main function when the script is executed directly
if __name__ == "__main__":
    main()

# Add this function to app.py, outside any other function
def generate_comprehensive_pdf():
    """
    Generate a comprehensive PDF report that includes all available data,
    insights, and recommendations regardless of the active tab.
    """
    logger.info("PDF EXPORT: Generating comprehensive PDF with all available data")
    
    try:
        # Use the globally defined report_template
        if report_template is None:
            logger.error("PDF EXPORT: Global report_template is None. PDF generation will fail.")
            st.error("PDF generation is not available. Please check if the template file exists and is properly loaded.")
            return None

        # Get property name
        current_prop_name = st.session_state.property_name if hasattr(st.session_state, "property_name") else "Property"
        
        # Get all comparison results from session state
        comparison_results = st.session_state.get("comparison_results", {})
        
        # Get current values
        current_values = comparison_results.get("current", {})
        
        # Get narrative and insights
        narrative_data = st.session_state.get("edited_narrative") or st.session_state.get("generated_narrative", "")
        insights_data = st.session_state.get("insights", {})
        
        # Create a comprehensive context dictionary with all available data
        context = {
            "property_name": current_prop_name,
            "datetime": datetime,
            "performance_data": {
                # Current period metrics
                "noi": current_values.get("noi", 0),
                "egi": current_values.get("egi", 0),
                "opex": current_values.get("opex", 0),
                "gpr": current_values.get("gpr", 0),
                "vacancy_loss": current_values.get("vacancy_loss", 0),
                "other_income": current_values.get("other_income", 0),
                
                # Prior month comparison
                "prior_noi": comparison_results.get("month_vs_prior", {}).get("noi_prior", 0),
                "noi_change": comparison_results.get("month_vs_prior", {}).get("noi_change", 0),
                "noi_percent_change": comparison_results.get("month_vs_prior", {}).get("noi_percent_change", 0),
                
                # Budget comparison
                "budget_noi": comparison_results.get("actual_vs_budget", {}).get("noi_budget", 0),
                "noi_budget_variance": comparison_results.get("actual_vs_budget", {}).get("noi_variance", 0),
                "noi_budget_percent_variance": comparison_results.get("actual_vs_budget", {}).get("noi_percent_variance", 0),
                
                # Year-over-year comparison
                "prior_year_noi": comparison_results.get("year_vs_year", {}).get("noi_prior_year", 0),
                "noi_yoy_change": comparison_results.get("year_vs_year", {}).get("noi_change", 0),
                "noi_yoy_percent_change": comparison_results.get("year_vs_year", {}).get("noi_percent_change", 0),
                
                # Insights and narrative
                "executive_summary": insights_data.get("summary", ""),
                "financial_narrative": narrative_data,
                
                # Add all insights sections
                "month_vs_prior_insights": insights_data.get("month_vs_prior", ""),
                "actual_vs_budget_insights": insights_data.get("actual_vs_budget", ""),
                "year_vs_year_insights": insights_data.get("year_vs_year", ""),
                
                # Add recommendations
                "recommendations": insights_data.get("recommendations", [])
            },
            # Include all comparison results for template access
            "comparison_results": comparison_results,
            "month_vs_prior": comparison_results.get("month_vs_prior", {}),
            "actual_vs_budget": comparison_results.get("actual_vs_budget", {}),
            "year_vs_year": comparison_results.get("year_vs_year", {}),
            
            # Add logo
            "logo_base64": get_reborn_logo_base64()
        }
        
        # Render the template with the comprehensive context
        html_content = report_template.render(**context)
        logger.info("PDF EXPORT: Comprehensive HTML content rendered from template")
        
        # Generate PDF from HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
            tmp.write(html_content.encode('utf-8'))
            tmp_path = tmp.name
        
        pdf_bytes = HTML(filename=tmp_path).write_pdf()
        logger.info("PDF EXPORT: Comprehensive PDF bytes generated successfully")
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"PDF EXPORT: Error generating comprehensive PDF: {str(e)}", exc_info=True)
        st.error(f"Error generating PDF report: {str(e)}")
        return None

def display_unified_insights(insights_data):
    """
    Display insights in a unified, non-repetitive manner.
    
    Args:
        insights_data: Dictionary containing insights from GPT
    """
    if not insights_data or not isinstance(insights_data, dict):
        st.info("No insights data available.")
        return
    
    # Display Executive Summary
    st.markdown("""
        <div class="reborn-section-title executive-summary">Executive Summary</div>
    """, unsafe_allow_html=True)
    
    if "summary" in insights_data and insights_data["summary"]:
        st.markdown(f"""
            <div class="reborn-content">{insights_data["summary"]}</div>
        """, unsafe_allow_html=True)
    else:
        st.info("No executive summary available.")
    
    # Display unified performance insights
    st.markdown("""
        <div class="reborn-section-title insights">Key Performance Insights</div>
    """, unsafe_allow_html=True)
    
    # Check if we have the new format with a single "performance" list
    if "performance" in insights_data and isinstance(insights_data["performance"], list) and insights_data["performance"]:
        insights_html = ""
        for point in insights_data["performance"]:
            insights_html += f"<p>• {point}</p>"
        
        st.markdown(f"""
            <div class="reborn-content">{insights_html}</div>
        """, unsafe_allow_html=True)
    
    # Otherwise, try to consolidate insights from different comparison types
    else:
        # Track insights to avoid duplication
        seen_insights = set()
        consolidated_insights = []
        
        # Process insights from each comparison type
        for comparison_type in ["month_vs_prior", "actual_vs_budget", "year_vs_year"]:
            if comparison_type in insights_data and insights_data[comparison_type]:
                # If it's a string, split into lines
                if isinstance(insights_data[comparison_type], str):
                    lines = insights_data[comparison_type].split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and line not in seen_insights:
                            seen_insights.add(line)
                            consolidated_insights.append(line)
                # If it's a list, add each item
                elif isinstance(insights_data[comparison_type], list):
                    for item in insights_data[comparison_type]:
                        if item and item not in seen_insights:
                            seen_insights.add(item)
                            consolidated_insights.append(item)
        
        if consolidated_insights:
            insights_html = ""
            for insight in consolidated_insights:
                insights_html += f"<p>• {insight}</p>"
            
            st.markdown(f"""
                <div class="reborn-content">{insights_html}</div>
            """, unsafe_allow_html=True)
        else:
            st.info("No detailed insights available.")
    
    # Display recommendations
    st.markdown("""
        <div class="reborn-section-title recommendations">Recommendations</div>
    """, unsafe_allow_html=True)
    
    if "recommendations" in insights_data and insights_data["recommendations"]:
        if isinstance(insights_data["recommendations"], list):
            recommendations_html = ""
            for rec in insights_data["recommendations"]:
                recommendations_html += f"<p>• {rec}</p>"
            
            st.markdown(f"""
                <div class="reborn-content">{recommendations_html}</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="reborn-content">{insights_data["recommendations"]}</div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recommendations available.")

