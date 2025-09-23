import pandas as pd
import io

# Test if we can create and read an Excel file in memory
print("Testing Excel file creation and reading...")

# Create a simple DataFrame
data = {
    'Category': ['Gross Potential Rent', 'Vacancy Loss', 'Concessions'],
    'Amount': [100000, -5000, -2000]
}
df = pd.DataFrame(data)
print("Created DataFrame:")
print(df)

# Write to BytesIO object
excel_buffer = io.BytesIO()
# Using type ignore comment to bypass type checker issue
# This is a known compatibility issue between type checkers and pandas
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:  # type: ignore
    df.to_excel(writer, sheet_name='Financials', index=False)

# Get the bytes
excel_buffer.seek(0)
excel_bytes = excel_buffer.getvalue()
print(f"\nExcel file size: {len(excel_bytes)} bytes")

# Try to read it back
excel_buffer.seek(0)
xl = pd.ExcelFile(excel_buffer)
sheet_names = xl.sheet_names
print(f"Sheet names: {sheet_names}")

df_read = pd.read_excel(xl, sheet_name='Financials')
print("Read DataFrame:")
print(df_read)

print("\n✅ Test completed successfully!")