#!/usr/bin/env python3
"""
Script to verify that the Excel export function can be imported from app.py
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Mock Streamlit
    import streamlit as st
    st.session_state = {}
    
    # Try to import the function from app.py
    from app import generate_comparison_excel
    print("SUCCESS: Excel export function imported successfully from app.py")
    print("Function:", generate_comparison_excel)
    print("Type:", type(generate_comparison_excel))
except ImportError as e:
    print("ERROR: Failed to import Excel export function from app.py")
    print("Error:", str(e))
    sys.exit(1)

print("Verification completed successfully!")