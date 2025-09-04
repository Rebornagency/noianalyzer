import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import both implementations for comparison
from utils.credit_ui import display_credit_store as display_credit_store_original
from utils.credit_ui_fresh import display_credit_store as display_credit_store_fresh

st.set_page_config(
    page_title="Credit Store Comparison",
    page_icon="💳",
    layout="wide"
)

st.title("Credit Store UI Comparison")

# Set a test email
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

# Create tabs for comparison
tab1, tab2 = st.tabs(["Original Implementation", "Fresh Implementation"])

with tab1:
    st.header("Original Credit UI Implementation")
    st.markdown("""
    <div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <h3 style="color: #FFFFFF; margin-top: 0;">Original Implementation</h3>
        <p style="color: #A0A0A0; margin-bottom: 0;">This shows the original credit store UI implementation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    display_credit_store_original()

with tab2:
    st.header("Fresh Credit UI Implementation")
    st.markdown("""
    <div style="background-color: #1a2436; border: 1px solid #2a3a50; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <h3 style="color: #FFFFFF; margin-top: 0;">Fresh Implementation</h3>
        <p style="color: #A0A0A0; margin-bottom: 0;">This shows the fresh credit store UI implementation with simplified CSS.</p>
    </div>
    """, unsafe_allow_html=True)
    
    display_credit_store_fresh()