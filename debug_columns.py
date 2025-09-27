"""
Debug the column detection in Excel files
"""

import pandas as pd
import io
import tempfile
import os
import re

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

def debug_columns():
    """Debug the column detection"""
    print("Creating test Excel file...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test with pandas directly to see the structure
        excel_file = io.BytesIO(file_content)
        xl = pd.ExcelFile(excel_file)
        
        for sheet_name in xl.sheet_names:
            print(f"\nAnalyzing sheet: {sheet_name}")
            excel_file.seek(0)
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            print(f"Original DataFrame shape: {df.shape}")
            print(f"Original columns: {list(df.columns)}")
            
            # Show some data from each column
            for col in df.columns:
                print(f"\nColumn '{col}' sample data:")
                col_data = df[col]
                for i in range(min(5, len(col_data))):
                    val = col_data.iloc[i]
                    print(f"  {i}: '{val}' (type: {type(val)})")
            
            # Test our column dropping logic
            columns_to_drop = []
            for col in df.columns:
                if str(col).startswith('Unnamed:'):
                    print(f"\nAnalyzing column '{col}' for dropping:")
                    # Check if this column contains financial data
                    col_data = df[col]
                    numeric_count = 0
                    total_count = 0
                    for val in col_data:
                        if pd.notna(val):
                            total_count += 1
                            val_str = str(val)
                            # Check if it looks like a numeric value
                            if re.search(r'[\d.,]+', val_str):
                                numeric_count += 1
                    
                    print(f"  Numeric count: {numeric_count}, Total count: {total_count}")
                    if total_count > 0:
                        ratio = numeric_count / total_count
                        print(f"  Ratio: {ratio:.2f}")
                    
                    # If less than 10% of values are numeric, consider it an artifact column
                    if total_count > 0 and numeric_count / total_count < 0.1:
                        columns_to_drop.append(col)
                        print(f"  -> Will drop this column")
                    else:
                        print(f"  -> Will keep this column (contains financial data)")
            
            print(f"\nColumns to drop: {columns_to_drop}")
            
            if columns_to_drop:
                df_filtered = df.drop(columns=columns_to_drop)
            else:
                df_filtered = df.copy()
            
            print(f"Filtered DataFrame shape: {df_filtered.shape}")
            print(f"Filtered columns: {list(df_filtered.columns)}")
        
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
    debug_columns()