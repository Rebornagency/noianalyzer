#!/usr/bin/env python3
"""
Comprehensive test script to verify improvements for all file types
"""

import io
import os
import tempfile
import pandas as pd
from ai_extraction import (
    extract_text_from_excel, 
    extract_text_from_pdf, 
    extract_text_from_csv,
    extract_financial_data_with_gpt,
    _format_text_content
)

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

def create_test_excel():
    """Create a test Excel file with financial data"""
    data = {
        'Category': [
            'Real Estate Financial Statement - Sep 2025 (Actual)',
            'Property: Example Commercial/Residential Property',
            'Period: September 1, 2025 - September 30, 2025',
            'Gross Potential Rent',
            'Vacancy Loss',
            'Concessions',
            'Bad Debt',
            'Other Income',
            'Effective Gross Income',
            'Operating Expenses',
            'Property Taxes',
            'Insurance',
            'Repairs & Maintenance',
            'Utilities',
            'Management Fees',
            'Parking',
            'Laundry',
            'Late Fees',
            'Total Operating Expenses',
            'Net Operating Income'
        ],
        'Sep 2025 Actual': [
            '', '', '',  # Headers
            80000.0,    # Gross Potential Rent
            -2000.0,    # Vacancy Loss
            -1000.0,    # Concessions
            -500.0,     # Bad Debt
            3950.0,     # Other Income
            80450.0,    # Effective Gross Income
            '',         # Operating Expenses header
            -3000.0,    # Property Taxes
            -1500.0,    # Insurance
            -2500.0,    # Repairs & Maintenance
            -2000.0,    # Utilities
            -4000.0,    # Management Fees
            2000.0,     # Parking
            500.0,      # Laundry
            150.0,      # Late Fees
            -16250.0,   # Total Operating Expenses
            64200.0     # Net Operating Income
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Create a temporary file to write the Excel content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_filename, sheet_name='Financial Statement', index=False)
    
    # Read the file content
    with open(tmp_filename, 'rb') as f:
        excel_content = f.read()
    
    # Clean up the temporary file
    os.unlink(tmp_filename)
    
    return excel_content

def create_test_csv():
    """Create a test CSV file with financial data"""
    csv_content = """Category,Amount
Gross Potential Rent,80000.00
Vacancy Loss,-2000.00
Concessions,-1000.00
Bad Debt,-500.00
Other Income,3950.00
Effective Gross Income,80450.00
Property Taxes,-3000.00
Insurance,-1500.00
Repairs & Maintenance,-2500.00
Utilities,-2000.00
Management Fees,-4000.00
Parking,2000.00
Laundry,500.00
Late Fees,150.00
Total Operating Expenses,-16250.00
Net Operating Income,64200.00"""
    
    return csv_content.encode('utf-8')

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
    
    return text_content.encode('utf-8')

def test_excel_extraction():
    """Test Excel file extraction"""
    print("1. Testing Excel file extraction...")
    
    excel_content = create_test_excel()
    extracted_text = extract_text_from_excel(excel_content, "test_financials.xlsx")
    
    print(f"   Extracted text length: {len(extracted_text)}")
    
    # Check for key financial terms
    required_terms = ["Gross Potential Rent", "Net Operating Income", "Property Taxes"]
    missing_terms = [term for term in required_terms if term not in extracted_text]
    
    if not missing_terms:
        print("   ✅ Excel extraction successful - all required terms found")
        return True
    else:
        print(f"   ❌ Excel extraction missing terms: {missing_terms}")
        return False

def test_csv_extraction():
    """Test CSV file extraction"""
    print("2. Testing CSV file extraction...")
    
    csv_content = create_test_csv()
    extracted_text = extract_text_from_csv(csv_content, "test_financials.csv")
    
    print(f"   Extracted text length: {len(extracted_text)}")
    
    # Check for key financial terms
    required_terms = ["Gross Potential Rent", "Net Operating Income", "Property Taxes"]
    missing_terms = [term for term in required_terms if term not in extracted_text]
    
    if not missing_terms:
        print("   ✅ CSV extraction successful - all required terms found")
        return True
    else:
        print(f"   ❌ CSV extraction missing terms: {missing_terms}")
        return False

def test_text_extraction():
    """Test text file extraction"""
    print("3. Testing text file extraction...")
    
    text_content = create_test_text()
    # For text files, we use our enhanced extraction function
    try:
        decoded_text = text_content.decode('utf-8', errors='ignore')
        extracted_text = _format_text_content(decoded_text, "test_financials.txt")
        print(f"   Extracted text length: {len(extracted_text)}")
        
        # Check for key financial terms - using the exact text from the test data
        required_terms = ["Gross Potential Rent", "NET OPERATING INCOME", "Property Taxes"]
        missing_terms = [term for term in required_terms if term not in extracted_text]
        
        if not missing_terms:
            print("   ✅ Text extraction successful - all required terms found")
            return True
        else:
            print(f"   ❌ Text extraction missing terms: {missing_terms}")
            return False
    except Exception as e:
        print(f"   ❌ Text extraction failed: {e}")
        return False

def test_gpt_extraction():
    """Test GPT extraction with all file types"""
    print("4. Testing GPT extraction with all file types...")
    
    results = []
    
    # Test with Excel
    try:
        print("   Testing with Excel file...")
        excel_content = create_test_excel()
        result = extract_financial_data_with_gpt(excel_content, "test_financials.xlsx", "current_month_actuals", "fake-api-key")
        if result.get('gpr', 0) > 0 and result.get('noi', 0) > 0:
            print("   ✅ GPT extraction with Excel successful")
            results.append(True)
        else:
            print("   ❌ GPT extraction with Excel returned zero values")
            results.append(False)
    except Exception as e:
        print(f"   ❌ GPT extraction with Excel failed: {e}")
        results.append(False)
    
    # Test with CSV
    try:
        print("   Testing with CSV file...")
        csv_content = create_test_csv()
        result = extract_financial_data_with_gpt(csv_content, "test_financials.csv", "current_month_actuals", "fake-api-key")
        if result.get('gpr', 0) > 0 and result.get('noi', 0) > 0:
            print("   ✅ GPT extraction with CSV successful")
            results.append(True)
        else:
            print("   ❌ GPT extraction with CSV returned zero values")
            results.append(False)
    except Exception as e:
        print(f"   ❌ GPT extraction with CSV failed: {e}")
        results.append(False)
    
    # Test with text
    try:
        print("   Testing with text file...")
        text_content = create_test_text()
        result = extract_financial_data_with_gpt(text_content, "test_financials.txt", "current_month_actuals", "fake-api-key")
        if result.get('gpr', 0) > 0 and result.get('noi', 0) > 0:
            print("   ✅ GPT extraction with text successful")
            results.append(True)
        else:
            print("   ❌ GPT extraction with text returned zero values")
            results.append(False)
    except Exception as e:
        print(f"   ❌ GPT extraction with text failed: {e}")
        results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print("Testing all file type handling improvements...")
    print("=" * 50)
    
    # Run individual extraction tests
    excel_ok = test_excel_extraction()
    print()
    
    csv_ok = test_csv_extraction()
    print()
    
    text_ok = test_text_extraction()
    print()
    
    # Run GPT extraction tests
    gpt_ok = test_gpt_extraction()
    print()
    
    # Restore original function
    ai_extraction.chat_completion = original_chat_completion
    
    # Summary
    print("=" * 50)
    print("SUMMARY:")
    print(f"  Excel extraction: {'✅ PASS' if excel_ok else '❌ FAIL'}")
    print(f"  CSV extraction: {'✅ PASS' if csv_ok else '❌ FAIL'}")
    print(f"  Text extraction: {'✅ PASS' if text_ok else '❌ FAIL'}")
    print(f"  GPT extraction: {'✅ PASS' if gpt_ok else '❌ FAIL'}")
    
    overall_success = excel_ok and csv_ok and text_ok and gpt_ok
    print()
    if overall_success:
        print("🎉 ALL TESTS PASSED! File type handling improvements are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return overall_success

if __name__ == "__main__":
    main()