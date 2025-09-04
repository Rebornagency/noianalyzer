import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.credit_ui_robust import display_credit_store

st.set_page_config(
    page_title="Credit Store Test - Robust",
    page_icon="💳",
    layout="wide"
)

st.title("Credit Store UI Test - Robust Implementation")

# Set a test email
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

# Add debug info
st.markdown("""
<div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
    <h3 style="color: #FFFFFF; margin-top: 0;">🧪 Testing Credit Store UI - Robust Implementation</h3>
    <p style="color: #A0A0A0; margin-bottom: 0;">This test page should show the credit store with:</p>
    <ul style="color: #A0A0A0;">
        <li>Modern card-based layout</li>
        <li>Centered text in all elements</li>
        <li>Red outlines around package cards (for debugging)</li>
        <li>Functional purchase buttons</li>
        <li>Robust styling using inline styles instead of CSS selectors</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Display the credit store
display_credit_store()