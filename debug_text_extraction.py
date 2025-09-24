#!/usr/bin/env python3
"""
Debug script to check text extraction
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_extraction import _format_text_content

def create_test_text():
    """Create a test text file with financial data"""
    text_content = """
REAL ESTATE FINANCIAL STATEMENT
SEPTEMBER 2025 (ACTUAL)

PROPERTY: Example Commercial/Residential Property
PERIOD: September 1, 2025 - September 30, 2025

REVENUE:
Gross Potential Rent: $80,000.00
Vacancy Loss: ($2,000.00)
Concessions: ($1,000.00)
Bad Debt: ($500.00)
Other Income: $3,950.00
Effective Gross Income: $80,450.00

EXPENSES:
Property Taxes: ($3,000.00)
Insurance: ($1,500.00)
Repairs & Maintenance: ($2,500.00)
Utilities: ($2,000.00)
Management Fees: ($4,000.00)
Parking: $2,000.00
Laundry: $500.00
Late Fees: $150.00
Total Operating Expenses: ($16,250.00)

NET OPERATING INCOME: $64,200.00
"""
    
    return text_content

if __name__ == "__main__":
    text_content = create_test_text()
    formatted_text = _format_text_content(text_content, "test_financials.txt")
    
    print("Original text length:", len(text_content))
    print("Formatted text length:", len(formatted_text))
    print("\nFormatted text:")
    print(formatted_text)
    
    # Check for key terms
    required_terms = ["Gross Potential Rent", "Net Operating Income", "Property Taxes"]
    print("\nChecking for required terms:")
    for term in required_terms:
        if term in formatted_text:
            print(f"  ✅ Found: {term}")
        else:
            print(f"  ❌ Missing: {term}")
    
    # Also check with case insensitive search
    print("\nCase insensitive search:")
    for term in required_terms:
        if term.lower() in formatted_text.lower():
            print(f"  ✅ Found (case insensitive): {term}")
        else:
            print(f"  ❌ Missing (case insensitive): {term}")