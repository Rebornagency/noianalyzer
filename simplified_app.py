import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import logging
from datetime import datetime

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom modules
from api_integration import extract_data_from_documents
from helpers import format_for_noi_comparison, calculate_noi_comparisons, create_comparison_dataframe
from ai_insights_gpt import generate_insights_with_gpt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_analyzer_app')

# Set page configuration
st.set_page_config(
    page_title="NOI Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f0ff;
        border-bottom: 2px solid #4da6ff;
    }
    .comparison-table th {
        background-color: #f0f2f6;
        font-weight: bold;
    }
    .comparison-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .comparison-table td, .comparison-table th {
        text-align: right;
        padding: 8px;
    }
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .header-title {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    .header-subtitle {
        font-size: 1rem;
        color: #666;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-container">
    <div>
        <h1 class="header-title">NOI Analyzer</h1>
        <p class="header-subtitle">Analyze and compare Net Operating Income (NOI) data</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_extracted' not in st.session_state:
    st.session_state.data_extracted = False
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None
if 'property_name' not in st.session_state:
    st.session_state.property_name = ""
if 'insights' not in st.session_state:
    st.session_state.insights = None

# Sidebar
with st.sidebar:
    st.header("Upload Financial Documents")
    
    # Property name input
    property_name = st.text_input("Property Name", value=st.session_state.property_name)
    st.session_state.property_name = property_name
    
    # File uploads
    current_month_file = st.file_uploader("Current Month Actuals", type=["xlsx", "xls", "csv", "pdf"])
    prior_month_file = st.file_uploader("Prior Month Actuals", type=["xlsx", "xls", "csv", "pdf"])
    budget_file = st.file_uploader("Budget", type=["xlsx", "xls", "csv", "pdf"])
    prior_year_file = st.file_uploader("Prior Year Actuals", type=["xlsx", "xls", "csv", "pdf"])
    
    # Process button
    process_button = st.button("Process Documents")
    
    if process_button and current_month_file:
        with st.spinner("Extracting data from documents..."):
            try:
                # Extract data from documents
                logger.info("Extracting data from documents")
                extracted_data = extract_data_from_documents(
                    current_month_file=current_month_file,
                    prior_month_file=prior_month_file,
                    budget_file=budget_file,
                    prior_year_file=prior_year_file
                )
                
                if 'error' in extracted_data:
                    st.error(f"Error extracting data: {extracted_data['error']}")
                    logger.error(f"Error extracting data: {extracted_data['error']}")
                else:
                    # Format data for NOI comparison
                    logger.info("Formatting data for NOI comparison")
                    current_data = format_for_noi_comparison(extracted_data.get('current_month_actuals', {}))
                    
                    # Format other data if available
                    budget_data = None
                    if 'current_month_budget' in extracted_data:
                        budget_data = format_for_noi_comparison(extracted_data['current_month_budget'])
                    
                    prior_month_data = None
                    if 'prior_month_actuals' in extracted_data:
                        prior_month_data = format_for_noi_comparison(extracted_data['prior_month_actuals'])
                    
                    prior_year_data = None
                    if 'prior_year_actuals' in extracted_data:
                        prior_year_data = format_for_noi_comparison(extracted_data['prior_year_actuals'])
                    
                    # Calculate NOI comparisons
                    logger.info("Calculating NOI comparisons")
                    comparison_results = calculate_noi_comparisons(
                        current_data=current_data,
                        budget_data=budget_data,
                        prior_month_data=prior_month_data,
                        prior_year_data=prior_year_data
                    )
                    
                    # Generate insights with GPT
                    logger.info("Generating insights with GPT")
                    insights = generate_insights_with_gpt(comparison_results, property_name)
                    
                    # Store results in session state
                    st.session_state.comparison_results = comparison_results
                    st.session_state.data_extracted = True
                    st.session_state.insights = insights
                    
                    st.success("Data extracted successfully!")
                    logger.info("Data extraction and processing completed successfully")
            except Exception as e:
                st.error(f"Error processing documents: {str(e)}")
                logger.error(f"Error processing documents: {str(e)}", exc_info=True)

# Main content
if st.session_state.data_extracted and st.session_state.comparison_results:
    tabs = st.tabs(["NOI Summary", "Actual vs Budget", "Month over Month", "Year over Year", "AI Insights"])
    
    comparison_results = st.session_state.comparison_results
    current_data = comparison_results.get('current', {})
    
    # NOI Summary Tab
    with tabs[0]:
        st.header("NOI Summary")
        
        # Create summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Effective Gross Income (EGI)", f"${current_data.get('egi', 0):,.2f}")
        
        with col2:
            st.metric("Operating Expenses", f"${current_data.get('opex', 0):,.2f}")
        
        with col3:
            st.metric("Net Operating Income (NOI)", f"${current_data.get('noi', 0):,.2f}")
        
        # Create summary chart
        st.subheader("Financial Overview")
        
        # Prepare data for chart
        labels = ["Gross Potential Rent", "Vacancy Loss", "Other Income", "Operating Expenses", "NOI"]
        values = [
            current_data.get('gpr', 0),
            current_data.get('vacancy_loss', 0),
            current_data.get('other_income', 0),
            current_data.get('opex', 0),
            current_data.get('noi', 0)
        ]
        
        # Create bar chart
        fig = go.Figure()
        
        # Add bars with different colors
        colors = ['#4da6ff', '#ff6666', '#66cc99', '#ff9933', '#9966ff']
        
        for i, (label, value) in enumerate(zip(labels, values)):
            fig.add_trace(go.Bar(
                x=[label],
                y=[abs(value)],
                name=label,
                marker_color=colors[i],
                text=f"${abs(value):,.2f}",
                textposition='auto'
            ))
        
        # Update layout
        fig.update_layout(
            title="Financial Components",
            xaxis_title="",
            yaxis_title="Amount ($)",
            legend_title="Components",
            height=500,
            margin=dict(l=20, r=20, t=60, b=80)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Actual vs Budget Tab
    with tabs[1]:
        st.header("Actual vs Budget Comparison")
        
        if 'actual_vs_budget' in comparison_results and comparison_results['actual_vs_budget']:
            avb = comparison_results['actual_vs_budget']
            
            # Create metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                noi_actual = current_data.get('noi', 0)
                noi_budget = avb.get('noi_budget', 0)
                noi_variance = avb.get('noi_variance', 0)
                noi_percent = avb.get('noi_percent_variance', 0)
                
                st.metric(
                    "NOI Actual vs Budget",
                    f"${noi_actual:,.2f}",
                    f"{noi_variance:,.2f} ({noi_percent:.1f}%)",
                    delta_color="normal" if noi_variance >= 0 else "inverse"
                )
            
            with col2:
                egi_actual = current_data.get('egi', 0)
                egi_budget = avb.get('egi_budget', 0)
                egi_variance = avb.get('egi_variance', 0)
                egi_percent = avb.get('egi_percent_variance', 0)
                
                st.metric(
                    "EGI Actual vs Budget",
                    f"${egi_actual:,.2f}",
                    f"{egi_variance:,.2f} ({egi_percent:.1f}%)",
                    delta_color="normal" if egi_variance >= 0 else "inverse"
                )
            
            with col3:
                opex_actual = current_data.get('opex', 0)
                opex_budget = avb.get('opex_budget', 0)
                opex_variance = avb.get('opex_variance', 0)
                opex_percent = avb.get('opex_percent_variance', 0)
                
                st.metric(
                    "OpEx Actual vs Budget",
                    f"${opex_actual:,.2f}",
                    f"{opex_variance:,.2f} ({opex_percent:.1f}%)",
                    delta_color="inverse" if opex_variance >= 0 else "normal"
                )
            
            # Create comparison table
            st.subheader("Detailed Comparison")
            
            df = create_comparison_dataframe(comparison_results, 'actual_vs_budget')
            
            if not df.empty:
                # Display the table
                st.markdown(
                    df.to_html(escape=False, index=False, classes='comparison-table'),
                    unsafe_allow_html=True
                )
                
                # Create comparison chart
                st.subheader("Actual vs Budget Chart")
                
                # Prepare data for chart
                categories = df['Category'].tolist()
                actual_values = df['Actual_raw'].tolist()
                budget_values = df['Budget_raw'].tolist()
                
                # Create grouped bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=categories,
                    y=actual_values,
                    name='Actual',
                    marker_color='#4da6ff',
                    text=[f"${v:,.2f}" for v in actual_values],
                    textposition='auto'
                ))
                
                fig.add_trace(go.Bar(
                    x=categories,
                    y=budget_values,
                    name='Budget',
                    marker_color='#ff9933',
                    text=[f"${v:,.2f}" for v in budget_values],
                    textposition='auto'
                ))
                
                # Update layout
                fig.update_layout(
                    title="Actual vs Budget Comparison",
                    xaxis_title="",
                    yaxis_title="Amount ($)",
                    legend_title="Type",
                    barmode='group',
                    height=500,
                    margin=dict(l=20, r=20, t=60, b=80)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No budget data available for comparison.")
        else:
            st.info("No budget data available for comparison.")
    
    # Month over Month Tab
    with tabs[2]:
        st.header("Month over Month Comparison")
        
        if 'month_vs_prior' in comparison_results and comparison_results['month_vs_prior']:
            mom = comparison_results['month_vs_prior']
            
            # Create metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                noi_current = current_data.get('noi', 0)
                noi_prior = mom.get('noi_prior', 0)
                noi_change = mom.get('noi_change', 0)
                noi_percent = mom.get('noi_percent_change', 0)
                
                st.metric(
                    "NOI Month over Month",
                    f"${noi_current:,.2f}",
                    f"{noi_change:,.2f} ({noi_percent:.1f}%)",
                    delta_color="normal" if noi_change >= 0 else "inverse"
                )
            
            with col2:
                egi_current = current_data.get('egi', 0)
                egi_prior = mom.get('egi_prior', 0)
                egi_change = mom.get('egi_change', 0)
                egi_percent = mom.get('egi_percent_change', 0)
                
                st.metric(
                    "EGI Month over Month",
                    f"${egi_current:,.2f}",
                    f"{egi_change:,.2f} ({egi_percent:.1f}%)",
                    delta_color="normal" if egi_change >= 0 else "inverse"
                )
            
            with col3:
                opex_current = current_data.get('opex', 0)
                opex_prior = mom.get('opex_prior', 0)
                opex_change = mom.get('opex_change', 0)
                opex_percent = mom.get('opex_percent_change', 0)
                
                st.metric(
                    "OpEx Month over Month",
                    f"${opex_current:,.2f}",
                    f"{opex_change:,.2f} ({opex_percent:.1f}%)",
                    delta_color="inverse" if opex_change >= 0 else "normal"
                )
            
            # Create comparison table
            st.subheader("Detailed Comparison")
            
            df = create_comparison_dataframe(comparison_results, 'month_vs_prior')
            
            if not df.empty:
                # Display the table
                st.markdown(
                    df.to_html(escape=False, index=False, classes='comparison-table'),
                    unsafe_allow_html=True
                )
                
                # Create comparison chart
                st.subheader("Month over Month Chart")
                
                # Prepare data for chart
                categories = df['Category'].tolist()
                current_values = df['Current_raw'].tolist()
                prior_values = df['Prior_raw'].tolist()
                
                # Create grouped bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=categories,
                    y=current_values,
                    name='Current Month',
                    marker_color='#4da6ff',
                    text=[f"${v:,.2f}" for v in current_values],
                    textposition='auto'
                ))
                
                fig.add_trace(go.Bar(
                    x=categories,
                    y=prior_values,
                    name='Prior Month',
                    marker_color='#ff9933',
                    text=[f"${v:,.2f}" for v in prior_values],
                    textposition='auto'
                ))
                
                # Update layout
                fig.update_layout(
                    title="Month over Month Comparison",
                    xaxis_title="",
                    yaxis_title="Amount ($)",
                    legend_title="Month",
                    barmode='group',
                    height=500,
                    margin=dict(l=20, r=20, t=60, b=80)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No prior month data available for comparison.")
        else:
            st.info("No prior month data available for comparison.")
    
    # Year over Year Tab
    with tabs[3]:
        st.header("Year over Year Comparison")
        
        if 'year_vs_year' in comparison_results and comparison_results['year_vs_year']:
            yoy = comparison_results['year_vs_year']
            
            # Create metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                noi_current = current_data.get('noi', 0)
                noi_prior = yoy.get('noi_prior_year', 0)
                noi_change = yoy.get('noi_change', 0)
                noi_percent = yoy.get('noi_percent_change', 0)
                
                st.metric(
                    "NOI Year over Year",
                    f"${noi_current:,.2f}",
                    f"{noi_change:,.2f} ({noi_percent:.1f}%)",
                    delta_color="normal" if noi_change >= 0 else "inverse"
                )
            
            with col2:
                egi_current = current_data.get('egi', 0)
                egi_prior = yoy.get('egi_prior_year', 0)
                egi_change = yoy.get('egi_change', 0)
                egi_percent = yoy.get('egi_percent_change', 0)
                
                st.metric(
                    "EGI Year over Year",
                    f"${egi_current:,.2f}",
                    f"{egi_change:,.2f} ({egi_percent:.1f}%)",
                    delta_color="normal" if egi_change >= 0 else "inverse"
                )
            
            with col3:
                opex_current = current_data.get('opex', 0)
                opex_prior = yoy.get('opex_prior_year', 0)
                opex_change = yoy.get('opex_change', 0)
                opex_percent = yoy.get('opex_percent_change', 0)
                
                st.metric(
                    "OpEx Year over Year",
                    f"${opex_current:,.2f}",
                    f"{opex_change:,.2f} ({opex_percent:.1f}%)",
                    delta_color="inverse" if opex_change >= 0 else "normal"
                )
            
            # Create comparison table
            st.subheader("Detailed Comparison")
            
            df = create_comparison_dataframe(comparison_results, 'year_vs_year')
            
            if not df.empty:
                # Display the table
                st.markdown(
                    df.to_html(escape=False, index=False, classes='comparison-table'),
                    unsafe_allow_html=True
                )
                
                # Create comparison chart
                st.subheader("Year over Year Chart")
                
                # Prepare data for chart
                categories = df['Category'].tolist()
                current_values = df['Current_raw'].tolist()
                prior_values = df['Prior_raw'].tolist()
                
                # Create grouped bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=categories,
                    y=current_values,
                    name='Current Year',
                    marker_color='#4da6ff',
                    text=[f"${v:,.2f}" for v in current_values],
                    textposition='auto'
                ))
                
                fig.add_trace(go.Bar(
                    x=categories,
                    y=prior_values,
                    name='Prior Year',
                    marker_color='#ff9933',
                    text=[f"${v:,.2f}" for v in prior_values],
                    textposition='auto'
                ))
                
                # Update layout
                fig.update_layout(
                    title="Year over Year Comparison",
                    xaxis_title="",
                    yaxis_title="Amount ($)",
                    legend_title="Year",
                    barmode='group',
                    height=500,
                    margin=dict(l=20, r=20, t=60, b=80)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No prior year data available for comparison.")
        else:
            st.info("No prior year data available for comparison.")
    
    # AI Insights Tab
    with tabs[4]:
        st.header("AI-Generated Insights")
        
        if st.session_state.insights:
            insights = st.session_state.insights
            
            # Display summary
            st.subheader("Executive Summary")
            st.write(insights.get('summary', 'No summary available.'))
            
            # Display performance insights
            st.subheader("Key Performance Insights")
            performance = insights.get('performance', [])
            if performance:
                for point in performance:
                    st.markdown(f"- {point}")
            else:
                st.info("No performance insights available.")
            
            # Display recommendations
            st.subheader("Actionable Recommendations")
            recommendations = insights.get('recommendations', [])
            if recommendations:
                for rec in recommendations:
                    st.markdown(f"- {rec}")
            else:
                st.info("No recommendations available.")
        else:
            st.info("No AI insights available. Please process documents to generate insights.")
else:
    # Display instructions when no data is loaded
    st.info("Please upload financial documents and click 'Process Documents' to analyze NOI data.")
    
    # Display sample images
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sample NOI Analysis")
        st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", 
                 caption="Sample NOI Dashboard")
    
    with col2:
        st.subheader("How It Works")
        st.markdown("""
        1. Upload your financial documents (current month, prior month, budget, prior year)
        2. Click 'Process Documents' to extract and analyze the data
        3. View NOI comparisons and AI-generated insights
        4. Make informed decisions based on the analysis
        """)

# Footer
st.markdown("""
---
<p style="text-align: center; color: #666;">
    NOI Analyzer | Last updated: April 2025
</p>
""", unsafe_allow_html=True)
