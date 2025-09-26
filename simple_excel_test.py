"""
Simple test to verify the Excel extraction fix
"""

import pandas as pd
import io
import tempfile
import os

def create_test_excel_file():
    """Create a test Excel file that exactly matches the structure from the logs"""
    # Based on the GPT input, the Excel file has this structure:
    data = {
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

def test_excel_structure():
    """Test the Excel structure extraction"""
    print("Creating test Excel file...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test with pandas directly to see the structure
        excel_file = io.BytesIO(file_content)
        df = pd.read_excel(excel_file, sheet_name='Real Estate Financial Statement')
        
        print("\nExcel DataFrame structure:")
        print("=" * 60)
        print(df.to_string())
        print("=" * 60)
        
        # Check columns
        print(f"\nColumns: {list(df.columns)}")
        
        # Check if we have the expected structure
        has_first_column = len(df.columns) >= 1
        has_second_column = len(df.columns) >= 2
        has_values = len(df) > 10  # Should have many rows
        
        print(f"\nStructure Analysis:")
        print(f"  Has first column: {'✅' if has_first_column else '❌'}")
        print(f"  Has second column: {'✅' if has_second_column else '❌'}")
        print(f"  Has sufficient rows: {'✅' if has_values else '❌'}")
        
        # Show some sample data
        print(f"\nSample data from first few rows:")
        for i in range(min(5, len(df))):
            if len(df.columns) >= 2:
                col1 = df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else ""
                col2 = df.iloc[i, 1] if len(df.columns) > 1 and not pd.isna(df.iloc[i, 1]) else ""
                print(f"  Row {i}: '{col1}' -> '{col2}'")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_excel_structure()