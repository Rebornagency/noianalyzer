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
    
    # Modern header styling with inline styles
    st.markdown(
        f"""
        <div style="
            text-align: center; 
            margin-bottom: 2rem;
            color: #FFFFFF;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        ">
            <h1 style="
                color: #FFFFFF; 
                font-size: 2.5rem; 
                font-weight: 700; 
                margin-bottom: 0.5rem;
            ">
                💳 Credit Store
            </h1>
            <p style="
                color: #A0A0A0; 
                font-size: 1.2rem; 
                margin-bottom: 1rem;
            ">
                Purchase credits to unlock NOI analysis capabilities
            </p>
            <p style="
                color: #FACC15; 
                font-size: 1.1rem; 
                font-weight: 600;
            ">
                ⏱ Save <span style="font-weight: 800;">up to 3 hours</span> of manual spreadsheet work per analysis
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Display packages in a responsive grid using Streamlit columns with custom styling
    num_packages = len(packages)
    if num_packages == 1:
        cols = st.columns(1)
    elif num_packages == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(min(num_packages, 3))
    
    log_credit_ui_debug(f"Created {len(cols)} columns for packages")
    
    # Define common styles as variables for consistency
    card_style = {
        "background": "linear-gradient(145deg, #1a2436, #0f1722)",
        "border": "1px solid #2a3a50",
        "border_radius": "16px",
        "box_shadow": "0 10px 25px rgba(0, 0, 0, 0.4)",
        "padding": "2rem",
        "margin": "1.5rem 0",
        "text_align": "center",
        "transition": "all 0.3s ease",
        "height": "100%",
        "display": "flex",
        "flex_direction": "column",
        "align_items": "center",
        "justify_content": "flex-start",
        "width": "100%",
        "position": "relative",
        "box_sizing": "border-box",
        "color": "#FFFFFF",
        "outline": "2px solid #ff0000"  # RED OUTLINE FOR DEBUGGING - should be visible now
    }
    
    # Convert card style to inline CSS string
    card_css = "; ".join([f"{k.replace('_', '-')}: {v}" for k, v in card_style.items()])
    
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
            
            # Create the card container with inline styles
            st.markdown(
                f"""
                <div style="{card_css}">
                    <h3 style="
                        color: #FFFFFF;
                        font-size: 1.8rem;
                        font-weight: 700;
                        margin: 0 0 1.5rem 0;
                        padding-bottom: 1rem;
                        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                        display: block;
                        width: 100%;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        {"🌟 " + package["name"] + " (Popular)" if idx == 1 and len(packages) > 2 else package["name"]}
                    </h3>
                    
                    <div style="
                        color: #FFFFFF;
                        font-size: 1.3rem;
                        font-weight: 600;
                        margin: 1rem 0;
                        display: block;
                        width: 100%;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        {package["credits"]} Credits
                    </div>
                    
                    <div style="
                        color: #FFFFFF;
                        font-size: 2.5rem;
                        font-weight: 800;
                        margin: 1rem 0;
                        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                        display: block;
                        width: 100%;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        ${package["price_dollars"]:.2f}
                    </div>
                    
                    <div style="
                        color: #A0A0A0;
                        font-size: 1rem;
                        font-style: italic;
                        margin: 0.5rem 0 1.5rem 0;
                        display: block;
                        width: 100%;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        ${package["per_credit_cost"]:.2f} per credit
                    </div>
                """,
                unsafe_allow_html=True
            )
            
            # Savings badge - Updated logic
            # Show "5 Credits!" for the Starter pack (first package)
            if idx == 0 and len(packages) > 1:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #3b82f6, #2563eb);
                        color: #FFFFFF;
                        font-weight: 700;
                        font-size: 1.1rem;
                        padding: 0.8rem 1.5rem;
                        border-radius: 50px;
                        margin: 1rem auto;
                        width: fit-content;
                        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
                        display: inline-block;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        5 Credits!
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            # Show "Best Value!" for the Professional pack (middle package)
            elif idx == 1 and len(packages) > 2:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #10b981, #059669);
                        color: #FFFFFF;
                        font-weight: 700;
                        font-size: 1.1rem;
                        padding: 0.8rem 1.5rem;
                        border-radius: 50px;
                        margin: 1rem auto;
                        width: fit-content;
                        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                        display: inline-block;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        Best Value! 🚀
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            # Show savings percentage for other packages
            elif savings_text:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #10b981, #059669);
                        color: #FFFFFF;
                        font-weight: 700;
                        font-size: 1.1rem;
                        padding: 0.8rem 1.5rem;
                        border-radius: 50px;
                        margin: 1rem auto;
                        width: fit-content;
                        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                        display: inline-block;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        {savings_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            # Show "Best Value!" for the first package (original logic as fallback)
            elif len(packages) > 1 and idx == 0:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #10b981, #059669);
                        color: #FFFFFF;
                        font-weight: 700;
                        font-size: 1.1rem;
                        padding: 0.8rem 1.5rem;
                        border-radius: 50px;
                        margin: 1rem auto;
                        width: fit-content;
                        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                        display: inline-block;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    ">
                        Best Value! 🚀
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Time savings calculation
            hours_saved = int(round(package['credits'] * 1.75))
            st.markdown(
                f"""
                <div style="
                    color: #FACC15;
                    font-weight: 700;
                    font-size: 1.1rem;
                    margin: 1rem 0;
                    display: block;
                    width: 100%;
                    text-align: center;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                ">
                    ⏱ Save ~{hours_saved} hours of work!
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Description
            description_text = package.get('description', f"Top up {package['credits']} credits")
            st.markdown(
                f"""
                <div style="
                    color: #D0D0D0;
                    font-size: 1rem;
                    line-height: 1.6;
                    margin: 1.5rem 0;
                    flex-grow: 1;
                    display: block;
                    width: 100%;
                    text-align: center;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                ">
                    {description_text}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Purchase button with loading state
            email = st.session_state.get('user_email', '')
            
            if not email:
                st.warning("Please enter your email in the main app to purchase credits.")
                st.markdown(
                    '<button class="purchase-button" disabled style="'
                    'background: #6b7280; '
                    'color: #FFFFFF; '
                    'border: none; '
                    'border-radius: 12px; '
                    'padding: 1rem 1.5rem; '
                    'font-size: 1.1rem; '
                    'font-weight: 700; '
                    'width: calc(100% - 2rem); '
                    'cursor: not-allowed; '
                    'margin: 0.5rem auto; '
                    'display: block; '
                    'text-align: center; '
                    'height: auto; '
                    'box-sizing: border-box; '
                    '">Enter Email to Buy</button>',
                    unsafe_allow_html=True
                )
            else:
                # Create unique key for each button (simplified)
                button_key = f"buy_{package['package_id']}"
                
                # Use Streamlit button with custom styling through CSS
                clicked = st.button(
                    f"Buy {package['name']}", 
                    key=button_key, 
                    use_container_width=True
                )
                
                if clicked:
                    logger.info(f"Purchase button clicked for package {package['name']} (ID: {package['package_id']})")
                    log_credit_ui_debug(f"Purchase button clicked for package {package['name']} (ID: {package['package_id']})")
                    
                    # Show loading state using Streamlit button
                    with st.spinner("Setting up secure payment..."):
                        # Call purchase function
                        purchase_credits(email, package['package_id'], package['name'])
            
            # Close card div
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add proper spacing after all cards are displayed
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    log_credit_ui_debug("Finished display_credit_store function")

def purchase_credits(email: str, package_id: str, package_name: str):
    """Handle credit purchase with loading states - minimal implementation"""
    try:
        # Show loading indicator
        with st.spinner("Setting up secure payment..."):
            # Make the purchase request
            url = f"{BACKEND_URL}/pay-per-use/credits/purchase"
            data = {"email": email, "package_id": package_id}
            
            response = requests.post(
                url,
                data=data,
                timeout=30,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                result = response.json()
                checkout_url = result.get('checkout_url')
                
                if checkout_url:
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
                    st.error("❌ Failed to create checkout session.")
            else:
                error_msg = f"Failed to initiate purchase: {response.text}"
                st.error(f"❌ {error_msg}")
                
    except Exception as e:
        logger.error(f"Unexpected error during purchase: {str(e)}", exc_info=True)
        st.error(f"❌ **Unexpected Error**")
        st.error(f"An unexpected error occurred: {str(e)}")

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
