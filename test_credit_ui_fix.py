import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.credit_ui import display_credit_store

st.set_page_config(
    page_title="Credit Store Test",
    page_icon="💳",
    layout="wide"
)

st.title("Credit Store UI Test")

# Set a test email
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

# Display the credit store
display_credit_store()