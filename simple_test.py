import pandas as pd
import io
import tempfile
import os
from ai_extraction import extract_text_from_excel

# Create a simple test
def test_excel_extraction():
    # Create a simple DataFrame
    data = {
        'Category': ['Gross Potential Rent', 'Vacancy Loss', 'Other Income', 'Property Taxes', 'Net Operating Income'],
        'Amount': [100000, -5000, 3000, -12000, 85000]
    }
    df = pd.DataFrame(data)
    
    # Save to Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        tmp_name = tmp.name
        df.to_excel(tmp_name, index=False)
    
    # Read back as bytes
    with open(tmp_name, 'rb') as f:
        content = f.read()
    
    # Clean up
    os.unlink(tmp_name)
    
    # Test our function
    result = extract_text_from_excel(content, "test.xlsx")
    print("Extraction result:")
    print(result)
    print("\nLength:", len(result))
    
    # Check if it contains expected content
    if "Gross Potential Rent" in result and "Net Operating Income" in result:
        print("✅ SUCCESS: Contains expected financial data")
        return True
    else:
        print("❌ FAILURE: Missing expected financial data")
        return False

if __name__ == "__main__":
    test_excel_extraction()