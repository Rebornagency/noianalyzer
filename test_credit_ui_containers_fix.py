import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Credit UI Containers Fix Test",
    page_icon="💳",
    layout="wide"
)

st.title("Credit UI Containers Fix Test")

# Set a test email
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

st.markdown("""
<div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
    <h3 style="color: #FFFFFF; margin-top: 0;">🔍 Testing Credit UI Containers Fix</h3>
    <p style="color: #A0A0A0; margin-bottom: 0;">This test should show:</p>
    <ul style="color: #A0A0A0;">
        <li>Main header section properly rendered (not raw HTML)</li>
        <li>Package cards with properly rendered information (not raw HTML)</li>
        <li>Green containers (badges) with marketing messages above CTAs:
            <ul>
                <li>"5 Credits!" tag on Starter pack</li>
                <li>"Best Value!" tag on Professional pack</li>
                <li>Savings percentage on other packages</li>
            </ul>
        </li>
        <li>Time savings section properly rendered (not raw HTML)</li>
        <li>CTAs that look like the "Buy More Credits" button with loading states</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Import and display the credit store
try:
    from utils.credit_ui_minimal import display_credit_store
    display_credit_store()
    st.success("✅ Credit store displayed successfully!")
except Exception as e:
    st.error(f"❌ Error displaying credit store: {e}")
    st.exception(e)

st.markdown("""
<div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-top: 2rem;">
    <h3 style="color: #FFFFFF; margin-top: 0;">📋 Verification Checklist</h3>
    <p style="color: #A0A0A0; margin-bottom: 0;">Check that all items are properly rendered (no raw HTML):</p>
    <ul style="color: #A0A0A0;">
        <li>✅ Main header with title, description, and "Save up to 3 hours" text</li>
        <li>✅ Package cards with credits, price, and per-credit cost</li>
        <li>✅ Green marketing badges above CTAs</li>
        <li>✅ Time savings section ("Save ~X hours of work!")</li>
        <li>✅ Package descriptions</li>
        <li>✅ CTAs that match the "Buy More Credits" button styling</li>
    </ul>
</div>
""", unsafe_allow_html=True)