import streamlit as st
import requests
import os
from typing import Dict, Any, Optional
import logging
import time
import json

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
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

def display_credit_store():
    """Display credit purchase interface with robust inline styling"""
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
    logger.info(f"[CREDITS_DEBUG] Session ID: {st.session_state.get('session_id', 'Not set')}")
    
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
    
    # Add debugging information to help troubleshoot
    st.markdown(
        f"""
        <div style="
            background-color: #1a2436; 
            border: 1px solid #2a3a50; 
            border-radius: 8px; 
            padding: 1rem; 
            margin-bottom: 1rem;
        ">
            <h3 style="color: #FFFFFF; margin-top: 0;">🔍 Debug Information</h3>
            <p style="color: #A0A0A0; margin-bottom: 0.5rem;">If you're seeing this, the credit store function is being called correctly.</p>
            <p style="color: #A0A0A0; margin-bottom: 0.5rem;">If the UI still looks wrong, it's likely a CSS specificity issue.</p>
            <p style="color: #FACC15; margin-bottom: 0;">This robust implementation uses inline styles to avoid CSS conflicts.</p>
            <p style="color: #6495ED; margin-bottom: 0;">Session ID: {st.session_state.get('session_id', 'Not set')}</p>
            <p style="color: #6495ED; margin-bottom: 0;">Environment: {"Render" if os.getenv('RENDER') else "Local"}</p>
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
        "outline": "3px solid #ff0000"  # RED OUTLINE FOR DEBUGGING - should be visible now
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
            
            # Savings badge
            if savings_text:
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
            elif len(packages) > 1 and idx == 0:
                # For the best value package (first one), show a different badge
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