import io
from ai_extraction import extract_noi_data

# Create a mock file object with sample financial data
sample_text = """
PROPERTY MANAGEMENT STATEMENT
JANUARY 2024

REVENUE:
Gross Potential Rent: $100,000
Vacancy Loss: ($5,000)
Concessions: ($2,000)
Other Income: $3,000
Effective Gross Income: $96,000

EXPENSES:
Property Taxes: $12,000
Insurance: $2,000
Repairs & Maintenance: $3,000
Utilities: $4,000
Management Fees: $6,000
Total Operating Expenses: $27,000

Net Operating Income: $69,000
"""

# Create a file-like object
file_obj = io.BytesIO(sample_text.encode('utf-8'))
file_obj.name = "sample_financial_statement.txt"

# Test the extraction function
try:
    result = extract_noi_data(file_obj, "current_month_actuals")
    print("Extraction successful!")
    print(f"Result keys: {list(result.keys())}")
    print(f"GPR: {result.get('gpr', 'Not found')}")
    print(f"NOI: {result.get('noi', 'Not found')}")
    print(f"OpEx: {result.get('opex', 'Not found')}")
except Exception as e:
    print(f"Error during extraction: {e}")