#!/usr/bin/env python3
"""
Comprehensive test to verify robust extraction works with different document formats
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
    _extract_financial_data_from_text,
    _format_text_content
)

# Mock the chat_completion function to avoid actual API calls
import ai_extraction
original_chat_completion = ai_extraction.chat_completion

def extract_text_from_txt(file_content: bytes, file_name: str) -> str:
    """
    Extract and format text content from text file bytes.
    
    Args:
        file_content: Text file content as bytes
        file_name: Name of the file
        
    Returns:
        Formatted text content
    """
    try:
        decoded_text = file_content.decode('utf-8', errors='ignore')
        return _format_text_content(decoded_text, file_name)
    except Exception as e:
        return f"[Text content from {file_name}]"

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

def create_test_excel_variations():
    """Create test Excel files with different formatting variations"""
    variations = []
    
    # Variation 1: Standard format
    data1 = {
        'Category': [
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
        'Amount': [
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
    
    df1 = pd.DataFrame(data1)
    
    # Create a temporary file to write the Excel content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df1.to_excel(tmp_filename, sheet_name='Financial Statement', index=False)
    
    # Read the file content
    with open(tmp_filename, 'rb') as f:
        excel_content1 = f.read()
    
    # Clean up the temporary file
    os.unlink(tmp_filename)
    variations.append(("standard_format.xlsx", excel_content1))
    
    # Variation 2: All caps format
    data2 = {
        'CATEGORY': [
            'GROSS POTENTIAL RENT',
            'VACANCY LOSS',
            'CONCESSIONS',
            'BAD DEBT',
            'OTHER INCOME',
            'EFFECTIVE GROSS INCOME',
            'OPERATING EXPENSES',
            'PROPERTY TAXES',
            'INSURANCE',
            'REPAIRS & MAINTENANCE',
            'UTILITIES',
            'MANAGEMENT FEES',
            'PARKING',
            'LAUNDRY',
            'LATE FEES',
            'TOTAL OPERATING EXPENSES',
            'NET OPERATING INCOME'
        ],
        'AMOUNT': [
            80000.0,    # GROSS POTENTIAL RENT
            -2000.0,    # VACANCY LOSS
            -1000.0,    # CONCESSIONS
            -500.0,     # BAD DEBT
            3950.0,     # OTHER INCOME
            80450.0,    # EFFECTIVE GROSS INCOME
            '',         # OPERATING EXPENSES header
            -3000.0,    # PROPERTY TAXES
            -1500.0,    # INSURANCE
            -2500.0,    # REPAIRS & MAINTENANCE
            -2000.0,    # UTILITIES
            -4000.0,    # MANAGEMENT FEES
            2000.0,     # PARKING
            500.0,      # LAUNDRY
            150.0,      # LATE FEES
            -16250.0,   # TOTAL OPERATING EXPENSES
            64200.0     # NET OPERATING INCOME
        ]
    }
    
    df2 = pd.DataFrame(data2)
    
    # Create a temporary file to write the Excel content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df2.to_excel(tmp_filename, sheet_name='Financial Statement', index=False)
    
    # Read the file content
    with open(tmp_filename, 'rb') as f:
        excel_content2 = f.read()
    
    # Clean up the temporary file
    os.unlink(tmp_filename)
    variations.append(("all_caps_format.xlsx", excel_content2))
    
    return variations

def create_test_csv_variations():
    """Create test CSV files with different formatting variations"""
    variations = []
    
    # Variation 1: Standard format
    csv_content1 = """Category,Amount
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
    
    variations.append(("standard_format.csv", csv_content1.encode('utf-8')))
    
    # Variation 2: Different separators and formatting
    csv_content2 = """Category;Amount
"GROSS POTENTIAL RENT";80000.00
"VACANCY LOSS";-2000.00
"CONCESSIONS";-1000.00
"BAD DEBT";-500.00
"OTHER INCOME";3950.00
"EFFECTIVE GROSS INCOME";80450.00
"PROPERTY TAXES";-3000.00
"INSURANCE";-1500.00
"REPAIRS & MAINTENANCE";-2500.00
"UTILITIES";-2000.00
"MANAGEMENT FEES";-4000.00
"PARKING";2000.00
"LAUNDRY";500.00
"LATE FEES";150.00
"TOTAL OPERATING EXPENSES";-16250.00
"NET OPERATING INCOME";64200.00"""
    
    variations.append(("different_format.csv", csv_content2.encode('utf-8')))
    
    return variations

def create_test_text_variations():
    """Create test text files with different formatting variations"""
    variations = []
    
    # Variation 1: Standard format
    text_content1 = """
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
    
    variations.append(("standard_format.txt", text_content1.encode('utf-8')))
    
    # Variation 2: All caps format
    text_content2 = """
REAL ESTATE FINANCIAL STATEMENT
SEPTEMBER 2025 (ACTUAL)

PROPERTY: EXAMPLE COMMERCIAL/RESIDENTIAL PROPERTY
PERIOD: SEPTEMBER 1, 2025 - SEPTEMBER 30, 2025

REVENUE:
GROSS POTENTIAL RENT: $80,000.00
VACANCY LOSS: ($2,000.00)
CONCESSIONS: ($1,000.00)
BAD DEBT: ($500.00)
OTHER INCOME: $3,950.00
EFFECTIVE GROSS INCOME: $80,450.00

EXPENSES:
PROPERTY TAXES: ($3,000.00)
INSURANCE: ($1,500.00)
REPAIRS & MAINTENANCE: ($2,500.00)
UTILITIES: ($2,000.00)
MANAGEMENT FEES: ($4,000.00)
PARKING: $2,000.00
LAUNDRY: $500.00
LATE FEES: $150.00
TOTAL OPERATING EXPENSES: ($16,250.00)

NET OPERATING INCOME: $64,200.00
"""
    
    variations.append(("all_caps_format.txt", text_content2.encode('utf-8')))
    
    # Variation 3: Unstructured format
    text_content3 = """
September 2025 Financial Results for Example Property

Total Rental Income Potential: $80,000.00
Lost Income from Vacant Units: ($2,000.00)
Rent Concessions Given: ($1,000.00)
Uncollected Rent: ($500.00)
Additional Income Sources: $3,950.00

Net Rental Income: $80,450.00

Property Tax Expenses: ($3,000.00)
Insurance Costs: ($1,500.00)
Maintenance and Repairs: ($2,500.00)
Utility Payments: ($2,000.00)
Management Fees: ($4,000.00)
Parking Revenue: $2,000.00
Laundry Income: $500.00
Late Payment Fees: $150.00

Total Operating Costs: ($16,250.00)

Final Operating Profit: $64,200.00
"""
    
    variations.append(("unstructured_format.txt", text_content3.encode('utf-8')))
    
    return variations

def test_excel_extraction_variations():
    """Test Excel file extraction with different variations"""
    print("1. Testing Excel file extraction variations...")
    
    variations = create_test_excel_variations()
    results = []
    
    for file_name, content in variations:
        try:
            extracted_text = extract_text_from_excel(content, file_name)
            print(f"   {file_name}: Extracted text length: {len(extracted_text)}")
            
            # Check for key financial terms
            required_terms = ["Gross Potential Rent", "Net Operating Income", "Property Taxes"]
            found_terms = [term for term in required_terms if term.lower() in extracted_text.lower()]
            
            if len(found_terms) >= 2:  # Expecting to find at least 2 of the 3 terms
                print(f"   ✅ {file_name}: Successful - found {len(found_terms)} required terms")
                results.append(True)
            else:
                print(f"   ❌ {file_name}: Failed - found only {len(found_terms)} required terms")
                results.append(False)
        except Exception as e:
            print(f"   ❌ {file_name}: Failed with error: {e}")
            results.append(False)
    
    return all(results)

def test_csv_extraction_variations():
    """Test CSV file extraction with different variations"""
    print("2. Testing CSV file extraction variations...")
    
    variations = create_test_csv_variations()
    results = []
    
    for file_name, content in variations:
        try:
            extracted_text = extract_text_from_csv(content, file_name)
            print(f"   {file_name}: Extracted text length: {len(extracted_text)}")
            
            # Check for key financial terms
            required_terms = ["Gross Potential Rent", "Net Operating Income", "Property Taxes"]
            found_terms = [term for term in required_terms if term.lower() in extracted_text.lower()]
            
            if len(found_terms) >= 2:  # Expecting to find at least 2 of the 3 terms
                print(f"   ✅ {file_name}: Successful - found {len(found_terms)} required terms")
                results.append(True)
            else:
                print(f"   ❌ {file_name}: Failed - found only {len(found_terms)} required terms")
                results.append(False)
        except Exception as e:
            print(f"   ❌ {file_name}: Failed with error: {e}")
            results.append(False)
    
    return all(results)

def test_text_extraction_variations():
    """Test text file extraction with different variations"""
    print("3. Testing text file extraction variations...")
    
    variations = create_test_text_variations()
    results = []
    
    for file_name, content in variations:
        try:
            extracted_text = extract_text_from_txt(content, file_name)
            print(f"   {file_name}: Extracted text length: {len(extracted_text)}")
            
            # Check for key financial terms
            required_terms = ["Gross Potential Rent", "Net Operating Income", "Property Taxes"]
            found_terms = [term for term in required_terms if term.lower() in extracted_text.lower()]
            
            if len(found_terms) >= 2:  # Expecting to find at least 2 of the 3 terms
                print(f"   ✅ {file_name}: Successful - found {len(found_terms)} required terms")
                results.append(True)
            else:
                print(f"   ❌ {file_name}: Failed - found only {len(found_terms)} required terms")
                results.append(False)
        except Exception as e:
            print(f"   ❌ {file_name}: Failed with error: {e}")
            results.append(False)
    
    return all(results)

def test_regex_extraction_variations():
    """Test regex-based extraction with different text variations"""
    print("4. Testing regex-based extraction variations...")
    
    # Test with different text formats
    test_texts = [
        ("Standard format", """
        Gross Potential Rent: $80,000.00
        Vacancy Loss: ($2,000.00)
        Concessions: ($1,000.00)
        Bad Debt: ($500.00)
        Other Income: $3,950.00
        Effective Gross Income: $80,450.00
        Property Taxes: ($3,000.00)
        Insurance: ($1,500.00)
        Repairs & Maintenance: ($2,500.00)
        Utilities: ($2,000.00)
        Management Fees: ($4,000.00)
        Parking: $2,000.00
        Laundry: $500.00
        Late Fees: $150.00
        Total Operating Expenses: ($16,250.00)
        Net Operating Income: $64,200.00
        """),
        
        ("All caps format", """
        GROSS POTENTIAL RENT: $80,000.00
        VACANCY LOSS: ($2,000.00)
        CONCESSIONS: ($1,000.00)
        BAD DEBT: ($500.00)
        OTHER INCOME: $3,950.00
        EFFECTIVE GROSS INCOME: $80,450.00
        PROPERTY TAXES: ($3,000.00)
        INSURANCE: ($1,500.00)
        REPAIRS & MAINTENANCE: ($2,500.00)
        UTILITIES: ($2,000.00)
        MANAGEMENT FEES: ($4,000.00)
        PARKING: $2,000.00
        LAUNDRY: $500.00
        LATE FEES: $150.00
        TOTAL OPERATING EXPENSES: ($16,250.00)
        NET OPERATING INCOME: $64,200.00
        """),
        
        ("Unstructured format", """
        September 2025 Financial Results
        
        Total Rental Income Potential: $80,000.00
        Lost Income from Vacant Units: ($2,000.00)
        Rent Concessions Given: ($1,000.00)
        Uncollected Rent: ($500.00)
        Additional Income Sources: $3,950.00
        
        Net Rental Income: $80,450.00
        
        Property Tax Expenses: ($3,000.00)
        Insurance Costs: ($1,500.00)
        Maintenance and Repairs: ($2,500.00)
        Utility Payments: ($2,000.00)
        Management Fees: ($4,000.00)
        Parking Revenue: $2,000.00
        Laundry Income: $500.00
        Late Payment Fees: $150.00
        
        Total Operating Costs: ($16,250.00)
        
        Final Operating Profit: $64,200.00
        """)
    ]
    
    results = []
    for name, text in test_texts:
        try:
            result = _extract_financial_data_from_text(text, f"test_{name.replace(' ', '_').lower()}.txt", "current_month_actuals")
            meaningful_fields = sum(1 for k, v in result.items() if k not in ['file_name', 'document_type'] and v != 0.0)
            
            if meaningful_fields >= 5:  # Expecting to extract at least 5 meaningful fields
                print(f"   ✅ {name}: Successful - extracted {meaningful_fields} meaningful fields")
                results.append(True)
            else:
                print(f"   ❌ {name}: Failed - extracted only {meaningful_fields} meaningful fields")
                results.append(False)
        except Exception as e:
            print(f"   ❌ {name}: Failed with error: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print("Testing robust extraction with different document formats...")
    print("=" * 60)
    
    # Run individual extraction tests
    excel_ok = test_excel_extraction_variations()
    print()
    
    csv_ok = test_csv_extraction_variations()
    print()
    
    text_ok = test_text_extraction_variations()
    print()
    
    regex_ok = test_regex_extraction_variations()
    print()
    
    # Restore original function
    ai_extraction.chat_completion = original_chat_completion
    
    # Summary
    print("=" * 60)
    print("SUMMARY:")
    print(f"  Excel extraction variations: {'✅ PASS' if excel_ok else '❌ FAIL'}")
    print(f"  CSV extraction variations: {'✅ PASS' if csv_ok else '❌ FAIL'}")
    print(f"  Text extraction variations: {'✅ PASS' if text_ok else '❌ FAIL'}")
    print(f"  Regex extraction variations: {'✅ PASS' if regex_ok else '❌ FAIL'}")
    
    overall_success = excel_ok and csv_ok and text_ok and regex_ok
    print()
    if overall_success:
        print("🎉 ALL TESTS PASSED! Robust extraction is working correctly with different document formats.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return overall_success

if __name__ == "__main__":
    main()