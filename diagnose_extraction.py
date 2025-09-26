#!/usr/bin/env python3
"""
Diagnostic script to understand what's happening with the Excel extraction
"""

import pandas as pd
import io
import tempfile
import os
from ai_extraction import extract_text_from_excel, create_gpt_extraction_prompt

def create_test_excel_file():
    """Create a test Excel file that mimics the structure from the logs"""
    # Based on the logs, it seems like we have a financial statement with specific structure
    data = {
        'Real Estate Financial Statement - Sep 2025 (Actual)': [
            'Property: Example Commercia...',
            'Period: September 1, 2025 -...',
            'Category',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Application Fees',
            'Late Fees',
            'Other Income',
            'Total Revenue',
            '',  # Empty row
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
            '',  # Empty row
            'Net Operating Income (NOI)',
            'Net Operating Income (NOI)'
        ],
        'Unnamed: 1': [
            '', '', '[EMPTY]', '30000.0', '20000.0', '2000.0', '500.0', '300.0', '150.0', '5000.0', '57950.0',
            '', '', '', '4000.0', '3000.0', '2000.0', '1500.0', '2500.0', '1000.0', '500.0', '1000.0', '500.0', '300.0', '200.0', '100.0', '100.0', '16000.0',
            '', '41950.0'
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_file, sheet_name='Real Estate Financial Statement', index=False)
    
    return tmp_filename

def diagnose_extraction():
    """Diagnose what's happening with the extraction process"""
    print("Creating test Excel file...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test Excel extraction
        print("\nTesting Excel extraction...")
        extracted_text = extract_text_from_excel(file_content, "financial_statement_september_2025_actual.xlsx")
        
        print("Extracted text length:", len(extracted_text))
        print("\nExtracted text:")
        print("=" * 60)
        print(extracted_text)
        print("=" * 60)
        
        # Create GPT prompt
        print("\nCreating GPT extraction prompt...")
        prompt = create_gpt_extraction_prompt(extracted_text, "financial_statement_september_2025_actual.xlsx", "current_month_actuals")
        
        print("Prompt length:", len(prompt))
        print("\nPrompt (first 1000 characters):")
        print("=" * 60)
        print(prompt[:1000])
        print("=" * 60)
        print("...")
        print("=" * 60)
        print(prompt[-1000:])  # Last 1000 characters
        print("=" * 60)
        
        # Analyze the structure
        print("\nANALYSIS:")
        print(f"  Extracted text contains '[FINANCIAL_STATEMENT_FORMAT]': {'✅' if '[FINANCIAL_STATEMENT_FORMAT]' in extracted_text else '❌'}")
        print(f"  Extracted text contains 'Net Operating Income': {'✅' if 'Net Operating Income' in extracted_text else '❌'}")
        print(f"  Extracted text contains actual values (e.g., '30000.0'): {'✅' if '30000.0' in extracted_text else '❌'}")
        print(f"  Extracted text contains category:value pairs: {'✅' if ':' in extracted_text else '❌'}")
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    diagnose_extraction()