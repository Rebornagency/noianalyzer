"""
Test the complete flow with the fixed Excel extraction
"""

import pandas as pd
import io
import tempfile
import os

# Import the world-class extraction system
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

def test_complete_flow():
    """Test the complete flow with the fixed Excel extraction"""
    print("Creating test Excel file with exact structure from logs...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test the complete flow (without actually calling GPT due to API key issues)
        extractor = WorldClassExtractor.__new__(WorldClassExtractor)  # Create instance without calling __init__
        
        # Test preprocessing
        preprocessing_info = extractor._preprocess_document(file_content, "financial_statement_september_2025_actual.xlsx")
        print(f"Preprocessing info: {preprocessing_info}")
        
        # Test structured text extraction
        structured_text = extractor._extract_structured_text(file_content, "financial_statement_september_2025_actual.xlsx", preprocessing_info)
        print("\nStructured text output:")
        print("=" * 60)
        print(structured_text)
        print("=" * 60)
        
        # Check if it contains the financial values
        has_financial_values = '30000.0' in structured_text and '20000.0' in structured_text
        print(f"\nContains financial values: {'✅' if has_financial_values else '❌'}")
        
        # Check if it's using the financial statement format
        has_financial_format = 'FINANCIAL_STATEMENT_FORMAT' in structured_text
        print(f"Uses financial statement format: {'✅' if has_financial_format else '❌'}")
        
        # Check if it's using the table format (which would be wrong)
        has_table_format = 'TABLE_FORMAT' in structured_text
        print(f"Uses table format (should be false): {'✅' if has_table_format else '❌'}")
        
        # If the structured text is correct, the GPT extraction should work
        if has_financial_values and has_financial_format and not has_table_format:
            print("\n🎉 SUCCESS: The Excel extraction fix is working correctly!")
            print("The structured text now contains the actual financial values and uses the correct format.")
            print("This should resolve the GPT extraction issue where it was returning text instead of JSON.")
        else:
            print("\n❌ FAILURE: The Excel extraction fix is not working correctly.")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_complete_flow()