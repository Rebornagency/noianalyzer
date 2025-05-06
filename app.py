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
        
        # Format for Streamlit metric
        delta_value = f"{change_val:,.0f} ({percent_change:.1f}%)"
        st.metric(
            label="Change",
            value=f"-{percent_change:.1f}%" if percent_change < 0 else f"{percent_change:.1f}%",
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
            "Change (%)": percent_change
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

        # Display table
        st.dataframe(df_display, use_container_width=True)
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
        logger.info(f"Creating charts for {name_suffix} comparison")
        # Create bar chart for visual comparison
        fig = go.Figure()

        # Calculate change percentages for hover data
        change_pcts = df["Change (%)"].tolist()
        change_vals = df["Change ($)"].tolist()
        
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
            customdata=list(zip(change_vals, change_pcts)),
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
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor=arrow_color,
                borderwidth=1,
                borderpad=4,
                font=dict(color="#333", size=12)
            )

        # Update layout with modern styling
        fig.update_layout(
            barmode='group',
            title=f"Current vs {name_suffix}",
            title_font=dict(size=18, color="#333", family="Roboto, sans-serif"),
            template="plotly_white",
            plot_bgcolor='rgba(250, 250, 250, 0.9)',
            paper_bgcolor='rgba(250, 250, 250, 0.9)',
            font=dict(
                family="Roboto, sans-serif",
                size=14,
                color="#333"
            ),
            margin=dict(l=20, r=20, t=60, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="#ddd",
                borderwidth=1
            ),
            xaxis=dict(
                title="",
                tickfont=dict(size=14),
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                title="Amount ($)",
                titlefont=dict(size=14),
                tickfont=dict(size=12),
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.5)',
                zeroline=False
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Roboto, sans-serif"
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


def generate_pdf_report(comparison_results: Dict[str, Any], property_name: str = "Property") -> Optional[str]:
    """
    Generate a PDF report from the comparison results.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        property_name: Name of the property
        
    Returns:
        Path to the generated PDF file or None if generation failed
    """
    try:
        logger.info("Generating PDF report")
        
        # Extract KPIs from comparison results
        current_data = comparison_results.get("current", {})
        
        if not current_data:
            logger.warning("No current data available for PDF report")
            return None
            
        # Calculate some additional KPIs
        egi = current_data.get("egi", 0)
        opex = current_data.get("opex", 0)
        noi = current_data.get("noi", 0)
        
        operating_expense_ratio = opex / egi if egi else 0
        noi_margin = noi / egi if egi else 0
        
        # Default value for gross rent multiplier
        gross_rent_multiplier = 10.0  # Example value, would be calculated from property value
        
        kpis = {
            "egi": egi,
            "opex": opex,
            "noi": noi,
            "operating_expense_ratio": operating_expense_ratio,
            "noi_margin": noi_margin,
            "gross_rent_multiplier": gross_rent_multiplier
        }
        
        # Prepare performance data for the table
        performance_data = []
        metrics = ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"]
        data_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]
        
        # Find the comparison with most data - prioritize budget comparison
        comparison_section = None
        for section in ["actual_vs_budget", "year_vs_year", "month_vs_prior"]:
            if section in comparison_results:
                comparison_section = section
                break
                
        if not comparison_section:
            logger.warning("No comparison data available for PDF report")
            return None
            
        comparison_data = comparison_results[comparison_section]
        
        for key, metric in zip(data_keys, metrics):
            current_val = current_data.get(key, 0)
            
            # Look for prior value in different formats
            prior_val = 0
            for prior_key in [f"{key}_compare", f"{key}_prior", f"{key}_budget", f"{key}_prior_year"]:
                if prior_key in comparison_data:
                    prior_val = comparison_data[prior_key]
                    break
                    
            # Calculate variance
            variance = (current_val - prior_val) / prior_val if prior_val else 0
            
            performance_data.append({
                "metric": metric,
                "current": current_val,
                "prior": prior_val,
                "variance": variance
            })
        
        # Configure Jinja environment
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        
        # Prepare template data
        template_data = {
            'datetime': datetime,
            'property_name': property_name,
            'kpis': kpis,
            'performance_data': performance_data
        }
        
        # Render template to HTML
        html_content = template.render(**template_data)
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            # Generate PDF from HTML
            html_doc = HTML(string=html_content)
            pdf_bytes = html_doc.write_pdf()
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
            
        logger.info(f"PDF report generated successfully: {tmp_path}")
        return tmp_path
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return None

def export_to_excel(comparison_results: Dict[str, Any], property_name: str = "Property") -> Optional[bytes]:
    """
    Export comparison results to Excel file.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        property_name: Name of the property
        
    Returns:
        Excel file as bytes or None if export failed
    """
    try:
        logger.info("Exporting data to Excel")
        
        # Create an Excel writer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Current Data Sheet
            if "current" in comparison_results:
                current_data = comparison_results["current"]
                df_current = pd.DataFrame({
                    "Metric": ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"],
                    "Value": [
                        current_data.get("gpr", 0),
                        current_data.get("vacancy_loss", 0),
                        current_data.get("other_income", 0),
                        current_data.get("egi", 0),
                        current_data.get("opex", 0),
                        current_data.get("noi", 0)
                    ]
                })
                df_current.to_excel(writer, sheet_name="Current Data", index=False)
                
                # Format the sheet
                workbook = writer.book
                worksheet = writer.sheets["Current Data"]
                money_format = workbook.add_format({'num_format': '$#,##0.00'})
                worksheet.set_column('B:B', 15, money_format)
            
            # Create sheets for each comparison type
            for comparison_type, title in [
                ("actual_vs_budget", "Actual vs Budget"),
                ("year_vs_year", "Year vs Year"),
                ("month_vs_prior", "Month vs Prior Month")
            ]:
                if comparison_type in comparison_results:
                    comparison_data = comparison_results[comparison_type]
                    
                    # Create DataFrame for the comparison
                    df_data = []
                    metrics = ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"]
                    data_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]
                    
                    for key, name in zip(data_keys, metrics):
                        # Handle both formats for current, prior, and change values
                        current_val = comparison_data.get(f"{key}_current", 0.0)
                        compare_val = comparison_data.get(f"{key}_compare", 0.0)
                        change_val = comparison_data.get(f"{key}_change", 0.0)
                        percent_change = comparison_data.get(f"{key}_percent_change", 0.0)
                        
                        df_data.append({
                            "Metric": name,
                            "Current": current_val,
                            "Comparison": compare_val,
                            "Change ($)": change_val,
                            "Change (%)": percent_change
                        })
                    
                    # Create DataFrame and write to Excel
                    df_comparison = pd.DataFrame(df_data)
                    df_comparison.to_excel(writer, sheet_name=title, index=False)
                    
                    # Format the sheet
                    worksheet = writer.sheets[title]
                    money_format = workbook.add_format({'num_format': '$#,##0.00'})
                    percent_format = workbook.add_format({'num_format': '0.00%'})
                    
                    worksheet.set_column('B:D', 15, money_format)
                    worksheet.set_column('E:E', 15, percent_format)
            
            # If insights are available, add them to the Excel file
            if "insights" in st.session_state and st.session_state.insights:
                insights = st.session_state.insights
                
                # Create insights sheet
                insights_data = []
                
                # Add summary
                if "summary" in insights:
                    insights_data.append({"Category": "Summary", "Content": insights["summary"]})
                
                # Add performance insights
                if "performance" in insights and insights["performance"]:
                    for i, insight in enumerate(insights["performance"], 1):
                        insights_data.append({"Category": f"Performance Insight {i}", "Content": insight})
                
                # Add recommendations
                if "recommendations" in insights and insights["recommendations"]:
                    for i, rec in enumerate(insights["recommendations"], 1):
                        insights_data.append({"Category": f"Recommendation {i}", "Content": rec})
                
                # Create DataFrame and write to Excel
                df_insights = pd.DataFrame(insights_data)
                df_insights.to_excel(writer, sheet_name="AI Insights", index=False)
                
                # Format the insights sheet
                worksheet = writer.sheets["AI Insights"]
                worksheet.set_column('A:A', 20)
                worksheet.set_column('B:B', 70)
        
        # Get the Excel file as bytes
        output.seek(0)
        excel_data = output.getvalue()
        
        logger.info("Excel export completed successfully")
        return excel_data
        
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return None

def export_to_csv(comparison_results: Dict[str, Any], property_name: str = "Property") -> Optional[Dict[str, bytes]]:
    """
    Export comparison results to CSV files.
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        property_name: Name of the property
        
    Returns:
        Dictionary with CSV files as bytes or None if export failed
    """
    try:
        logger.info("Exporting data to CSV")
        
        csv_files = {}
        
        # Current Data CSV
        if "current" in comparison_results:
            current_data = comparison_results["current"]
            df_current = pd.DataFrame({
                "Metric": ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"],
                "Value": [
                    current_data.get("gpr", 0),
                    current_data.get("vacancy_loss", 0),
                    current_data.get("other_income", 0),
                    current_data.get("egi", 0),
                    current_data.get("opex", 0),
                    current_data.get("noi", 0)
                ]
            })
            
            # Convert to CSV
            csv_buffer = io.StringIO()
            df_current.to_csv(csv_buffer, index=False)
            csv_files["current_data.csv"] = csv_buffer.getvalue().encode()
        
        # Create CSV for each comparison type
        for comparison_type, title in [
            ("actual_vs_budget", "Actual vs Budget"),
            ("year_vs_year", "Year vs Year"),
            ("month_vs_prior", "Month vs Prior Month")
        ]:
            if comparison_type in comparison_results:
                comparison_data = comparison_results[comparison_type]
                
                # Create DataFrame for the comparison
                df_data = []
                metrics = ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"]
                data_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]
                
                for key, name in zip(data_keys, metrics):
                    # Handle both formats for current, prior, and change values
                    current_val = comparison_data.get(f"{key}_current", 0.0)
                    compare_val = comparison_data.get(f"{key}_compare", 0.0)
                    change_val = comparison_data.get(f"{key}_change", 0.0)
                    percent_change = comparison_data.get(f"{key}_percent_change", 0.0)
                    
                    df_data.append({
                        "Metric": name,
                        "Current": current_val,
                        "Comparison": compare_val,
                        "Change ($)": change_val,
                        "Change (%)": percent_change
                    })
                
                # Create DataFrame and convert to CSV
                df_comparison = pd.DataFrame(df_data)
                csv_buffer = io.StringIO()
                df_comparison.to_csv(csv_buffer, index=False)
                csv_files[f"{comparison_type.replace('_', '-')}.csv"] = csv_buffer.getvalue().encode()
        
        logger.info(f"CSV export completed successfully with {len(csv_files)} files")
        return csv_files
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return None

def display_insights(insights: Dict[str, Any], property_name: str = "Property"):
    """
    Display AI-generated insights with enhanced visual styling.
    
    Args:
        insights: Dictionary with insights generated by GPT
        property_name: Name of the property
    """
    if not insights:
        st.warning("No AI insights available.")
        return
        
    st.markdown('<h2 class="section-header">AI-Generated Insights</h2>', unsafe_allow_html=True)
    
    # Display summary in a styled card with icon
    summary_text = insights.get("summary", "No summary available.")
    st.markdown(f'''
    <div class="card" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; background: linear-gradient(to right, #f8f9fa, #e9ecef);">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div style="background-color: #0D6EFD; width: 40px; height: 40px; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 15px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" viewBox="0 0 16 16">
                    <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
                </svg>
            </div>
            <h3 style="margin: 0; color: #333; font-weight: 600;">Executive Summary</h3>
        </div>
        <p style="color: #444; font-size: 16px; line-height: 1.6; margin: 0; padding-left: 55px;">
            {summary_text}
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Create columns for performance insights and recommendations
    col1, col2 = st.columns(2)
    
    # Display performance insights with enhanced styling
    with col1:
        st.markdown('''
        <div class="card" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); padding: 20px; height: 100%; background: linear-gradient(to bottom right, #ffffff, #f0f7ff);">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background-color: #20C997; width: 40px; height: 40px; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 15px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" viewBox="0 0 16 16">
                        <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                    </svg>
                </div>
                <h3 style="margin: 0; color: #333; font-weight: 600;">Key Performance Insights</h3>
            </div>
        ''', unsafe_allow_html=True)
        
        performance_insights = insights.get("performance", [])
        if performance_insights:
            for i, insight in enumerate(performance_insights):
                # Alternate background colors for better visual separation
                bg_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"
                insight_text = insight
                st.markdown(f'''
                <div style="background-color: {bg_color}; padding: 12px 12px 12px 20px; margin: 8px 0; border-radius: 6px; border-left: 4px solid #20C997;">
                    <p style="margin: 0; color: #444; font-size: 15px; line-height: 1.5;">
                        {insight_text}
                    </p>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color: #666; font-style: italic;">No performance insights available.</p>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display recommendations with enhanced styling
    with col2:
        st.markdown('''
        <div class="card" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); padding: 20px; height: 100%; background: linear-gradient(to bottom right, #ffffff, #fff0f7);">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background-color: #FD7E14; width: 40px; height: 40px; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 15px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
                    </svg>
                </div>
                <h3 style="margin: 0; color: #333; font-weight: 600;">Actionable Recommendations</h3>
            </div>
        ''', unsafe_allow_html=True)
        
        recommendations = insights.get("recommendations", [])
        if recommendations:
            for i, recommendation in enumerate(recommendations):
                # Alternate background colors for better visual separation
                bg_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"
                rec_text = recommendation
                st.markdown(f'''
                <div style="background-color: {bg_color}; padding: 12px 12px 12px 20px; margin: 8px 0; border-radius: 6px; border-left: 4px solid #FD7E14;">
                    <p style="margin: 0; color: #444; font-size: 15px; line-height: 1.5;">
                        {rec_text}
                    </p>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color: #666; font-style: italic;">No recommendations available.</p>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Add a small footer with timestamp
    st.markdown(f'''
    <div style="text-align: right; margin-top: 20px; font-size: 12px; color: #999;">
        Analysis generated for {property_name} | {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </div>
    ''', unsafe_allow_html=True)


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
                            
                            # Debug the structure of comparison results
                            debug_comparison_structure(st.session_state.comparison_results)
                            
                            # Log the comparison results structure
                            logger.info(f"Calculated comparison results with keys: {list(st.session_state.comparison_results.keys())}")

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
                        
                        # Debug the structure of comparison results
                        debug_comparison_structure(st.session_state.comparison_results)
                        
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
                
            # Add export options
            st.markdown('<h2 class="section-header">Export Options</h2>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Export to Excel", key="export_excel_btn", use_container_width=True):
                    try:
                        excel_data = export_to_excel(st.session_state.comparison_results, property_name)
                        if excel_data:
                            # Create a download button for the Excel file
                            safe_property_name = "".join(c if c.isalnum() else "_" for c in property_name) if property_name else "Property"
                            filename = f"{safe_property_name}_NOI_Analysis_{datetime.now().strftime('%Y%m%d')}.xlsx"
                            
                            st.download_button(
                                label="Download Excel File",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.error("Failed to generate Excel file. Please try again.")
                    except Exception as e:
                        logger.error(f"Error in Excel export button action: {str(e)}")
                        st.error(f"Error exporting to Excel: {str(e)}")
            with col2:
                if st.button("Export to CSV", key="export_csv_btn", use_container_width=True):
                    try:
                        csv_files = export_to_csv(st.session_state.comparison_results, property_name)
                        if csv_files:
                            # If only one CSV file, provide direct download
                            if len(csv_files) == 1:
                                file_name, file_data = next(iter(csv_files.items()))
                                st.download_button(
                                    label="Download CSV File",
                                    data=file_data,
                                    file_name=file_name,
                                    mime="text/csv"
                                )
                            else:
                                # If multiple files, let user select which one to download
                                selected_file = st.selectbox(
                                    "Select file to download:",
                                    list(csv_files.keys())
                                )
                                
                                if selected_file:
                                    st.download_button(
                                        label=f"Download {selected_file}",
                                        data=csv_files[selected_file],
                                        file_name=selected_file,
                                        mime="text/csv"
                                    )
                        else:
                            st.error("Failed to generate CSV files. Please try again.")
                    except Exception as e:
                        logger.error(f"Error in CSV export button action: {str(e)}")
                        st.error(f"Error exporting to CSV: {str(e)}")
            with col3:
                if st.button("Generate PDF Report", key="share_report_btn", use_container_width=True):
                    try:
                        with st.spinner("Generating PDF report..."):
                            pdf_path = generate_pdf_report(st.session_state.comparison_results, property_name)
                            
                        if pdf_path and os.path.exists(pdf_path):
                            # Read the PDF file
                            with open(pdf_path, "rb") as f:
                                pdf_data = f.read()
                            
                            # Clean up the temporary file
                            try:
                                os.unlink(pdf_path)
                            except Exception as e:
                                logger.error(f"Error removing temporary PDF file: {str(e)}")
                            
                            # Create a download button for the PDF
                            safe_property_name = "".join(c if c.isalnum() else "_" for c in property_name) if property_name else "Property"
                            filename = f"{safe_property_name}_NOI_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
                            
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_data,
                                file_name=filename,
                                mime="application/pdf"
                            )
                        else:
                            st.error("Failed to generate PDF report. Please try again.")
                    except Exception as e:
                        logger.error(f"Error in PDF report button action: {str(e)}")
                        st.error(f"Error generating PDF report: {str(e)}")
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            st.error(f"Error displaying results: {str(e)}")
            # Display raw data as fallback
            st.subheader("Raw Data (Error Fallback)")
            st.json(st.session_state.comparison_results)
    else:
        # Display instructions when no data is processed
        if st.session_state.processing_status == "processing":
            st.info("Processing documents... Please wait.")
        else:
            # Use native Streamlit info component instead of custom card div
            st.info("Upload your financial documents using the sidebar and click 'Process Documents' to begin analysis.")

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
