#!/usr/bin/env python3
"""
Test script to verify that the credit_ui module can be imported without errors.
"""

try:
    from utils.credit_ui import display_credit_store, purchase_credits
    print("SUCCESS: Both display_credit_store and purchase_credits imported successfully!")
except Exception as e:
    print(f"ERROR: Failed to import functions: {e}")
    import traceback
    traceback.print_exc()