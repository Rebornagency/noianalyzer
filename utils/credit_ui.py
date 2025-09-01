import streamlit as st
import requests
import os
from typing import Dict, Any, Optional
import logging
import time

import uuid

# Import loading functions
try:
    from .ui_helpers import (
        display_loading_spinner, display_inline_loading, 
        get_loading_message_for_action, LoadingContext,
        create_loading_button, show_button_loading, restore_button
    )
except ImportError:
    # Fallback functions if ui_helpers is not available
    def display_loading_spinner(message, subtitle=None):
        st.info(f"{message} {subtitle or ''}")
    def display_inline_loading(message, icon="⏳"):
        st.info(f"{icon} {message}")
    def get_loading_message_for_action(action, file_count=1):
        return "Processing...", "Please wait..."
    def create_loading_button(label, key=None, **kwargs):
        return st.button(label, key=key, **kwargs), st.empty()
    def show_button_loading(placeholder, label):
        placeholder.button(label, disabled=True)
    def restore_button(placeholder, label, key=None, **kwargs):
        placeholder.button(label, key=key, **kwargs)

logger = logging.getLogger(__name__)

def get_backend_url():
    """Get the correct backend URL by testing available options"""
    backend_url = os.getenv("BACKEND_URL")
    if backend_url:
        return backend_url
    
    # Try production server first since it's more likely to be working
    test_urls = [
        "https://noianalyzer-1.onrender.com",  # Production server (primary)
        "http://localhost:8000",  # FastAPI servers
        "http://localhost:10000"  # Ultra minimal server
    ]
    
    for url in test_urls:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"Backend connected successfully: {url}")
                return url
        except:
            continue
    
    # Default fallback to production
    logger.warning("No backend server responding, using production as fallback")
    return "https://noianalyzer-1.onrender.com"

# Update the global BACKEND_URL
BACKEND_URL = get_backend_url()

def get_user_credits(email: str) -> Optional[Dict[str, Any]]:
    """Get user credit information from API"""
    try:
        response = requests.get(f"{BACKEND_URL}/pay-per-use/credits/{email}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get credits for {email}: HTTP {response.status_code} - {response.text[:200]}")
            return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to backend API at {BACKEND_URL}: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to backend API at {BACKEND_URL}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting credits: {e}")
        return None

def get_credit_packages() -> list:
    """Get available credit packages"""
    try:
        response = requests.get(f"{BACKEND_URL}/pay-per-use/packages", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get packages: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error getting packages: {e}")
        return []

def test_backend_connection() -> bool:
    """Test if backend API is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def display_credit_balance_header(email: str):
    """Display user's credit balance in the main page header"""
    if not email:
        return
    
    # First test if backend is available
    if not test_backend_connection():
        st.markdown("""
        <div style="
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <div style="color: #EF4444; font-weight: 600;">💳 Backend API Unavailable</div>
            <div style="color: #ffffff; font-size: 0.8rem;">Please start the API server</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    credit_data = get_user_credits(email)
    if not credit_data:
        st.markdown("""
        <div style="
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <div style="color: #EF4444; font-weight: 600;">💳 Unable to load credits</div>
            <div style="color: #ffffff; font-size: 0.8rem;">Check API server connection</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    credits = credit_data.get("credits", 0)
    
    # Color coding based on credit level
    if credits >= 10:
        color = "#22C55E"  # Green
        emoji = "🟢"
        status = "Good"
    elif credits >= 3:
        color = "#F59E0B"  # Amber
        emoji = "🟡"
        status = "Low"
    elif credits > 0:
        color = "#EF4444"  # Red
        emoji = "🔴"
        status = "Very Low"
    else:
        color = "#6B7280"  # Gray
        emoji = "⚫"
        status = "Empty"
    
    # Compact header display
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}22, {color}11);
            border: 1px solid {color}44;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            text-align: center;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        ">
            <div style="font-size: 1.2rem;">{emoji}</div>
            <div style="font-size: 1.1rem; font-weight: bold; color: {color};">{credits}</div>
            <div style="color: #ffffff; font-size: 0.9rem;">Credits</div>
            <div style="color: #ffffff; font-size: 0.8rem;">({status})</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_credit_balance(email: str):
    """Display user's credit balance in sidebar"""
    if not email:
        return
    
    # First test if backend is available
    if not test_backend_connection():
        st.sidebar.error("💳 Backend API Unavailable")
        st.sidebar.info(f"🔧 **Debug Info:**\n- Backend URL: `{BACKEND_URL}`\n- The API server is not responding\n- Start it with: `python api_server.py`")
        return
    
    credit_data = get_user_credits(email)
    if not credit_data:
        st.sidebar.error("💳 Unable to load credit balance")
        st.sidebar.info(f"🔧 **Debug Info:**\n- Backend URL: `{BACKEND_URL}`\n- Make sure your API server is running\n- Check that API server includes the `/pay-per-use/credits/{email}` endpoint")
        return
    
    credits = credit_data.get("credits", 0)
    
    # Credit balance display
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💳 Your Credits")
    
    # Color coding based on credit level
    if credits >= 10:
        color = "#22C55E"  # Green
        emoji = "🟢"
    elif credits >= 3:
        color = "#F59E0B"  # Amber
        emoji = "🟡"
    elif credits > 0:
        color = "#EF4444"  # Red
        emoji = "🔴"
    else:
        color = "#6B7280"  # Gray
        emoji = "⚫"
    
    st.sidebar.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}22, {color}11);
            border: 1px solid {color}44;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            margin-bottom: 1rem;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{emoji}</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{credits}</div>
            <div style="color: #ffffff; font-size: 0.9rem;">Credits Available</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Show usage info
    credits_per_analysis = 1  # This should come from config
    analyses_remaining = credits // credits_per_analysis
    
    if analyses_remaining > 0:
        st.sidebar.success(f"✅ You can run {analyses_remaining} more analysis{'es' if analyses_remaining != 1 else ''}")
    else:
        st.sidebar.error("❌ No credits remaining")
        
    # Buy more credits button with loading state
    with st.sidebar:
        buy_clicked, buy_button_placeholder = create_loading_button(
            "🛒 Buy More Credits", 
            key="sidebar_buy_credits", 
            use_container_width=True
        )
        
        if buy_clicked:
            logger.info("🛒 Sidebar Buy More Credits button clicked - showing credit store")
            
            # Show loading state
            show_button_loading(buy_button_placeholder, "Loading Store...")
            
            # Brief loading to show feedback
            time.sleep(0.5)
            
            st.session_state.show_credit_store = True
            # Clear any conflicting flags
            if 'show_credit_success' in st.session_state:
                del st.session_state.show_credit_success
            st.rerun()
    
    # Transaction history in expander
    with st.sidebar.expander("📊 Recent Activity"):
        transactions = credit_data.get("recent_transactions", [])
        if transactions:
            for tx in transactions[:5]:  # Show last 5 transactions
                tx_type = tx["type"]
                amount = tx["amount"]
                description = tx["description"]
                
                # Format transaction display
                if tx_type == "purchase":
                    icon = "💰"
                    color_style = "color: #22C55E;"
                    amount_str = f"+{amount}"
                elif tx_type == "usage":
                    icon = "📊"
                    color_style = "color: #EF4444;"
                    amount_str = f"{amount}"  # Already negative
                elif tx_type == "bonus":
                    icon = "🎁"
                    color_style = "color: #3B82F6;"
                    amount_str = f"+{amount}"
                else:
                    icon = "📝"
                    color_style = "color: #6B7280;"
                    amount_str = f"{amount:+d}"
                
                st.markdown(
                    f"""
                    <div style="font-size: 0.8rem; margin-bottom: 0.5rem; padding: 0.25rem; border-left: 2px solid #E5E7EB;">
                        {icon} <span style="{color_style}">{amount_str}</span><br/>
                        <span style="color: #6B7280;">{description}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown("*No recent activity*")

def display_credit_store():
    """Display credit purchase interface"""
    # st.title("🛒 Buy Credits")  # Removed: single headline will be used below per new UI spec
    
    packages = get_credit_packages()
    if not packages:
        st.error("Unable to load credit packages. Please try again later.")
        return
    
    st.markdown("## Choose a Credit Package")
    # Center-align subtitle and follow with a value-proposition blurb on time saved
    st.markdown(
        """
        <div style="text-align: center; font-size: 1.05rem; color: rgba(255,255,255,0.85); margin-bottom: 0.75rem;">
            Credits never expire and can be used for any NOI analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Highlight the key benefit – time saved – in a subtle accent colour
    st.markdown(
        """
        <div style="text-align: center; font-size: 1.15rem; color: #FACC15; margin-bottom: 2.5rem; font-weight: 600;">
            ⏱ Save <span style="font-weight: 800;">up to 3 hours</span> of manual spreadsheet work per analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Display packages in columns using Streamlit native components
    cols = st.columns(min(len(packages), 3))
    
    # Add custom HTML attributes to columns for better CSS targeting
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Add custom attributes to credit store columns
        const columns = document.querySelectorAll('[data-testid="column"]');
        columns.forEach((col, index) => {
            if (!col.hasAttribute('data-credit-store-column')) {
                col.setAttribute('data-credit-store-column', 'true');
                col.setAttribute('data-column-index', index);
            }
        });
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Inject specific CSS for credit store with highest specificity to override global styles
    # Using ID-based selectors and multiple levels of specificity to ensure styles take precedence
    st.markdown("""
    <style>
    /* Credit Store Package Card Styling - Using maximum specificity */
    
    /* Main card container - using ID and multiple attribute selectors */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]):not([style*="display: none"]) {
        background: #101922 !important;
        border: 1px solid #1f2a36 !important;
        border-radius: 12px !important;
        padding: 2rem 1.5rem 4rem 1.5rem !important;
        margin: 0.75rem !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.3s ease !important;
        height: 580px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        position: relative !important;
        box-sizing: border-box !important;
    }
    
    /* Card hover effect with maximum specificity */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]):hover,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]):hover,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]):hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.45) !important;
        border-color: #0E4DE3 !important;
        background: rgba(14, 77, 227, 0.05) !important;
    }
    
    /* Package Title Styling */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] h3 {
        margin-top: 0 !important;
        margin-bottom: 1.25rem !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        text-align: center !important;
        color: #FFFFFF !important;
        padding-bottom: 0.75rem !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Credits Display */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > p:first-of-type,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > p:first-of-type,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > p:first-of-type {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        text-align: center !important;
        margin: 1.25rem 0 !important;
    }
    
    /* Price Display */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] h3:nth-of-type(2),
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] h3:nth-of-type(2),
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] h3:nth-of-type(2) {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        margin: 1.5rem 0 !important;
        text-align: center !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Per Credit Price */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > p:nth-of-type(2),
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > p:nth-of-type(2),
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > p:nth-of-type(2) {
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 1.1rem !important;
        font-style: italic !important;
        margin: 1rem 0 1.5rem 0 !important;
        text-align: center !important;
    }
    
    /* Savings Badge */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"],
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"],
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"] {
        margin: 1.5rem auto !important;
        padding: 0.85rem 1.25rem !important;
        border-radius: 30px !important;
        text-align: center !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        color: #FFFFFF !important;
        background: linear-gradient(135deg, #22C55E, #16A34A) !important;
        border: 2px solid rgba(34, 197, 94, 0.5) !important;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3) !important;
        min-height: 52px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: calc(100% - 2rem) !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        position: relative !important;
    }
    
    /* Savings Badge Text */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"] *,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"] *,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Description Text */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > div:last-of-type,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > div:last-of-type,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > div:last-of-type {
        color: rgba(255, 255, 255, 0.85) !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        margin: 1.5rem 0 2rem 0 !important;
        text-align: center !important;
        flex-grow: 1 !important;
    }
    
    /* Time Savings Highlight */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > div[style*="color:#FACC15"],
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > div[style*="color:#FACC15"],
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] > div > div[style*="color:#FACC15"] {
        color: #FACC15 !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        margin: 1rem 0 !important;
    }
    
    /* Button Container */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"],
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"],
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] {
        margin-top: auto !important;
        padding: 1.25rem 0 0 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
        display: flex !important;
        justify-content: center !important;
    }
    
    /* CTA Button - Maximum specificity to override global styles */
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button {
        width: calc(100% - 2rem) !important;
        height: 52px !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        background: linear-gradient(135deg, #0E4DE3 0%, #1C5CF5 100%) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 6px 16px rgba(14, 77, 227, 0.4) !important;
        text-transform: none !important;
        letter-spacing: 0.5px !important;
        box-sizing: border-box !important;
        margin: 0 auto !important;
        display: block !important;
        cursor: pointer !important;
        padding: 0 !important;
    }
    
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:hover,
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:hover,
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button:hover,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:hover,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:hover,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button:hover,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:hover,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:hover,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #1C5CF5 0%, #2563EB 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 20px rgba(14, 77, 227, 0.6) !important;
    }
    
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:active,
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:active,
    div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button:active,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:active,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:active,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button:active,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:active,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:active,
    .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button:active {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(14, 77, 227, 0.4) !important;
    }
    
    /* Header styling */
    div[id^="credit-store"] .stApp [data-testid="stVerticalBlock"]:nth-child(3) h1,
    #credit-store-container .stApp [data-testid="stVerticalBlock"]:nth-child(3) h1,
    .stApp [data-testid="stVerticalBlock"]:nth-child(3) h1 {
        margin-bottom: 2rem !important;
        text-align: center !important;
        font-size: 2.75rem !important;
        color: #FFFFFF !important;
    }
    
    div[id^="credit-store"] .stApp [data-testid="stVerticalBlock"]:nth-child(3) h2,
    #credit-store-container .stApp [data-testid="stVerticalBlock"]:nth-child(3) h2,
    .stApp [data-testid="stVerticalBlock"]:nth-child(3) h2 {
        color: #ffffff !important;
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        text-align: center !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Subtitle styling */
    div[id^="credit-store"] .stApp [data-testid="stVerticalBlock"]:nth-child(3) > div:nth-child(3),
    #credit-store-container .stApp [data-testid="stVerticalBlock"]:nth-child(3) > div:nth-child(3),
    .stApp [data-testid="stVerticalBlock"]:nth-child(3) > div:nth-child(3) {
        margin-bottom: 3rem !important;
        text-align: center !important;
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1.15rem !important;
        font-weight: 500 !important;
    }
    
    /* Highlighted savings text */
    div[id^="credit-store"] .stApp [data-testid="stVerticalBlock"]:nth-child(3) > div:nth-child(4),
    #credit-store-container .stApp [data-testid="stVerticalBlock"]:nth-child(3) > div:nth-child(4),
    .stApp [data-testid="stVerticalBlock"]:nth-child(3) > div:nth-child(4) {
        text-align: center !important;
        color: #FACC15 !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        margin-bottom: 3rem !important;
    }
    
    /* Column spacing */
    div[id^="credit-store"] [data-testid="column"],
    #credit-store-container [data-testid="column"],
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
        #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
        .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]) {
            height: auto !important;
            min-height: 500px !important;
            padding: 1.5rem 1rem 3rem 1rem !important;
        }
        
        div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
        #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
        .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] h3 {
            font-size: 1.5rem !important;
        }
        
        div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] h3:nth-of-type(2),
        #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] h3:nth-of-type(2),
        .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] h3:nth-of-type(2) {
            font-size: 2.2rem !important;
        }
        
        div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
        div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
        div[id^="credit-store"] [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button,
        #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
        #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
        #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button,
        .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
        .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
        .stApp [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stButton"] > button {
            height: 48px !important;
            font-size: 1.1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add a container with ID to help with CSS specificity
    st.markdown('<div id="credit-store-container">', unsafe_allow_html=True)
    
    for idx, package in enumerate(packages):
        col = cols[idx % len(cols)]
        
        with col:
            # Calculate savings
            savings_text = ""
            if idx > 0 and len(packages) > 1:
                base_per_credit = packages[0]["per_credit_cost"]
                current_per_credit = package["per_credit_cost"]
                savings_percent = ((base_per_credit - current_per_credit) / base_per_credit) * 100
                if savings_percent > 0:
                    savings_text = f"Save {savings_percent:.0f}%!"
            
            # Use Streamlit container for styling
            with st.container():
                # Package title
                if idx == 1:  # Highlight middle package
                    st.markdown(f"### **{package['name']}**")
                else:
                    st.markdown(f"### {package['name']}")
                
                # Credits amount
                st.markdown(f"**{package['credits']} Credits**")
                
                # Price
                st.markdown(f"### ${package['price_dollars']:.2f}")
                
                # Per credit cost
                st.markdown(f"*${package['per_credit_cost']:.2f} per credit*")

                # Realistic estimate: on average, each NOI analysis takes ~2 hours when done manually.
                # With the tool, most of that labour is automated, leaving only review/adjustment (~15 min).
                # That equates to roughly 1.75 hours saved per analysis. We round to whole hours for clarity:
                hours_saved = int(round(package['credits'] * 1.75))
                st.markdown(
                    f"""
                    <div style='color:#FACC15; font-weight:600; text-align:center; margin-top:0.5rem;'>
                        ⏱ Save ~{hours_saved} hours of work!
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                # Savings badge (or placeholder for consistent height)
                if savings_text:
                    st.success(savings_text)
                else:
                    # Use st.success to create identical styling to other badges
                    st.success("Ideal entry point 🚀")
                
                # Description
                st.caption(package.get('description', f"Top up {package['credits']} credits"))
                
                # Purchase button with loading state
                email = st.session_state.get('user_email', '')
                button_key = f"buy_{package['package_id']}"
                
                if not email:
                    st.warning("Please enter your email in the main app to purchase credits.")
                else:
                    # Create loading button for package purchase
                    purchase_clicked, purchase_button_placeholder = create_loading_button(
                        f"Buy {package['name']}",
                        key=button_key,
                        use_container_width=True,
                        type="primary"
                    )
                    
                    if purchase_clicked:
                        logger.info(f"Purchase button clicked for package {package['name']}")
                        
                        # Show button loading state
                        show_button_loading(purchase_button_placeholder, "Processing...")
                        
                        # Call purchase function
                        purchase_credits(email, package['package_id'], package['name'])
                        
                        # Restore button state (in case of error)
                        restore_button(
                            purchase_button_placeholder, 
                            f"Buy {package['name']}", 
                            key=f"{button_key}_restored",
                            use_container_width=True,
                            type="primary"
                        )
    
    # Add proper spacing after all cards are displayed
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Close the container div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional CSS injection to ensure styles take precedence
    # Using even more specific selectors with ID-based targeting
    st.markdown("""
    <style>
    /* Final override styles with maximum specificity */
    
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]) {
        background: #101922 !important;
        border: 1px solid #1f2a36 !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.35) !important;
    }
    
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]):hover,
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]):hover {
        border-color: #0E4DE3 !important;
        background: rgba(14, 77, 227, 0.05) !important;
    }
    
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"],
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button {
        background: linear-gradient(135deg, #0E4DE3 0%, #1C5CF5 100%) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 16px rgba(14, 77, 227, 0.4) !important;
    }
    
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:hover,
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:hover,
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] button[kind="primary"]:hover,
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:hover {
        background: linear-gradient(135deg, #1C5CF5 0%, #2563EB 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 20px rgba(14, 77, 227, 0.6) !important;
    }
    
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"],
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"] {
        background: linear-gradient(135deg, #22C55E, #16A34A) !important;
        color: #FFFFFF !important;
        border: 2px solid rgba(34, 197, 94, 0.5) !important;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3) !important;
    }
    
    /* Ensure text colors are properly set */
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] h3 {
        color: #FFFFFF !important;
    }
    
    #credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"] *,
    div#credit-store-container [data-testid="column"] > div[data-testid="stVerticalBlock"] [data-testid="stAlert"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

def purchase_credits(email: str, package_id: str, package_name: str):
    """Handle credit purchase with loading states"""
    # Get loading message for credit purchase
    loading_msg, loading_subtitle = get_loading_message_for_action("credit_purchase")
    
    # Show loading indicator with payment-specific messaging
    loading_container = st.empty()
    with loading_container.container():
        display_loading_spinner(
            f"Setting up secure payment for {package_name}...",
            "You'll be redirected to Stripe to complete your purchase safely."
        )
    
    try:
        # Add debug logging
        logger.info(f"Attempting to purchase credits: email={email}, package_id={package_id}, package_name={package_name}")
        logger.info(f"Backend URL: {BACKEND_URL}")
        
        # Test backend connection first
        if not test_backend_connection():
            loading_container.empty()
            st.error("❌ **Backend API Unavailable**")
            st.info(f"""
            **Debug Information:**
            - Backend URL: `{BACKEND_URL}`
            - The API server is not responding
            - Please ensure the API server is running
            
            **Quick Fix:**
            Try running one of these commands to start the API server:
            ```
            python api_server_minimal.py
            ```
            or
            ```
            python ultra_minimal_api.py
            ```
            """)
            return
        
        # Make the purchase request
        url = f"{BACKEND_URL}/pay-per-use/credits/purchase"
        data = {"email": email, "package_id": package_id}
        
        logger.info(f"Making POST request to: {url}")
        logger.info(f"Request data: {data}")
        
        response = requests.post(
            url,
            data=data,
            timeout=30,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response text: {response.text[:500]}...")  # Log first 500 chars
        
        if response.status_code == 200:
            result = response.json()
            checkout_url = result.get('checkout_url')
            
            if checkout_url:
                # Clear loading spinner first
                loading_container.empty()
                
                # Show payment redirect with inline loading
                with st.container():
                    display_inline_loading(
                        "🔄 Redirecting to secure Stripe checkout...",
                        "💳"
                    )
                    
                    # Brief delay to show the redirect message
                    time.sleep(1)
                    
                    # Immediate redirect via meta refresh and JS fallback
                    st.markdown(f"""
                    <meta http-equiv='refresh' content='0; url={checkout_url}' />
                    <script>
                        window.location.href = '{checkout_url}';
                    </script>
                    """, unsafe_allow_html=True)
                    
                    # Provide manual link only if redirect fails (rare)
                    st.markdown(f"<small>If you are not redirected, <a href='{checkout_url}' target='_blank'>click here to continue to Stripe.</a></small>", unsafe_allow_html=True)
            else:
                loading_container.empty()
                st.error("❌ Failed to create checkout session.")
                st.info(f"Server response: {result}")
        else:
            loading_container.empty()
            error_msg = f"Failed to initiate purchase: {response.text}"
            st.error(f"❌ {error_msg}")
            
            # Show detailed error info
            with st.expander("🔧 Debug Information"):
                st.code(f"""
Status Code: {response.status_code}
URL: {url}
Request Data: {data}
Response: {response.text}
                """)
                
                # Suggest alternative solutions
                st.markdown("""
                **Possible Solutions:**
                1. Check if the API server is running
                2. Verify the BACKEND_URL environment variable
                3. Check if the package_id is valid
                4. Try refreshing the page and trying again
                """)
            
    except requests.exceptions.ConnectionError as e:
        loading_container.empty()
        st.error("❌ **Connection Error**")
        st.error("Cannot connect to the backend API server.")
        with st.expander("🔧 Technical Details"):
            st.code(f"""
Backend URL: {BACKEND_URL}
Error: {str(e)}
            """)
            st.markdown("""
            **Solutions:**
            1. Make sure the API server is running
            2. Check your internet connection
            3. Verify the BACKEND_URL is correct
            """)
        
    except requests.exceptions.Timeout as e:
        loading_container.empty()
        st.error("❌ **Request Timeout**")
        st.error("The request took too long to complete.")
        st.info("Please try again. If the problem persists, contact support.")
        
    except Exception as e:
        loading_container.empty()
        logger.error(f"Unexpected error during purchase: {str(e)}", exc_info=True)
        st.error(f"❌ **Unexpected Error**")
        st.error(f"An unexpected error occurred: {str(e)}")
        with st.expander("🔧 Technical Details"):
            st.code(f"""
Error Type: {type(e).__name__}
Error Message: {str(e)}
Backend URL: {BACKEND_URL}
            """)
            st.markdown("""
            **Next Steps:**
            1. Try refreshing the page
            2. Check that all required information is correct
            3. Contact support if the issue persists
            """)

def check_credits_for_analysis(email: str) -> tuple[bool, str]:
    """Check if user has enough credits for analysis"""
    if not email:
        return False, "Please enter your email address"
    
    credit_data = get_user_credits(email)
    if not credit_data:
        return False, "Unable to check credit balance"
    
    credits = credit_data.get("credits", 0)
    credits_needed = 1  # Should come from config
    
    if credits >= credits_needed:
        return True, f"You have {credits} credits available"
    else:
        return False, f"You need {credits_needed} credit(s) but only have {credits}"

def deduct_credits_for_analysis(email: str) -> tuple[bool, str, dict]:
    """Actually deduct credits for analysis via backend API
    
    Returns:
        (success, message, user_data)
    """
    if not email:
        return False, "Please enter your email address", {}
    
    try:
        from uuid import uuid4
        analysis_id = str(uuid4())
        
        # Make actual API call to deduct credits
        response = requests.post(
            f"{BACKEND_URL}/pay-per-use/use-credits",
            data={
                "email": email,
                "analysis_id": analysis_id
            },
            timeout=10
        )
        
        if response.status_code == 200:
            # Credits successfully deducted
            result = response.json()
            
            # Get updated user data
            credit_data = get_user_credits(email)
            if credit_data:
                remaining_credits = credit_data.get("credits", 0)
                success_msg = f"Analysis started! 1 credit deducted. {remaining_credits} credits remaining."
                return True, success_msg, credit_data
            else:
                return True, "Analysis started! 1 credit deducted.", {}
        else:
            # Credit deduction failed
            error_msg = f"Credit deduction failed: {response.text}"
            logger.error(f"Credit deduction failed for {email}: {response.status_code} - {response.text}")
            return False, error_msg, {}
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to credit service for {email}: {e}")
        return False, "Cannot connect to credit service", {}
    except Exception as e:
        logger.error(f"Unexpected error during credit deduction for {email}: {e}")
        return False, f"Credit system error: {str(e)}", {}

def display_insufficient_credits():
    """Display message when user has insufficient credits with loading states"""
    st.error("🔴 **Insufficient Credits**")
    st.markdown("""
    You don't have enough credits to run this analysis. Each analysis requires **1 credit**.
    
    **New users get 1 free credit** to try our service!
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced buy credits button with loading state
        buy_clicked, buy_button_placeholder = create_loading_button(
            "🛒 Buy Credits", 
            key="insufficient_buy_credits",
            use_container_width=True
        )
        
        if buy_clicked:
            logger.info("Insufficient credits - Buy Credits button clicked")
            
            # Show loading state
            show_button_loading(buy_button_placeholder, "Loading Store...")
            
            # Brief loading feedback
            time.sleep(0.3)
            
            st.session_state.show_credit_store = True
            st.rerun()
    
    with col2:
        # Enhanced view pricing button with loading state
        pricing_clicked, pricing_button_placeholder = create_loading_button(
            "📊 View Pricing", 
            key="insufficient_view_pricing",
            use_container_width=True
        )
        
        if pricing_clicked:
            logger.info("Insufficient credits - View Pricing button clicked")
            
            # Show loading state
            show_button_loading(pricing_button_placeholder, "Loading Pricing...")
            
            # Brief loading feedback
            time.sleep(0.3)
            
            st.session_state.show_credit_store = True  # Use the same store interface
            st.rerun()

def display_free_trial_welcome(email: str):
    """Display welcome message for new users with free trial - only once per session"""
    # Check if we've already shown the welcome message for this email in this session
    welcome_key = f"free_trial_welcome_shown_{email}"
    if st.session_state.get(welcome_key, False):
        return
    
    credit_data = get_user_credits(email)
    if not credit_data:
        return
    
    # Check if this is a new user who just got free trial credits (never used any)
    # Fixed logic: free_trial_used should be True for users who received free credits
    is_new_user = (credit_data.get("total_used", 0) == 0 and 
                   credit_data.get("free_trial_used", False) and  # This should be True for users with free trial
                   credit_data.get("credits", 0) > 0)
    
    # Check if this is a returning user
    is_returning_user = (credit_data.get("total_used", 0) > 0 or 
                        credit_data.get("total_purchased", 0) > 0)
    
    if is_new_user:
        # Get the actual number of free trial credits from environment
        free_credits = int(os.getenv("FREE_TRIAL_CREDITS", "1"))
        
        st.success(f"🎉 **Welcome! You've received {free_credits} free trial credit{'s' if free_credits != 1 else ''}!**")
        st.info("Each NOI analysis uses 1 credit. Try our service risk-free!")
        
        # Store that we've shown this message for this email in this session
        st.session_state[welcome_key] = True
        st.balloons()
    elif is_returning_user:
        # Show returning user message
        st.info(f"👋 **Welcome back!** You have {credit_data.get('credits', 0)} credits remaining.")
        
        # Store that we've shown this message for this email in this session
        st.session_state[welcome_key] = True

def init_credit_system():
    """Initialize credit system - call this early in your main app"""
    # No initialization needed for simple server implementation
    pass
    
    # Add JavaScript to handle credit purchase success messages
    st.markdown("""
    <script>
    // Listen for credit purchase success messages from payment window
    window.addEventListener('message', function(event) {
        if (event.data.type === 'CREDIT_PURCHASE_SUCCESS' && event.data.action === 'RETURN_TO_MAIN') {
            console.log('Credit purchase successful, returning to main interface');
            // Clear credit store flag and return to main app
            window.parent.postMessage({
                type: 'STREAMLIT_MESSAGE',
                message: 'CLEAR_CREDIT_STORE'
            }, '*');
        }
    });
    
    // Check URL parameters for credit success
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('credit_success') === '1' && urlParams.get('return_to_main') === '1') {
        console.log('Credit success detected in URL, clearing store flag');
        // Remove the URL parameters and refresh to main interface
        const newUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
        
        // Force a refresh to clear the credit store state
        setTimeout(function() {
            window.location.reload();
        }, 100);
    }
    </script>
    """, unsafe_allow_html=True) 
