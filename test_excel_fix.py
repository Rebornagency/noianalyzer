#!/usr/bin/env python3
"""
Test script to verify the Excel extraction fix works correctly.
"""

import pandas as pd
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

def test_excel_extraction_fix():
    """Test the improved Excel extraction function"""
    
    print("Testing improved Excel extraction...")
    
    # Create test Excel file
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        # Test extraction
        extracted_text = extract_text_from_excel(file_content, "test_financial_statement.xlsx")
        
        print("Extracted text length:", len(extracted_text))
        print("\nExtracted text (first 1000 characters):")
        print("=" * 50)
        print(extracted_text[:1000])
        print("=" * 50)
        
        # Check if key features are present
        checks = [
            ("Sheet name detected", "[SHEET_START] Real Estate Financial Statement" in extracted_text),
            ("Financial statement format detected", "[FINANCIAL_STATEMENT_FORMAT]" in extracted_text),
            ("Categories with values", ":" in extracted_text),
            ("Net Operating Income", "Net Operating Income" in extracted_text),
            ("Property Taxes", "Property Taxes" in extracted_text),
            ("Total Revenue", "Total Revenue" in extracted_text),
            ("Actual values extracted", "50000.0" in extracted_text),  # Check if actual values are extracted
            ("Negative values extracted", "-4000.0" in extracted_text),  # Check if negative values are extracted
        ]
        
        print("\nVerification checks:")
        all_passed = True
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"  {status}: {check_name}")
            if not check_result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 Excel extraction fix is working correctly!")
        else:
            print("\n⚠️  Some checks failed. Review the implementation.")
            
        return all_passed
            
    finally:
        # Clean up the temporary file
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_excel_extraction_fix()