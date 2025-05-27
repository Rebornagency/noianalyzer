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
import streamlit.components.v1 as components

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
                                    <th>""" + name_suffix + """</th>
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
                        
                        # Get category color
                        color = row["Color"]
                        category = row["Expense Category"]
                        
                        # Add the row with color indicator
                        html_table += f"""
                        <tr>
                            <td>
                                <div class="opex-category-cell">
                                    <span class="opex-category-indicator" style="background-color: {color};"></span>
                                    {category}
                                </div>
                            </td>
                            <td class="opex-neutral-value">{row["Current"]}</td>
                            <td class="opex-neutral-value">{row[name_suffix]}</td>
                            <td class="{value_class}">{row["Change ($)"]}</td>
                            <td class="{value_class}">{row["Change (%)"]}</td>
                        </tr>
                        """
                    
                    # Close the table
                    html_table += """
                            </tbody>
                        </table>
                    </div>
                    """
                    
                    # Display the custom HTML table
                    components.html(html_table, height=250, scrolling=True)
                    
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
                
                # Calculate the difference and percentage change
                noi_diff = current_noi - prior_noi
                noi_pct = (noi_diff / prior_noi * 100) if prior_noi != 0 else 0
                
                # Create annotation text based on whether NOI increased or decreased
                # For NOI, an increase is positive (green), decrease is negative (red)
                if noi_diff > 0:
                    annotation_text = f"NOI increased by<br>${noi_diff:,.0f}<br>({noi_pct:.1f}%)"
                    arrow_color = "#00bfa5"  # Teal green for positive
                elif noi_diff < 0:
                    annotation_text = f"NOI decreased by<br>${abs(noi_diff):,.0f}<br>({noi_pct:.1f}%)"
                    arrow_color = "#f44336"  # Red for negative
                else:
                    annotation_text = "NOI unchanged"
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
    """
    Display the NOI Coach interface for asking questions about the financial data.
    This provides an AI-powered assistant to help users understand their NOI analysis.
    """
    st.markdown('<h2 class="section-header">NOI Coach</h2>', unsafe_allow_html=True)
    
    # Directly display instructions without expander
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

def display_unified_insights(insights_data):
    """
    Display unified insights including summary, performance insights, and recommendations.
    
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
        st.markdown('<h2 class="results-section-header">Executive Summary</h2>', unsafe_allow_html=True)
        
        summary_html = '<div class="results-card">'
        summary_text = insights_data['summary']
        
        # Remove redundant "Executive Summary:" prefix if it exists
        if summary_text.startswith("Executive Summary:"):
            summary_text = summary_text[len("Executive Summary:"):].strip()
            
        summary_html += f'<div class="results-text">{summary_text}</div>'
        summary_html += '</div>'
        
        st.markdown(summary_html, unsafe_allow_html=True)
    
    # Display Key Performance Insights
    if 'performance' in insights_data and insights_data['performance']:
        st.markdown('<h2 class="results-section-header">Key Performance Insights</h2>', unsafe_allow_html=True)
        
        insights_html = '<div class="results-card"><ul class="results-bullet-list">'
        for insight in insights_data['performance']:
            insights_html += f"""
            <li class="results-bullet-item">
                <div class="results-bullet-marker">•</div>
                <div class="results-bullet-text">{insight}</div>
            </li>
            """
        insights_html += '</ul></div>'
        
        st.markdown(insights_html, unsafe_allow_html=True)
    
    # Display Recommendations
    if 'recommendations' in insights_data and insights_data['recommendations']:
        st.markdown('<h2 class="results-section-header">Recommendations</h2>', unsafe_allow_html=True)
        
        recommendations_html = '<div class="results-card"><ul class="results-bullet-list">'
        for recommendation in insights_data['recommendations']:
            recommendations_html += f"""
            <li class="results-bullet-item">
                <div class="results-bullet-marker">•</div>
                <div class="results-bullet-text">{recommendation}</div>
            </li>
            """
        recommendations_html += '</ul></div>'
        
        st.markdown(recommendations_html, unsafe_allow_html=True)

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
    load_css()
    
    # Display logo at the very top of the app
    display_logo()
    
    # Log session state at the beginning of a run for debugging narrative
    logger.info(f"APP.PY (main start): st.session_state.generated_narrative is: {st.session_state.get('generated_narrative')}")
    logger.info(f"APP.PY (main start): st.session_state.edited_narrative is: {st.session_state.get('edited_narrative')}")
    
    # Sidebar configuration
    with st.sidebar:
        # Modern sidebar title
        st.markdown("""
        <div class="sidebar-title">
            <span class="noi-title-accent">NOI</span> Analyzer
        </div>
        """, unsafe_allow_html=True)
        
        # Modern style overrides for sidebar
        st.markdown("""
        <style>
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: rgba(16, 23, 42, 0.8) !important;
            border-right: 1px solid rgba(59, 130, 246, 0.1) !important;
        }
        
        .sidebar-title {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1.8rem !important;
            font-weight: 600 !important;
            color: #e6edf3 !important;
            margin-bottom: 1.5rem !important;
            padding-bottom: 0.5rem !important;
            border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
        }
        
        /* Sidebar headers */
        .sidebar-section-header {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1.2rem !important;
            font-weight: 500 !important;
            color: #64B5F6 !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
        }
        
        /* Sidebar subheaders */
        .sidebar-subsection-header {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1rem !important;
            font-weight: 500 !important;
            color: #e6edf3 !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # File uploaders for NOI data
        st.markdown('<div class="sidebar-section-header">Upload Documents</div>', unsafe_allow_html=True)
        
        # Upload current month actuals
        current_month_file = st.file_uploader(
            "Current Month Actuals (Required)", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="sidebar_current_month_upload",
            help="Upload your current month's financial data"
        )
        
        # Upload prior month actuals
        prior_month_file = st.file_uploader(
            "Prior Month Actuals", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="sidebar_prior_month_upload",
            help="Upload your prior month's financial data for month-over-month comparison"
        )
        
        # Upload budget
        budget_file = st.file_uploader(
            "Current Month Budget", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="sidebar_budget_upload",
            help="Upload your budget data for budget vs actuals comparison"
        )
        
        # Upload prior year actuals
        prior_year_file = st.file_uploader(
            "Prior Year Same Month", 
            type=["xlsx", "xls", "csv", "pdf"],
            key="sidebar_prior_year_upload",
            help="Upload the same month from prior year for year-over-year comparison"
        )
        
        # Property name input
        property_name = st.text_input(
            "Property Name (Optional)",
            value=st.session_state.property_name,
            help="Enter the name of the property being analyzed",
            key="sidebar_property_name_input"
        )
        
        if property_name != st.session_state.property_name:
            st.session_state.property_name = property_name
        
        # Process button
        process_clicked = st.button(
            "Process Documents", 
            type="primary",
            use_container_width=True,
            help="Process the uploaded documents to generate NOI analysis",
            key="sidebar_process_button"
        )
        
        # Options
        st.markdown('<div class="sidebar-section-header">Options</div>', unsafe_allow_html=True)
        
        # Show zero values toggle
        show_zero_values = st.checkbox(
            "Show Zero Values", 
            value=st.session_state.show_zero_values,
            help="Show metrics with zero values in the comparison tables",
            key="sidebar_show_zero_values_check"
        )
        
        if show_zero_values != st.session_state.show_zero_values:
            st.session_state.show_zero_values = show_zero_values
            st.rerun()
        
        # NOI Coach context selection
        st.markdown('<div class="sidebar-subsection-header">NOI Coach Context</div>', unsafe_allow_html=True)
        view_options = {
            "budget": "Budget Comparison",
            "prior_year": "Year-over-Year",
            "prior_month": "Month-over-Month"
        }
        selected_view = st.selectbox(
            "Select context for NOI Coach",
            options=list(view_options.keys()),
            format_func=lambda x: view_options[x],
            index=list(view_options.keys()).index(st.session_state.current_comparison_view),
            key="sidebar_noi_coach_context_select"
        )
        
        if selected_view != st.session_state.current_comparison_view:
            st.session_state.current_comparison_view = selected_view
            st.success(f"NOI Coach context set to {view_options[selected_view]}")
    
    # Main content area
    if not st.session_state.processing_completed:
        # Show welcome content when no data has been processed
        # Modern title with accent color
        st.markdown("""
        <h1 class="noi-title">
            <span class="noi-title-accent">NOI</span> Analyzer
        </h1>
        """, unsafe_allow_html=True)
        
        # Two-column layout for better space utilization
        col1, col2 = st.columns([1, 1.2])
        
        with col1:
            # Modern Upload Documents section
            st.markdown('<h2 class="section-header">Upload Documents</h2>', unsafe_allow_html=True)
            
            # Create modern file upload cards
            st.markdown('<div class="upload-container">', unsafe_allow_html=True)
            
            # Current Month Actuals (Required)
            st.markdown("""
            <div class="upload-card">
                <div class="upload-card-header">Current Month Actuals <span class="required-badge">Required</span></div>
            """, unsafe_allow_html=True)
            current_month_file = st.file_uploader(
                "", 
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_current_month_upload",
                help="Upload your current month's financial data"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Prior Month Actuals
            st.markdown("""
            <div class="upload-card">
                <div class="upload-card-header">Prior Month Actuals</div>
            """, unsafe_allow_html=True)
            prior_month_file = st.file_uploader(
                "", 
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_prior_month_upload",
                help="Upload your prior month's financial data for month-over-month comparison"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Current Month Budget
            st.markdown("""
            <div class="upload-card">
                <div class="upload-card-header">Current Month Budget</div>
            """, unsafe_allow_html=True)
            budget_file = st.file_uploader(
                "", 
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_budget_upload",
                help="Upload your budget data for budget vs actuals comparison"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Prior Year Same Month
            st.markdown("""
            <div class="upload-card">
                <div class="upload-card-header">Prior Year Same Month</div>
            """, unsafe_allow_html=True)
            prior_year_file = st.file_uploader(
                "", 
                type=["xlsx", "xls", "csv", "pdf"],
                key="main_prior_year_upload",
                help="Upload the same month from prior year for year-over-year comparison"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Property name input with modern styling
            st.markdown('<div class="upload-card">', unsafe_allow_html=True)
            st.markdown('<div class="upload-card-header">Property Information</div>', unsafe_allow_html=True)
            property_name = st.text_input(
                "Property Name (Optional)",
                value=st.session_state.property_name,
                help="Enter the name of the property being analyzed",
                key="main_property_name_input"
            )
            
            if property_name != st.session_state.property_name:
                st.session_state.property_name = property_name
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Modern process button
            st.markdown("""
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
            """, unsafe_allow_html=True)
            
            # Process button
            process_clicked = st.button(
                "Process Documents", 
                type="primary",
                use_container_width=True,
                help="Process the uploaded documents to generate NOI analysis",
                key="main_process_button"
            )
        
        with col2:
            # Enhanced Instructions section
            st.markdown("""
            <div class="info-card">
                <h3 class="info-card-header">Instructions:</h3>
                <ol class="info-list">
                    <li>Upload your financial documents using the file uploaders</li>
                    <li>At minimum, upload a <span class="highlight">Current Month Actuals</span> file</li>
                    <li>For comparative analysis, upload additional files (Prior Month, Budget, Prior Year)</li>
                    <li>Click "<span class="highlight">Process Documents</span>" to analyze the data</li>
                    <li>View the results in the analysis tabs</li>
                    <li>Export your results as PDF or Excel using the export options</li>
                </ol>
                <p style="color: #e6edf3; font-style: italic; font-size: 0.9rem; background-color: rgba(59, 130, 246, 0.1); padding: 0.75rem; border-radius: 6px;">Note: Supported file formats include Excel (.xlsx, .xls), CSV, and PDF</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced Features section
            st.markdown("<h2 class='section-header'>Features</h2>", unsafe_allow_html=True)

            features_html = """
            <div class="card-container">
                <div class="feature-list">
                    <div class="feature-item">
                        <div class="feature-number">1</div>
                        <div class="feature-content">
                            <div class="feature-title">Comparative Analysis</div>
                            <div class="feature-description">Compare current performance against budget, prior month, and prior year</div>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <div class="feature-number">2</div>
                        <div class="feature-content">
                            <div class="feature-title">Financial Insights</div>
                            <div class="feature-description">AI-generated analysis of key metrics and trends</div>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <div class="feature-number">3</div>
                        <div class="feature-content">
                            <div class="feature-title">NOI Coach</div>
                            <div class="feature-description">Ask questions about your financial data and get AI-powered insights</div>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <div class="feature-number">4</div>
                        <div class="feature-content">
                            <div class="feature-title">Export Options</div>
                            <div class="feature-description">Save results as PDF or Excel for sharing and reporting</div>
                        </div>
                    </div>
                </div>
            </div>
            """
            st.markdown(features_html, unsafe_allow_html=True)
    else:
        # Show results after processing
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
                    display_unified_insights(st.session_state.insights)
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
            if not current_month_file:
                show_processing_status("Current Month Actuals file is required. Please upload it to proceed.", status_type="error")
                st.session_state.processing_completed = False # Ensure it's false if we exit early
                return
                
            st.session_state.current_month_actuals = current_month_file
            st.session_state.prior_month_actuals = prior_month_file
            st.session_state.current_month_budget = budget_file
            st.session_state.prior_year_actuals = prior_year_file

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

            # Process the data if it's valid
            if raw_consolidated_data and isinstance(raw_consolidated_data, dict) and not raw_consolidated_data.get('error'):
                logger.info("APP.PY: Condition to transform data met. Calling calculate_noi_comparisons.")
                try:
                    transformed_data = calculate_noi_comparisons(raw_consolidated_data)
                    logger.info(f"APP.PY: calculate_noi_comparisons returned. Transformed_data type: {type(transformed_data)}. Keys: {list(transformed_data.keys()) if isinstance(transformed_data, dict) else 'Not a dict'}")
                    
                    # Log the month_vs_prior data if available
                    if isinstance(transformed_data, dict) and "month_vs_prior" in transformed_data:
                        mvp_data = transformed_data["month_vs_prior"]
                        logger.info(f"APP.PY: transformed_data['month_vs_prior'] type: {type(mvp_data)}. Keys: {list(mvp_data.keys()) if isinstance(mvp_data, dict) else 'Not a dict'}")
                        if isinstance(mvp_data, dict):
                            try:
                                logger.info(f"APP.PY: Snippet of transformed_data['month_vs_prior']: {summarize_data_for_log(mvp_data)}")
                                logger.debug(f"APP.PY: Full transformed_data['month_vs_prior']: {json.dumps(mvp_data, default=str, indent=2)}")
                            except Exception as e_log_snippet_mvp:
                                logger.error(f"APP.PY: Error logging transformed_data['month_vs_prior'] snippet: {e_log_snippet_mvp}")
                    else:
                        logger.warning("APP.PY: 'month_vs_prior' key missing in transformed_data or transformed_data is not a dict.")

                    # Save the transformed data to session state
                    st.session_state.comparison_results = transformed_data
                    logger.info(f"APP.PY: st.session_state.comparison_results assigned. Type: {type(st.session_state.comparison_results)}. Keys: {list(st.session_state.comparison_results.keys()) if isinstance(st.session_state.comparison_results, dict) else 'Not a dict'}")
                    
                    # Generate insights and narrative only if comparison results are valid
                    if not st.session_state.comparison_results.get("error"):
                        logger.info("APP.PY: comparison_results seem okay. Generating insights and narrative.")
                        show_processing_status("Generating insights and narrative...", is_running=True)
                        
                        # Optional debugging of comparison structure
                        enable_structure_debug = True  # Set to False to disable detailed structure logging
                        if enable_structure_debug:
                            logger.info(f"APP.PY: Calling debug_comparison_structure with st.session_state.comparison_results. Keys: {list(st.session_state.comparison_results.keys())}")
                            debug_comparison_structure(st.session_state.comparison_results)
                        
                        # Generate insights
                        try:
                            insights = generate_insights_with_gpt(st.session_state.comparison_results)
                            # Create a properly structured insights dictionary
                            structured_insights = {
                                "summary": insights.get("summary", "No summary available"),
                                "performance": insights.get("performance", []),
                                "recommendations": insights.get("recommendations", [])
                            }
                            
                            # Store the insights in session state
                            st.session_state.insights = structured_insights
                            logger.info(f"Structured insights keys: {list(structured_insights.keys())}")
                        except Exception as e_insights:
                            logger.error(f"Error generating insights: {e_insights}")
                            st.session_state.insights = {
                                "summary": "Error generating insights",
                                "performance": [],
                                "recommendations": []
                            }
                        
                        # Generate narrative
                        try:
                            narrative = create_narrative(st.session_state.comparison_results, st.session_state.property_name)
                            if narrative and isinstance(narrative, str):
                                st.session_state.generated_narrative = narrative
                                logger.info(f"Narrative generated successfully: {len(narrative)} characters")
                            else:
                                logger.warning(f"create_narrative returned invalid data: {type(narrative)}")
                                st.session_state.generated_narrative = "Unable to generate narrative due to data issues."
                        except Exception as e_narrative:
                            logger.error(f"Error generating narrative: {e_narrative}")
                            st.session_state.generated_narrative = "An error occurred while generating the narrative."
                        
                        # Mark processing as completed
                        st.session_state.processing_completed = True
                        show_processing_status("Documents processed successfully!", status_type="success")
                    else:
                        st.session_state.processing_completed = False
                        show_processing_status(f"Error in data processing: {st.session_state.comparison_results.get('error')}", status_type="error")
                except Exception as e_calc:
                    logger.error(f"APP.PY: Error during calculate_noi_comparisons: {str(e_calc)}", exc_info=True)
                    st.session_state.comparison_results = {"error": f"Calculation error: {str(e_calc)}"}
                    st.session_state.processing_completed = False
                    show_processing_status(f"Calculation error: {str(e_calc)}", status_type="error")
            elif isinstance(raw_consolidated_data, dict) and raw_consolidated_data.get('error'):
                logger.error(f"APP.PY: Error reported by process_all_documents: {raw_consolidated_data.get('error')}")
                st.session_state.comparison_results = raw_consolidated_data
                st.session_state.processing_completed = False
                show_processing_status(f"Error: {raw_consolidated_data.get('error')}", status_type="error")
            else:
                logger.warning(f"APP.PY: Condition to transform data NOT met or raw_consolidated_data is not as expected. raw_consolidated_data type: {type(raw_consolidated_data)}")
                st.session_state.comparison_results = {"error": "No data from document processing or unexpected data structure."}
                st.session_state.processing_completed = False
                show_processing_status("Error: No data from document processing or unexpected data structure.", status_type="error")
            
            logger.info(f"APP.PY: --- Document Processing END --- processing_completed: {st.session_state.processing_completed}")
            # Force rerun to refresh UI
            st.experimental_rerun()
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

# Run the main function when the script is executed directly
if __name__ == "__main__":
    main()

