import streamlit as st
import requests
import os
from typing import Dict, Any, Optional
import logging
import time

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
            <div style="color: #888; font-size: 0.8rem;">Please start the API server</div>
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
            <div style="color: #888; font-size: 0.8rem;">Check API server connection</div>
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
            <div style="color: #888; font-size: 0.9rem;">Credits</div>
            <div style="color: #888; font-size: 0.8rem;">({status})</div>
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
            <div style="color: #888; font-size: 0.9rem;">Credits Available</div>
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
        
    # Buy more credits button
    if st.sidebar.button("🛒 Buy More Credits", use_container_width=True):
        st.session_state.show_credit_store = True
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
    st.title("🛒 Buy Credits")
    
    packages = get_credit_packages()
    if not packages:
        st.error("Unable to load credit packages. Please try again later.")
        return
    
    st.markdown("### Choose a Credit Package")
    st.markdown("Credits never expire and can be used for any NOI analysis.")
    
    # Display packages in columns using Streamlit native components
    cols = st.columns(min(len(packages), 3))
    
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
                    st.markdown(f"### 🔥 **{package['name']}**")
                else:
                    st.markdown(f"### {package['name']}")
                
                # Credits amount
                st.markdown(f"**{package['credits']} Credits**")
                
                # Price
                st.markdown(f"### ${package['price_dollars']:.2f}")
                
                # Per credit cost
                st.markdown(f"*${package['per_credit_cost']:.2f} per credit*")
                
                # Savings badge (or placeholder for consistent height)
                if savings_text:
                    st.success(savings_text)
                else:
                    # Invisible placeholder to maintain equal card height
                    st.markdown('<div style="height: 2.2rem"></div>', unsafe_allow_html=True)
                
                # Description
                st.caption(package.get('description', f"Top up {package['credits']} credits"))
                
                # Purchase button
                email = st.session_state.get('user_email', '')
                button_key = f"buy_{package['package_id']}"
                
                if not email:
                    st.warning("Please enter your email in the main app to purchase credits.")
                else:
                    if st.button(f"Buy {package['name']}", key=button_key, use_container_width=True, type="primary"):
                        purchase_credits(email, package['package_id'], package['name'])
                
                # Add spacing between cards
                st.markdown("---")

def purchase_credits(email: str, package_id: str, package_name: str):
    """Handle credit purchase"""
    try:
        # Add debug logging
        logger.info(f"Attempting to purchase credits: email={email}, package_id={package_id}, package_name={package_name}")
        logger.info(f"Backend URL: {BACKEND_URL}")
        
        # Test backend connection first
        if not test_backend_connection():
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
                # Use Streamlit's built-in redirect or direct browser navigation
                st.success("🔄 **Redirecting to Stripe checkout...**")
                st.info("Taking you to Stripe to complete your purchase...")
                
                # Use direct browser redirect instead of opening new tab
                st.markdown(f"""
                <script>
                setTimeout(function() {{
                    window.location.href = '{checkout_url}';
                }}, 1000);
                </script>
                """, unsafe_allow_html=True)
                
                # Also provide a manual link as backup
                st.markdown(f"**[Click here if not redirected automatically →]({checkout_url})**")
            else:
                st.error("❌ Failed to create checkout session.")
                st.info(f"Server response: {result}")
        else:
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
        st.error("❌ **Request Timeout**")
        st.error("The request took too long to complete.")
        st.info("Please try again. If the problem persists, contact support.")
        
    except Exception as e:
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

def display_insufficient_credits():
    """Display message when user has insufficient credits"""
    st.error("🔴 **Insufficient Credits**")
    st.markdown("""
    You don't have enough credits to run this analysis. Each analysis requires **1 credit**.
    
    **New users get 3 free credits** to try our service!
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛒 Buy Credits", use_container_width=True, key="insufficient_buy_credits"):
            st.session_state.show_credit_store = True
            st.rerun()
    
    with col2:
        if st.button("📊 View Pricing", use_container_width=True, key="insufficient_view_pricing"):
            st.session_state.show_credit_store = True  # Use the same store interface
            st.rerun()

def display_free_trial_welcome(email: str):
    """Display welcome message for new users with free trial"""
    credit_data = get_user_credits(email)
    if not credit_data:
        return
    
    # Check if this is a new user who just got free trial credits
    if credit_data.get("total_used", 0) == 0 and credit_data.get("free_trial_used", False):
        st.success("🎉 **Welcome! You've received 3 free trial credits!**")
        st.info("Each NOI analysis uses 1 credit. Try our service risk-free!")
        
        # Store that we've shown this message
        if "free_trial_welcome_shown" not in st.session_state:
            st.session_state.free_trial_welcome_shown = True
            st.balloons()

def init_credit_system():
    """Initialize credit system - call this early in your main app"""
    # Create default packages if they don't exist
    try:
        response = requests.post(f"{BACKEND_URL}/pay-per-use/init", timeout=10)
        if response.status_code != 200:
            logger.warning("Failed to initialize credit packages")
    except Exception as e:
        logger.warning(f"Could not initialize credit system: {e}")
    
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