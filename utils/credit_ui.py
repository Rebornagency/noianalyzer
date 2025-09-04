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
    def display_loading_spinner(message: str = "Processing...", subtitle: str = ""):
        st.info(f"{message} {subtitle or ''}")
    def display_inline_loading(message: str = "Loading...", icon: str = "⏳"):
        st.info(f"{icon} {message}")
    def get_loading_message_for_action(action: str, file_count: int = 1) -> tuple:
        return ("Processing...", "Please wait...")
    def create_loading_button(label: str, key: str = "", help_text: str = "", **kwargs):
        # Handle help parameter conflicts - prefer explicit help_text over kwargs help
        if help_text:
            kwargs['help'] = help_text
        return st.button(label, key=key or None, **kwargs), st.empty()
    def show_button_loading(button_placeholder, label: str = "Processing..."):
        button_placeholder.button(label, disabled=True)
    def restore_button(button_placeholder, label: str, key: str = "", **kwargs):
        button_placeholder.button(label, key=key or None, **kwargs)

# Configure logging with better formatting for Render and Sentry
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This ensures logs go to stdout which Render captures
    ]
)
logger = logging.getLogger(__name__)

# Add specific logging for credit UI debugging
credit_ui_logger = logging.getLogger("credit_ui_debug")
credit_ui_logger.setLevel(logging.DEBUG)

def log_credit_ui_debug(message):
    """Log debug messages specifically for credit UI issues"""
    credit_ui_logger.debug(f"[CREDIT_UI_DEBUG] {message}")

def get_backend_url():
    """Get the correct backend URL by testing available options"""
    # First check environment variable
    backend_url = os.getenv("BACKEND_URL")
    if backend_url:
        logger.info(f"Using BACKEND_URL from environment variable: {backend_url}")
        return backend_url
    
    # Try production server first since it's more likely to be working
    test_urls = [
        "https://noianalyzer-1.onrender.com",  # Production credit service (primary)
        "http://localhost:8000",  # FastAPI servers
        "http://localhost:10000"  # Ultra minimal server
    ]
    
    for url in test_urls:
        try:
            logger.info(f"Testing connection to backend: {url}")
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"Backend connected successfully: {url}")
                return url
        except Exception as e:
            logger.warning(f"Failed to connect to {url}: {e}")
            continue
    
    # Default fallback to production
    logger.warning("No backend server responding, using production as fallback")
    return "https://noianalyzer-1.onrender.com"

# Update the global BACKEND_URL
BACKEND_URL = get_backend_url()

def get_user_credits(email: str) -> Optional[Dict[str, Any]]:
    """Get user credit information from API"""
    try:
        # Try the new endpoint first
        response = requests.get(f"{BACKEND_URL}/pay-per-use/credits/{email}", timeout=10)
        if response.status_code == 200:
            return response.json()
        # If that fails, try the old endpoint
        elif response.status_code == 404:
            response = requests.get(f"{BACKEND_URL}/credits?email={email}", timeout=10)
            if response.status_code == 200:
                return response.json()
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
        # Try the new endpoint first
        response = requests.get(f"{BACKEND_URL}/pay-per-use/packages", timeout=10)
        if response.status_code == 200:
            return response.json()
        # If that fails, try the old endpoint
        elif response.status_code == 404:
            response = requests.get(f"{BACKEND_URL}/packages", timeout=10)
            if response.status_code == 200:
                return response.json()
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
    except Exception as e:
        logger.error(f"Backend connection test failed: {e}")
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
    """Display credit purchase interface with modern, organized layout"""
    # Add comprehensive debug logging
    log_credit_ui_debug("Starting display_credit_store function")
    log_credit_ui_debug(f"Session state keys: {list(st.session_state.keys())}")
    
    # Server-side debug logging
    logger.info("[CREDITS] GET /credits requested", { 
        "path": "/credits",
        "function": "display_credit_store"
    })
    
    packages = get_credit_packages()
    log_credit_ui_debug(f"Retrieved {len(packages)} credit packages")
    
    # Additional debugging for Render environment
    logger.info(f"[CREDITS_DEBUG] Running on Render: {os.getenv('RENDER', 'false')}")
    logger.info(f"[CREDITS_DEBUG] Backend URL: {BACKEND_URL}")
    logger.info(f"[CREDITS_DEBUG] User email: {st.session_state.get('user_email', 'Not set')}")
    
    if not packages:
        st.error("Unable to load credit packages. Please try again later.")
        log_credit_ui_debug("Failed to load credit packages")
        return
    
    # Modern header styling
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #FFFFFF; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">
            💳 Credit Store
        </h1>
        <p style="color: #A0A0A0; font-size: 1.2rem; margin-bottom: 1rem;">
            Purchase credits to unlock NOI analysis capabilities
        </p>
        <p style="color: #FACC15; font-size: 1.1rem; font-weight: 600;">
            ⏱ Save <span style="font-weight: 800;">up to 3 hours</span> of manual spreadsheet work per analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add debugging information to help troubleshoot
    st.markdown("""
    <div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <h3 style="color: #FFFFFF; margin-top: 0;">🔍 Debug Information</h3>
        <p style="color: #A0A0A0; margin-bottom: 0.5rem;">If you're seeing this, the credit store function is being called correctly.</p>
        <p style="color: #A0A0A0; margin-bottom: 0.5rem;">If the UI still looks wrong, it's likely a CSS specificity issue.</p>
        <p style="color: #FACC15; margin-bottom: 0;">Look for the red outline around package cards to confirm CSS is loading.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced CSS for modern, clean package cards with proper centering
    st.markdown("""
    <style>
    /* ULTRA-SPECIFIC CSS RESET for credit store to override all global styles */
    
    /* Nuclear option: Reset everything inside our container with highest specificity */
    #credit-store-container,
    #credit-store-container *,
    #credit-store-container *::before,
    #credit-store-container *::after {
        all: unset !important;
        box-sizing: border-box !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* Reapply essential base styles */
    #credit-store-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 0 1rem !important;
        width: 100% !important;
        display: block !important;
        color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* Ultra-specific column layout fix */
    #credit-store-container [data-testid="column"],
    #credit-store-container div[data-testid="column"],
    #credit-store-container div[data-testid="column"] > div,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Nuclear option for credit package cards - maximum specificity */
    #credit-store-container div[data-testid="column"] > div:not([data-testid="stVerticalBlockBorderWrapper"]),
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div:not([data-testid="stVerticalBlockBorderWrapper"]),
    #credit-store-container div.credit-package-card,
    #credit-store-container div[data-testid="column"] div.credit-package-card {
        background: linear-gradient(145deg, #1a2436, #0f1722) !important;
        border: 1px solid #2a3a50 !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
        padding: 2rem !important;
        margin: 1.5rem 0 !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        position: relative !important;
        box-sizing: border-box !important;
        color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* Hover effect with maximum specificity */
    #credit-store-container div[data-testid="column"] > div:not([data-testid="stVerticalBlockBorderWrapper"]):hover,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]):hover,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div:not([data-testid="stVerticalBlockBorderWrapper"]):hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5) !important;
        border-color: #3b82f6 !important;
    }
    
    /* Text elements - nuclear option for centering */
    #credit-store-container h3,
    #credit-store-container div h3,
    #credit-store-container div[data-testid="column"] h3,
    #credit-store-container div[data-testid="column"] > div h3,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div h3,
    #credit-store-container div.credit-package-card h3,
    #credit-store-container .credits-amount,
    #credit-store-container div .credits-amount,
    #credit-store-container div[data-testid="column"] .credits-amount,
    #credit-store-container div[data-testid="column"] > div .credits-amount,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .credits-amount,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .credits-amount,
    #credit-store-container div.credit-package-card .credits-amount,
    #credit-store-container .price,
    #credit-store-container div .price,
    #credit-store-container div[data-testid="column"] .price,
    #credit-store-container div[data-testid="column"] > div .price,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .price,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .price,
    #credit-store-container div.credit-package-card .price,
    #credit-store-container .per-credit,
    #credit-store-container div .per-credit,
    #credit-store-container div[data-testid="column"] .per-credit,
    #credit-store-container div[data-testid="column"] > div .per-credit,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .per-credit,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .per-credit,
    #credit-store-container div.credit-package-card .per-credit,
    #credit-store-container .savings-badge,
    #credit-store-container div .savings-badge,
    #credit-store-container div[data-testid="column"] .savings-badge,
    #credit-store-container div[data-testid="column"] > div .savings-badge,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .savings-badge,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .savings-badge,
    #credit-store-container div.credit-package-card .savings-badge,
    #credit-store-container .description,
    #credit-store-container div .description,
    #credit-store-container div[data-testid="column"] .description,
    #credit-store-container div[data-testid="column"] > div .description,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .description,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .description,
    #credit-store-container div.credit-package-card .description,
    #credit-store-container .time-savings,
    #credit-store-container div .time-savings,
    #credit-store-container div[data-testid="column"] .time-savings,
    #credit-store-container div[data-testid="column"] > div .time-savings,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .time-savings,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .time-savings,
    #credit-store-container div.credit-package-card .time-savings {
        text-align: center !important;
        width: 100% !important;
        display: block !important;
        color: #FFFFFF !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* Specific text styling with maximum specificity */
    #credit-store-container h3,
    #credit-store-container div h3,
    #credit-store-container div[data-testid="column"] h3,
    #credit-store-container div[data-testid="column"] > div h3,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div h3,
    #credit-store-container div.credit-package-card h3 {
        color: #FFFFFF !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin: 0 0 1.5rem 0 !important;
        padding-bottom: 1rem !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1) !important;
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    #credit-store-container .credits-amount,
    #credit-store-container div .credits-amount,
    #credit-store-container div[data-testid="column"] .credits-amount,
    #credit-store-container div[data-testid="column"] > div .credits-amount,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .credits-amount,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .credits-amount,
    #credit-store-container div.credit-package-card .credits-amount {
        color: #FFFFFF !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        margin: 1rem 0 !important;
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    #credit-store-container .price,
    #credit-store-container div .price,
    #credit-store-container div[data-testid="column"] .price,
    #credit-store-container div[data-testid="column"] > div .price,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .price,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .price,
    #credit-store-container div.credit-package-card .price {
        color: #FFFFFF !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        margin: 1rem 0 !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    #credit-store-container .per-credit,
    #credit-store-container div .per-credit,
    #credit-store-container div[data-testid="column"] .per-credit,
    #credit-store-container div[data-testid="column"] > div .per-credit,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .per-credit,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .per-credit,
    #credit-store-container div.credit-package-card .per-credit {
        color: #A0A0A0 !important;
        font-size: 1rem !important;
        font-style: italic !important;
        margin: 0.5rem 0 1.5rem 0 !important;
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    #credit-store-container .savings-badge,
    #credit-store-container div .savings-badge,
    #credit-store-container div[data-testid="column"] .savings-badge,
    #credit-store-container div[data-testid="column"] > div .savings-badge,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .savings-badge,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .savings-badge,
    #credit-store-container div.credit-package-card .savings-badge {
        background: linear-gradient(135deg, #10b981, #059669) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 0.8rem 1.5rem !important;
        border-radius: 50px !important;
        margin: 1rem auto !important;
        width: fit-content !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
        display: inline-block !important;
        text-align: center !important;
    }
    
    #credit-store-container .description,
    #credit-store-container div .description,
    #credit-store-container div[data-testid="column"] .description,
    #credit-store-container div[data-testid="column"] > div .description,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .description,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .description,
    #credit-store-container div.credit-package-card .description {
        color: #D0D0D0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        margin: 1.5rem 0 !important;
        flex-grow: 1 !important;
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    #credit-store-container .time-savings,
    #credit-store-container div .time-savings,
    #credit-store-container div[data-testid="column"] .time-savings,
    #credit-store-container div[data-testid="column"] > div .time-savings,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .time-savings,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .time-savings,
    #credit-store-container div.credit-package-card .time-savings {
        color: #FACC15 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        margin: 1rem 0 !important;
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    /* Button styling with nuclear specificity */
    #credit-store-container .stButton,
    #credit-store-container div .stButton,
    #credit-store-container div[data-testid="column"] .stButton,
    #credit-store-container div[data-testid="column"] > div .stButton,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .stButton,
    #credit-store-container div.credit-package-card .stButton {
        width: 100% !important;
        margin-top: auto !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-sizing: border-box !important;
    }
    
    #credit-store-container .stButton > button,
    #credit-store-container div .stButton > button,
    #credit-store-container div[data-testid="column"] .stButton > button,
    #credit-store-container div[data-testid="column"] > div .stButton > button,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .stButton > button,
    #credit-store-container div.credit-package-card .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 1.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        width: calc(100% - 2rem) !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.5) !important;
        margin: 0.5rem auto !important;
        display: block !important;
        text-align: center !important;
        height: auto !important;
        box-sizing: border-box !important;
    }
    
    #credit-store-container .stButton > button:hover,
    #credit-store-container div .stButton > button:hover,
    #credit-store-container div[data-testid="column"] .stButton > button:hover,
    #credit-store-container div[data-testid="column"] > div .stButton > button:hover,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:hover,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .stButton > button:hover,
    #credit-store-container div.credit-package-card .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(37, 99, 235, 0.7) !important;
    }
    
    #credit-store-container .stButton > button:disabled,
    #credit-store-container div .stButton > button:disabled,
    #credit-store-container div[data-testid="column"] .stButton > button:disabled,
    #credit-store-container div[data-testid="column"] > div .stButton > button:disabled,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button:disabled,
    #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .stButton > button:disabled,
    #credit-store-container div.credit-package-card .stButton > button:disabled {
        background: #6b7280 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
        opacity: 0.7 !important;
    }
    
    /* Responsive adjustments with maximum specificity */
    @media (max-width: 768px) {
        #credit-store-container div[data-testid="column"] > div:not([data-testid="stVerticalBlockBorderWrapper"]),
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div:not([data-testid="stVerticalBlockBorderWrapper"]) {
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
        }
        
        #credit-store-container h3,
        #credit-store-container div h3,
        #credit-store-container div[data-testid="column"] h3,
        #credit-store-container div[data-testid="column"] > div h3,
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] h3,
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div h3,
        #credit-store-container div.credit-package-card h3 {
            font-size: 1.5rem !important;
        }
        
        #credit-store-container .price,
        #credit-store-container div .price,
        #credit-store-container div[data-testid="column"] .price,
        #credit-store-container div[data-testid="column"] > div .price,
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .price,
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .price,
        #credit-store-container div.credit-package-card .price {
            font-size: 2rem !important;
        }
        
        #credit-store-container .stButton > button,
        #credit-store-container div .stButton > button,
        #credit-store-container div[data-testid="column"] .stButton > button,
        #credit-store-container div[data-testid="column"] > div .stButton > button,
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] .stButton > button,
        #credit-store-container div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div .stButton > button,
        #credit-store-container div.credit-package-card .stButton > button {
            padding: 0.8rem !important;
            font-size: 1rem !important;
        }
    }
    
    /* Nuclear override for any global Streamlit interference */
    #credit-store-container [data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]),
    #credit-store-container div[data-testid="stVerticalBlock"]:not([data-testid="stVerticalBlockBorderWrapper"]) {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Add a visible border to help with debugging */
    #credit-store-container div[data-testid="column"] > div:not([data-testid="stVerticalBlockBorderWrapper"]) {
        outline: 2px solid #ff0000 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Client-side debug logging for page mount
    st.markdown("""
    <script>
    console.info("[CREDITS] mounted", { 
        timestamp: new Date().toISOString(), 
        route: window.location.pathname 
    });
    
    // Add comprehensive debug overlay for development
    if (typeof window !== 'undefined') {
        // Remove existing overlay if present
        const existingOverlay = document.getElementById('credits-debug-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        const debugOverlay = document.createElement('div');
        debugOverlay.id = 'credits-debug-overlay';
        debugOverlay.style.position = 'fixed';
        debugOverlay.style.top = '10px';
        debugOverlay.style.right = '10px';
        debugOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
        debugOverlay.style.color = '#00ff00';
        debugOverlay.style.padding = '10px';
        debugOverlay.style.borderRadius = '5px';
        debugOverlay.style.zIndex = '9999';
        debugOverlay.style.fontSize = '12px';
        debugOverlay.style.fontFamily = 'monospace';
        debugOverlay.style.maxWidth = '300px';
        debugOverlay.style.overflow = 'hidden';
        debugOverlay.innerHTML = 'Credits: mounted ✓ (ultra-specific CSS)';
        document.body.appendChild(debugOverlay);
        
        // Log CSS application status
        setTimeout(function() {
            const container = document.getElementById('credit-store-container');
            if (container) {
                debugOverlay.innerHTML += '<br>Container: ✓';
                
                // Check if our styles are applied
                const computedStyle = window.getComputedStyle(container);
                if (computedStyle.maxWidth === '1200px') {
                    debugOverlay.innerHTML += '<br>CSS Applied: ✓';
                } else {
                    debugOverlay.innerHTML += '<br>CSS Applied: ✗';
                    debugOverlay.style.color = '#ff0000';
                }
                
                // Check package cards
                const cards = container.querySelectorAll('[data-testid="column"] > div:not([data-testid="stVerticalBlockBorderWrapper"])');
                debugOverlay.innerHTML += '<br>Cards found: ' + cards.length;
                
                // Log first card styles
                if (cards.length > 0) {
                    const firstCard = cards[0];
                    const cardStyle = window.getComputedStyle(firstCard);
                    debugOverlay.innerHTML += '<br>Card bg: ' + cardStyle.background;
                }
            } else {
                debugOverlay.innerHTML += '<br>Container: ✗';
                debugOverlay.style.color = '#ff0000';
            }
        }, 1000);
        
        // Update overlay with last click info
        window.addEventListener('click', function(e) {
            if (e.target.closest('[data-testid="stButton"] button')) {
                debugOverlay.innerHTML = 'Credits: mounted ✓<br>Last CTA click: ' + new Date().toLocaleTimeString();
            }
        });
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Container div for all packages
    st.markdown('<div id="credit-store-container">', unsafe_allow_html=True)
    
    # Display packages in a responsive grid
    num_packages = len(packages)
    if num_packages == 1:
        cols = st.columns(1)
    elif num_packages == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(min(num_packages, 3))
    
    log_credit_ui_debug(f"Created {len(cols)} columns for packages")
    
    for idx, package in enumerate(packages):
        log_credit_ui_debug(f"Rendering package {idx}: {package.get('name', 'Unknown')}")
        
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
            
            # Modern card container
            st.markdown('<div class="credit-package-card">', unsafe_allow_html=True)
            
            # Package title with special highlighting for popular package
            if idx == 1 and len(packages) > 2:  # Middle package in 3+ packages
                st.markdown(f'<h3>🌟 {package["name"]} (Popular)</h3>', unsafe_allow_html=True)
            else:
                st.markdown(f'<h3>{package["name"]}</h3>', unsafe_allow_html=True)
            
            # Credits amount
            st.markdown(f'<div class="credits-amount">{package["credits"]} Credits</div>', unsafe_allow_html=True)
            
            # Price
            st.markdown(f'<div class="price">${package["price_dollars"]:.2f}</div>', unsafe_allow_html=True)
            
            # Per credit cost
            st.markdown(f'<div class="per-credit">${package["per_credit_cost"]:.2f} per credit</div>', unsafe_allow_html=True)

            # Savings badge - Updated logic
            # Show "5 Credits!" for the Starter pack (first package)
            if idx == 0 and len(packages) > 1:
                st.markdown("""
                <div class="savings-badge" style="
                    background: linear-gradient(135deg, #3b82f6, #2563eb);
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 1.1rem;
                    padding: 0.8rem 1.5rem;
                    border-radius: 50px;
                    margin: 1rem auto;
                    width: fit-content;
                    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
                    text-align: center;
                    display: inline-block;
                ">
                    5 Credits!
                </div>
                """, unsafe_allow_html=True)
            # Show "Best Value!" for the Professional pack (middle package)
            elif idx == 1 and len(packages) > 2:
                st.markdown("""
                <div class="savings-badge" style="
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 1.1rem;
                    padding: 0.8rem 1.5rem;
                    border-radius: 50px;
                    margin: 1rem auto;
                    width: fit-content;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                    text-align: center;
                    display: inline-block;
                ">
                    Best Value! 🚀
                </div>
                """, unsafe_allow_html=True)
            # Show savings percentage for other packages
            elif savings_text:
                st.markdown(f"""
                <div class="savings-badge" style="
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 1.1rem;
                    padding: 0.8rem 1.5rem;
                    border-radius: 50px;
                    margin: 1rem auto;
                    width: fit-content;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                    text-align: center;
                    display: inline-block;
                ">
                    {savings_text}
                </div>
                """, unsafe_allow_html=True)
            # Show "Best Value!" for the first package (original logic as fallback)
            elif len(packages) > 1 and idx == 0:
                st.markdown("""
                <div class="savings-badge" style="
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 1.1rem;
                    padding: 0.8rem 1.5rem;
                    border-radius: 50px;
                    margin: 1rem auto;
                    width: fit-content;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                    text-align: center;
                    display: inline-block;
                ">
                    Best Value! 🚀
                </div>
                """, unsafe_allow_html=True)
            
            # Time savings calculation
            hours_saved = int(round(package['credits'] * 1.75))
            st.markdown(
                f'<div class="time-savings">⏱ Save ~{hours_saved} hours of work!</div>',
                unsafe_allow_html=True,
            )
            
            # Description
            description_text = package.get('description', f"Top up {package['credits']} credits")
            st.markdown(f'<div class="description">{description_text}</div>', unsafe_allow_html=True)
            
            # Purchase button with loading state - Using Streamlit's native button styling to match "Buy More Credits"
            email = st.session_state.get('user_email', '')
            
            if not email:
                st.warning("Please enter your email in the main app to purchase credits.")
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #6b7280, #4b5563);
                    color: #FFFFFF;
                    border: none;
                    border-radius: 12px;
                    padding: 1rem 1.5rem;
                    font-size: 1.1rem;
                    font-weight: 700;
                    width: calc(100% - 2rem);
                    text-align: center;
                    height: auto;
                    box-sizing: border-box;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    margin: 0.5rem auto;
                ">Enter Email to Buy</div>
                """, unsafe_allow_html=True)
            else:
                # Create unique key for each button (simplified)
                button_key = f"buy_{package['package_id']}"
                
                # Use Streamlit button with primary styling to match "Buy More Credits"
                clicked = st.button(f"Buy {package['name']}", key=button_key, use_container_width=True, type="primary")
                
                if clicked:
                    logger.info(f"Purchase button clicked for package {package['name']} (ID: {package['package_id']})")
                    log_credit_ui_debug(f"Purchase button clicked for package {package['name']} (ID: {package['package_id']})")
                    
                    # Show loading state using Streamlit button
                    with st.spinner("Setting up secure payment..."):
                        # Call purchase function
                        purchase_credits(email, package['package_id'], package['name'])
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close card div
    
    # Close the container div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add proper spacing after all cards are displayed
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    log_credit_ui_debug("Finished display_credit_store function")

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
        elif response.status_code == 402:
            # Insufficient credits
            result = response.json()
            error_msg = f"Insufficient credits: {result.get('error', 'Not enough credits')}"
            logger.error(f"Insufficient credits for {email}: {response.status_code} - {response.text}")
            return False, error_msg, {}
        else:
            # Credit deduction failed
            error_msg = f"Credit deduction failed: {response.text}"
            logger.error(f"Credit deduction failed for {email}: {response.status_code} - {response.text}")
            return False, error_msg, {}
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to credit service for {email}: {e}")
        return False, "Cannot connect to credit service. Please try again later.", {}
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to credit service for {email}: {e}")
        return False, "Request timed out. Please try again later.", {}
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