import pandas as pd
import tempfile
import os
from ai_extraction import extract_text_from_excel

# Recreate the structure that appears in the logs
# This appears to be a single row with many columns
data = {
    'Category': ['Rental Income - Commercial'],
    'Rental Income - Residential': [30000.0],
    'Parking Fees': [2000.0],
    'Laundry Income': [500.0],
    'Application Fees': [300.0],
    'Late Fees': [150.0],
    'Other Income': [1000.0],
    'Total Revenue': [83950.0],
    'Operating Expenses': [''],
    'Property Management Fees': [-4000.0],
    'Utilities': [-2000.0],
    'Property Taxes': [-3000.0],
    'Property Insurance': [-1500.0],
    'Repairs & Maintenance': [-2500.0],
    'Cleaning & Janitorial': [-1000.0],
    'Landscaping & Grounds': [-500.0],
    'Security': [-1000.0],
    'Marketing & Advertising': [-500.0],
    'Administrative Expenses': [-1000.0],
    'HOA Fees (if applicable)': [0.0],
    'Pest Control': [-300.0],
    'Supplies': [-200.0],
    'Total Operating Expenses': [-17000.0],
    'Net Operating Income (NOI)': [66950.0]
}

df = pd.DataFrame(data)

# Save to Excel
with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
    tmp_filename = tmp_file.name
    df.to_excel(tmp_file, sheet_name='Real Estate Financial Statement', index=False)

# Read the file content
with open(tmp_filename, 'rb') as f:
    file_content = f.read()

# Test extraction
print("Testing Excel extraction with transposed data structure...")
extracted_text = extract_text_from_excel(file_content, "test_financial_statement.xlsx")

print("EXTRACTED TEXT LENGTH:", len(extracted_text))
print("\nEXTRACTED TEXT:")
print("=" * 60)
print(extracted_text)
print("=" * 60)

print("\nANALYSIS:")
# Check for key indicators
checks = [
    ("TRANSPOSED FINANCIAL STATEMENT DETECTED", "TRANSPOSED FINANCIAL STATEMENT DETECTED" in extracted_text),
    ("Financial line items and their corresponding values", "Financial line items and their corresponding values" in extracted_text),
    ("Category:", "Category:" in extracted_text),
    ("Property Taxes:", "Property Taxes:" in extracted_text),
    ("Net Operating Income (NOI):", "Net Operating Income (NOI):" in extracted_text),
    ("Total Revenue:", "Total Revenue:" in extracted_text)
]

for description, found in checks:
    status = "✅ FOUND" if found else "❌ MISSING"
    print(f"  {status}: {description}")

# Clean up
os.unlink(tmp_filename)

print("\nIf most of the above are found, the fix is working correctly!")