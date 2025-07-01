import streamlit as st
import requests
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def get_user_credits(email: str) -> Optional[Dict[str, Any]]:
    """Get user credit information from API"""
    try:
        response = requests.get(f"{BACKEND_URL}/pay-per-use/credits/{email}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get credits for {email}: {response.text}")
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

def display_credit_balance(email: str):
    """Display user's credit balance in sidebar"""
    if not email:
        return
    
    credit_data = get_user_credits(email)
    if not credit_data:
        st.sidebar.error("Unable to load credit balance")
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
    
    # Display packages in columns
    cols = st.columns(min(len(packages), 3))
    
    for idx, package in enumerate(packages):
        col = cols[idx % len(cols)]
        
        with col:
            # Calculate savings
            if idx == 0:
                savings_text = ""
            else:
                base_per_credit = packages[0]["per_credit_cost"]
                current_per_credit = package["per_credit_cost"]
                savings_percent = ((base_per_credit - current_per_credit) / base_per_credit) * 100
                if savings_percent > 0:
                    savings_text = f"<span style='color: #22C55E; font-weight: bold;'>Save {savings_percent:.0f}%!</span>"
                else:
                    savings_text = ""
            
            # Package card
            st.markdown(
                f"""
                <div style="
                    border: 2px solid #E5E7EB;
                    border-radius: 12px;
                    padding: 1.5rem;
                    text-align: center;
                    background: white;
                    margin-bottom: 1rem;
                    {('border-color: #3B82F6; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);' if idx == 1 else '')}
                ">
                    <h3 style="margin-bottom: 0.5rem; color: #1F2937;">{package['name']}</h3>
                    <div style="font-size: 2rem; font-weight: bold; color: #1F2937; margin-bottom: 0.5rem;">
                        {package['credits']} Credits
                    </div>
                    <div style="font-size: 1.5rem; color: #3B82F6; margin-bottom: 0.5rem;">
                        ${package['price_dollars']:.2f}
                    </div>
                    <div style="color: #6B7280; font-size: 0.9rem; margin-bottom: 0.5rem;">
                        ${package['per_credit_cost']:.2f} per credit
                    </div>
                    {savings_text}
                    <div style="color: #6B7280; font-size: 0.8rem; margin-top: 1rem;">
                        {package['description']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Purchase button
            email = st.session_state.get('user_email', '')
            if email and st.button(f"Buy {package['name']}", key=f"buy_{package['package_id']}", use_container_width=True):
                purchase_credits(email, package['package_id'], package['name'])

def purchase_credits(email: str, package_id: str, package_name: str):
    """Handle credit purchase"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/pay-per-use/credits/purchase",
            data={"email": email, "package_id": package_id},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            checkout_url = result.get('checkout_url')
            
            if checkout_url:
                st.success(f"Redirecting to checkout for {package_name}...")
                
                # JavaScript redirect
                st.markdown(f"""
                <script>
                window.open('{checkout_url}', '_self');
                </script>
                """, unsafe_allow_html=True)
                
                # Fallback link
                st.markdown(f"If you're not redirected automatically, [click here to complete purchase]({checkout_url})")
            else:
                st.error("Failed to create checkout session.")
        else:
            st.error(f"Failed to initiate purchase: {response.text}")
            
    except Exception as e:
        st.error(f"Error initiating purchase: {str(e)}")

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
        if st.button("🛒 Buy Credits", use_container_width=True):
            st.session_state.show_credit_store = True
            st.rerun()
    
    with col2:
        if st.button("📊 View Pricing", use_container_width=True):
            st.session_state.show_pricing = True
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