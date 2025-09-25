import pandas as pd
import tempfile
import os
from ai_extraction import extract_text_from_excel

# Create a simple test DataFrame that matches the structure from the logs
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
        50000.0, 30000.0, 2000.0, 500.0, 300.0, 150.0, 1000.0, 83950.0, 
        '', -4000.0, -2000.0, -3000.0, -1500.0, -2500.0, -1000.0, -500.0,
        -1000.0, -500.0, -1000.0, 0.0, -300.0, -200.0, -17000.0, 66950.0
    ]
}

df = pd.DataFrame(data)

# Save to Excel
with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
    tmp_filename = tmp_file.name
    df.to_excel(tmp_filename, sheet_name='Real Estate Financial Statement', index=False)

# Read the file content
with open(tmp_filename, 'rb') as f:
    file_content = f.read()

# Test extraction
print("Testing Excel extraction...")
extracted_text = extract_text_from_excel(file_content, "test_financial_statement.xlsx")

print("EXTRACTED TEXT:")
print("=" * 50)
print(extracted_text)
print("=" * 50)

print("\nKEY FEATURES CHECK:")
features = [
    ("Sheet name detected", "Sheet: Real Estate Financial Statement" in extracted_text),
    ("Financial statement format detected", "FINANCIAL STATEMENT FORMAT DETECTED" in extracted_text),
    ("Categories with values", ":" in extracted_text),
    ("Net Operating Income", "Net Operating Income" in extracted_text),
    ("Property Taxes", "Property Taxes" in extracted_text),
    ("Total Revenue", "Total Revenue" in extracted_text)
]

for feature_name, is_present in features:
    status = "✅" if is_present else "❌"
    print(f"  {status} {feature_name}")

# Clean up
os.unlink(tmp_filename)