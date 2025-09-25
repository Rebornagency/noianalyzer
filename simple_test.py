import pandas as pd
import io
import tempfile
import os
from ai_extraction import extract_text_from_excel

# Create a simple test DataFrame
data = {
    'Category': [
        'Gross Potential Rent',
        'Vacancy Loss',
        'Concessions',
        'Bad Debt',
        'Other Income',
        'Effective Gross Income',
        'Operating Expenses',
        'Property Taxes',
        'Insurance',
        'Repairs & Maintenance',
        'Utilities',
        'Management Fees',
        'Parking',
        'Laundry',
        'Late Fees',
        'Total Operating Expenses',
        'Net Operating Income'
    ],
    'Amount': [
        80000.0,    # Gross Potential Rent
        -2000.0,    # Vacancy Loss
        -1000.0,    # Concessions
        -500.0,     # Bad Debt
        3950.0,     # Other Income
        80450.0,    # Effective Gross Income
        '',         # Operating Expenses header
        -3000.0,    # Property Taxes
        -1500.0,    # Insurance
        -2500.0,    # Repairs & Maintenance
        -2000.0,    # Utilities
        -4000.0,    # Management Fees
        2000.0,     # Parking
        500.0,      # Laundry
        150.0,      # Late Fees
        -16250.0,   # Total Operating Expenses
        64200.0     # Net Operating Income
    ]
}

df = pd.DataFrame(data)

# Save to Excel
with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
    tmp_filename = tmp_file.name
    df.to_excel(tmp_filename, sheet_name='Financial Statement', index=False)

# Read the file content
with open(tmp_filename, 'rb') as f:
    file_content = f.read()

# Test extraction
extracted_text = extract_text_from_excel(file_content, "test_file.xlsx")

print("Extracted text length:", len(extracted_text))
print("Extracted text:")
print(extracted_text)

# Clean up
os.unlink(tmp_filename)