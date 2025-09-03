#!/usr/bin/env python3
"""
Test script for credit UI fixes
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
        page_title="Credit UI Test",
        page_icon="💳",
        layout="wide"
    )
    
    st.title("Credit UI Test Page")
    
    # Initialize session state
    if 'show_credit_store' not in st.session_state:
        st.session_state.show_credit_store = True
        
    if 'user_email' not in st.session_state:
        st.session_state.user_email = "test@example.com"
    
    # Display the credit store
    display_credit_store()

if __name__ == "__main__":
    main()