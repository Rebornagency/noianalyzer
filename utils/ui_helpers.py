import streamlit as st
import os
import logging
from typing import Dict, Any, Optional

# Attempt to import from reborn_logo, handle potential ImportError if structure changes
try:
    from reborn_logo import get_reborn_logo_base64
except ImportError:
    # Fallback if direct import fails (e.g. if reborn_logo.py is in root)
    try:
        import sys
        # Add project root to path if utils is a subdirectory
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from reborn_logo import get_reborn_logo_base64
    except ImportError:
        # If still not found, provide a dummy function to avoid crashing
        def get_reborn_logo_base64():
            # This is a placeholder, actual base64 string should be used
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        logging.getLogger(__name__).warning("Failed to import get_reborn_logo_base64. Using placeholder.")


# Configure logger for this module
logger = logging.getLogger(__name__)

# Helper function to inject custom CSS
def inject_custom_css():
    """Inject custom CSS to ensure font consistency and apply reborn theme styling"""
    # Comprehensive CSS for Reborn theme
    # This includes font settings, layout adjustments, dark theme colors,
    # and specific styling for Streamlit components.
    st.markdown("""
    <style>
    /* Global Font and Base Styling */
    :root {
        --reborn-bg-primary: #111827; /* Dark Blue-Gray */
        --reborn-bg-secondary: #1F2937; /* Medium Blue-Gray */
        --reborn-bg-tertiary: #374151; /* Light Blue-Gray */
        --reborn-text-primary: #F3F4F6; /* Off-white */
        --reborn-text-secondary: #D1D5DB; /* Light Gray */
        --reborn-accent-blue: #3B82F6; /* Bright Blue */
        --reborn-accent-green: #10B981; /* Bright Green */
        --reborn-accent-red: #EF4444;   /* Bright Red */
        --reborn-border-color: #4B5563; /* Gray for borders */
        --reborn-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    body, .stApp, .stMarkdown, .stText, .stTextInput, .stTextArea, 
    .stSelectbox, .stMultiselect, .stDateInput, .stTimeInput, .stNumberInput,
    .stButton > button, .stDataFrame, .stTable, .stExpander, .stTabs {
        font-family: var(--reborn-font-family) !important;
    }
    
    body {
        background-color: var(--reborn-bg-primary) !important;
        color: var(--reborn-text-primary) !important;
    }
    
    .stApp {
        background-color: var(--reborn-bg-primary) !important;
        max-width: 100% !important; /* Full width layout */
        margin: 0 auto !important;
        padding: 0 !important;
    }

    /* Main content area adjustments */
    .main .block-container {
        max-width: 95% !important;
        padding-top: 1rem !important; 
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        margin-top: 0 !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--reborn-bg-secondary) !important;
        border-right: 1px solid var(--reborn-border-color) !important;
        width: 20rem !important; /* Slightly wider sidebar */
    }
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] .stButton > button {
        color: var(--reborn-text-primary) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--reborn-accent-blue) !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5 {
        color: var(--reborn-text-primary) !important;
        font-family: var(--reborn-font-family) !important;
        font-weight: 600 !important;
    }
    h1 { font-size: 2.75rem !important; margin-bottom: 1.5rem; }
    h2 { font-size: 2rem !important; margin-bottom: 1.25rem; color: var(--reborn-accent-blue) !important; }
    h3 { font-size: 1.6rem !important; margin-bottom: 1rem; color: var(--reborn-accent-green) !important; }

    /* Markdown content styling */
    .stMarkdown p, .stMarkdown li {
        font-family: var(--reborn-font-family) !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        color: var(--reborn-text-secondary) !important;
    }
    .stMarkdown strong {
        color: var(--reborn-text-primary) !important;
        font-weight: 600;
    }
    .stMarkdown a {
        color: var(--reborn-accent-blue) !important;
        text-decoration: none;
    }
    .stMarkdown a:hover {
        text-decoration: underline;
    }

    /* Button Styling */
    .stButton > button {
        background-color: var(--reborn-accent-blue) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 500 !important;
        transition: background-color 0.2s ease-in-out, transform 0.1s ease;
    }
    .stButton > button:hover {
        background-color: #2563EB !important; /* Darker blue on hover */
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(0px);
    }
    /* Secondary button style */
    .stButton[kind="secondary"] > button {
        background-color: var(--reborn-bg-tertiary) !important;
        color: var(--reborn-text-primary) !important;
    }
    .stButton[kind="secondary"] > button:hover {
        background-color: #4B5563 !important; /* Darker gray on hover */
    }
    
    /* Input Fields Styling */
    .stTextInput {
        margin-bottom: 0.25rem !important; /* tighten spacing below Property Name input */
    }
    .stTextInput > div > div > input, 
    .stTextArea > div > textarea,
    .stNumberInput > div > div > input {
        background-color: var(--reborn-bg-secondary) !important;
        color: var(--reborn-text-primary) !important;
        border: 1px solid var(--reborn-border-color) !important;
        border-radius: 6px !important;
        padding: 0.5rem 0.75rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--reborn-accent-blue) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Expander Styling */
    .stExpander {
        border: 1px solid var(--reborn-border-color) !important;
        border-radius: 8px !important;
        background-color: var(--reborn-bg-secondary) !important;
        margin-bottom: 1rem !important;
    }
    .stExpander header {
        font-weight: 600 !important;
        color: var(--reborn-text-primary) !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 1rem !important;
    }
    .stExpander header:hover {
        background-color: var(--reborn-bg-tertiary) !important;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid var(--reborn-border-color) !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: var(--reborn-text-secondary) !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.25rem !important;
        border-bottom: 2px solid transparent !important;
        transition: color 0.2s ease, border-color 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--reborn-accent-blue) !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--reborn-accent-blue) !important;
        border-bottom-color: var(--reborn-accent-blue) !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1.5rem 0 !important; /* Add padding to tab content */
    }

    /* Dataframe Styling */
    .stDataFrame {
        border: 1px solid var(--reborn-border-color) !important;
        border-radius: 8px !important;
        overflow: hidden; /* To respect border radius */
    }
    .stDataFrame table {
        width: 100% !important;
        font-size: 1rem !important; /* Increased base font size for readability */
    }
    .stDataFrame thead th {
        background-color: var(--reborn-bg-tertiary) !important;
        color: var(--reborn-text-primary) !important;
        font-weight: 700 !important; /* Bolder headers */
        text-align: center !important; /* Center-align column headers */
        padding: 1rem 1.25rem !important; /* More vertical + horizontal padding */
    }
    .stDataFrame tbody td {
        padding: 1rem 1.25rem !important; /* More spacious rows */
        border-bottom: 1px solid var(--reborn-border-color) !important;
        color: var(--reborn-text-secondary) !important;
        font-size: 1rem !important; /* Match table base font size */
        vertical-align: middle !important; /* Vertically center content */
    }
    /* Alternate row striping for subtle visual separation */
    .stDataFrame tbody tr:nth-child(even) td {
        background-color: rgba(31, 41, 55, 0.3) !important;
    }
    /* Alignment rules: first column left-aligned, others right-aligned for numbers */
    .stDataFrame tbody td:first-child {
        text-align: left !important;
        font-weight: 500 !important; /* Slightly bolder metric names */
    }
    .stDataFrame tbody td:not(:first-child) {
        text-align: right !important;
    }
    /* Remove last row border */
    .stDataFrame tbody tr:last-child td {
        border-bottom: none !important;
    }

    /* File uploaders now use targeted hiding per container */

    /* Custom Card Styling */
    .custom-card {
        background-color: var(--reborn-bg-secondary) !important;
        border: 1px solid var(--reborn-border-color) !important;
        border-radius: 10px !important;
        padding: 1.5rem !important; /* Increased padding */
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    .custom-card-title {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: var(--reborn-accent-blue) !important;
        margin-bottom: 1rem !important;
    }
    .custom-card-content p, .custom-card-content li {
        color: var(--reborn-text-secondary) !important;
    }
    
    /* Section titles (used for Executive Summary, Key Perf. Insights etc.) */
    .reborn-section-title {
        font-family: var(--reborn-font-family) !important;
        font-size: 1.6rem !important;
        font-weight: 600 !important;
        color: var(--reborn-accent-blue) !important;
        margin-top: 2rem !important; /* Increased top margin */
        margin-bottom: 1.25rem !important;
        padding: 0.6rem 1rem !important;
        background-color: rgba(30, 41, 59, 0.8) !important; /* Slightly darker for contrast */
        border-radius: 8px !important;
        border-left: 5px solid var(--reborn-accent-blue) !important;
        line-height: 1.4 !important;
        display: block;
    }
    
    /* Metric Card Styling (for dashboards, if needed) */
    .metric-card {
        background-color: var(--reborn-bg-secondary); 
        border-radius: 10px; 
        padding: 1rem 1.25rem; 
        margin-bottom: 1rem;
        border: 1px solid var(--reborn-border-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-title {
        color: var(--reborn-text-secondary); 
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        color: var(--reborn-text-primary); 
        font-size: 1.75rem; 
        font-weight: 600;
    }
    .metric-change.positive { color: var(--reborn-accent-green); }
    .metric-change.negative { color: var(--reborn-accent-red); }
    .metric-change span { font-size: 0.85rem; margin-left: 0.5rem; }

    /* Alert/Status Message Styling */
    .status-message-info {
        border-left-color: var(--reborn-accent-blue) !important;
    }
    .status-message-success {
        border-left-color: var(--reborn-accent-green) !important;
    }
    .status-message-warning {
        border-left-color: #F59E0B !important; /* Amber */
    }
    .status-message-error {
        border-left-color: var(--reborn-accent-red) !important;
    }
    .status-message { /* Common base for status messages */
        display: flex;
        align-items: center;
        background-color: var(--reborn-bg-secondary);
        border-left: 4px solid var(--reborn-text-secondary); /* Default border */
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .status-text {
        color: var(--reborn-text-primary);
        font-size: 1rem;
        line-height: 1.5;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    .status-dot.running {
        animation: pulse 1.5s infinite ease-in-out;
    }
    
    </style>
    """, unsafe_allow_html=True)
    logger.info("Custom CSS injected for Reborn theme.")

# Logo display function
def display_logo(alignment: str = "center", width: str = "180px"):
    """Display the Reborn logo in the Streamlit app with customizable alignment and width."""
    try:
        logo_base64 = get_reborn_logo_base64()
        
        logo_html = f"""
        <div style="
            display: flex; 
            justify-content: {alignment}; 
            align-items: center; 
            margin-bottom: 15px; 
            margin-top: 0; 
            padding: 5px 0;
        ">
            <img 
                src="data:image/png;base64,{logo_base64}" 
                width="{width}" 
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
        logger.info(f"Successfully displayed logo (alignment: {alignment}, width: {width})")
    except Exception as e:
        logger.error(f"Error displaying logo: {str(e)}")
        st.markdown("<h2 style='text-align: center; color: #3B82F6; margin-top: 0; padding: 15px 0; font-size: 2rem; font-weight: 600;'>REBORN NOI ANALYZER</h2>", unsafe_allow_html=True)

# Small logo display function
def display_logo_small(height: str = "36px"):
    """Display the Reborn logo (small) aligned to the left, typically for headers or titles."""
    try:
        logo_b64 = get_reborn_logo_base64()
        
        logo_html = f"""
        <div style="
            display: flex; 
            align-items: center; 
            margin: 0; 
            padding: 5px 0;
        ">
            <img 
                src="data:image/png;base64,{logo_b64}"
                height="{height}"
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
        logger.info(f"Successfully displayed small logo (height: {height})")
    except Exception as e:
        logger.error(f"Error displaying small logo: {str(e)}")
        # No fallback for small logo as it's often inline

# Show instructions to the user
def show_instructions():
    """Display instructions for using the NOI Analyzer with enhanced styling."""
    instructions_html = """
    <div class="custom-card" style="border-left: 5px solid var(--reborn-accent-green);">
        <h3 style="color: var(--reborn-accent-green); font-size: 1.3rem; margin-bottom: 1rem; font-weight: 600;">Instructions:</h3>
        <ol style="color: var(--reborn-text-secondary); padding-left: 1.5rem; margin-bottom: 0;">
            <li style="margin-bottom: 0.6rem; line-height: 1.6;">Upload your financial documents using the file uploaders.</li>
            <li style="margin-bottom: 0.6rem; line-height: 1.6;">At minimum, upload a <strong style="color: var(--reborn-accent-green);">Current Month Actuals</strong> file.</li>
            <li style="margin-bottom: 0.6rem; line-height: 1.6;">For comparative analysis, upload additional files (Prior Month, Budget, Prior Year).</li>
            <li style="margin-bottom: 0.6rem; line-height: 1.6;">Click "<strong style="color: var(--reborn-accent-blue);">Process Documents</strong>" to analyze the data.</li>
            <li style="margin-bottom: 0.6rem; line-height: 1.6;">View the results in the analysis tabs.</li>
            <li style="line-height: 1.6;">Export your results as PDF or Excel using the export options.</li>
        </ol>
        <p style="color: #A0AEC0; font-style: italic; font-size: 0.9rem; background-color: rgba(59, 130, 246, 0.1); padding: 0.75rem; border-radius: 6px; display: inline-block; margin-top: 1rem;">
            Note: Supported file formats include Excel (.xlsx, .xls), CSV, and PDF.
        </p>
    </div>
    """
    st.markdown(instructions_html, unsafe_allow_html=True)
    logger.info("Displayed instructions to the user.")

# Function to show processing status with better visual indicators
def show_processing_status(message: str, is_running: bool = False, status_type: str = "info"):
    """
    Display a processing status message with enhanced visual styling.
    
    Args:
        message (str): The status message to display.
        is_running (bool): Whether the process is currently running (adds an animation).
        status_type (str): Type of status - "info", "success", "warning", or "error".
    """
    status_class_map = {
        "info": "status-message-info",
        "success": "status-message-success",
        "warning": "status-message-warning",
        "error": "status-message-error"
    }
    status_color_map = {
        "info": "var(--reborn-accent-blue)",
        "success": "var(--reborn-accent-green)",
        "warning": "#F59E0B", # Amber
        "error": "var(--reborn-accent-red)"
    }
    
    status_class = status_class_map.get(status_type, "status-message-info")
    dot_color = status_color_map.get(status_type, "var(--reborn-accent-blue)")
    dot_animation_class = "running" if is_running else ""

    status_html = f"""
    <div class="status-message {status_class}">
        <div class="status-dot {dot_animation_class}" style="background-color: {dot_color};"></div>
        <div class="status-text">
            {message}
        </div>
    </div>
    """
    st.markdown(status_html, unsafe_allow_html=True)
    logger.info(f"Displayed processing status: {message} (type: {status_type}, running: {is_running})")

# Function to display file information with enhanced styling
def show_file_info(file_name: str, file_size: Optional[str] = None, file_type: Optional[str] = None, uploaded: bool = False):
    """
    Display uploaded file information with enhanced visual styling.
    
    Args:
        file_name (str): Name of the file.
        file_size (str, optional): Size of the file (e.g., "2.5 MB").
        file_type (str, optional): Type of file (e.g., "Excel", "PDF", "CSV").
        uploaded (bool): Whether the file has been successfully uploaded/processed.
    """
    icon_map = {
        "pdf": "📄",
        "excel": "📊",
        "csv": "📈",
        "image": "🖼️",
        "unknown": "📁"
    }
    file_type_lower = (file_type or "unknown").lower()
    icon = icon_map.get(file_type_lower, icon_map["unknown"])
    
    status_text = "Processed" if uploaded else "Pending"
    status_color = "var(--reborn-accent-green)" if uploaded else "var(--reborn-text-secondary)"
    
    file_info_html = f"""
    <div style="
        display: flex; justify-content: space-between; align-items: center;
        background-color: var(--reborn-bg-secondary);
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid var(--reborn-border-color);
    ">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 0.75rem;">{icon}</span>
            <div>
                <div style="font-weight: 500; color: var(--reborn-text-primary); font-size: 0.95rem;">{file_name}</div>
                <div style="font-size: 0.8rem; color: var(--reborn-text-secondary);">
                    {file_size if file_size else ""}
                    {(" • " if file_size and file_type else "") + (file_type if file_type else "")}
                </div>
            </div>
        </div>
        <div style="
            color: {status_color};
            font-size: 0.8rem;
            font-weight: 500;
            background-color: rgba(var(--reborn-bg-primary-rgb, 17, 24, 39), 0.5); /* Use RGB version if defined, else fallback */
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
        ">
            {status_text}
        </div>
    </div>
    """
    st.markdown(file_info_html, unsafe_allow_html=True)
    logger.debug(f"Displayed file info for: {file_name} (status: {status_text})")

# load_css is essentially an older version of inject_custom_css.
# Keeping inject_custom_css as the primary one.
# If load_css was intended for a specific theme file, that needs to be integrated.
# For now, `load_css` from app.py is not moved as `inject_custom_css` seems more comprehensive.

# Function to create styled cards for content display
def display_card_container(title: str, content_func: callable, card_id: Optional[str] = None):
    """
    Display content in a consistently styled card container.
    
    Args:
        title (str): Card title.
        content_func (callable): A function that renders the card's content using Streamlit elements.
        card_id (str, optional): An optional ID for the card container div.
    """
    card_id_attr = f"id='{card_id}'" if card_id else ""
    
    st.markdown(f"<div class='custom-card' {card_id_attr}>", unsafe_allow_html=True)
    if title:
        st.markdown(f"<h3 class='custom-card-title'>{title}</h3>", unsafe_allow_html=True)
    
    # Call the content rendering function
    with st.container(): # Ensures Streamlit elements are correctly placed within the logical "card"
        content_func()
        
    st.markdown("</div>", unsafe_allow_html=True) # Close the custom-card div
    logger.debug(f"Displayed card container with title: {title}")


def display_features_section():
    """Displays the features of the NOI Analyzer using styled cards for a modern look."""
    
    st.markdown("<h2 class='reborn-section-title'>Key Features</h2>", unsafe_allow_html=True)

    features = [
        {
            "icon": "🔍",
            "title": "Comprehensive Data Extraction",
            "description": "Automatically extract financial data from PDF, Excel, and CSV documents using advanced AI."
        },
        {
            "icon": "📊",
            "title": "Comparative Analysis",
            "description": "Gain insights by comparing current performance against budget, prior month, and prior year actuals."
        },
        {
            "icon": "💡",
            "title": "AI-Powered Insights & Narratives",
            "description": "Receive AI-generated executive summaries, key performance insights, and actionable recommendations."
        },
        {
            "icon": "🤖",
            "title": "Interactive NOI Coach",
            "description": "Ask questions about your financial data in natural language and get AI-driven answers and explanations."
        },
        {
            "icon": "📋",
            "title": "Detailed Data Validation",
            "description": "Ensure data accuracy with built-in validation checks and clear warnings for discrepancies."
        },
        {
            "icon": "📄",
            "title": "Flexible Export Options",
            "description": "Export your analysis and reports to PDF or Excel for easy sharing and record-keeping."
        }
    ]

    cols = st.columns(3)
    for i, feature in enumerate(features):
        with cols[i % 3]:
            content_html = f"""
            <div style="text-align: center; margin-bottom: 0.5rem; font-size: 2.5rem;">{feature['icon']}</div>
            <h4 style="font-size: 1.1rem; color: var(--reborn-text-primary); margin-bottom: 0.5rem; text-align: center;">{feature['title']}</h4>
            <p style="font-size: 0.9rem; color: var(--reborn-text-secondary); text-align: center; line-height: 1.5;">{feature['description']}</p>
            """
            
            # Use a lambda to pass the HTML to display_card_container
            display_card_container(
                title="",  # Title is part of the content_html for better control
                content_func=lambda html=content_html: st.markdown(html, unsafe_allow_html=True),
                card_id=f"feature-card-{i}"
            )
    logger.info("Displayed features section.")

# --- Convenience wrapper used by app.py ---

def load_custom_css_universal() -> None:
    """Backward-compatibility shim – delegates to inject_custom_css().
    app.py expects this symbol; keeping here ensures the call succeeds in all modes.
    """
    inject_custom_css()
    logger.debug("load_custom_css_universal called – custom CSS injected.") 