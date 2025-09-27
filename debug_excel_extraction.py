"""
Debug the Excel extraction to understand why it's not detecting financial statements correctly
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

def debug_excel_structure():
    """Debug the Excel structure to understand the detection logic"""
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
            
            # Remove unnamed columns
            columns_to_drop = [col for col in df.columns if str(col).startswith('Unnamed:')]
            if columns_to_drop:
                df = df.drop(columns=columns_to_drop)
            
            print(f"DataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            if not df.empty:
                # Check if this looks like a financial statement
                first_column_data = df.iloc[:, 0].astype(str).str.lower() if len(df.columns) > 0 else pd.Series([])
                financial_keywords = [
                    'rent', 'income', 'revenue', 'expense', 'tax', 'insurance', 
                    'maintenance', 'utilities', 'management', 'parking', 'laundry', 
                    'fee', 'noi', 'egi', 'operating', 'total'
                ]
                has_financial_terms = any(
                    first_column_data.str.contains(keyword, na=False).any() 
                    for keyword in financial_keywords
                )
                
                print(f"Has financial terms: {has_financial_terms}")
                
                # Check first column for financial terms
                print("First column sample data:")
                for i in range(min(10, len(first_column_data))):
                    print(f"  {i}: '{first_column_data.iloc[i]}'")
                
                # Check if we have multiple columns (category-value structure)
                has_multiple_columns = len(df.columns) >= 2
                print(f"Has multiple columns: {has_multiple_columns}")
                
                # Check if second column has numeric values (more robust check)
                has_numeric_values = False
                if len(df.columns) >= 2:
                    second_column = df.iloc[:, 1]
                    numeric_count = 0
                    total_count = 0
                    print("Second column sample data:")
                    for i in range(min(10, len(second_column))):
                        val = second_column.iloc[i]
                        print(f"  {i}: '{val}' (type: {type(val)})")
                        if pd.notna(val):
                            total_count += 1
                            val_str = str(val)
                            # Check if it looks like a numeric value (allowing for currency symbols, commas, etc.)
                            if re.search(r'[\d.,]+', val_str):
                                numeric_count += 1
                                print(f"    -> Numeric match: {val_str}")
                    
                    print(f"Numeric count: {numeric_count}, Total count: {total_count}")
                    
                    # If more than 30% of non-null values in second column are numeric, consider it numeric
                    if total_count > 0 and numeric_count / total_count > 0.3:
                        has_numeric_values = True
                
                print(f"Has numeric values: {has_numeric_values}")
                print(f"Should use FINANCIAL_STATEMENT_FORMAT: {has_financial_terms and has_multiple_columns and has_numeric_values}")
        
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
    debug_excel_structure()