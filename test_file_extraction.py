import io
import os
import pandas as pd
from ai_extraction import extract_financial_data_with_gpt

# Add the missing import for BufferedWriter if needed
from io import BytesIO

# Mock the chat_completion function to avoid actual API calls
def mock_chat_completion(messages, model="gpt-3.5-turbo", temperature=0.1, max_tokens=None, **kwargs):
    """Mock function to simulate GPT response"""
    # Return a sample JSON response with extracted financial data
    return '''{
  "file_name": "test_financials.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 100000.0,
  "vacancy_loss": 5000.0,
  "concessions": 2000.0,
  "bad_debt": 0.0,
  "other_income": 3000.0,
  "egi": 96000.0,
  "opex": 27000.0,
  "noi": 69000.0,
  "property_taxes": 12000.0,
  "insurance": 2000.0,
  "repairs_maintenance": 3000.0,
  "utilities": 4000.0,
  "management_fees": 6000.0,
  "parking": 0.0,
  "laundry": 0.0,
  "late_fees": 0.0,
  "pet_fees": 0.0,
  "application_fees": 0.0,
  "storage_fees": 0.0,
  "amenity_fees": 0.0,
  "utility_reimbursements": 0.0,
  "cleaning_fees": 0.0,
  "cancellation_fees": 0.0,
  "miscellaneous": 0.0
}'''

# Monkey patch the chat_completion function
import utils.openai_utils
utils.openai_utils.chat_completion = mock_chat_completion

# Also mock get_openai_api_key to avoid API key issues
import config
config.get_openai_api_key = lambda: "fake-api-key"

# Create a simple Excel file in memory for testing
def create_test_excel():
    """Create a test Excel file with sample financial data"""
    # Create a DataFrame with sample financial data
    data = {
        'Category': ['Gross Potential Rent', 'Vacancy Loss', 'Concessions', 'Other Income', 
                    'Property Taxes', 'Insurance', 'Repairs & Maintenance', 'Utilities', 'Management Fees'],
        'Amount': [100000, -5000, -2000, 3000, -12000, -2000, -3000, -4000, -6000]
    }
    df = pd.DataFrame(data)
    
    # Write to BytesIO object using the correct approach for pandas 2.2.3
    excel_buffer = BytesIO()
    # Using type ignore comment to bypass type checker issue
    # This is a known compatibility issue between type checkers and pandas
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:  # type: ignore
        df.to_excel(writer, sheet_name='Financials', index=False)
    
    # Get the bytes
    excel_buffer.seek(0)
    return excel_buffer.getvalue()

# Create a simple CSV file in memory for testing
def create_test_csv():
    """Create a test CSV file with sample financial data"""
    # Create CSV content
    csv_content = """Category,Amount
Gross Potential Rent,100000
Vacancy Loss,-5000
Concessions,-2000
Other Income,3000
Property Taxes,-12000
Insurance,-2000
Repairs & Maintenance,-3000
Utilities,-4000
Management Fees,-6000"""
    
    return csv_content.encode('utf-8')

# Create a simple text file for testing
def create_test_text():
    """Create a test text file with sample financial data"""
    text_content = """
PROPERTY MANAGEMENT STATEMENT
SEPTEMBER 2025

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
    
    return text_content.encode('utf-8')

# Test the extraction function
if __name__ == "__main__":
    print("Testing file extraction for different file types...")
    
    # Test Excel file
    print("\n1. Testing Excel file extraction:")
    try:
        excel_content = create_test_excel()
        result = extract_financial_data_with_gpt(excel_content, "test_financials.xlsx", "current_month_actuals", "fake-api-key")
        print("✅ Excel extraction successful!")
        print(f"   GPR: {result.get('gpr', 'Not found')}")
        print(f"   NOI: {result.get('noi', 'Not found')}")
        print(f"   OpEx: {result.get('opex', 'Not found')}")
    except Exception as e:
        print(f"❌ Excel extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test CSV file
    print("\n2. Testing CSV file extraction:")
    try:
        csv_content = create_test_csv()
        result = extract_financial_data_with_gpt(csv_content, "test_financials.csv", "current_month_actuals", "fake-api-key")
        print("✅ CSV extraction successful!")
        print(f"   GPR: {result.get('gpr', 'Not found')}")
        print(f"   NOI: {result.get('noi', 'Not found')}")
        print(f"   OpEx: {result.get('opex', 'Not found')}")
    except Exception as e:
        print(f"❌ CSV extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test text file
    print("\n3. Testing text file extraction:")
    try:
        text_content = create_test_text()
        result = extract_financial_data_with_gpt(text_content, "test_financials.txt", "current_month_actuals", "fake-api-key")
        print("✅ Text extraction successful!")
        print(f"   GPR: {result.get('gpr', 'Not found')}")
        print(f"   NOI: {result.get('noi', 'Not found')}")
        print(f"   OpEx: {result.get('opex', 'Not found')}")
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 All tests completed!")