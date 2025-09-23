import io
import os
from unittest.mock import patch, MagicMock
from ai_extraction import extract_financial_data_with_gpt

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
file_content = sample_text.encode('utf-8')
file_name = "sample_financial_statement.txt"

print("Testing extract_financial_data_with_gpt function...")

# Test the function with preprocessing module not available
try:
    # Since we can't actually call OpenAI API without a key, we'll mock the chat_completion function
    with patch('ai_extraction.chat_completion') as mock_chat_completion:
        # Mock a successful response from GPT
        mock_response = '{"gpr": 100000.0, "vacancy_loss": 5000.0, "concessions": 2000.0, "other_income": 3000.0, "egi": 96000.0, "opex": 27000.0, "noi": 69000.0, "property_taxes": 12000.0, "insurance": 2000.0, "repairs_maintenance": 3000.0, "utilities": 4000.0, "management_fees": 6000.0}'
        mock_chat_completion.return_value = mock_response
        
        # Test the function
        result = extract_financial_data_with_gpt(file_content, file_name, "current_month_actuals", "fake-api-key")
        
        print("Extraction successful!")
        print(f"Result keys: {list(result.keys())}")
        print(f"GPR: {result.get('gpr', 'Not found')}")
        print(f"NOI: {result.get('noi', 'Not found')}")
        print(f"OpEx: {result.get('opex', 'Not found')}")
        
        # Verify that the mock was called
        assert mock_chat_completion.called, "chat_completion was not called"
        print("✓ chat_completion was called successfully")
        
        # Verify the extracted values
        expected_values = {
            'gpr': 100000.0,
            'noi': 69000.0,
            'opex': 27000.0
        }
        
        for key, expected_value in expected_values.items():
            actual_value = result.get(key, None)
            assert actual_value == expected_value, f"Expected {key}={expected_value}, got {actual_value}"
            print(f"✓ {key}: {actual_value}")
            
        print("\n✅ All tests passed! The extract_financial_data_with_gpt function works correctly.")
        
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()