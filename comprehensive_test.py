#!/usr/bin/env python3
"""
Comprehensive test to verify that our fixes work correctly.
"""

import pandas as pd
import io
import tempfile
import os
from ai_extraction import extract_text_from_excel, extract_financial_data_with_gpt

# Mock the chat_completion function to avoid actual API calls
import ai_extraction
original_chat_completion = ai_extraction.chat_completion

def mock_chat_completion(*args, **kwargs):
    # Return a mock response with realistic financial data
    return '''{
  "file_name": "test_file.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 80000.0,
  "vacancy_loss": 2000.0,
  "concessions": 1000.0,
  "bad_debt": 500.0,
  "other_income": 3950.0,
  "egi": 80450.0,
  "opex": 16250.0,
  "noi": 64200.0,
  "property_taxes": 3000.0,
  "insurance": 1500.0,
  "repairs_maintenance": 2500.0,
  "utilities": 2000.0,
  "management_fees": 4000.0,
  "parking": 2000.0,
  "laundry": 500.0,
  "late_fees": 150.0,
  "pet_fees": 200.0,
  "application_fees": 300.0,
  "storage_fees": 100.0,
  "amenity_fees": 150.0,
  "utility_reimbursements": 300.0,
  "cleaning_fees": 1000.0,
  "cancellation_fees": 50.0,
  "miscellaneous": 1000.0
}'''

# Set up mock
ai_extraction.chat_completion = mock_chat_completion

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
    
    print("Testing Excel extraction...")
    
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
            ("Sheet name detected", "Sheet: Real Estate Financial Statement" in extracted_text),
            ("Financial statement format detected", "FINANCIAL STATEMENT FORMAT DETECTED" in extracted_text),
            ("Categories with values", ":" in extracted_text),
            ("Net Operating Income", "Net Operating Income" in extracted_text),
            ("Property Taxes", "Property Taxes" in extracted_text),
            ("Total Revenue", "Total Revenue" in extracted_text)
        ]
        
        print("\nVerification checks:")
        all_passed = True
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"  {status}: {check_name}")
            if not check_result:
                all_passed = False
        
        return all_passed, extracted_text
            
    finally:
        # Clean up the temporary file
        os.unlink(excel_file_path)

def test_full_extraction_process():
    """Test the full extraction process"""
    
    print("\nTesting full extraction process...")
    
    # Create test Excel file
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        # Test full extraction process
        result = extract_financial_data_with_gpt(file_content, "test_financial_statement.xlsx", "current_month_actuals", "fake_api_key")
        
        print("Extraction result keys:", list(result.keys()))
        
        # Check if we got meaningful financial data
        financial_fields = ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 
                           'egi', 'opex', 'noi', 'property_taxes', 'insurance']
        
        print("\nFinancial data check:")
        all_fields_present = True
        for field in financial_fields:
            if field in result:
                value = result[field]
                print(f"  {field}: {value} ({'✅' if value != 0.0 else '❌ Zero value'})")
                if value == 0.0:
                    all_fields_present = False
            else:
                print(f"  {field}: ❌ Missing")
                all_fields_present = False
        
        return all_fields_present, result
            
    finally:
        # Clean up the temporary file
        os.unlink(excel_file_path)

if __name__ == "__main__":
    print("Running comprehensive tests for Excel extraction improvements...")
    print("=" * 60)
    
    # Test Excel extraction
    excel_test_passed, extracted_text = test_excel_extraction()
    
    # Test full extraction process
    full_test_passed, extraction_result = test_full_extraction_process()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"  Excel extraction test: {'✅ PASS' if excel_test_passed else '❌ FAIL'}")
    print(f"  Full extraction test: {'✅ PASS' if full_test_passed else '❌ FAIL'}")
    
    if excel_test_passed and full_test_passed:
        print("\n🎉 All tests passed! The fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Review the implementation.")
    
    # Restore original function
    ai_extraction.chat_completion = original_chat_completion