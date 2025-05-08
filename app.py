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

from utils.helpers import format_for_noi_comparison
from noi_calculations import calculate_noi_comparisons
from noi_tool_batch_integration import process_all_documents
from ai_extraction import extract_noi_data
from ai_insights_gpt import generate_insights_with_gpt, ask_noi_coach
from financial_storyteller import create_narrative
from storyteller_display import display_financial_narrative, display_narrative_in_tabs
from config import get_openai_api_key, get_extraction_api_url, get_api_key, save_api_settings
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

# Import the logo function
from reborn_logo import get_reborn_logo_base64

# Logo display function - updated to use direct embedding with better error handling
def display_logo():
    """Display the Reborn logo in the Streamlit app"""
    try:
        # Read the logo directly from file if possible
        logo_path = os.path.join(os.path.dirname(__file__), "Reborn Logo.jpeg")
        
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_bytes = f.read()
                logo_base64 = base64.b64encode(logo_bytes).decode("utf-8")
                logger.info(f"Successfully read logo from {logo_path}")
        else:
            # Fallback to embedded base64 logo
            logger.info("Using embedded base64 logo as fallback")
            logo_base64 = get_reborn_logo_base64()
        
        # Direct embedding of the logo with proper sizing and alignment
        logo_html = f"""
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 25px; margin-top: 10px;">
            <img src="data:image/jpeg;base64,{logo_base64}" width="180px" alt="Reborn Logo" style="object-fit: contain;">
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
        # Read the logo directly from file
        logo_path = os.path.join(os.path.dirname(__file__), "static/images/reborn_logo.png")
        
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode("utf-8")
                logger.info(f"Successfully read logo from {logo_path}")
        else:
            # Fallback to embedded base64 logo
            logger.warning(f"Logo file not found at {logo_path}, using fallback")
            logo_b64 = get_reborn_logo_base64()
        
        # Inline logo with proper sizing and alignment
        logo_html = f"""
        <div style="display:flex; align-items:center; margin:0; padding:0;">
            <img src="data:image/png;base64,{logo_b64}"
                 height="32px"
                 style="background:transparent; object-fit:contain; margin-right:8px;"
                 alt="Reborn Logo" />
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
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
                logger.info(f"Successfully loaded CSS from {css_path}")
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
        h1, h2, h3, h4, h5 {color: #4DB6AC !important;}
        .section-header {color: #4DB6AC; font-size: 1.5rem; margin-top: 2rem;}
        .positive-change {color: #22C55E !important;}
        .negative-change {color: #EF4444 !important;}
        </style>
        """, unsafe_allow_html=True)

# Debug helper function to diagnose comparison structure issues
def debug_comparison_structure(comparison_results: Dict[str, Any]) -> None:
    """
    Debug function to analyze and log the structure of comparison results
    """
    if not comparison_results:
        logger.error("No comparison results available for debugging")
        return
        
    logger.info("=== COMPARISON RESULTS STRUCTURE DEBUG ===")
    logger.info(f"Top level keys: {list(comparison_results.keys())}")
    
    # Check for current data
    if "current" in comparison_results:
        logger.info(f"Current data keys: {list(comparison_results['current'].keys())}")
        
        # Check for financial metrics in current data
        financial_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]
        for key in financial_keys:
            if key in comparison_results["current"]:
                logger.info(f"Current.{key} = {comparison_results['current'][key]}")
            else:
                logger.warning(f"Missing key in current data: {key}")
    else:
        logger.warning("No 'current' key in comparison results")
    
    # Check comparison data sections
    for section in ["month_vs_prior", "actual_vs_budget", "year_vs_year"]:
        if section in comparison_results:
            logger.info(f"{section} keys: {list(comparison_results[section].keys())}")
            
            # Check for common patterns in the data
            patterns = [
                "_current",    # current values
                "_compare",    # comparison values 
                "_change",     # absolute change
                "_percent_change"  # percentage change
            ]
            
            found_patterns = {}
            for pattern in patterns:
                matches = [key for key in comparison_results[section].keys() if key.endswith(pattern)]
                found_patterns[pattern] = matches
                
                if matches:
                    logger.info(f"  Found {len(matches)} keys with pattern '{pattern}': {matches[:3]}...")
                    # Show sample values
                    if matches:
                        logger.info(f"  Sample value ({matches[0]}): {comparison_results[section][matches[0]]}")
                else:
                    logger.warning(f"  No keys found with pattern '{pattern}'")
        else:
            logger.warning(f"Missing comparison section: {section}")
    
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

# Display comparison tab
def display_comparison_tab(tab_data: Dict[str, Any], prior_key_suffix: str, name_suffix: str):
    """
    Display a comparison tab with KPI cards and detailed metrics.
    
    Args:
        tab_data: Comparison data for the tab
        prior_key_suffix: Suffix for prior period keys (e.g., 'prior', 'budget', 'prior_year')
        name_suffix: Display name for the prior period (e.g., 'Prior Month', 'Budget', 'Prior Year')
    """
    # Log detailed debugging information
    logger.info(f"Starting display_comparison_tab for {name_suffix} comparison")
    logger.info(f"tab_data keys: {list(tab_data.keys())}")
    
    # Get current data from the tab_data or from the 'current' key in comparison_results
    current_data = {}
    if "current" in tab_data:
        current_data = tab_data["current"]
        logger.info(f"Found 'current' data with keys: {list(current_data.keys())}")
    
    # Check if we have the expected data format
    has_current_format = False
    for key in ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]:
        if key in current_data:
            has_current_format = True
            break
    
    logger.info(f"Current data has standard format: {has_current_format}")
    
    # If we don't have the expected format, we need to extract data from the comparison structure
    if not has_current_format and any(f"{key}_current" in tab_data for key in ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]):
        logger.info(f"Using alternative data format for {name_suffix} comparison")
        for key in ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]:
            if f"{key}_current" in tab_data:
                current_data[key] = tab_data.get(f"{key}_current", 0.0)
        
        logger.info(f"Extracted current data with keys: {list(current_data.keys())}")
    
    if not current_data:
        logger.warning(f"No current data available for {name_suffix} comparison")
        st.warning(f"No current data available for {name_suffix} comparison.")
        return
        
    # Log the data structure for debugging
    logger.info(f"display_comparison_tab processing {name_suffix} comparison")
    logger.info(f"current_data keys: {list(current_data.keys())}")
    logger.info(f"current_data NOI value: {current_data.get('noi', 'Not found')}")
    
    # Look for prior values in different formats
    prior_keys = [f"noi_{prior_key_suffix}", "noi_compare", "noi_budget", "noi_prior", "noi_prior_year"]
    found_prior_keys = [key for key in prior_keys if key in tab_data]
    logger.info(f"Looking for prior NOI in keys: {prior_keys}")
    logger.info(f"Found prior NOI keys: {found_prior_keys}")
    
    if found_prior_keys:
        logger.info(f"Prior NOI value ({found_prior_keys[0]}): {tab_data.get(found_prior_keys[0], 'Not found')}")
    
    # Create columns for KPI cards
    col1, col2, col3 = st.columns(3)
    
    # Display KPI cards using Streamlit's metric component instead of custom HTML
    with col1:
        # Current value
        current_noi = current_data.get("noi", 0.0)
        st.metric(label="Current", value=f"${current_noi:,.0f}")
        
    with col2:
        # Prior period value - handle both formats (_prior_key_suffix or _compare)
        prior_noi = tab_data.get(f"noi_{prior_key_suffix}", tab_data.get("noi_compare", 0.0))
        st.metric(label=f"{name_suffix}", value=f"${prior_noi:,.0f}")
        
    with col3:
        # Change - handle both formats
        change_val = tab_data.get("noi_change", tab_data.get("noi_variance", 0.0))
        percent_change = tab_data.get("noi_percent_change", tab_data.get("noi_percent_variance", 0.0))
        
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
        current_val = current_data.get(key, tab_data.get(f"{key}_current", 0.0))
        prior_val = tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_compare", 0.0))
        change_val = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance", 0.0))
        percent_change = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance", 0.0))
        
        # Debug logging for data extraction
        logger.debug(f"Metric: {name}, Current: {current_val}, Prior: {prior_val}, Change: {change_val}, %Change: {percent_change}")
        
        # Skip zero values if show_zero_values is False
        if not st.session_state.show_zero_values and current_val == 0 and prior_val == 0:
            continue
            
        df_data.append({
            "Metric": name,
            "Current": current_val,
            name_suffix: prior_val,
            "Change ($)": change_val,
            "Change (%)": percent_change,
            # Add business impact direction for proper color coding
            "Direction": "inverse" if name in ["Vacancy Loss", "Total OpEx"] else "normal"
        })

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
            st.experimental_rerun()
            
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
            
            if any(component in current_data for component in opex_components):
                # Create DataFrame for OpEx components
                opex_df_data = []
                opex_metrics = ["Property Taxes", "Insurance", "Repairs & Maintenance", "Utilities", "Management Fees"]
                
                for key, name in zip(opex_components, opex_metrics):
                    # Handle both formats for current, prior, and change values
                    current_val = current_data.get(key, tab_data.get(f"{key}_current", 0.0))
                    prior_val = tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_compare", 0.0))
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
            
            if any(component in current_data for component in other_income_components):
                # Create DataFrame for Other Income components
                income_df_data = []
                
                for key, name in zip(other_income_components, income_metrics):
                    # Handle both formats for current, prior, and change values
                    current_val = current_data.get(key, tab_data.get(f"{key}_current", 0.0))
                    prior_val = tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_compare", 0.0))
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
            else:
                st.info("Other income breakdown is not available for this comparison.")

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
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        st.error(f"Error creating visualization: {str(e)}")
        
    try:
        # Prepare OpEx breakdown data
        opex_breakdown_data = []
        opex_breakdown_available = False
        
        opex_total = current_data.get("opex", 0)
        
        if opex_total and opex_total > 0:
            # OpEx components
            opex_components = [
                ("property_taxes", "Property Taxes"),
                ("insurance", "Insurance"),
                ("repairs_and_maintenance", "Repairs & Maintenance"),
                ("utilities", "Utilities"),
                ("management_fees", "Management Fees")
            ]
            
            # Check if we have detailed OpEx data
            has_detail = False
            for key, _ in opex_components:
                if key in current_data:
                    has_detail = True
                    break
            
            if has_detail:
                opex_breakdown_available = True
                
                for key, label in opex_components:
                    if key in current_data:
                        current_val = current_data.get(key, 0)
                        percentage = (current_val / opex_total * 100) if opex_total > 0 else 0
                        
                        # Get comparison value if available
                        if "compare" in tab_data:
                            compare_val = tab_data["compare"].get(key, 0)
                            
                            # Calculate percent change safely
                            if compare_val and compare_val != 0:
                                variance = (current_val - compare_val) / compare_val
                            else:
                                variance = 0
                        else:
                            compare_val = 0
                            variance = 0
                        
                        opex_breakdown_data.append({
                            "category": label,
                            "current": current_val,
                            "prior": compare_val,
                            "variance": variance,
                            "percentage": percentage
                        })
        
        # Calculate KPIs
        egi = current_data.get("egi", 0)
        noi = current_data.get("noi", 0)
        gpr = current_data.get("gpr", 0)
        opex = current_data.get("opex", 0)
        
        operating_expense_ratio = opex / egi if egi else 0
        noi_margin = noi / egi if egi else 0
        gross_rent_multiplier = 10  # Placeholder value
        
        kpis = {
            "egi": egi,
            "operating_expense_ratio": operating_expense_ratio,
            "noi_margin": noi_margin,
            "gross_rent_multiplier": gross_rent_multiplier
        }
        
        # Get executive summary if available
        executive_summary = ""
        if hasattr(st.session_state, "insights") and st.session_state.insights:
            executive_summary = st.session_state.insights.get("summary", "")
        
        # Include financial narrative if available
        financial_narrative = None
        if "edited_narrative" in st.session_state:
            financial_narrative = st.session_state.edited_narrative
        elif "generated_narrative" in st.session_state:
            financial_narrative = st.session_state.generated_narrative
        
        # Create context for template
        context = {
            "property_name": name_suffix,
            "datetime": datetime,
            "performance_data": {
                "egi": egi,
                "opex": opex,
                "noi": noi,
                "gpr": gpr,
                "vacancy_loss": current_data.get("vacancy_loss", 0),
                "other_income": current_data.get("other_income", 0),
                "opex_breakdown_data": opex_breakdown_data,
                "opex_breakdown_available": opex_breakdown_available,
                "kpis": kpis,
                "executive_summary": executive_summary,
                "financial_narrative": financial_narrative,
                "comparison_title": name_suffix
            },
            "comparison_results": tab_data
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
            tmp.write(html_content.encode('utf-8'))
            tmp_path = tmp.name
        
        # Convert HTML to PDF using weasyprint
        pdf_bytes = HTML(filename=tmp_path).write_pdf()
    except Exception as e:
        logger.error(f"Error in data preparation or PDF generation: {str(e)}")
        st.error(f"Error preparing data for export: {str(e)}")

# Display NOI Coach (Chat Widget)
def display_noi_coach():
    """
    Display the "Ask Your NOI Coach" chat widget with context awareness
    """
    if not st.session_state.comparison_results:
        st.warning("No financial data available. Please process documents to use the NOI Coach.")
        return
        
    st.header("Ask Your NOI Coach", anchor=False)
    
    # Determine current context label based on session state
    current_context_label = {
        "budget": "Budget vs Actual", 
        "prior_year": "Year-over-Year", 
        "prior_month": "Month-over-Month"
    }.get(st.session_state.current_comparison_view, "Budget vs Actual")
    
    # Information about data source and context with styled container
    st.markdown(f"""
    <div style="background-color: rgba(30, 41, 59, 0.8); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="color: #4DB6AC; margin-top: 0;">Your Personal NOI Advisor</h4>
        <p style="color: #F0F0F0;">Ask any question about <strong>your financial data</strong> and get AI-powered insights based on the metrics you've uploaded.</p>
        <p style="color: #F0F0F0; font-style: italic;">The NOI Coach analyzes your specific property data and is currently focused on <span style="color: #4DB6AC; font-weight: bold;">{current_context_label}</span> comparisons.</p>
        <p style="color: #F0F0F0;">Examples: "Why is my NOI down this month?", "What's driving my expense increases?", "How can I improve my vacancy rate?"</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat history
    for i, (role, message) in enumerate(st.session_state.noi_coach_history):
        with st.chat_message(role):
            st.markdown(message)
    
    # Get user input
    user_question = st.chat_input("Ask a question about your NOI metrics...")
    
    if user_question:
        # Add user message to chat history
        st.session_state.noi_coach_history.append(("user", user_question))
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_question)
        
        # Get property name
        property_name = st.session_state.property_name or "Property"
        
        # Get response from NOI Coach with enhanced loading state
        with st.chat_message("assistant"):
            # Create a placeholder for the animated loading state
            with st.status("NOI Coach is analyzing your data...", expanded=True) as status:
                st.write("Processing your financial metrics...")
                
                try:
                    # Get response with context awareness
                    response = ask_noi_coach(
                        question=user_question,
                        comparison_results=st.session_state.comparison_results,
                        current_view=st.session_state.current_comparison_view
                    )
                    
                    # Update status to complete
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                    
                    # Display the response
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.noi_coach_history.append(("assistant", response))
                    
                except Exception as e:
                    # If there's an error, show it to the user
                    status.update(label="Error in analysis", state="error", expanded=False)
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    
                    # Still add the error to chat history
                    st.session_state.noi_coach_history.append(("assistant", error_msg))
                    logger.error(f"NOI Coach error: {str(e)}")

# Display NOI comparisons with tabs
def display_noi_comparisons(comparison_results: Dict[str, Any]):
    """
    Display NOI comparisons with tabs for different comparison types and
    track which comparison is currently viewed for NOI Coach context.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
    """
    if not comparison_results:
        st.warning("No comparison results available.")
        return
        
    # Log the comparison results structure for debugging
    logger.info(f"display_noi_comparisons called with keys: {list(comparison_results.keys())}")
    
    st.markdown('<h2 class="section-header">Comparative Analysis</h2>', unsafe_allow_html=True)
    
    # Create tabs for different comparison types
    tab1, tab2, tab3 = st.tabs(["Current vs Budget", "Current vs Prior Year", "Current vs Prior Month"])
    
    # Track which tab is selected in session state for context-aware NOI Coach
    # We use this workaround since Streamlit doesn't provide a direct way to detect the active tab
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Set Budget Context", key="set_budget_tab", 
                     help="Set the NOI Coach context to Budget comparisons",
                     use_container_width=True):
            st.session_state.current_comparison_view = "budget"
            st.success("NOI Coach context set to Budget comparisons")
    
    with col2:
        if st.button("Set Prior Year Context", key="set_prior_year_tab", 
                     help="Set the NOI Coach context to Prior Year comparisons",
                     use_container_width=True):
            st.session_state.current_comparison_view = "prior_year"
            st.success("NOI Coach context set to Prior Year comparisons")
            
    with col3:
        if st.button("Set Prior Month Context", key="set_prior_month_tab", 
                     help="Set the NOI Coach context to Prior Month comparisons",
                     use_container_width=True):
            st.session_state.current_comparison_view = "prior_month"
            st.success("NOI Coach context set to Prior Month comparisons")
    
    # Display comparison tabs
    with tab1:
        if "actual_vs_budget" in comparison_results:
            try:
                # Add current data to the actual_vs_budget dict if it doesn't have it
                budget_data = comparison_results["actual_vs_budget"].copy()
                if "current" not in budget_data and "current" in comparison_results:
                    budget_data["current"] = comparison_results["current"]
                    
                display_comparison_tab(budget_data, "budget", "Budget")
            except Exception as e:
                logger.error(f"Error in Budget comparison tab: {str(e)}")
                st.error(f"Error displaying Budget comparison: {str(e)}")
        else:
            st.info("No budget data available for comparison.")
    
    with tab2:
        if "year_vs_year" in comparison_results:
            try:
                # Add current data to the year_vs_year dict if it doesn't have it
                yoy_data = comparison_results["year_vs_year"].copy()
                if "current" not in yoy_data and "current" in comparison_results:
                    yoy_data["current"] = comparison_results["current"]
                    
                display_comparison_tab(yoy_data, "prior_year", "Prior Year")
            except Exception as e:
                logger.error(f"Error in Prior Year comparison tab: {str(e)}")
                st.error(f"Error displaying Prior Year comparison: {str(e)}")
        else:
            st.info("No prior year data available for comparison.")
    
    with tab3:
        if "month_vs_prior" in comparison_results:
            try:
                # Add current data to the month_vs_prior dict if it doesn't have it
                mom_data = comparison_results["month_vs_prior"].copy()
                if "current" not in mom_data and "current" in comparison_results:
                    mom_data["current"] = comparison_results["current"]
                    
                display_comparison_tab(mom_data, "prior", "Prior Month")
            except Exception as e:
                logger.error(f"Error in Prior Month comparison tab: {str(e)}")
                st.error(f"Error displaying Prior Month comparison: {str(e)}")
        else:
            st.info("No prior month data available for comparison.")

# Main function for the NOI Analyzer application
def main():
    """
    Main function for the NOI Analyzer Enhanced application.
    Sets up the UI and coordinates all functionality.
    """
    # Display app header and logo
    display_logo()
    
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
        
        # Display tabs with comparison data
        if st.session_state.comparison_results:
            # Call our new comparison function
            display_noi_comparisons(st.session_state.comparison_results)
            
            # Display insights
            if st.session_state.insights:
                st.markdown('<h2 class="section-header">Financial Insights</h2>', unsafe_allow_html=True)
                display_insights(st.session_state.insights)
            
            # Display NOI Coach with enhanced UI
            display_noi_coach()
    
    # Process documents when button is clicked
    if process_clicked:
        # (Existing document processing code)
        st.session_state.processing_completed = True
        
        # Add call to calculate_noi_comparisons and store in session state
        # This would set st.session_state.comparison_results
        
        # Generate insights if needed
        # This would set st.session_state.insights

# Run the main function when the script is executed directly
if __name__ == "__main__":
    main()
