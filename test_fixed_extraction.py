"""
Test the fixed Excel extraction
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

def extract_excel_text(file_content: bytes, file_name: str) -> str:
    """
    Extract structured text from Excel files (fixed version).
    """
    text_parts = [f"EXCEL DOCUMENT: {file_name}", "=" * 60, ""]
    
    try:
        excel_file = io.BytesIO(file_content)
        xl = pd.ExcelFile(excel_file)
        
        for sheet_name in xl.sheet_names:
            text_parts.append(f"[SHEET_START] {sheet_name}")
            text_parts.append("-" * 40)
            
            # Reset file pointer and read sheet
            excel_file.seek(0)
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Remove unnamed columns that are truly artifacts (not containing financial data)
            columns_to_drop = []
            for col in df.columns:
                if str(col).startswith('Unnamed:'):
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
                    
                    # If less than 10% of values are numeric, consider it an artifact column
                    if total_count > 0 and numeric_count / total_count < 0.1:
                        columns_to_drop.append(col)
            
            if columns_to_drop:
                df = df.drop(columns=columns_to_drop)
            
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
                
                # Check if we have multiple columns (category-value structure)
                has_multiple_columns = len(df.columns) >= 2
                
                # Check if second column has numeric values (more robust check)
                has_numeric_values = False
                if len(df.columns) >= 2:
                    second_column = df.iloc[:, 1]
                    numeric_count = 0
                    total_count = 0
                    for val in second_column:
                        if pd.notna(val):
                            total_count += 1
                            val_str = str(val)
                            # Check if it looks like a numeric value (allowing for currency symbols, commas, etc.)
                            if re.search(r'[\d.,]+', val_str):
                                numeric_count += 1
                    
                    # If more than 30% of non-null values in second column are numeric, consider it numeric
                    if total_count > 0 and numeric_count / total_count > 0.3:
                        has_numeric_values = True
                
                print(f"Detection results:")
                print(f"  Has financial terms: {has_financial_terms}")
                print(f"  Has multiple columns: {has_multiple_columns}")
                print(f"  Has numeric values: {has_numeric_values}")
                print(f"  Should use FINANCIAL_STATEMENT_FORMAT: {has_financial_terms and has_multiple_columns and has_numeric_values}")
                
                if has_financial_terms and has_multiple_columns and has_numeric_values:
                    # Format as financial statement with proper category:value pairs
                    text_parts.append("[FINANCIAL_STATEMENT_FORMAT]")
                    text_parts.append("LINE ITEMS:")
                    text_parts.append("")
                    
                    # Process rows to create category:value pairs
                    # Use the first column as categories and subsequent columns for values
                    for idx, row in df.iterrows():
                        if len(row) >= 1:
                            category = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                            
                            # Only include rows with meaningful data
                            if category.strip() and not category.startswith('Unnamed') and category.strip() != '[EMPTY]':
                                category = category.strip()
                                
                                # Check if we have a value in the second column
                                value = ""
                                if len(row) >= 2 and pd.notna(row.iloc[1]):
                                    value = str(row.iloc[1])
                                
                                if value and value != "nan" and value.strip() != '[EMPTY]':
                                    # Clean the value
                                    cleaned_value = value.replace('$', '').replace(',', '').strip()
                                    text_parts.append(f"  {category}: {cleaned_value}")
                                else:
                                    # Section header
                                    text_parts.append(f"  SECTION: {category}")
                else:
                    # Standard table format
                    text_parts.append("[TABLE_FORMAT]")
                    text_parts.append("COLUMN HEADERS: " + " | ".join(str(col) for col in df.columns))
                    text_parts.append("")
                    text_parts.append("DATA ROWS:")
                    table_text = df.to_string(index=False, na_rep='[EMPTY]', max_colwidth=30)
                    for line in table_text.split('\n'):
                        text_parts.append(f"  {line}")
            else:
                text_parts.append("[EMPTY_SHEET]")
            
            text_parts.append("")
            text_parts.append("[SHEET_END]")
            text_parts.append("")
        
        text_parts.append("[DOCUMENT_END]")
        
    except Exception as e:
        print(f"Error extracting Excel text: {str(e)}")
        text_parts = [f"[Excel content from {file_name}]"]
    
    return "\n".join(text_parts)

def test_fixed_extraction():
    """Test the fixed extraction"""
    print("Creating test Excel file...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test the Excel text extraction
        structured_text = extract_excel_text(file_content, "financial_statement_september_2025_actual.xlsx")
        
        print("\nStructured text output:")
        print("=" * 60)
        print(structured_text)
        print("=" * 60)
        
        # Check if it contains the financial values
        has_financial_values = '30000.0' in structured_text and '20000.0' in structured_text
        print(f"\nContains financial values: {'✅' if has_financial_values else '❌'}")
        
        # Check if it's using the financial statement format
        has_financial_format = 'FINANCIAL_STATEMENT_FORMAT' in structured_text
        print(f"Uses financial statement format: {'✅' if has_financial_format else '❌'}")
        
        # Check if it's using the table format (which would be wrong)
        has_table_format = 'TABLE_FORMAT' in structured_text
        print(f"Uses table format (should be false): {'✅' if has_table_format else '❌'}")
        
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
    test_fixed_extraction()