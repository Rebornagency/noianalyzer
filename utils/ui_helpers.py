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
def inject_custom_css() -> None:
    """
    Inject all custom CSS styles for the application UI, including responsive design, theming, and component styling.
    This function should be called once at the beginning of the Streamlit app to apply consistent styling throughout.
    """
    # Inject the loading styles for buttons
    inject_loading_styles()
    
    # Inject the main CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    logger.debug("Custom CSS injected successfully.")

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

# Enhanced loading indicator functions
def display_loading_spinner(message: str = "Processing...", subtitle: str = None):
    """
    Display a prominent loading spinner with message.
    
    Args:
        message (str): Main loading message
        subtitle (str): Optional subtitle with additional context
    """
    subtitle_html = f"<div class='loading-subtitle'>{subtitle}</div>" if subtitle else ""
    
    loading_html = f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-message">{message}</div>
        {subtitle_html}
    </div>
    """
    st.markdown(loading_html, unsafe_allow_html=True)
    logger.info(f"Displayed loading spinner: {message}")

def display_progress_bar(progress: float, message: str = "Processing...", show_percentage: bool = True):
    """
    Display a progress bar with customizable message.
    
    Args:
        progress (float): Progress value between 0.0 and 1.0
        message (str): Message to display above the progress bar
        show_percentage (bool): Whether to show percentage text
    """
    progress_percent = min(max(progress * 100, 0), 100)
    percentage_text = f"({progress_percent:.0f}%)" if show_percentage else ""
    
    progress_html = f"""
    <div class="progress-container">
        <div class="progress-message">{message} {percentage_text}</div>
        <div class="progress-bar-track">
            <div class="progress-bar-fill" style="width: {progress_percent}%"></div>
        </div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)
    logger.debug(f"Displayed progress bar: {progress_percent:.1f}% - {message}")

def display_inline_loading(message: str = "Loading...", icon: str = "⏳"):
    """
    Display a compact inline loading indicator.
    
    Args:
        message (str): Loading message
        icon (str): Icon to display (emoji or text)
    """
    inline_html = f"""
    <div class="inline-loading">
        <span class="inline-loading-icon pulse-animation">{icon}</span>
        <span class="inline-loading-text">{message}</span>
    </div>
    """
    st.markdown(inline_html, unsafe_allow_html=True)
    logger.debug(f"Displayed inline loading: {message}")

def display_overlay_loading(message: str = "Processing your request...", subtitle: str = None):
    """
    Display a full-screen overlay loading indicator (use sparingly).
    
    Args:
        message (str): Main loading message
        subtitle (str): Optional subtitle
    """
    subtitle_html = f"<div class='overlay-subtitle'>{subtitle}</div>" if subtitle else ""
    
    overlay_html = f"""
    <div class="loading-overlay">
        <div class="loading-overlay-content">
            <div class="overlay-spinner"></div>
            <div class="overlay-message">{message}</div>
            {subtitle_html}
        </div>
    </div>
    """
    st.markdown(overlay_html, unsafe_allow_html=True)
    logger.info(f"Displayed overlay loading: {message}")

def clear_loading_indicators():
    """
    Clear all loading indicators by rendering empty content.
    Call this when loading is complete.
    """
    st.markdown("<div class='loading-clear'></div>", unsafe_allow_html=True)
    logger.debug("Cleared loading indicators")

# Context manager for loading states
class LoadingContext:
    """
    Context manager for handling loading states automatically.
    
    Usage:
        with LoadingContext("Processing documents...", "This may take 1-2 minutes"):
            # Your processing code here
            result = some_long_running_function()
    """
    def __init__(self, message: str, subtitle: str = None, loading_type: str = "spinner"):
        self.message = message
        self.subtitle = subtitle
        self.loading_type = loading_type
        self.container = None
        
    def __enter__(self):
        self.container = st.empty()
        with self.container.container():
            if self.loading_type == "spinner":
                display_loading_spinner(self.message, self.subtitle)
            elif self.loading_type == "inline":
                display_inline_loading(self.message)
            elif self.loading_type == "overlay":
                display_overlay_loading(self.message, self.subtitle)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.container:
            self.container.empty()
        logger.debug(f"LoadingContext completed: {self.message}")
    
    def update_message(self, new_message: str, subtitle: str = None):
        """Update the loading message while in context."""
        if self.container:
            with self.container.container():
                if self.loading_type == "spinner":
                    display_loading_spinner(new_message, subtitle)
                elif self.loading_type == "inline":
                    display_inline_loading(new_message)

# Helper functions for button loading states
def create_loading_button(label: str, key: str = None, help_text: str = None, **kwargs):
    """
    Create a button that shows loading state when clicked.
    Returns a tuple of (clicked, button_placeholder) for manual loading management.
    
    Args:
        label (str): Button label
        key (str): Unique key for the button
        help_text (str): Help text for the button
        **kwargs: Additional button arguments
        
    Returns:
        tuple: (clicked, button_placeholder)
    """
    button_placeholder = st.empty()
    
    # Handle help parameter conflicts - prefer explicit help_text over kwargs help
    if help_text is not None:
        kwargs['help'] = help_text
    
    with button_placeholder.container():
        clicked = st.button(label, key=key, **kwargs)
    
    return clicked, button_placeholder

def show_button_loading(button_placeholder, label: str = "Processing..."):
    """
    Show loading state for a button.
    
    Args:
        button_placeholder: The button placeholder from create_loading_button
        label (str): Loading label to display
    """
    with button_placeholder.container():
        st.markdown(f"""
        <div class="stButton">
            <button class="button-loading" disabled>
                {label}
            </button>
        </div>
        """, unsafe_allow_html=True)

def restore_button(button_placeholder, label: str, key: str = "", **kwargs):
    """
    Restore a button to its normal state after loading.
    
    Args:
        button_placeholder: The placeholder where the button should be restored
        label: The button text
        key: Unique key for the button
        **kwargs: Additional arguments for the button
    """
    # Ensure consistent styling by always setting type="primary"
    kwargs.setdefault("type", "primary")
    
    # Ensure the button has proper styling even when restored
    if "use_container_width" not in kwargs:
        kwargs["use_container_width"] = True
        
    # Create the restored button
    button_placeholder.button(label, key=key or None, **kwargs)

# Enhanced timing estimation helpers
def get_loading_message_for_action(action: str, file_count: int = 1) -> tuple:
    """
    Get appropriate loading message and estimated time for different actions.
    
    Args:
        action (str): Type of action ("process_documents", "generate_pdf", "generate_insights", etc.)
        file_count (int): Number of files being processed
        
    Returns:
        tuple: (message, subtitle_with_timing)
    """
    action_configs = {
        "process_documents": {
            "message": "Processing your documents...",
            "base_time": 60,  # 1 minute base
            "per_file": 30,   # 30 seconds per additional file
            "icon": "📄"
        },
        "generate_insights": {
            "message": "Generating AI insights...",
            "base_time": 30,
            "per_file": 10,
            "icon": "🤖"
        },
        "generate_pdf": {
            "message": "Creating PDF report...",
            "base_time": 15,
            "per_file": 5,
            "icon": "📊"
        },
        "confirm_data": {
            "message": "Confirming and processing data...",
            "base_time": 10,
            "per_file": 2,
            "icon": "✅"
        },
        "credit_purchase": {
            "message": "Redirecting to payment...",
            "base_time": 5,
            "per_file": 0,
            "icon": "💳"
        },
        "noi_coach": {
            "message": "Getting AI recommendations...",
            "base_time": 15,
            "per_file": 0,
            "icon": "💡"
        }
    }
    
    config = action_configs.get(action, {
        "message": "Processing...",
        "base_time": 30,
        "per_file": 5,
        "icon": "⏳"
    })
    
    estimated_seconds = config["base_time"] + (config["per_file"] * max(0, file_count - 1))
    
    if estimated_seconds < 60:
        time_text = f"about {estimated_seconds} seconds"
    else:
        minutes = estimated_seconds // 60
        remaining_seconds = estimated_seconds % 60
        if remaining_seconds > 0:
            time_text = f"about {minutes}:{remaining_seconds:02d} minutes"
        else:
            time_text = f"about {minutes} minute{'s' if minutes != 1 else ''}"
    
    message = f"{config['icon']} {config['message']}"
    subtitle = f"This may take {time_text}. Please wait..."
    
    return message, subtitle

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
    logger.debug(f"Displayed card container with title: {title})


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

# Add CSS styling for the button-loading class to ensure it matches primary button styling
def inject_loading_styles():
    """Inject CSS styles for loading buttons to match primary button styling"""
    st.markdown("""
    <style>
    /* Ensure loading buttons match primary button styling */
    .button-loading {
        background-color: #000000 !important;
        color: #79b8f3 !important;
        border: 1px solid #79b8f3 !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(121, 184, 243, 0.3) !important;
        transition: all 0.3s ease !important;
        margin-top: 1rem !important;
        margin-bottom: 1.5rem !important;
        width: 100% !important;
        cursor: not-allowed !important;
        opacity: 0.8 !important;
    }
    
    .button-loading:hover {
        background-color: #000000 !important;
        border-color: #79b8f3 !important;
        color: #79b8f3 !important;
        box-shadow: 0 2px 8px rgba(121, 184, 243, 0.3) !important;
        transform: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
