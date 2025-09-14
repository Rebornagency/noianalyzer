#!/usr/bin/env python3
"""
Test script for Excel export functionality
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from excel_export import generate_comparison_excel
    print("SUCCESS: Excel export function imported successfully")
    print("Function:", generate_comparison_excel)
except ImportError as e:
    print("ERROR: Failed to import Excel export function")
    print("Error:", str(e))
    sys.exit(1)

# Test if xlsxwriter is available
try:
    import xlsxwriter
    print("SUCCESS: xlsxwriter is available")
except ImportError as e:
    print("ERROR: xlsxwriter is not available")
    print("Error:", str(e))
    sys.exit(1)

print("All tests passed!")