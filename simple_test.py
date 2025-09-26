import pandas as pd
import io

# Create test data similar to what we saw in the logs
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
print("Original DataFrame:")
print(df)
print("\n" + "="*50 + "\n")

# Test our improved logic for identifying value columns
value_column_indices = []
for col_idx in range(len(df.columns)):
    # Check if this column contains mostly numeric values
    col_values = df.iloc[:, col_idx]
    numeric_count = 0
    total_count = 0
    for val in col_values:
        if pd.notna(val):
            total_count += 1
            try:
                # Handle various number formats
                val_str = str(val).strip().replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
                if val_str and val_str != 'nan':
                    float(val_str)
                    numeric_count += 1
            except ValueError:
                pass
    
    # If more than 30% of non-null values are numeric, consider this a value column
    if total_count > 0 and numeric_count / total_count > 0.3:
        value_column_indices.append(col_idx)

print(f"Value column indices: {value_column_indices}")

# If we couldn't find clear numeric columns, use a heuristic approach
if not value_column_indices and len(df.columns) >= 2:
    # Assume the last column contains values
    value_column_indices = [len(df.columns) - 1]
    print(f"No clear numeric columns found, using heuristic: {value_column_indices}")

print(f"Final value column indices: {value_column_indices}")