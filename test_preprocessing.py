"""
Simple test to verify preprocessing module works with actual data
"""

import pandas as pd
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing_module import preprocess_file

def create_test_csv():
    """Create a simple CSV file with financial data"""
    data = {
        'Category': ['Rental Income', 'Property Taxes', 'Insurance', 'Net Operating Income'],
        'Amount': [50000.0, 10000.0, 5000.0, 35000.0]
    }
    df = pd.DataFrame(data)
    file_path = 'test_financial_data.csv'
    df.to_csv(file_path, index=False)
    return file_path

def test_preprocessing():
    """Test the preprocessing module with actual data"""
    print("Creating test CSV file...")
    csv_file_path = create_test_csv()
    
    try:
        print(f"Created test file: {csv_file_path}")
        
        # Test preprocessing
        print("\nPreprocessing file...")
        result = preprocess_file(csv_file_path)
        
        print("Preprocessing successful!")
        print(f"File type: {result['metadata']['file_type']}")
        print(f"Extension: {result['metadata']['extension']}")
        print(f"Content length: {len(result['content'].get('combined_text', ''))} characters")
        
        # Show a sample of the extracted content
        combined_text = result['content'].get('combined_text', '')
        print(f"\nSample of extracted content (first 500 chars):")
        print("-" * 50)
        print(combined_text[:500])
        print("-" * 50)
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(csv_file_path):
            os.unlink(csv_file_path)
            print(f"\nCleaned up temporary file: {csv_file_path}")

if __name__ == "__main__":
    test_preprocessing()