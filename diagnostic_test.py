import pandas as pd
import tempfile
import os
from ai_extraction import extract_text_from_excel

print("Diagnostic Test for Excel Extraction")
print("=" * 40)

# Create a simple test case similar to what might be in the logs
# Based on the logs, it seems like the data is being read as a single row
data = {
    'Category': ['Rental Income - Commercial'],
    'Rental Income - Residential': ['30000.0'],
    'Parking Fees': ['2000.0'],
    'Laundry Income': ['500.0'],
    'Application Fees': ['300.0'],
    'Late Fees': ['150.0']
}

df = pd.DataFrame(data)
print("Created DataFrame with shape:", df.shape)
print("DataFrame columns:", list(df.columns))
print("DataFrame content:")
print(df)
print()

# Save to Excel
with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
    tmp_filename = tmp_file.name
    df.to_excel(tmp_file, sheet_name='Real Estate Financial Statement', index=False)

print("Saved to Excel file:", tmp_filename)

# Read the file content
with open(tmp_filename, 'rb') as f:
    file_content = f.read()

print("File size:", len(file_content), "bytes")

# Test extraction
print("\nTesting extraction...")
extracted_text = extract_text_from_excel(file_content, "test_financial_statement.xlsx")

print("Extracted text length:", len(extracted_text))
print("\nFirst 500 characters of extracted text:")
print(extracted_text[:500])

# Clean up
os.unlink(tmp_filename)