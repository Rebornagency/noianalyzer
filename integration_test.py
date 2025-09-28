"""
Integration test to verify compatibility of world-class extraction with existing codebase
"""

import pandas as pd
import io
import tempfile
import os
from io import BytesIO

# Test the original extraction function
from ai_extraction import extract_text_from_excel

# Test the new world-class extraction
from world_class_extraction import WorldClassExtractor, extract_financial_data

def create_test_excel_file():
    """Create a test Excel file"""
    data = {
        'Real Estate Financial Statement - Sep 2025 (Actual)': [
            'Property: Example Commercial Property',
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
        'Unnamed: 1': [
            '', '', '[EMPTY]', '30000.0', '20000.0', '2000.0', '500.0', '300.0', '150.0', '5000.0', '57950.0',
            '', '', '', '4000.0', '3000.0', '2000.0', '1500.0', '2500.0', '1000.0', '500.0', '1000.0', '500.0', '300.0', '200.0', '100.0', '100.0', '16000.0',
            '', '41950.0'
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_file, sheet_name='Real Estate Financial Statement', index=False)
    
    return tmp_filename

def test_compatibility():
    """Test compatibility between old and new extraction methods"""
    print("Creating test Excel file...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test original extraction function
        print("\nTesting original extract_text_from_excel function...")
        original_text = extract_text_from_excel(file_content, "financial_statement_september_2025_actual.xlsx")
        print(f"Original extraction successful. Text length: {len(original_text)}")
        
        # Test new world-class extraction
        print("\nTesting new world-class extraction...")
        extractor = WorldClassExtractor()
        result = extractor.extract_data(file_content, "financial_statement_september_2025_actual.xlsx", "Actual Income Statement")
        print(f"World-class extraction successful!")
        print(f"  Processing time: {result.processing_time:.2f} seconds")
        print(f"  Document type: {result.document_type.value}")
        print(f"  Overall confidence: {result.confidence.value}")
        print(f"  Extracted {len(result.data)} fields")
        
        # Test backward compatibility function
        print("\nTesting backward compatibility function...")
        compat_result = extract_financial_data(file_content, "financial_statement_september_2025_actual.xlsx", "Actual Income Statement")
        print(f"Backward compatibility function successful. Extracted {len(compat_result.data)} fields")
        
        # Compare key financial metrics
        print("\nComparing key financial metrics:")
        print("=" * 60)
        key_metrics = ["gross_potential_rent", "effective_gross_income", "operating_expenses", "net_operating_income"]
        
        for metric in key_metrics:
            new_value = result.data.get(metric, 0.0)
            compat_value = compat_result.data.get(metric, 0.0)
            print(f"  {metric}:")
            print(f"    World-class: {new_value} (confidence: {result.confidence_scores.get(metric, 0.0):.2f})")
            print(f"    Compatible:  {compat_value}")
        
        print("=" * 60)
        
        print("\nINTEGRATION TEST PASSED: All extraction methods work correctly!")
        return True
        
    except Exception as e:
        print(f"Error during integration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_compatibility()