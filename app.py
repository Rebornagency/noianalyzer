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

from utils.helpers import format_for_noi_comparison
from noi_calculations import calculate_noi_comparisons
from noi_tool_batch_integration import process_all_documents
from fixed_ai_extraction import extract_noi_data
from ai_insights_gpt import generate_insights_with_gpt
from config import get_openai_api_key, get_extraction_api_url, get_api_key, save_api_settings

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

# Set page configuration
st.set_page_config(
    page_title="NOI Analyzer Enhanced",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Load custom CSS
def load_css():
    with open(os.path.join(os.path.dirname(__file__), "static/css/reborn_theme.css")) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Display comparison tab
def display_comparison_tab(tab_data: Dict[str, Any], prior_key_suffix: str, name_suffix: str):
    """
    Display a comparison tab with KPI cards and detailed metrics.
    
    Args:
        tab_data: Comparison data for the tab
        prior_key_suffix: Suffix for prior period keys (e.g., 'prior', 'budget', 'prior_year')
        name_suffix: Display name for the prior period (e.g., 'Prior Month', 'Budget', 'Prior Year')
    """
    # Get current data
    current_data = tab_data.get("current", {})
    if not current_data:
        st.warning(f"No current data available for {name_suffix} comparison.")
        return
        
    # Log the data structure for debugging
    logger.info(f"display_comparison_tab called with {name_suffix} comparison")
    logger.info(f"tab_data keys: {list(tab_data.keys())}")
    logger.info(f"current_data keys: {list(current_data.keys())}")
    
    # Create columns for KPI cards
    col1, col2, col3 = st.columns(3)
    
    # Display KPI cards
    with col1:
        # Current value
        current_noi = current_data.get("noi", 0.0)
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-title">Current</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">${current_noi:,.0f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        # Prior period value
        prior_noi = tab_data.get(f"noi_{prior_key_suffix}", 0.0)
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-title">{name_suffix}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">${prior_noi:,.0f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        # Change
        change_val = tab_data.get("noi_change", tab_data.get("noi_variance", 0.0))
        percent_change = tab_data.get("noi_percent_change", tab_data.get("noi_percent_variance", 0.0))
        
        # Determine color based on change
        change_class = "positive" if change_val > 0 else "negative" if change_val < 0 else "neutral"
        change_sign = "+" if change_val > 0 else ""
        
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-title">Change</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value {change_class}">{change_sign}{percent_change:.1f}%</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-label">${change_val:,.0f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Create DataFrame for data
    metrics = ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"]
    data_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]

    df_data = []
    for key, name in zip(data_keys, metrics):
        current_val = current_data.get(key, 0.0)
        prior_val = tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_budget", 0.0))
        change_val = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance", 0.0))
        percent_change = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance", 0.0))
        
        # Skip zero values if show_zero_values is False
        if not st.session_state.show_zero_values and current_val == 0 and prior_val == 0:
            continue
            
        df_data.append({
            "Metric": name,
            "Current": current_val,
            name_suffix: prior_val,
            "Change ($)": change_val,
            "Change (%)": percent_change
        })

    # Create DataFrame for display
    if not df_data:
        st.info("No data available for display. Try enabling 'Show Zero Values' in the sidebar.")
        return
        
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

        # Display table
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.dataframe(df_display, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except KeyError as e:
        logger.error(f"KeyError in DataFrame operation: {str(e)}")
        st.error(f"Error accessing DataFrame column: {str(e)}")
        # Display the raw data as a fallback
        st.json(df_data)
        return
    except Exception as e:
        logger.error(f"Error formatting DataFrame: {str(e)}")
        st.error(f"Error formatting data for display: {str(e)}")
        # Display the raw data as a fallback
        st.json(df_data)
        return

    try:
        # Create bar chart for visual comparison
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Create bar chart for visual comparison
        fig = go.Figure()

        # Add current period bars
        fig.add_trace(go.Bar(
            x=df["Metric"],
            y=df["Current"],
            name="Current",
            marker_color='#0D6EFD'
        ))

        # Add prior period bars
        fig.add_trace(go.Bar(
            x=df["Metric"],
            y=df[name_suffix],
            name=name_suffix,
            marker_color='#6C757D'
        ))

        # Update layout
        fig.update_layout(
            barmode='group',
            title=f"Current vs {name_suffix}",
            xaxis_title="Metric",
            yaxis_title="Amount ($)",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(
                family="Inter, sans-serif",
                size=12,
                color="white"
            ),
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # Add dollar sign to y-axis labels
        fig.update_yaxes(tickprefix="$")

        # Display chart
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        st.error(f"Error creating chart: {str(e)}")


# Display NOI comparisons
def display_noi_comparisons(comparison_results: Dict[str, Any]):
    """
    Display NOI comparisons with tabs for different comparison types.
    
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
    
    # Display comparison tabs
    with tab1:
        if "actual_vs_budget" in comparison_results:
            try:
                display_comparison_tab(comparison_results["actual_vs_budget"], "budget", "Budget")
            except Exception as e:
                logger.error(f"Error in Budget comparison tab: {str(e)}")
                st.error(f"Error displaying Budget comparison: {str(e)}")
        else:
            st.info("No budget data available for comparison.")
    with tab2:
        if "year_vs_year" in comparison_results:
            try:
                display_comparison_tab(comparison_results["year_vs_year"], "prior_year", "Prior Year")
            except Exception as e:
                logger.error(f"Error in Prior Year comparison tab: {str(e)}")
                st.error(f"Error displaying Prior Year comparison: {str(e)}")
        else:
            st.info("No prior year data available for comparison.")
    with tab3:
        if "month_vs_prior" in comparison_results:
            try:
                display_comparison_tab(comparison_results["month_vs_prior"], "prior", "Prior Month")
            except Exception as e:
                logger.error(f"Error in Prior Month comparison tab: {str(e)}")
                st.error(f"Error displaying Prior Month comparison: {str(e)}")
        else:
            st.info("No prior month data available for comparison.")


def generate_pdf_report(comparison_results: Dict[str, Any], property_name: str = "Property") -> Optional[str]:
    """
    Generate a PDF report from the comparison results.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        property_name: Name of the property
        
    Returns:
        Path to the generated PDF file or None if generation failed
    """
    # This is a placeholder for future PDF generation functionality
    return None


def display_insights(insights: Dict[str, Any], property_name: str = "Property"):
    """
    Display AI-generated insights.
    
    Args:
        insights: Dictionary with insights generated by GPT
        property_name: Name of the property
    """
    if not insights:
        st.warning("No AI insights available.")
        return
        
    st.markdown('<h2 class="section-header">AI-Generated Insights</h2>', unsafe_allow_html=True)
    
    # Display summary
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>Executive Summary</h3>', unsafe_allow_html=True)
    st.markdown(f'<p class="body-text">{insights.get("summary", "No summary available.")}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create columns for performance insights and recommendations
    col1, col2 = st.columns(2)
    
    # Display performance insights
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3>Key Performance Insights</h3>', unsafe_allow_html=True)
        
        performance_insights = insights.get("performance", [])
        if performance_insights:
            for insight in performance_insights:
                st.markdown(f'<p class="insight-item">• {insight}</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="body-text">No performance insights available.</p>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display recommendations
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3>Actionable Recommendations</h3>', unsafe_allow_html=True)
        
        recommendations = insights.get("recommendations", [])
        if recommendations:
            for recommendation in recommendations:
                st.markdown(f'<p class="insight-item">• {recommendation}</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="body-text">No recommendations available.</p>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)


def main():
    """
    Main function to run the Streamlit app.
    """
    # Load custom CSS
    load_css()
    
    # Display logo and title
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("static/images/reborn_logo.png", width=100)
    with col2:
        st.markdown('<h1 class="main-title">NOI Analyzer Enhanced</h1>', unsafe_allow_html=True)
    
    # Get property name from session state or set default
    property_name = st.session_state.get("property_name", "")
    
    # Sidebar
    with st.sidebar:
        st.image("static/images/reborn_logo.png", width=100)
        st.markdown('<h2 class="sidebar-header">Property Information</h2>', unsafe_allow_html=True)
        
        # Document Upload Section
        st.markdown('<h2 class="sidebar-header">Document Upload</h2>', unsafe_allow_html=True)
        st.markdown('<p class="sidebar-text">Upload your financial documents for analysis.</p>', unsafe_allow_html=True)
        
        # Current Month Actuals (Required)
        st.markdown('<h3 class="sidebar-subheader">Current Month Actuals (Required)</h3>', unsafe_allow_html=True)
        current_month_actuals = st.file_uploader(
            "Upload current month actuals",
            type=["pdf", "xlsx", "xls", "csv"],
            key="current_month_actuals_uploader"
        )
        if current_month_actuals:
            st.session_state.current_month_actuals = current_month_actuals
            st.success(f"✅ {current_month_actuals.name}")

        # Prior Month Actuals (Optional)
        st.markdown('<h3 class="sidebar-subheader">Prior Month Actuals (Optional)</h3>', unsafe_allow_html=True)
        prior_month_actuals = st.file_uploader(
            "Upload prior month actuals",
            type=["pdf", "xlsx", "xls", "csv"],
            key="prior_month_actuals_uploader"
        )
        if prior_month_actuals:
            st.session_state.prior_month_actuals = prior_month_actuals
            st.success(f"✅ {prior_month_actuals.name}")

        # Current Month Budget (Optional)
        st.markdown('<h3 class="sidebar-subheader">Current Month Budget (Optional)</h3>', unsafe_allow_html=True)
        current_month_budget = st.file_uploader(
            "Upload current month budget",
            type=["pdf", "xlsx", "xls", "csv"],
            key="current_month_budget_uploader"
        )
        if current_month_budget:
            st.session_state.current_month_budget = current_month_budget
            st.success(f"✅ {current_month_budget.name}")

        # Prior Year Actuals (Optional)
        st.markdown('<h3 class="sidebar-subheader">Prior Year Actuals (Optional)</h3>', unsafe_allow_html=True)
        prior_year_actuals = st.file_uploader(
            "Upload prior year actuals",
            type=["pdf", "xlsx", "xls", "csv"],
            key="prior_year_actuals_uploader"
        )
        if prior_year_actuals:
            st.session_state.prior_year_actuals = prior_year_actuals
            st.success(f"✅ {prior_year_actuals.name}")
        
        # Process Documents Button
        if st.button("Process Documents", key="process_docs_upload_section"):
            if not st.session_state.current_month_actuals:
                st.error("Current Month Actuals is required.")
            else:
                st.session_state.processing_completed = False
                st.session_state.comparison_results = None
                st.session_state.insights = None

                # Process documents
                with st.spinner("Processing documents..."):
                    try:
                        consolidated_data = process_all_documents()
                        
                        # Calculate comparisons if processing was successful
                        if st.session_state.processing_completed:
                            st.session_state.comparison_results = calculate_noi_comparisons(consolidated_data)
                            
                            # Generate insights if OpenAI API key is provided
                            openai_key = get_openai_api_key()
                            if openai_key and len(openai_key) > 10:
                                st.session_state.insights = generate_insights_with_gpt(
                                    st.session_state.comparison_results,
                                    property_name
                                )
                    except Exception as e:
                        logger.error(f"Error processing documents: {str(e)}")
                        st.error(f"Error processing documents: {str(e)}")

                # Rerun to update the main content area
                st.rerun()
        
        # Property information
        st.markdown('<h2 class="sidebar-header">Property Information</h2>', unsafe_allow_html=True)
        property_name = st.text_input("Property Name (Optional)", value=property_name)
        st.session_state.property_name = property_name
        
        property_id = st.text_input("Property ID (Optional)")
        
        # Display options
        st.markdown('<h2 class="sidebar-header">Display Options</h2>', unsafe_allow_html=True)
        show_zero_values = st.checkbox("Show Zero Values", value=st.session_state.show_zero_values)
        st.session_state.show_zero_values = show_zero_values
        
        # API configuration
        st.markdown('<h2 class="sidebar-header">API Configuration</h2>', unsafe_allow_html=True)
        with st.expander("API Configuration"):
            # Get current values
            current_api_url = get_extraction_api_url()
            current_api_key = get_api_key()
            current_openai_key = get_openai_api_key()
            
            # Remove /extract from display URL
            if current_api_url and current_api_url.endswith('/extract'):
                display_url = current_api_url[:-8]
            else:
                display_url = current_api_url
                
            # API URL
            st.markdown('<div class="api-config-label">Extraction API URL</div>', unsafe_allow_html=True)
            api_url = st.text_input("", value=display_url, key="api_url_input", help="URL of the extraction API service")
            
            # API Key
            st.markdown('<div class="api-config-label">API Key</div>', unsafe_allow_html=True)
            api_key = st.text_input("", value=current_api_key, key="api_key_input", type="password", help="API key for the extraction service")
            
            # OpenAI API Key
            st.markdown('<div class="api-config-label">OpenAI API Key</div>', unsafe_allow_html=True)
            openai_api_key = st.text_input("", value=current_openai_key, key="openai_api_key_input", type="password", help="OpenAI API key for generating insights")
            
            # Save button
            if st.button("Save API Settings", key="save_api_settings_btn"):
                save_api_settings(openai_api_key, api_url, api_key)
                st.success("API settings saved successfully!")

        # Process button
        process_button = st.button("Process Documents", key="process_docs_sidebar", use_container_width=True)
        if process_button:
            if not st.session_state.current_month_actuals:
                st.error("Current Month Actuals is required.")
            else:
                st.session_state.processing_completed = False
                st.session_state.comparison_results = None
                st.session_state.insights = None
                st.session_state.processing_status = "processing"

                # Initialize progress tracking
                st.session_state.progress_bar = st.progress(0)
                st.session_state.status_text = st.empty()

                # Process documents
                with st.spinner("Processing documents..."):
                    consolidated_data = process_all_documents()

                    # Calculate comparisons if processing was successful
                    if st.session_state.processing_completed:
                        st.session_state.comparison_results = calculate_noi_comparisons(consolidated_data)
                        
                        # Log the comparison results structure
                        logger.info(f"Calculated comparison results with keys: {list(st.session_state.comparison_results.keys())}")

                        # Generate insights if OpenAI API key is provided
                        openai_key = get_openai_api_key()
                        if openai_key and len(openai_key) > 10:
                            st.session_state.status_text.text("Generating AI insights...")
                            st.session_state.progress_bar.progress(90)
                            
                            # Log the call to generate_insights_with_gpt
                            logger.info(f"Calling generate_insights_with_gpt with OpenAI key: {'*' * (len(openai_key) - 5)}{openai_key[-5:]}")
                            logger.info(f"Comparison results keys: {list(st.session_state.comparison_results.keys())}")
                            
                            try:
                                st.session_state.insights = generate_insights_with_gpt(
                                    st.session_state.comparison_results,
                                    property_name
                                )
                                logger.info(f"Generated insights: {st.session_state.insights is not None}")
                            except Exception as e:
                                logger.error(f"Error generating insights: {str(e)}")
                                st.error(f"Error generating insights: {str(e)}")
                                st.session_state.insights = None
                                
                            st.session_state.progress_bar.progress(100)
                            st.session_state.status_text.text("Processing complete!")
                        else:
                            logger.warning("Skipping AI insights generation - no valid OpenAI API key")
                            st.session_state.progress_bar.progress(100)
                            st.session_state.status_text.text("Processing complete! (AI insights skipped - no API key)")

                # Clean up progress tracking
                if 'progress_bar' in st.session_state:
                    st.session_state.progress_bar.empty()
                if 'status_text' in st.session_state:
                    st.session_state.status_text.empty()
                    
                st.session_state.processing_status = "complete"

                # Rerun to update the main content area
                st.rerun()

        # Clear data button
        if st.session_state.processing_completed:
            if st.button("Clear Data", key="clear_data_btn", use_container_width=True):
                # Reset session state
                st.session_state.current_month_actuals = None
                st.session_state.prior_month_actuals = None
                st.session_state.current_month_budget = None
                st.session_state.prior_year_actuals = None
                st.session_state.consolidated_data = None
                st.session_state.processing_completed = False
                st.session_state.comparison_results = None
                st.session_state.insights = None
                st.session_state.processing_status = None
                
                # Rerun to update the UI
                st.rerun()

    # Main content area
    if st.session_state.processing_completed and st.session_state.comparison_results:
        try:
            # Display NOI comparisons
            display_noi_comparisons(st.session_state.comparison_results)

            # Display AI insights if available
            if st.session_state.insights:
                display_insights(st.session_state.insights, property_name)
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            st.error(f"Error displaying results: {str(e)}")
            # Display raw data as fallback
            st.subheader("Raw Data (Error Fallback)")
            st.json(st.session_state.comparison_results)
            
        # Add export options
        st.markdown('<h2 class="section-header">Export Options</h2>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Export to Excel", key="export_excel_btn", use_container_width=True):
                st.info("Excel export functionality will be available in the next update.")
        with col2:
            if st.button("Export to CSV", key="export_csv_btn", use_container_width=True):
                st.info("CSV export functionality will be available in the next update.")
        with col3:
            if st.button("Share Report", key="share_report_btn", use_container_width=True):
                st.info("Report sharing functionality will be available in the next update.")
    else:
        # Display instructions when no data is processed
        if st.session_state.processing_status == "processing":
            st.info("Processing documents... Please wait.")
        else:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="body-text">Upload your financial documents using the sidebar and click \'Process Documents\' to begin analysis.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Display sample images or instructions
            st.markdown('<h2 class="section-header">How to use this tool:</h2>', unsafe_allow_html=True)
            
            st.markdown("""
            1. **Upload Documents**: Start by uploading your current month actuals (required). For more comprehensive analysis, also upload prior month actuals, budget, and prior year actuals.

            2. **Process Documents**: Click the 'Process Documents' button to extract and analyze the financial data.

            3. **Review Results**: Examine the comparative analysis and AI-generated insights to understand your property's financial performance.

            4. **Export or Share**: Use the export options to download reports or share insights with your team.
            """)
            
            # Add sample data option
            st.markdown('<h3>Try with Sample Data</h3>', unsafe_allow_html=True)
            if st.button("Load Sample Data", key="load_sample_data_btn", use_container_width=True):
                st.info("Sample data functionality will be available in the next update.")


if __name__ == "__main__":
    main()
