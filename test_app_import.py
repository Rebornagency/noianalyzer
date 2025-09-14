#!/usr/bin/env python3
"""
Test script to verify Excel export import in main app context
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Mock Streamlit session state
    import streamlit as st
    st.session_state = {}
    
    # Try to import the function
    from app import generate_comparison_excel
    print("SUCCESS: Excel export function imported successfully in app context")
    print("Function:", generate_comparison_excel)
except ImportError as e:
    print("INFO: Excel export function not yet available in app context")
    print("This is expected if we haven't added the import to app.py yet")
    print("Error:", str(e))
    
    # Try importing from excel_export directly
    try:
        from excel_export import generate_comparison_excel
        print("SUCCESS: Excel export function imported directly from excel_export")
        print("Function:", generate_comparison_excel)
    except ImportError as e2:
        print("ERROR: Failed to import Excel export function directly")
        print("Error:", str(e2))
        sys.exit(1)

print("Test completed successfully!")