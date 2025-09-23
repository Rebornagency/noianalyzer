import io
import os
import tempfile
import pandas as pd
from ai_extraction import extract_text_from_excel

# Create a simple Excel file in memory for testing
def create_test_excel():
    # Create a DataFrame with sample financial data
    data = {
        'Category': ['Gross Potential Rent', 'Vacancy Loss', 'Concessions', 'Other Income', 'Property Taxes', 'Insurance', 'Repairs & Maintenance', 'Utilities', 'Management Fees'],
        'Amount': [100000, -5000, -2000, 3000, -12000, -2000, -3000, -4000, -6000]
    }
    df = pd.DataFrame(data)
    
    # Create a temporary file to write the Excel content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_filename, sheet_name='Financials', index=False)
    
    # Read the file content
    with open(tmp_filename, 'rb') as f:
        excel_content = f.read()
    
    # Clean up the temporary file
    os.unlink(tmp_filename)
    
    return excel_content

# Test the Excel extraction function
if __name__ == "__main__":
    print("Testing Excel extraction...")
    
    # Create test Excel content
    excel_content = create_test_excel()
    
    # Test extraction
    try:
        extracted_text = extract_text_from_excel(excel_content, "test_financials.xlsx")
        print("Extraction successful!")
        print("Extracted text length:", len(extracted_text))
        print("First 500 characters:")
        print(extracted_text[:500])
        print("...")
        
        # Check if it contains expected content
        if "Gross Potential Rent" in extracted_text and "Vacancy Loss" in extracted_text:
            print("✅ Extracted text contains expected financial data")
        else:
            print("❌ Extracted text may be missing financial data")
            
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()