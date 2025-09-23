import io
import os
import tempfile
from preprocessing_module import FilePreprocessor

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

# Create a temporary text file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
    temp_file.write(sample_text)
    temp_file_path = temp_file.name

try:
    # Test the preprocessing module
    preprocessor = FilePreprocessor()
    result = preprocessor.preprocess(temp_file_path, filename="sample_financial_statement.txt")
    
    print("Preprocessing successful!")
    print(f"Result keys: {list(result.keys())}")
    
    if 'content' in result:
        content = result['content']
        print(f"Content keys: {list(content.keys()) if isinstance(content, dict) else 'Not a dict'}")
        
        if isinstance(content, dict) and 'combined_text' in content:
            print("Combined text found:")
            print(content['combined_text'][:200] + "..." if len(content['combined_text']) > 200 else content['combined_text'])
        elif isinstance(content, dict) and 'text' in content:
            print("Text content found:")
            if isinstance(content['text'], list):
                for i, page in enumerate(content['text']):
                    print(f"Page {i+1}: {page.get('content', '')[:100]}...")
            else:
                print(content['text'][:200] + "..." if len(content['text']) > 200 else content['text'])
        else:
            print(f"Content: {str(content)[:200]}...")
    
    print("\nMetadata:")
    if 'metadata' in result:
        for key, value in result['metadata'].items():
            print(f"  {key}: {value}")

except Exception as e:
    print(f"Error during preprocessing: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Clean up temporary file
    try:
        os.unlink(temp_file_path)
    except Exception:
        pass