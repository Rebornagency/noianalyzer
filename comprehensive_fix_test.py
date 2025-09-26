"""
Comprehensive test to verify our complete fix for the data extraction issue
"""

import pandas as pd
import io
import tempfile
import os
from world_class_extraction import WorldClassExtractor

def create_test_excel_file():
    """Create a test Excel file that exactly matches the structure from the logs"""
    # Based on the GPT input, the Excel file has this structure:
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

def test_complete_fix():
    """Test the complete fix for the data extraction issue"""
    print("Creating test Excel file with exact structure from logs...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test the world-class extraction
        print("\nTesting world-class extraction...")
        extractor = WorldClassExtractor()
        
        # Test preprocessing
        preprocessing_info = extractor._preprocess_document(file_content, "financial_statement_september_2025_actual.xlsx")
        print(f"Preprocessing info: {preprocessing_info}")
        
        # Test structured text extraction
        structured_text = extractor._extract_structured_text(file_content, "financial_statement_september_2025_actual.xlsx", preprocessing_info)
        print("\nStructured text extracted:")
        print("=" * 60)
        print(structured_text[:1000])  # Show first 1000 characters
        print("=" * 60)
        
        # Check if we have the financial format and values
        has_financial_format = '[FINANCIAL_STATEMENT_FORMAT]' in structured_text
        has_values = '30000.0' in structured_text and '20000.0' in structured_text
        has_category_value_pairs = 'Rental Income - Commercial: 30000.0' in structured_text or 'Rental Income - Commercial' in structured_text
        
        print(f"\nSTRUCTURE ANALYSIS:")
        print(f"  Structured text contains '[FINANCIAL_STATEMENT_FORMAT]': {'✅' if has_financial_format else '❌'}")
        print(f"  Structured text contains actual values: {'✅' if has_values else '❌'}")
        print(f"  Structured text contains category information: {'✅' if has_category_value_pairs else '❌'}")
        
        # Test JSON parsing function with a sample response
        sample_response = '''{
  "financial_data": {
    "gross_potential_rent": 50000.0,
    "vacancy_loss": 2000.0,
    "concessions": 1000.0,
    "bad_debt": 500.0,
    "other_income": 7000.0,
    "effective_gross_income": 53500.0,
    "operating_expenses": 16000.0,
    "property_taxes": 2000.0,
    "insurance": 1500.0,
    "repairs_maintenance": 2500.0,
    "utilities": 3000.0,
    "management_fees": 4000.0,
    "parking_income": 2000.0,
    "laundry_income": 500.0,
    "late_fees": 300.0,
    "pet_fees": 0.0,
    "application_fees": 150.0,
    "storage_fees": 0.0,
    "amenity_fees": 0.0,
    "utility_reimbursements": 0.0,
    "cleaning_fees": 1000.0,
    "cancellation_fees": 0.0,
    "miscellaneous_income": 1000.0,
    "net_operating_income": 37500.0
  },
  "confidence_scores": {
    "gross_potential_rent": 0.9,
    "vacancy_loss": 0.8,
    "concessions": 0.8,
    "bad_debt": 0.7,
    "other_income": 0.9,
    "effective_gross_income": 0.95,
    "operating_expenses": 0.9,
    "property_taxes": 0.95,
    "insurance": 0.95,
    "repairs_maintenance": 0.9,
    "utilities": 0.9,
    "management_fees": 0.9,
    "parking_income": 0.8,
    "laundry_income": 0.8,
    "late_fees": 0.7,
    "pet_fees": 0.5,
    "application_fees": 0.7,
    "storage_fees": 0.5,
    "amenity_fees": 0.5,
    "utility_reimbursements": 0.5,
    "cleaning_fees": 0.8,
    "cancellation_fees": 0.5,
    "miscellaneous_income": 0.7,
    "net_operating_income": 0.95
  }
}'''
        
        print("\nTesting JSON parsing with sample response...")
        parsed_data, confidence_scores = extractor._parse_gpt_response(sample_response)
        print(f"Parsed data keys: {list(parsed_data.keys()) if parsed_data else 'None'}")
        print(f"Confidence scores keys: {list(confidence_scores.keys()) if confidence_scores else 'None'}")
        
        json_parsing_success = bool(parsed_data) and bool(confidence_scores)
        print(f"JSON parsing success: {'✅' if json_parsing_success else '❌'}")
        
        structure_success = has_financial_format and has_values
        print(f"\n{'SUCCESS' if structure_success else 'PARTIAL SUCCESS'}: Excel structure extraction {'works correctly' if structure_success else 'needs improvement'}")
        print(f"{'SUCCESS' if json_parsing_success else 'PARTIAL SUCCESS'}: JSON parsing {'works correctly' if json_parsing_success else 'needs improvement'}")
        
        return structure_success and json_parsing_success
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    success = test_complete_fix()
    print(f"\n{'🎉 COMPLETE SUCCESS' if success else '❌ NEEDS MORE WORK'}")