"""
Test script to verify the financial content validation works correctly
"""

import pandas as pd
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing_module import FilePreprocessor

def create_test_files():
    """Create test files with different types of content"""
    # 1. Template file (no financial data)
    template_data = {
        'Category': [
            'Property:',
            'Period:',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Total Revenue',
            'Operating Expenses',
            'Property Taxes',
            'Total Operating Expenses',
            'Net Operating Income (NOI)'
        ],
        'Amount': ['', '', '', '', '', '', '', '', '', '']
    }
    template_df = pd.DataFrame(template_data)
    template_file = 'template_test.csv'
    template_df.to_csv(template_file, index=False)
    
    # 2. File with actual financial data
    financial_data = {
        'Category': [
            'Property: Sample Property',
            'Period: September 2025',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Total Revenue',
            'Operating Expenses',
            'Property Taxes',
            'Total Operating Expenses',
            'Net Operating Income (NOI)'
        ],
        'Amount': [
            '', 
            '',
            30000.0,
            20000.0,
            2000.0,
            52000.0,
            '',
            5000.0,
            5000.0,
            47000.0
        ]
    }
    financial_df = pd.DataFrame(financial_data)
    financial_file = 'financial_test.csv'
    financial_df.to_csv(financial_file, index=False)
    
    return template_file, financial_file

def test_validation():
    """Test the financial content validation"""
    print("Creating test files...")
    template_file, financial_file = create_test_files()
    
    try:
        preprocessor = FilePreprocessor()
        
        # Test template file
        print(f"\n1. Testing template file: {template_file}")
        template_result = preprocessor.preprocess(template_file)
        template_has_data = preprocessor.validate_financial_content(template_result['content'])
        print(f"Template has financial data: {template_has_data}")
        
        # Show template content
        if 'combined_text' in template_result['content']:
            print("Template content sample:")
            print(template_result['content']['combined_text'][:200])
        
        # Test financial file
        print(f"\n2. Testing financial file: {financial_file}")
        financial_result = preprocessor.preprocess(financial_file)
        financial_has_data = preprocessor.validate_financial_content(financial_result['content'])
        print(f"Financial file has financial data: {financial_has_data}")
        
        # Show financial content
        if 'combined_text' in financial_result['content']:
            print("Financial content sample:")
            print(financial_result['content']['combined_text'][:200])
        
        print(f"\nValidation Results:")
        print(f"  Template correctly identified as lacking data: {not template_has_data}")
        print(f"  Financial file correctly identified as having data: {financial_has_data}")
        
        # Overall result
        success = (not template_has_data) and financial_has_data
        print(f"\nValidation Test: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        for file in [template_file, financial_file]:
            if os.path.exists(file):
                os.unlink(file)
                print(f"Cleaned up: {file}")

if __name__ == "__main__":
    test_validation()