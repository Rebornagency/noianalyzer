#!/usr/bin/env python3
"""
Test script to create an Excel file that matches the structure shown in the logs
and test our extraction improvements.
"""

import pandas as pd
import io
import tempfile
import os
from ai_extraction import extract_text_from_excel

def create_test_excel_file():
    """Create a test Excel file that matches the structure from the logs"""
    
    # Create a DataFrame that matches the structure from the logs
    data = {
        'Category': [
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Application Fees',
            'Late Fees',
            'Other Income',
            'Total Revenue',
            'Operating Expenses',
            'Property Management Fees',
            'Utilities',
            'Property Taxes',
            'Property Insurance',
            'Repairs & Maintenance',
            'Cleaning & Janitorial',
            'Landscaping & Grounds',
            'Security',
            'Marketing & Advertising',
            'Administrative Expenses',
            'HOA Fees (if applicable)',
            'Pest Control',
            'Supplies',
            'Total Operating Expenses',
            'Net Operating Income (NOI)'
        ],
        'Amount': [
            50000.0,    # Rental Income - Commercial
            30000.0,    # Rental Income - Residential
            2000.0,     # Parking Fees
            500.0,      # Laundry Income
            300.0,      # Application Fees
            150.0,      # Late Fees
            1000.0,     # Other Income
            83950.0,    # Total Revenue
            '',         # Operating Expenses (header)
            -4000.0,    # Property Management Fees
            -2000.0,    # Utilities
            -3000.0,    # Property Taxes
            -1500.0,    # Property Insurance
            -2500.0,    # Repairs & Maintenance
            -1000.0,    # Cleaning & Janitorial
            -500.0,     # Landscaping & Grounds
            -1000.0,    # Security
            -500.0,     # Marketing & Advertising
            -1000.0,    # Administrative Expenses
            0.0,        # HOA Fees (if applicable)
            -300.0,     # Pest Control
            -200.0,     # Supplies
            -17000.0,   # Total Operating Expenses
            66950.0     # Net Operating Income (NOI)
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Create a temporary file to write the Excel content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_filename, sheet_name='Real Estate Financial Statement', index=False)
    
    return tmp_filename

def test_excel_extraction():
    """Test the Excel extraction function with our improved implementation"""
    
    # Create test Excel file
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        # Test extraction
        extracted_text = extract_text_from_excel(file_content, "test_financial_statement.xlsx")
        
        print("Extracted text:")
        print("=" * 50)
        print(extracted_text)
        print("=" * 50)
        
        # Check if key financial terms are present
        key_terms = [
            "Gross Potential Rent",
            "Net Operating Income",
            "Property Taxes",
            "Total Revenue",
            "Operating Expenses"
        ]
        
        print("\nChecking for key financial terms:")
        for term in key_terms:
            if term.lower() in extracted_text.lower():
                print(f"  ✅ Found: {term}")
            else:
                print(f"  ❌ Missing: {term}")
        
        # Check if we have a proper financial statement format
        if "FINANCIAL STATEMENT FORMAT DETECTED" in extracted_text:
            print("\n✅ Financial statement format detected")
        else:
            print("\n❌ Financial statement format not detected")
            
        # Check if we have categories with values
        if ":" in extracted_text:
            print("✅ Categories with values found")
        else:
            print("❌ Categories with values not found")
            
    finally:
        # Clean up the temporary file
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_excel_extraction()