import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the display_credit_store function
from utils.credit_ui_minimal import display_credit_store

st.set_page_config(
    page_title="Minimal Credit Store Test",
    page_icon="💳",
    layout="wide"
)

st.title("Minimal Credit Store UI Test")

# Set a test email
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

# Add info about what we're testing
st.markdown("""
<div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
    <h3 style="color: #FFFFFF; margin-top: 0;">🧪 Testing Minimal Credit Store UI</h3>
    <p style="color: #A0A0A0; margin-bottom: 0;">This test page should show the credit store with:</p>
    <ul style="color: #A0A0A0;">
        <li>Modern card-based layout</li>
        <li>RED OUTLINES around package cards (CRITICAL - this confirms CSS is working)</li>
        <li>No debug information container at the top</li>
        <li>"5 Credits!" tag on Starter pack</li>
        <li>"Best Value!" tag on Professional pack</li>
        <li>Properly rendered package information (not raw HTML)</li>
        <li>Functional purchase buttons</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Display the credit store
display_credit_store()