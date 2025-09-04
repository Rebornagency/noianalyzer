"""
Minimal Credit UI Implementation
This implementation avoids complex dependencies and focuses purely on UI rendering.
"""
import streamlit as st
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_backend_url():
    """Get the correct backend URL"""
    backend_url = os.getenv("BACKEND_URL")
    if backend_url:
        return backend_url
    return "https://noianalyzer-1.onrender.com"

def get_credit_packages():
    """Get available credit packages with minimal dependencies"""
    try:
        BACKEND_URL = get_backend_url()
        response = requests.get(f"{BACKEND_URL}/pay-per-use/packages", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        logger.error(f"Error getting packages: {e}")
        return []

def display_credit_store():
    """Display credit purchase interface with minimal, robust styling"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; color: #FFFFFF;">
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
    
    # Debug information
    st.markdown(f"""
    <div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <h3 style="color: #FFFFFF; margin-top: 0;">🔍 Debug Information</h3>
        <p style="color: #A0A0A0; margin-bottom: 0;">Minimal implementation active</p>
        <p style="color: #FACC15; margin-bottom: 0;">If you see red outlines, CSS is working</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get packages
    packages = get_credit_packages()
    
    if not packages:
        st.error("Unable to load credit packages. Please try again later.")
        return
    
    # Display packages in columns
    cols = st.columns(min(len(packages), 3))
    
    for idx, package in enumerate(packages):
        with cols[idx % len(cols)]:
            # Calculate savings
            savings_text = ""
            if idx > 0 and len(packages) > 1:
                base_per_credit = packages[0]["per_credit_cost"]
                current_per_credit = package["per_credit_cost"]
                savings_percent = ((base_per_credit - current_per_credit) / base_per_credit) * 100
                if savings_percent > 0:
                    savings_text = f"Save {savings_percent:.0f}%!"
            
            # Package card with prominent red outline for debugging
            st.markdown(f"""
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
                outline: 4px solid #ff0000;  /* RED OUTLINE FOR DEBUGGING */
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            ">
                <h3 style="
                    color: #FFFFFF;
                    font-size: 1.8rem;
                    font-weight: 700;
                    margin: 0 0 1.5rem 0;
                    padding-bottom: 1rem;
                    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                    width: 100%;
                    text-align: center;
                ">
                    {package["name"] + " (Popular)" if idx == 1 and len(packages) > 2 else package["name"]}
                </h3>
                
                <div style="
                    color: #FFFFFF;
                    font-size: 1.3rem;
                    font-weight: 600;
                    margin: 1rem 0;
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
                    width: 100%;
                    text-align: center;
                ">
                    ${package["per_credit_cost"]:.2f} per credit
                </div>
            """, unsafe_allow_html=True)
            
            # Savings badge
            if savings_text:
                st.markdown(f"""
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
                    text-align: center;
                ">
                    {savings_text}
                </div>
                """, unsafe_allow_html=True)
            elif len(packages) > 1 and idx == 0:
                st.markdown("""
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
                    text-align: center;
                ">
                    Best Value! 🚀
                </div>
                """, unsafe_allow_html=True)
            
            # Time savings
            hours_saved = int(round(package['credits'] * 1.75))
            st.markdown(f"""
            <div style="
                color: #FACC15;
                font-weight: 700;
                font-size: 1.1rem;
                margin: 1rem 0;
                width: 100%;
                text-align: center;
            ">
                ⏱ Save ~{hours_saved} hours of work!
            </div>
            """, unsafe_allow_html=True)
            
            # Description
            description_text = package.get('description', f"Top up {package['credits']} credits")
            st.markdown(f"""
            <div style="
                color: #D0D0D0;
                font-size: 1rem;
                line-height: 1.6;
                margin: 1.5rem 0;
                flex-grow: 1;
                width: 100%;
                text-align: center;
            ">
                {description_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Purchase button
            email = st.session_state.get('user_email', '')
            if not email:
                st.warning("Please enter your email in the main app to purchase credits.")
                st.markdown("""
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
                """, unsafe_allow_html=True)
            else:
                button_key = f"buy_{package['package_id']}"
                if st.button(f"Buy {package['name']}", key=button_key, use_container_width=True):
                    # In a real implementation, this would redirect to Stripe
                    st.info(f"Would purchase {package['name']} for {email}")
            
            # Close card div
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Add spacing
    st.markdown("<br><br>", unsafe_allow_html=True)