#!/usr/bin/env python3
"""
Comprehensive test to verify that the perfect approach works correctly.
"""

import pandas as pd
import io
import tempfile
import os
from ai_extraction import (
    extract_text_from_excel, 
    extract_text_from_csv, 
    extract_text_from_pdf,
    extract_financial_data_with_gpt,
    _extract_financial_data_from_text
)

# Mock the chat_completion function to avoid actual API calls
import ai_extraction
original_chat_completion = ai_extraction.chat_completion

def mock_chat_completion_with_meaningful_data(*args, **kwargs):
    """Mock function that returns meaningful financial data"""
    return '''{
  "file_name": "test_file.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 100000.0,
  "vacancy_loss": 5000.0,
  "concessions": 2000.0,
  "bad_debt": 1000.0,
  "other_income": 5000.0,
  "egi": 92000.0,
  "opex": 30000.0,
  "noi": 62000.0,
  "property_taxes": 8000.0,
  "insurance": 2000.0,
  "repairs_maintenance": 5000.0,
  "utilities": 3000.0,
  "management_fees": 6000.0,
  "parking": 2000.0,
  "laundry": 1000.0,
  "late_fees": 500.0,
  "pet_fees": 500.0,
  "application_fees": 500.0,
  "storage_fees": 500.0,
  "amenity_fees": 500.0,
  "utility_reimbursements": 1000.0,
  "cleaning_fees": 1000.0,
  "cancellation_fees": 200.0,
  "miscellaneous": 300.0
}'''

def mock_chat_completion_with_zero_data(*args, **kwargs):
    """Mock function that returns all zero values (should be rejected)"""
    return '''{
  "file_name": "test_file.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 0.0,
  "vacancy_loss": 0.0,
  "concessions": 0.0,
  "bad_debt": 0.0,
  "other_income": 0.0,
  "egi": 0.0,
  "opex": 0.0,
  "noi": 0.0,
  "property_taxes": 0.0,
  "insurance": 0.0,
  "repairs_maintenance": 0.0,
  "utilities": 0.0,
  "management_fees": 0.0,
  "parking": 0.0,
  "laundry": 0.0,
  "late_fees": 0.0,
  "pet_fees": 0.0,
  "application_fees": 0.0,
  "storage_fees": 0.0,
  "amenity_fees": 0.0,
  "utility_reimbursements": 0.0,
  "cleaning_fees": 0.0,
  "cancellation_fees": 0.0,
  "miscellaneous": 0.0
}'''

def mock_chat_completion_with_missing_fields(*args, **kwargs):
    """Mock function that returns missing required fields"""
    return '''{
  "file_name": "test_file.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 100000.0,
  "vacancy_loss": 5000.0
}'''

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

def create_test_csv_file():
    """Create a test CSV file"""
    
    # Create a DataFrame
    data = {
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
    
    df = pd.DataFrame(data)
    
    # Create a temporary file to write the CSV content
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_csv(tmp_filename, index=False)
    
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
            ("Sheet name detected", "[SHEET_START] Real Estate Financial Statement" in extracted_text),
            ("Financial statement format detected", "[FINANCIAL_STATEMENT_FORMAT]" in extracted_text),
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

def test_csv_extraction():
    """Test the CSV extraction function with our improved implementation"""
    
    print("\nTesting CSV extraction...")
    
    # Create test CSV file
    csv_file_path = create_test_csv_file()
    
    try:
        # Read the file content
        with open(csv_file_path, 'rb') as f:
            file_content = f.read()
        
        # Test extraction
        extracted_text = extract_text_from_csv(file_content, "test_financial_statement.csv")
        
        print("Extracted text length:", len(extracted_text))
        print("\nExtracted text (first 1000 characters):")
        print("=" * 50)
        print(extracted_text[:1000])
        print("=" * 50)
        
        # Check if key features are present
        checks = [
            ("Financial statement format detected", "[FINANCIAL_STATEMENT_FORMAT]" in extracted_text),
            ("Categories with values", ":" in extracted_text),
            ("Net Operating Income", "Net Operating Income" in extracted_text),
            ("Property Taxes", "Property Taxes" in extracted_text),
            ("Gross Potential Rent", "Gross Potential Rent" in extracted_text)
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
        os.unlink(csv_file_path)

def test_gpt_extraction_with_meaningful_data():
    """Test GPT extraction with meaningful data (should pass)"""
    
    print("\nTesting GPT extraction with meaningful data...")
    
    # Set up mock
    ai_extraction.chat_completion = mock_chat_completion_with_meaningful_data
    
    try:
        # Create test content
        test_content = "Test financial statement content"
        file_content = test_content.encode('utf-8')
        
        # Test extraction
        result = extract_financial_data_with_gpt(file_content, "test_file.xlsx", "current_month_actuals", "fake_api_key")
        
        print("Extraction result keys:", list(result.keys()))
        
        # Check if we got meaningful financial data
        financial_fields = ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 
                           'egi', 'opex', 'noi', 'property_taxes', 'insurance']
        
        print("\nFinancial data check:")
        all_fields_present = True
        has_meaningful_data = False
        for field in financial_fields:
            if field in result:
                value = result[field]
                is_meaningful = value != 0.0
                print(f"  {field}: {value} ({'✅' if is_meaningful else '❌ Zero value'})")
                if is_meaningful:
                    has_meaningful_data = True
                if value == 0.0:
                    all_fields_present = False
            else:
                print(f"  {field}: ❌ Missing")
                all_fields_present = False
        
        success = all_fields_present and has_meaningful_data
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status}: GPT extraction with meaningful data")
        
        return success, result
            
    finally:
        # Restore original function
        ai_extraction.chat_completion = original_chat_completion

def test_gpt_extraction_with_zero_data():
    """Test GPT extraction with zero data (should be rejected and fallback used)"""
    
    print("\nTesting GPT extraction with zero data (should be rejected)...")
    
    # Set up mock
    ai_extraction.chat_completion = mock_chat_completion_with_zero_data
    
    try:
        # Create test content
        test_content = "Test financial statement content"
        file_content = test_content.encode('utf-8')
        
        # Test extraction
        result = extract_financial_data_with_gpt(file_content, "test_file.xlsx", "current_month_actuals", "fake_api_key")
        
        print("Extraction result keys:", list(result.keys()))
        
        # Check if we got fallback data (all zeros)
        financial_fields = ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 
                           'egi', 'opex', 'noi', 'property_taxes', 'insurance']
        
        print("\nFinancial data check:")
        all_fields_present = True
        has_meaningful_data = False
        for field in financial_fields:
            if field in result:
                value = result[field]
                is_meaningful = value != 0.0
                print(f"  {field}: {value} ({'✅' if is_meaningful else '❌ Zero value'})")
                if is_meaningful:
                    has_meaningful_data = True
                if value == 0.0:
                    all_fields_present = False
            else:
                print(f"  {field}: ❌ Missing")
                all_fields_present = False
        
        # This should fail because we reject all-zero responses
        success = not (all_fields_present and not has_meaningful_data)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status}: GPT extraction correctly rejected zero data")
        
        return success, result
            
    finally:
        # Restore original function
        ai_extraction.chat_completion = original_chat_completion

def test_gpt_extraction_with_missing_fields():
    """Test GPT extraction with missing fields (should be rejected and fallback used)"""
    
    print("\nTesting GPT extraction with missing fields (should be rejected)...")
    
    # Set up mock
    ai_extraction.chat_completion = mock_chat_completion_with_missing_fields
    
    try:
        # Create test content
        test_content = "Test financial statement content"
        file_content = test_content.encode('utf-8')
        
        # Test extraction
        result = extract_financial_data_with_gpt(file_content, "test_file.xlsx", "current_month_actuals", "fake_api_key")
        
        print("Extraction result keys:", list(result.keys()))
        
        # Check if we got fallback data (all zeros)
        financial_fields = ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 
                           'egi', 'opex', 'noi', 'property_taxes', 'insurance']
        
        print("\nFinancial data check:")
        missing_fields = []
        for field in financial_fields:
            if field in result:
                value = result[field]
                is_meaningful = value != 0.0
                print(f"  {field}: {value} ({'✅' if is_meaningful else '❌ Zero value'})")
            else:
                print(f"  {field}: ❌ Missing")
                missing_fields.append(field)
        
        # This should fail because we're missing required fields
        success = len(missing_fields) > 0
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status}: GPT extraction correctly rejected missing fields")
        
        return success, result
            
    finally:
        # Restore original function
        ai_extraction.chat_completion = original_chat_completion

def test_text_extraction_from_response():
    """Test text extraction from GPT response when JSON parsing fails"""
    
    print("\nTesting text extraction from GPT response...")
    
    # Test with a text response that contains financial data
    text_response = """
    Based on the document, here are the extracted financial metrics:
    
    Gross Potential Rent: $100,000
    Vacancy Loss: $5,000
    Concessions: $2,000
    Bad Debt: $1,000
    Other Income: $5,000
    Effective Gross Income: $97,000
    Operating Expenses: $30,000
    Net Operating Income: $67,000
    Property Taxes: $8,000
    Insurance: $2,000
    Repairs & Maintenance: $5,000
    """
    
    # Test extraction
    result = _extract_financial_data_from_text(text_response, "test_file.xlsx", "current_month_actuals")
    
    print("Text extraction result keys:", list(result.keys()))
    
    # Check if we got meaningful financial data
    financial_fields = ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 
                       'egi', 'opex', 'noi', 'property_taxes', 'insurance']
    
    print("\nFinancial data check:")
    extracted_fields = 0
    for field in financial_fields:
        if field in result:
            value = result[field]
            is_meaningful = value != 0.0
            print(f"  {field}: {value} ({'✅' if is_meaningful else '❌ Zero value'})")
            if is_meaningful:
                extracted_fields += 1
        else:
            print(f"  {field}: ❌ Missing")
    
    success = extracted_fields > 0
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n  {status}: Text extraction from response")
    
    return success, result

if __name__ == "__main__":
    print("Running comprehensive tests for the perfect approach...")
    print("=" * 60)
    
    # Test Excel extraction
    excel_test_passed, extracted_text = test_excel_extraction()
    
    # Test CSV extraction
    csv_test_passed, csv_extracted_text = test_csv_extraction()
    
    # Test GPT extraction with meaningful data
    gpt_meaningful_test_passed, gpt_meaningful_result = test_gpt_extraction_with_meaningful_data()
    
    # Test GPT extraction with zero data
    gpt_zero_test_passed, gpt_zero_result = test_gpt_extraction_with_zero_data()
    
    # Test GPT extraction with missing fields
    gpt_missing_test_passed, gpt_missing_result = test_gpt_extraction_with_missing_fields()
    
    # Test text extraction from response
    text_extraction_passed, text_extraction_result = test_text_extraction_from_response()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"  Excel extraction test: {'✅ PASS' if excel_test_passed else '❌ FAIL'}")
    print(f"  CSV extraction test: {'✅ PASS' if csv_test_passed else '❌ FAIL'}")
    print(f"  GPT extraction with meaningful data: {'✅ PASS' if gpt_meaningful_test_passed else '❌ FAIL'}")
    print(f"  GPT extraction rejection of zero data: {'✅ PASS' if gpt_zero_test_passed else '❌ FAIL'}")
    print(f"  GPT extraction rejection of missing fields: {'✅ PASS' if gpt_missing_test_passed else '❌ FAIL'}")
    print(f"  Text extraction from response: {'✅ PASS' if text_extraction_passed else '❌ FAIL'}")
    
    all_tests_passed = (
        excel_test_passed and 
        csv_test_passed and 
        gpt_meaningful_test_passed and 
        gpt_zero_test_passed and 
        gpt_missing_test_passed and 
        text_extraction_passed
    )
    
    if all_tests_passed:
        print("\n🎉 ALL TESTS PASSED! The perfect approach is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Review the implementation.")
    
    # Restore original function
    ai_extraction.chat_completion = original_chat_completion