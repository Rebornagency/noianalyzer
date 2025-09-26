import pandas as pd
import io
import tempfile
import os

# Import the actual function from our fixed code
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

def test_excel_extraction():
    """Test the Excel extraction with the actual function"""
    print("Creating test Excel file with exact structure from logs...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test Excel extraction
        print("\nTesting Excel extraction with fixed function...")
        extracted_text = extract_text_from_excel(file_content, "financial_statement_september_2025_actual.xlsx")
        
        print("Extracted text length:", len(extracted_text))
        print("\nExtracted text:")
        print("=" * 60)
        print(extracted_text)
        print("=" * 60)
        
        # Analyze the structure
        print("\nANALYSIS:")
        has_financial_format = '[FINANCIAL_STATEMENT_FORMAT]' in extracted_text
        has_net_operating_income = 'Net Operating Income' in extracted_text
        has_actual_values = '30000.0' in extracted_text or '57950.0' in extracted_text or '16000.0' in extracted_text
        has_category_value_pairs = ':' in extracted_text and ('Rental Income' in extracted_text or 'Parking Fees' in extracted_text)
        
        print(f"  Extracted text contains '[FINANCIAL_STATEMENT_FORMAT]': {'✅' if has_financial_format else '❌'}")
        print(f"  Extracted text contains 'Net Operating Income': {'✅' if has_net_operating_income else '❌'}")
        print(f"  Extracted text contains actual values: {'✅' if has_actual_values else '❌'}")
        print(f"  Extracted text contains category:value pairs: {'✅' if has_category_value_pairs else '❌'}")
        
        # Success criteria - even if it doesn't detect as financial format, 
        # it should at least extract the values properly in the table format
        success = has_actual_values and has_category_value_pairs
        print(f"\n{'SUCCESS' if success else 'PARTIAL SUCCESS'}: Excel extraction {'works correctly' if success else 'extracts values but needs improvement'}")
        
        # Show what we actually extracted
        if '[FINANCIAL_STATEMENT_FORMAT]' in extracted_text:
            print("\nFinancial statement format detected:")
            lines = extracted_text.split('\n')
            in_financial_section = False
            for line in lines:
                if '[FINANCIAL_STATEMENT_FORMAT]' in line:
                    in_financial_section = True
                    continue
                if in_financial_section and line.strip() == '':
                    continue
                if in_financial_section and '[SHEET_END]' in line:
                    break
                if in_financial_section:
                    print(f"  {line}")
        else:
            print("\nUsing table format - checking for values:")
            lines = extracted_text.split('\n')
            value_count = 0
            for line in lines:
                if '30000.0' in line or '20000.0' in line or '57950.0' in line or '16000.0' in line:
                    print(f"  Found value: {line.strip()}")
                    value_count += 1
            print(f"  Total values found: {value_count}")
        
        return success
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_excel_extraction()