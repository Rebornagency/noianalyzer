"""
Test script to verify the fix for the data extraction issue
"""

import pandas as pd
import tempfile
import os
from world_class_extraction import WorldClassExtractor
from preprocessing_module import FilePreprocessor

def create_test_excel_file_with_data():
    """Create a test Excel file with actual financial data"""
    data = {
        'Category': [
            'Property: Example Commercial Property',
            'Period: September 1, 2025 - September 30, 2025',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Application Fees',
            'Late Fees',
            'Other Income',
            'Total Revenue',
            '',  # Empty row
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
            '',  # Empty row
            'Net Operating Income (NOI)',
            'Net Operating Income (NOI)'
        ],
        'Amount': [
            '', '', 30000.0, 20000.0, 2000.0, 500.0, 300.0, 150.0, 5000.0, 57950.0,
            '', '', 4000.0, 3000.0, 2000.0, 1500.0, 2500.0, 1000.0, 500.0, 1000.0, 500.0, 300.0, 200.0, 100.0, 100.0, 16000.0,
            '', 41950.0
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_file, sheet_name='Real Estate Financial Statement', index=False)
    
    return tmp_filename

def test_fix():
    """Test that our fix works correctly"""
    print("Creating test Excel file with financial data...")
    excel_file_path = create_test_excel_file_with_data()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File created successfully: {len(file_content)} bytes")
        
        # Test the preprocessing and validation
        print("\nTesting preprocessing and validation...")
        preprocessor = FilePreprocessor()
        preprocessed = preprocessor.preprocess(excel_file_path)
        
        print(f"Preprocessing successful")
        print(f"Preprocessed content keys: {list(preprocessed.keys())}")
        
        # Test validation with correct parameter
        has_financial_data = preprocessor.validate_financial_content(preprocessed['content'])
        print(f"Financial content validation result: {has_financial_data}")
        
        if has_financial_data:
            print("✅ SUCCESS: File correctly identified as having financial data")
        else:
            print("❌ FAILURE: File incorrectly identified as template")
            return False
        
        # Test the world-class extraction
        print("\nTesting world-class extraction...")
        extractor = WorldClassExtractor()
        result = extractor.extract_data(file_content, "test_financial_statement.xlsx", "Actual Income Statement")
        
        print(f"Extraction method: {result.extraction_method}")
        print(f"Processing time: {result.processing_time:.2f} seconds")
        print(f"Document type: {result.document_type.value}")
        print(f"Overall confidence: {result.confidence.value}")
        
        # Check if we got actual financial data (not template validation)
        if result.extraction_method == "template-validation":
            print("❌ FAILURE: Extraction still using template validation")
            return False
        else:
            print("✅ SUCCESS: Extraction correctly bypassed template validation")
            
            # Show some key extracted values
            print("\nExtracted financial data sample:")
            print("=" * 50)
            key_metrics = ['gross_potential_rent', 'effective_gross_income', 'net_operating_income']
            for key in key_metrics:
                value = result.data.get(key, 0.0)
                confidence = result.confidence_scores.get(key, 0.0)
                print(f"  {key}: {value} (confidence: {confidence:.2f})")
            print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(excel_file_path):
            os.unlink(excel_file_path)
            print(f"Cleaned up test file: {excel_file_path}")

if __name__ == "__main__":
    print("Testing fix for data extraction issue...")
    success = test_fix()
    
    if success:
        print("\n🎉 Fix verification successful!")
        print("The data extraction issue should now be resolved.")
    else:
        print("\n❌ Fix verification failed!")
        print("Please check the implementation.")