"""
Verify the Excel extraction fix works with the actual ai_extraction module
"""

import pandas as pd
import io
import tempfile
import os

# Import the extract_text_from_excel function directly
from ai_extraction import extract_text_from_excel

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

def verify_fix():
    """Verify the fix works with the actual ai_extraction module"""
    print("Creating test Excel file...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test the extract_text_from_excel function directly
        # We need to mock the WorldClassExtractor to avoid API key issues
        import world_class_extraction
        
        # Monkey patch the WorldClassExtractor to avoid API key requirement
        original_init = world_class_extraction.WorldClassExtractor.__init__
        
        def mock_init(self):
            # Skip the API key check
            self.openai_api_key = "mock_key"
            self.client = None
            # Define the standard financial metrics structure
            self.financial_metrics = {
                "gross_potential_rent": 0.0,
                "vacancy_loss": 0.0,
                "concessions": 0.0,
                "bad_debt": 0.0,
                "other_income": 0.0,
                "effective_gross_income": 0.0,
                "operating_expenses": 0.0,
                "property_taxes": 0.0,
                "insurance": 0.0,
                "repairs_maintenance": 0.0,
                "utilities": 0.0,
                "management_fees": 0.0,
                "parking_income": 0.0,
                "laundry_income": 0.0,
                "late_fees": 0.0,
                "pet_fees": 0.0,
                "application_fees": 0.0,
                "storage_fees": 0.0,
                "amenity_fees": 0.0,
                "utility_reimbursements": 0.0,
                "cleaning_fees": 0.0,
                "cancellation_fees": 0.0,
                "miscellaneous_income": 0.0,
                "net_operating_income": 0.0,
                "file_name": "",
                "document_type_hint": "",
                "extraction_status": "",
                "requires_manual_entry": False
            }
        
        world_class_extraction.WorldClassExtractor.__init__ = mock_init
        
        try:
            extracted_text = extract_text_from_excel(file_content, "financial_statement_september_2025_actual.xlsx")
            
            print("\nExtracted text from ai_extraction module:")
            print("=" * 60)
            print(extracted_text)
            print("=" * 60)
            
            # Check if it contains the financial values
            has_financial_values = '30000.0' in extracted_text and '20000.0' in extracted_text
            print(f"\nContains financial values: {'✅' if has_financial_values else '❌'}")
            
            # Check if it's using the financial statement format
            has_financial_format = 'FINANCIAL_STATEMENT_FORMAT' in extracted_text
            print(f"Uses financial statement format: {'✅' if has_financial_format else '❌'}")
            
            # Check if it's using the table format (which would be wrong)
            has_table_format = 'TABLE_FORMAT' in extracted_text
            print(f"Uses table format (should be false): {'✅' if has_table_format else '❌'}")
            
            if has_financial_values and has_financial_format and not has_table_format:
                print("\n🎉 SUCCESS: The Excel extraction fix is working correctly with the ai_extraction module!")
                print("The structured text now contains the actual financial values and uses the correct format.")
                print("This should resolve the GPT extraction issue where it was returning text instead of JSON.")
                return True
            else:
                print("\n❌ FAILURE: The Excel extraction fix is not working correctly with the ai_extraction module.")
                return False
                
        finally:
            # Restore the original init method
            world_class_extraction.WorldClassExtractor.__init__ = original_init
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    verify_fix()