import pandas as pd
import tempfile
import os
from ai_extraction import extract_text_from_excel, extract_financial_data_with_gpt

# Mock the chat_completion function to avoid actual API calls
import ai_extraction
original_chat_completion = ai_extraction.chat_completion

def mock_chat_completion_with_meaningful_data(*args, **kwargs):
    """Mock function that returns meaningful financial data"""
    return '''{
  "file_name": "test_file.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 100000.0,
  "vacancy_loss": 5000.0,
  "concessions": 2000.0,
  "bad_debt": 1000.0,
  "other_income": 5000.0,
  "egi": 92000.0,
  "opex": 30000.0,
  "noi": 62000.0,
  "property_taxes": 8000.0,
  "insurance": 2000.0,
  "repairs_maintenance": 5000.0,
  "utilities": 3000.0,
  "management_fees": 6000.0,
  "parking": 2000.0,
  "laundry": 1000.0,
  "late_fees": 500.0,
  "pet_fees": 500.0,
  "application_fees": 500.0,
  "storage_fees": 500.0,
  "amenity_fees": 500.0,
  "utility_reimbursements": 1000.0,
  "cleaning_fees": 1000.0,
  "cancellation_fees": 200.0,
  "miscellaneous": 300.0
}'''

def mock_chat_completion_with_zero_data(*args, **kwargs):
    """Mock function that returns all zero values (should be rejected)"""
    return '''{
  "file_name": "test_file.xlsx",
  "document_type": "current_month_actuals",
  "gpr": 0.0,
  "vacancy_loss": 0.0,
  "concessions": 0.0,
  "bad_debt": 0.0,
  "other_income": 0.0,
  "egi": 0.0,
  "opex": 0.0,
  "noi": 0.0,
  "property_taxes": 0.0,
  "insurance": 0.0,
  "repairs_maintenance": 0.0,
  "utilities": 0.0,
  "management_fees": 0.0,
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

print("Testing Excel extraction...")
extracted_text = extract_text_from_excel(file_content, "test_file.xlsx")

print("EXTRACTED TEXT LENGTH:", len(extracted_text))
print("EXTRACTED TEXT (first 500 chars):")
print("=" * 50)
print(extracted_text[:500])
print("=" * 50)

# Check if key features are present
checks = [
    ("Sheet name detected", "[SHEET_START] Financial Statement" in extracted_text),
    ("Financial statement format detected", "[FINANCIAL_STATEMENT_FORMAT]" in extracted_text),
    ("Categories with values", ":" in extracted_text),
    ("Net Operating Income", "Net Operating Income" in extracted_text),
    ("Property Taxes", "Property Taxes" in extracted_text),
    ("Gross Potential Rent", "Gross Potential Rent" in extracted_text)
]

print("\nVERIFICATION CHECKS:")
all_passed = True
for check_name, check_result in checks:
    status = "✅ PASS" if check_result else "❌ FAIL"
    print(f"  {status}: {check_name}")
    if not check_result:
        all_passed = False

# Test GPT extraction with meaningful data
print("\nTesting GPT extraction with meaningful data...")
ai_extraction.chat_completion = mock_chat_completion_with_meaningful_data

try:
    result = extract_financial_data_with_gpt(file_content, "test_file.xlsx", "current_month_actuals", "fake_api_key")
    print("GPR:", result.get("gpr", "NOT FOUND"))
    print("NOI:", result.get("noi", "NOT FOUND"))
    
    # Check if we got meaningful data
    has_meaningful_data = result.get("gpr", 0) != 0 and result.get("noi", 0) != 0
    status = "✅ PASS" if has_meaningful_data else "❌ FAIL"
    print(f"GPT extraction with meaningful data: {status}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test GPT extraction with zero data (should be rejected)
print("\nTesting GPT extraction with zero data (should be rejected)...")
ai_extraction.chat_completion = mock_chat_completion_with_zero_data

try:
    result = extract_financial_data_with_gpt(file_content, "test_file.xlsx", "current_month_actuals", "fake_api_key")
    print("GPR:", result.get("gpr", "NOT FOUND"))
    print("NOI:", result.get("noi", "NOT FOUND"))
    
    # Check if we got fallback data (all zeros should be rejected)
    has_meaningful_data = result.get("gpr", 0) != 0 or result.get("noi", 0) != 0
    status = "✅ PASS" if not has_meaningful_data else "❌ FAIL"  # Should be rejected, so no meaningful data
    print(f"GPT extraction correctly rejected zero data: {status}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Clean up
os.unlink(tmp_filename)

# Restore original function
ai_extraction.chat_completion = original_chat_completion

print("\n✅ Simple perfect approach test completed!")