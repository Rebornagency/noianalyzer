#!/usr/bin/env python3
"""
Test script to verify the Excel extraction fix
"""

import io
import os
import tempfile
import pandas as pd
from ai_extraction import extract_text_from_excel, extract_financial_data_with_gpt

# Create a test Excel file that mimics the structure from the logs
def create_test_excel():
    # Create a DataFrame with sample financial data similar to the logs
    data = {
        'Category': [
            'Real Estate Financial Statement - Sep 2025 (Actual)',
            'Property: Example Commercial/Residential Property',
            'Period: September 1, 2025 - September 30, 2025',
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
        'Sep 2025 Actual': [
            '', '', '',  # Headers
            50000.0,    # Rental Income - Commercial
            30000.0,    # Rental Income - Residential
            2000.0,     # Parking Fees
            500.0,      # Laundry Income
            300.0,      # Application Fees
            150.0,      # Late Fees
            1000.0,     # Other Income
            83950.0,    # Total Revenue
            '',         # Operating Expenses header
            4000.0,     # Property Management Fees
            2000.0,     # Utilities
            3000.0,     # Property Taxes
            1500.0,     # Property Insurance
            2500.0,     # Repairs & Maintenance
            1000.0,     # Cleaning & Janitorial
            500.0,      # Landscaping & Grounds
            800.0,      # Security
            300.0,      # Marketing & Advertising
            400.0,      # Administrative Expenses
            0.0,        # HOA Fees
            200.0,      # Pest Control
            150.0,      # Supplies
            16250.0,    # Total Operating Expenses
            67700.0     # Net Operating Income
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Create a temporary file to write the Excel content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_filename, sheet_name='Real Estate Financial Statement', index=False)
    
    # Read the file content
    with open(tmp_filename, 'rb') as f:
        excel_content = f.read()
    
    # Clean up the temporary file
    os.unlink(tmp_filename)
    
    return excel_content

# Test the Excel extraction function
if __name__ == "__main__":
    print("Testing Excel extraction fix...")
    
    # Create test Excel content
    excel_content = create_test_excel()
    
    # Test extraction
    try:
        print("1. Testing extract_text_from_excel function:")
        extracted_text = extract_text_from_excel(excel_content, "financial_statement_september_2025_actual.xlsx")
        print("Extraction successful!")
        print("Extracted text length:", len(extracted_text))
        print("First 1000 characters:")
        print(extracted_text[:1000])
        print("...")
        print("Last 500 characters:")
        print(extracted_text[-500:])
        
        # Check if it contains expected content
        if "Rental Income" in extracted_text and "Net Operating Income" in extracted_text:
            print("✅ Extracted text contains expected financial data")
        else:
            print("❌ Extracted text may be missing financial data")
            
        # Test with mock GPT response
        print("\n2. Testing with mock GPT response:")
        # Mock the chat_completion function to avoid actual API calls
        import ai_extraction
        original_chat_completion = ai_extraction.chat_completion
        
        # Mock response with realistic financial data
        mock_response = '''{
  "file_name": "financial_statement_september_2025_actual.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 80000.0,
  "vacancy_loss": 0.0,
  "concessions": 0.0,
  "bad_debt": 0.0,
  "other_income": 3950.0,
  "egi": 83950.0,
  "opex": 16250.0,
  "noi": 67700.0,
  "property_taxes": 3000.0,
  "insurance": 1500.0,
  "repairs_maintenance": 2500.0,
  "utilities": 2000.0,
  "management_fees": 4000.0,
  "parking": 2000.0,
  "laundry": 500.0,
  "late_fees": 150.0,
  "pet_fees": 0.0,
  "application_fees": 300.0,
  "storage_fees": 0.0,
  "amenity_fees": 0.0,
  "utility_reimbursements": 0.0,
  "cleaning_fees": 1000.0,
  "cancellation_fees": 0.0,
  "miscellaneous": 1000.0
}'''
        
        def mock_chat_completion(*args, **kwargs):
            return mock_response
            
        # Replace the chat_completion function
        ai_extraction.chat_completion = mock_chat_completion
        
        try:
            result = extract_financial_data_with_gpt(excel_content, "financial_statement_september_2025_actual.xlsx", "current_month_actuals", "fake-api-key")
            print("✅ GPT extraction simulation successful!")
            print(f"   GPR: {result.get('gpr', 'Not found')}")
            print(f"   NOI: {result.get('noi', 'Not found')}")
            print(f"   OpEx: {result.get('opex', 'Not found')}")
            
            # Verify we got meaningful values
            if result.get('gpr', 0) > 0 and result.get('noi', 0) > 0:
                print("✅ Extracted financial values are meaningful (non-zero)")
            else:
                print("❌ Extracted financial values are zero or missing")
                
        except Exception as e:
            print(f"❌ GPT extraction simulation failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Restore original function
            ai_extraction.chat_completion = original_chat_completion
            
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n✅ Excel extraction fix test completed!")