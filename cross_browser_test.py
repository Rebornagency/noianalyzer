#!/usr/bin/env python3
"""
Cross-Browser Test Application for NOI Analyzer
Tests core functionality across Chrome, Firefox, and Safari

This is a simplified version of the main app for testing browser compatibility.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="NOI Analyzer - Cross-Browser Test",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

def test_browser_compatibility():
    """Test browser compatibility features"""
    
    # Browser detection (client-side info)
    st.markdown("""
    <script>
    var browserInfo = {
        userAgent: navigator.userAgent,
        vendor: navigator.vendor,
        platform: navigator.platform,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine,
        language: navigator.language
    };
    window.parent.postMessage({type: 'browserInfo', data: browserInfo}, '*');
    </script>
    """, unsafe_allow_html=True)
    
    return True

def test_file_upload():
    """Test file upload functionality"""
    st.subheader("📁 File Upload Test")
    
    uploaded_file = st.file_uploader(
        "Upload a test file",
        type=["pdf", "xlsx", "xls", "csv", "txt"],
        help="Test file upload across browsers"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
        st.info(f"File size: {uploaded_file.size} bytes")
        st.info(f"File type: {uploaded_file.type}")
        
        # Test file reading
        try:
            if uploaded_file.type == "text/csv":
                df = pd.read_csv(uploaded_file)
                st.write("Preview of CSV data:")
                st.dataframe(df.head())
            elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of Excel data:")
                st.dataframe(df.head())
            else:
                content = uploaded_file.read()
                st.write(f"File content length: {len(content)} bytes")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
    
    return uploaded_file is not None

def test_interactive_components():
    """Test interactive Streamlit components"""
    st.subheader("🎛️ Interactive Components Test")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Buttons & Actions**")
        button_clicked = st.button("Test Button")
        if button_clicked:
            st.success("Button works!")
        
        checkbox = st.checkbox("Test Checkbox")
        if checkbox:
            st.info("Checkbox checked!")
    
    with col2:
        st.write("**Input Controls**")
        text_input = st.text_input("Test Text Input", placeholder="Type here...")
        number_input = st.number_input("Test Number Input", min_value=0, max_value=100, value=50)
        slider_value = st.slider("Test Slider", 0, 100, 25)
    
    with col3:
        st.write("**Selection Controls**")
        selectbox_value = st.selectbox("Test Selectbox", ["Option 1", "Option 2", "Option 3"])
        multiselect_values = st.multiselect("Test Multiselect", ["A", "B", "C", "D"])
        radio_value = st.radio("Test Radio", ["Yes", "No", "Maybe"])
    
    # Display results
    if any([text_input, number_input != 50, slider_value != 25, selectbox_value, multiselect_values, radio_value]):
        st.write("**Input Values:**")
        st.json({
            "text_input": text_input,
            "number_input": number_input,
            "slider_value": slider_value,
            "selectbox_value": selectbox_value,
            "multiselect_values": multiselect_values,
            "radio_value": radio_value
        })

def test_charts_and_graphs():
    """Test chart rendering across browsers"""
    st.subheader("📊 Charts & Graphs Test")
    
    # Sample data
    data = {
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Revenue': [10000, 12000, 11000, 13000, 14500, 16000],
        'Expenses': [7000, 8000, 7500, 8500, 9000, 9500],
        'NOI': [3000, 4000, 3500, 4500, 5500, 6500]
    }
    df = pd.DataFrame(data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Plotly Interactive Chart**")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Month'], y=df['Revenue'], name='Revenue'))
        fig.add_trace(go.Bar(x=df['Month'], y=df['Expenses'], name='Expenses'))
        fig.add_trace(go.Scatter(x=df['Month'], y=df['NOI'], mode='lines+markers', name='NOI'))
        fig.update_layout(title="Financial Performance", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Streamlit Native Charts**")
        st.line_chart(df.set_index('Month')[['Revenue', 'Expenses', 'NOI']])
        
        st.write("**Bar Chart**")
        st.bar_chart(df.set_index('Month')[['Revenue', 'Expenses']])

def test_layout_responsiveness():
    """Test responsive layout across different screen sizes"""
    st.subheader("📱 Layout Responsiveness Test")
    
    # Test different column layouts
    st.write("**2-Column Layout**")
    col1, col2 = st.columns(2)
    with col1:
        st.info("Column 1 content")
    with col2:
        st.warning("Column 2 content")
    
    st.write("**3-Column Layout**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("Column 1")
    with col2:
        st.error("Column 2")
    with col3:
        st.info("Column 3")
    
    st.write("**4-Column Layout**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Metric 1", "100", "10")
    with col2:
        st.metric("Metric 2", "200", "-5")
    with col3:
        st.metric("Metric 3", "300", "15")
    with col4:
        st.metric("Metric 4", "400", "0")

def test_css_and_styling():
    """Test CSS and custom styling"""
    st.subheader("🎨 CSS & Styling Test")
    
    # Custom CSS
    st.markdown("""
    <style>
    .test-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .test-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
        margin: 20px 0;
    }
    .test-card {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="test-box">This is a custom styled box with gradient background</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="test-grid">
        <div class="test-card">
            <h4>Card 1</h4>
            <p>This is a test card with custom CSS</p>
        </div>
        <div class="test-card">
            <h4>Card 2</h4>
            <p>Testing responsive grid layout</p>
        </div>
        <div class="test-card">
            <h4>Card 3</h4>
            <p>CSS Grid support across browsers</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application"""
    st.title("🧪 NOI Analyzer - Cross-Browser Compatibility Test")
    
    st.markdown("""
    ## Welcome to the Cross-Browser Test Suite!
    
    This test application checks if all the key features of NOI Analyzer work properly across different browsers:
    - **Chrome** (recommended)
    - **Firefox** 
    - **Safari**
    
    Please test each section below and report any issues you encounter.
    """)
    
    # Browser compatibility check
    test_browser_compatibility()
    
    # Sidebar with test navigation
    st.sidebar.title("🧪 Test Categories")
    st.sidebar.markdown("Select tests to run:")
    
    run_file_upload = st.sidebar.checkbox("📁 File Upload Test", value=True)
    run_interactive = st.sidebar.checkbox("🎛️ Interactive Components", value=True)
    run_charts = st.sidebar.checkbox("📊 Charts & Graphs", value=True)
    run_layout = st.sidebar.checkbox("📱 Layout Responsiveness", value=True)
    run_styling = st.sidebar.checkbox("🎨 CSS & Styling", value=True)
    
    # Browser info display
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌐 Browser Info")
    st.sidebar.markdown("""
    **Test Instructions:**
    1. Open this app in Chrome, Firefox, and Safari
    2. Test each component thoroughly
    3. Note any visual differences or errors
    4. Check console for JavaScript errors (F12)
    """)
    
    # Run selected tests
    if run_file_upload:
        test_file_upload()
        st.markdown("---")
    
    if run_interactive:
        test_interactive_components()
        st.markdown("---")
    
    if run_charts:
        test_charts_and_graphs()
        st.markdown("---")
    
    if run_layout:
        test_layout_responsiveness()
        st.markdown("---")
    
    if run_styling:
        test_css_and_styling()
        st.markdown("---")
    
    # Test results summary
    st.subheader("📋 Test Results Summary")
    
    # Create a simple test results form
    with st.expander("🔍 Report Test Results", expanded=False):
        browser_tested = st.selectbox("Browser Tested", ["Chrome", "Firefox", "Safari", "Edge", "Other"])
        
        col1, col2 = st.columns(2)
        with col1:
            file_upload_ok = st.checkbox("✅ File upload works")
            interactive_ok = st.checkbox("✅ Interactive components work")
            charts_ok = st.checkbox("✅ Charts render correctly")
        
        with col2:
            layout_ok = st.checkbox("✅ Layout is responsive")
            styling_ok = st.checkbox("✅ Styling displays correctly")
            overall_ok = st.checkbox("✅ Overall app works well")
        
        issues_found = st.text_area("Issues Found (if any):", placeholder="Describe any problems, visual glitches, or errors...")
        
        if st.button("📊 Generate Test Report"):
            report = {
                "browser": browser_tested,
                "timestamp": datetime.now().isoformat(),
                "tests": {
                    "file_upload": file_upload_ok,
                    "interactive_components": interactive_ok,
                    "charts": charts_ok,
                    "layout": layout_ok,
                    "styling": styling_ok,
                    "overall": overall_ok
                },
                "issues": issues_found,
                "success_rate": sum([file_upload_ok, interactive_ok, charts_ok, layout_ok, styling_ok, overall_ok]) / 6 * 100
            }
            
            st.success(f"Test report generated for {browser_tested}!")
            st.json(report)
            
            # Save report to session state
            if "test_reports" not in st.session_state:
                st.session_state.test_reports = []
            st.session_state.test_reports.append(report)
    
    # Display all test reports
    if "test_reports" in st.session_state and st.session_state.test_reports:
        st.subheader("📈 All Test Reports")
        for i, report in enumerate(st.session_state.test_reports):
            with st.expander(f"Report {i+1}: {report['browser']} - {report['success_rate']:.0f}% Success"):
                st.json(report)

if __name__ == "__main__":
    main()