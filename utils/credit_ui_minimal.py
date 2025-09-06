import streamlit as st
import requests
import os
from typing import Dict, Any, Optional
import logging
import time

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


def display_credit_store():
    """Display credit purchase interface with minimal, robust styling"""
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
            
            # Calculate time savings
            hours_saved = int(round(package['credits'] * 1.75))
            
            # Description text
            description_text = package.get('description', f"Top up {package['credits']} credits")
            
            # Build the complete card HTML in one piece to avoid rendering issues
            card_html = f"""
            <div style="
                background: linear-gradient(145deg, #1a2436, #0f1722);
                border: 1px solid #2a3a50;
                border-radius: 16px;
                padding: 2rem;
                margin: 1.5rem 0;
                text-align: center;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
                width: 100%;
                box-sizing: border-box;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            ">
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
                ">
                    {("🌟 " + package["name"] + " (Popular)") if idx == 1 and len(packages) > 2 else package["name"]}
                </h3>
                
                <div style="
                    color: #FFFFFF;
                    font-size: 1.3rem;
                    font-weight: 600;
                    margin: 1rem 0;
                    display: block;
                    width: 100%;
                    text-align: center;
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
                ">
                    ${package["per_credit_cost"]:.2f} per credit
                </div>
            """
            
            # Add savings badge based on package position
            # Show "5 Credits!" for the Starter pack (first package when there are multiple packages)
            if idx == 0 and len(packages) > 1:
                card_html += f"""
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
                ">
                    5 Credits!
                </div>
                """
            # Show "Best Value!" for the Professional pack (second package when there are 3+ packages, or first package when there are only 2)
            elif (len(packages) > 2 and idx == 1) or (len(packages) == 2 and idx == 1):
                card_html += f"""
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
                ">
                    Best Value! 🚀
                </div>
                """
            # Show savings percentage for other packages (third package and beyond when there are 3+ packages)
            elif savings_text and idx > 1:
                card_html += f"""
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
                ">
                    {savings_text}
                </div>
                """
            
            # Add time savings and description
            card_html += f"""
                <div style="
                    color: #FACC15;
                    font-weight: 700;
                    font-size: 1.1rem;
                    margin: 1rem 0;
                    display: block;
                    width: 100%;
                    text-align: center;
                ">
                    ⏱ Save ~{hours_saved} hours of work!
                </div>
                
                <div style="
                    color: #D0D0D0;
                    font-size: 1rem;
                    line-height: 1.6;
                    margin: 1.5rem 0;
                    flex-grow: 1;
                    display: block;
                    width: 100%;
                    text-align: center;
                ">
                    {description_text}
                </div>
            """
            
            # Add purchase button section
            email = st.session_state.get('user_email', '')
            if not email:
                card_html += """
    <button disabled style="
        background: #6b7280;
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        font-size: 1.1rem;
        font-weight: 700;
        width: calc(100% - 2rem);
        cursor: not-allowed;
        margin: 0.5rem auto;
        display: block;
        text-align: center;
        height: auto;
        box-sizing: border-box;
    ">Enter Email to Buy</button>
</div>
"""
                # Display the complete card
                st.markdown(card_html, unsafe_allow_html=True)
            else:
                # Close the card div but we'll add the button separately using Streamlit
                card_html += "</div>"
                
                # Display the card
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Add debug logging if enabled
                if os.getenv('DEBUG_CREDITS', 'false').lower() == 'true':
                    st.markdown(f"""
<script>
console.info("[CREDITS] mounted");
console.info("[CREDITS] pack render", "{package['package_id']}");
console.info("[CREDITS] pack body type", typeof "{card_html[:50]}...", {{ length: "{len(card_html)}" }});
</script>
""", unsafe_allow_html=True)
                
                # Create unique key for each button
                button_key = f"buy_{package['package_id']}"
                
                # Use loading button to match "Buy More Credits" styling
                clicked, button_placeholder = create_loading_button(
                    f"Buy {package['name']}", 
                    key=button_key, 
                    use_container_width=True,
                    # Add styling to match the homepage "Buy More Credits" button
                    type="primary"
                )
                
                if clicked:
                    logger.info(f"Purchase button clicked for package {package['name']} (ID: {package['package_id']})")
                    log_credit_ui_debug(f"Purchase button clicked for package {package['name']} (ID: {package['package_id']})")
                    
                    # Show loading state
                    show_button_loading(button_placeholder, "Setting up payment...")
                    
                    # Brief loading to show feedback
                    time.sleep(0.5)
                    
                    # Call purchase function
                    purchase_credits(email, package['package_id'], package['name'])
    
    # Add proper spacing after all cards are displayed
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    log_credit_ui_debug("Finished display_credit_store function")