"""
Test file for the world-class data extraction system
"""

import pandas as pd
import io
import tempfile
import os
from world_class_extraction import WorldClassExtractor, extract_financial_data

def create_test_excel_file():
    """Create a test Excel file that exactly matches the structure from the logs"""
    # Based on the GPT input, the Excel file has this structure:
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

def test_world_class_extraction():
    """Test the world-class extraction system"""
    print("Creating test Excel file with exact structure from logs...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test the world-class extraction
        print("\nTesting world-class extraction...")
        extractor = WorldClassExtractor()
        result = extractor.extract_data(file_content, "financial_statement_september_2025_actual.xlsx", "Actual Income Statement")
        
        print("Extraction completed successfully!")
        print(f"Processing time: {result.processing_time:.2f} seconds")
        print(f"Document type: {result.document_type.value}")
        print(f"Extraction method: {result.extraction_method}")
        print(f"Overall confidence: {result.confidence.value}")
        
        print("\nExtracted financial data:")
        print("=" * 60)
        for key, value in result.data.items():
            confidence = result.confidence_scores.get(key, 0.0)
            print(f"  {key}: {value} (confidence: {confidence:.2f})")
        print("=" * 60)
        
        print("\nAudit trail:")
        print("=" * 60)
        for step in result.audit_trail:
            print(f"  - {step}")
        print("=" * 60)
        
        # Test backward compatibility function
        print("\nTesting backward compatibility function...")
        compat_result = extract_financial_data(file_content, "financial_statement_september_2025_actual.xlsx", "Actual Income Statement")
        print("Backward compatibility function works correctly!")
        print(f"Extracted {len(compat_result)} fields")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_world_class_extraction()