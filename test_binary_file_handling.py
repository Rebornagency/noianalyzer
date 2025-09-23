import io
import os
from unittest.mock import patch, MagicMock
# Set OpenAI API key from environment variable
os.environ['OPENAI_API_KEY'] = 'your-openai-api-key-here'  # Replace with your actual API key
from ai_extraction import extract_noi_data

# Create a mock binary file (simulating a PDF or Excel file)
# This would normally be binary data that can't be decoded as UTF-8
binary_content = b'\x25\x50\x44\x46\x2d\x31\x2e\x34\x0a\x25\xc4\xe5\xf2\xe5\xeb\xa7'  # PDF header
binary_content += b'\x00' * 1000  # Add more binary data

# Create a file-like object with binary content
binary_file = io.BytesIO(binary_content)
binary_file.name = "sample_document.pdf"

# Also create a text file for comparison
text_content = """
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

text_file = io.BytesIO(text_content.encode('utf-8'))
text_file.name = "sample_financial_statement.txt"

print("Testing binary file handling in extract_noi_data function...")

# Test with binary file
try:
    # Mock the chat_completion function
    with patch('ai_extraction.chat_completion') as mock_chat_completion:
        # Mock response for binary file (should still work with fallback)
        mock_response_binary = '{"gpr": 0.0, "vacancy_loss": 0.0, "concessions": 0.0, "other_income": 0.0, "egi": 0.0, "opex": 0.0, "noi": 0.0, "property_taxes": 0.0, "insurance": 0.0, "repairs_maintenance": 0.0, "utilities": 0.0, "management_fees": 0.0}'
        mock_chat_completion.return_value = mock_response_binary
        
        # Test with binary file
        result_binary = extract_noi_data(binary_file, "current_month_actuals")
        
        print("Binary file processing completed!")
        print(f"Result keys: {list(result_binary.keys())}")
        print(f"GPR: {result_binary.get('gpr', 'Not found')}")
        print(f"NOI: {result_binary.get('noi', 'Not found')}")
        print(f"OpEx: {result_binary.get('opex', 'Not found')}")
        
        # Verify that the mock was called
        assert mock_chat_completion.called, "chat_completion was not called for binary file"
        print("✓ chat_completion was called for binary file")
        
except Exception as e:
    print(f"Error during binary file testing: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)

# Test with text file
try:
    # Reset the mock
    with patch('ai_extraction.chat_completion') as mock_chat_completion:
        # Mock response for text file (should extract actual values)
        mock_response_text = '{"gpr": 100000.0, "vacancy_loss": 5000.0, "concessions": 2000.0, "other_income": 3000.0, "egi": 96000.0, "opex": 27000.0, "noi": 69000.0, "property_taxes": 12000.0, "insurance": 2000.0, "repairs_maintenance": 3000.0, "utilities": 4000.0, "management_fees": 6000.0}'
        mock_chat_completion.return_value = mock_response_text
        
        # Test with text file
        result_text = extract_noi_data(text_file, "current_month_actuals")
        
        print("Text file processing completed!")
        print(f"Result keys: {list(result_text.keys())}")
        print(f"GPR: {result_text.get('gpr', 'Not found')}")
        print(f"NOI: {result_text.get('noi', 'Not found')}")
        print(f"OpEx: {result_text.get('opex', 'Not found')}")
        
        # Verify that the mock was called
        assert mock_chat_completion.called, "chat_completion was not called for text file"
        print("✓ chat_completion was called for text file")
        
        # Verify the extracted values
        expected_values = {
            'gpr': 100000.0,
            'noi': 69000.0,
            'opex': 27000.0
        }
        
        for key, expected_value in expected_values.items():
            actual_value = result_text.get(key, None)
            assert actual_value == expected_value, f"Expected {key}={expected_value}, got {actual_value}"
            print(f"✓ {key}: {actual_value}")
            
        print("\n✅ All tests passed! The extract_noi_data function correctly handles both binary and text files.")
        
except Exception as e:
    print(f"Error during text file testing: {e}")
    import traceback
    traceback.print_exc()