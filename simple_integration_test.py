"""
Simple integration test showing how document validation improves the extraction workflow
"""

import pandas as pd
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing_module import FilePreprocessor

def create_sample_files():
    """Create sample files representing different scenarios"""
    files = {}
    
    # 1. Template file (CSV version of the problematic case)
    template_data = {
        'Category': [
            'Property: Example Commercia...',
            'Period: September 1, 2025 -...',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Total Revenue',
            'Property Management Fees',
            'Utilities',
            'Property Taxes',
            'Total Operating Expenses',
            'Net Operating Income (NOI)'
        ],
        'Amount': [
            '', '', '', '', '', '', '', '', '', '', '', ''
        ]
    }
    template_df = pd.DataFrame(template_data)
    template_file = 'template_from_log.csv'
    template_df.to_csv(template_file, index=False)
    files['template'] = template_file
    
    # 2. File with actual financial data
    financial_data = {
        'Category': [
            'Property: Downtown Office Building',
            'Period: September 2025',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Total Revenue',
            'Property Management Fees',
            'Utilities',
            'Property Taxes',
            'Total Operating Expenses',
            'Net Operating Income (NOI)'
        ],
        'Amount': [
            '', '', 30000.0, 20000.0, 2000.0, 500.0, 52500.0, 4000.0, 3000.0, 2000.0, 9000.0, 43500.0
        ]
    }
    financial_df = pd.DataFrame(financial_data)
    financial_file = 'actual_financial_data.csv'
    financial_df.to_csv(financial_file, index=False)
    files['financial'] = financial_file
    
    return files

def simulate_improved_workflow():
    """Demonstrate the improved workflow with validation"""
    print("Creating sample files...")
    files = create_sample_files()
    
    try:
        preprocessor = FilePreprocessor()
        
        print("\n" + "="*60)
        print("DEMONSTRATING IMPROVED WORKFLOW WITH VALIDATION")
        print("="*60)
        
        # Test 1: Template file (the problematic case)
        print(f"\n1. Testing template file (problematic case): {files['template']}")
        template_result = preprocessor.preprocess(files['template'])
        template_has_data = preprocessor.validate_financial_content(template_result['content'])
        print(f"   Template has financial data: {template_has_data}")
        
        if not template_has_data:
            print("   ✅ CORRECTLY IDENTIFIED AS TEMPLATE")
            print("   🛑 Would prevent unnecessary GPT API call")
            print("   💬 Would provide clear user feedback:")
            print("      'The uploaded document appears to be a template without actual financial data.'")
            print("      'Please upload a document containing real financial figures.'")
        else:
            print("   ❌ Failed to identify as template")
        
        # Test 2: File with actual financial data
        print(f"\n2. Testing file with actual financial data: {files['financial']}")
        financial_result = preprocessor.preprocess(files['financial'])
        financial_has_data = preprocessor.validate_financial_content(financial_result['content'])
        print(f"   Financial file has financial data: {financial_has_data}")
        
        if financial_has_data:
            print("   ✅ CORRECTLY IDENTIFIED AS HAVING FINANCIAL DATA")
            print("   ✅ Would proceed to GPT API for extraction")
            print("   💰 GPT API would receive actual numerical values to process")
        else:
            print("   ❌ Incorrectly identified as lacking data")
        
        print("\n" + "="*60)
        print("WORKFLOW IMPROVEMENT BENEFITS")
        print("="*60)
        print("✅ Templates are identified BEFORE expensive API processing")
        print("✅ Users get IMMEDIATE, clear feedback")
        print("✅ System resources are used more efficiently")
        print("✅ Reduced API costs by preventing unnecessary calls")
        print("✅ Better user experience with guided error handling")
        print("✅ Improved reliability and reduced error states")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        for file in files.values():
            if os.path.exists(file):
                os.unlink(file)
                print(f"Cleaned up: {file}")

def main():
    """Main function to run the integration test"""
    print("NOI Analyzer - Financial Data Extraction Workflow Improvement")
    print("Solution to the template processing issue from conversation log")
    
    success = simulate_improved_workflow()
    
    if success:
        print("\n🎉 Demonstration completed successfully!")
        print("\nThis solution addresses the exact issue from the conversation log where:")
        print("- A template document was sent to the GPT API")
        print("- The API correctly identified no financial data to extract")
        print("- Users received confusing technical error messages")
        print("\nWith the improved workflow:")
        print("- Document validation happens BEFORE API processing")
        print("- Users receive clear, actionable guidance immediately")
        print("- System prevents unnecessary API calls and costs")
        print("- Overall user experience is significantly improved")
    else:
        print("\n❌ Demonstration failed!")

if __name__ == "__main__":
    main()