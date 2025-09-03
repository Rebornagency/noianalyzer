#!/usr/bin/env python3
"""
Test script for credit UI debugging
"""

import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the credit UI module
from utils.credit_ui import display_credit_store

def main():
    st.set_page_config(
        page_title="Credit UI Debug Test",
        page_icon="💳",
        layout="wide"
    )
    
    st.title("Credit UI Debug Test Page")
    
    # Initialize session state
    if 'show_credit_store' not in st.session_state:
        st.session_state.show_credit_store = True
        
    if 'user_email' not in st.session_state:
        st.session_state.user_email = "test@example.com"
    
    # Add a debug toggle
    debug_mode = st.checkbox("Debug Mode", value=False)
    
    if debug_mode:
        st.markdown("""
        <div style="position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.8); color: #00ff00; padding: 10px; border-radius: 5px; z-index: 9999; font-family: monospace;">
            Debug Mode: ON<br>
            Check browser console for logs
        </div>
        """, unsafe_allow_html=True)
    
    # Display the credit store
    display_credit_store()

if __name__ == "__main__":
    main()