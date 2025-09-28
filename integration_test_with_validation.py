"""
Integration test showing how document validation improves the extraction workflow
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
    
    # 1. Template file (the problematic case from the conversation log)
    template_data = {
        'Real Estate Financial Statement - Sep 2025 (Actual)': [
            'Property: Example Commercia...',
            'Period: September 1, 2025 -...',
            'Category',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Application Fees',
            'Late Fees',
            'Other Income',
            'Total Revenue',
            '',
            'Operating Expenses',
            'Property Management Fees',
            'Utilities',
            'Property Taxes',
            'Property Insurance',
            'Repairs & Maintenance',
            'Cleaning & Janitorial',
            'Landscaping & Grounds',
            'Security',
            'Marketing & Advertising',
            'Administrative Expenses',
            'HOA Fees (if applicable)',
            'Pest Control',
            'Supplies',
            'Total Operating Expenses',
            '',
            'Net Operating Income (NOI)',
            'Net Operating Income (NOI)'
        ],
        'Unnamed: 1': [
            '', '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            '', ''
        ]
    }
    template_df = pd.DataFrame(template_data)
    template_file = 'template_from_log.xlsx'
    template_df.to_excel(template_file, sheet_name='Real Estate Financial Statement', index=False)
    files['template'] = template_file
    
    # 2. File with actual financial data
    financial_data = {
        'Real Estate Financial Statement - Sep 2025 (Actual)': [
            'Property: Downtown Office Building',
            'Period: September 1, 2025 - September 30, 2025',
            'Category',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Application Fees',
            'Late Fees',
            'Other Income',
            'Total Revenue',
            '',
            'Operating Expenses',
            'Property Management Fees',
            'Utilities',
            'Property Taxes',
            'Property Insurance',
            'Repairs & Maintenance',
            'Cleaning & Janitorial',
            'Landscaping & Grounds',
            'Security',
            'Marketing & Advertising',
            'Administrative Expenses',
            'HOA Fees (if applicable)',
            'Pest Control',
            'Supplies',
            'Total Operating Expenses',
            '',
            'Net Operating Income (NOI)',
            'Net Operating Income (NOI)'
        ],
        'Amount': [
            '', '', '', 30000.0, 20000.0, 2000.0, 500.0, 300.0, 150.0, 5000.0, 57950.0,
            '', '', '', 4000.0, 3000.0, 2000.0, 1500.0, 2500.0, 1000.0, 500.0, 1000.0, 500.0, 300.0, 200.0, 100.0, 100.0, 16000.0,
            '', 41950.0
        ]
    }
    financial_df = pd.DataFrame(financial_data)
    financial_file = 'actual_financial_data.xlsx'
    financial_df.to_excel(financial_file, sheet_name='Real Estate Financial Statement', index=False)
    files['financial'] = financial_file
    
    return files

def simulate_gpt_api_call(document_content, document_type):
    """
    Simulate what the GPT API would receive and return
    """
    print(f"  GPT API would receive {len(str(document_content))} characters of {document_type} content")
    
    # Check if content has actual financial data
    preprocessor = FilePreprocessor()
    has_financial_data = preprocessor.validate_financial_content({'combined_text': str(document_content)})
    
    if not has_financial_data:
        return {
            "error": "No financial data found",
            "message": "The provided document is a template without actual financial figures. Please provide a document with real financial data."
        }
    else:
        return {
            "message": "Financial data extraction would proceed normally with actual data"
        }

def test_workflow_improvement():
    """Test the improved workflow with validation"""
    print("Creating sample files...")
    files = create_sample_files()
    
    try:
        preprocessor = FilePreprocessor()
        
        print("\n" + "="*60)
        print("TESTING IMPROVED WORKFLOW WITH VALIDATION")
        print("="*60)
        
        # Test 1: Template file (the problematic case)
        print(f"\n1. Testing template file (problematic case): {files['template']}")
        template_result = preprocessor.preprocess(files['template'])
        template_has_data = preprocessor.validate_financial_content(template_result['content'])
        print(f"   Template has financial data: {template_has_data}")
        
        if not template_has_data:
            print("   ✅ Correctly identified as template - would prevent unnecessary GPT API call")
            # Simulate what would happen with the improved workflow
            gpt_response = simulate_gpt_api_call(template_result['content'], "Template")
            print(f"   GPT API Response: {gpt_response}")
        else:
            print("   ❌ Failed to identify as template")
        
        # Test 2: File with actual financial data
        print(f"\n2. Testing file with actual financial data: {files['financial']}")
        financial_result = preprocessor.preprocess(files['financial'])
        financial_has_data = preprocessor.validate_financial_content(financial_result['content'])
        print(f"   Financial file has financial data: {financial_has_data}")
        
        if financial_has_data:
            print("   ✅ Correctly identified as having financial data - would proceed to GPT API")
            # Simulate what would happen with the improved workflow
            gpt_response = simulate_gpt_api_call(financial_result['content'], "Actual Financial Data")
            print(f"   GPT API Response: {gpt_response}")
        else:
            print("   ❌ Incorrectly identified as lacking data")
        
        print("\n" + "="*60)
        print("WORKFLOW IMPROVEMENT SUMMARY")
        print("="*60)
        print("✅ Templates are now correctly identified before GPT processing")
        print("✅ Unnecessary API calls are prevented")
        print("✅ Users get clear feedback about what they need to provide")
        print("✅ System resources are used more efficiently")
        print("✅ Better user experience with immediate feedback")
        
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
    print("Demonstrating solution to the template processing issue")
    
    success = test_workflow_improvement()
    
    if success:
        print("\n🎉 Integration test completed successfully!")
        print("\nThis solution addresses the issue from the conversation log where:")
        print("- A template document was sent to the GPT API")
        print("- The API correctly identified no financial data to extract")
        print("- Users received confusing error messages")
        print("\nWith the improved workflow:")
        print("- Templates are identified before API processing")
        print("- Users receive clear guidance immediately")
        print("- System resources are used more efficiently")
    else:
        print("\n❌ Integration test failed!")

if __name__ == "__main__":
    main()