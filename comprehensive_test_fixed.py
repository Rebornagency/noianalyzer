import pandas as pd
import io
import tempfile
import os

def extract_text_from_excel_fixed(file_content: bytes, file_name: str) -> str:
    """
    Fixed version of extract_text_from_excel with improved value column detection
    """
    # Create a temporary file-like object
    excel_file = io.BytesIO(file_content)
    
    # Read all sheets and convert to text
    text_parts = []
    
    # Get list of sheet names
    xl = pd.ExcelFile(excel_file)
    sheet_names = xl.sheet_names
    
    # Add file header
    text_parts.append(f"EXCEL DOCUMENT: {file_name}")
    text_parts.append("=" * 60)
    text_parts.append("")
    
    for sheet_name in sheet_names:
        # Reset file pointer to beginning
        excel_file.seek(0)
        
        # Read the sheet
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Add sheet header with clear structure markers
        text_parts.append(f"[SHEET_START] {sheet_name}")
        text_parts.append("-" * 40)
        
        # Improve table representation for better GPT understanding
        # Remove unnamed columns that are typically artifacts of merged cells
        columns_to_drop = [col for col in df.columns if str(col).startswith('Unnamed:')]
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
        
        # Convert DataFrame to string representation with better formatting
        if not df.empty:
            # Check if this is likely a financial statement
            first_column_data = df.iloc[:, 0].astype(str).str.lower() if len(df.columns) > 0 else pd.Series([])
            financial_keywords = ['rent', 'income', 'revenue', 'expense', 'tax', 'insurance', 'maintenance', 
                                'utilities', 'management', 'parking', 'laundry', 'fee', 'noi', 'egi', 'operating']
            has_financial_terms = any(
                first_column_data.str.contains(keyword, na=False).any() 
                for keyword in financial_keywords
            )
            
            if has_financial_terms and len(df.columns) >= 2:
                # Format as financial statement with clear category:value pairs
                text_parts.append("[FINANCIAL_STATEMENT_FORMAT]")
                text_parts.append("LINE ITEMS:")
                text_parts.append("")
                
                # Enhanced approach to identify value columns
                # Check all columns for numeric values
                value_column_indices = []
                for col_idx in range(len(df.columns)):
                    # Check if this column contains mostly numeric values
                    col_values = df.iloc[:, col_idx]
                    numeric_count = 0
                    total_count = 0
                    for val in col_values:
                        if pd.notna(val):
                            total_count += 1
                            try:
                                # Handle various number formats
                                val_str = str(val).strip().replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
                                if val_str and val_str != 'nan':
                                    float(val_str)
                                    numeric_count += 1
                            except ValueError:
                                pass
                    
                    # If more than 30% of non-null values are numeric, consider this a value column
                    if total_count > 0 and numeric_count / total_count > 0.3:
                        value_column_indices.append(col_idx)
                
                # If we couldn't find clear numeric columns, use a heuristic approach
                if not value_column_indices and len(df.columns) >= 2:
                    # Assume the last column contains values
                    value_column_indices = [len(df.columns) - 1]
                
                # Extract data using the identified columns
                category_column_idx = 0  # Assume first column has categories
                
                # Keep track of previous non-empty category for handling multi-row categories
                previous_category = ""
                
                for idx, row in df.iterrows():
                    # Get category from the first column
                    category = str(row.iloc[category_column_idx]) if len(row) > category_column_idx and pd.notna(row.iloc[category_column_idx]) else ""
                    
                    # Find the best value from value columns
                    amount = ""
                    for col_idx in value_column_indices:
                        if len(row) > col_idx:
                            raw_amount = row.iloc[col_idx]
                            if pd.notna(raw_amount):
                                amount = str(raw_amount)
                                break
                    
                    # If no amount in value columns, try other columns
                    if not amount:
                        for col_idx in range(len(df.columns)):
                            if col_idx not in value_column_indices and col_idx != category_column_idx and len(row) > col_idx:
                                val = row.iloc[col_idx]
                                if pd.notna(val):
                                    val_str = str(val)
                                    # Check if this looks like a monetary value
                                    if any(char.isdigit() for char in val_str):
                                        amount = val_str
                                        break
                    
                    # Only include rows that have meaningful data
                    if category.strip() and not category.startswith('Unnamed'):
                        # Clean up category name
                        category = category.strip()
                        # Format amount properly
                        if amount and amount != "nan":
                            # Clean the amount string
                            cleaned_amount = amount.replace('$', '').replace(',', '').strip()
                            text_parts.append(f"  {category}: {cleaned_amount}")
                            previous_category = category
                        else:
                            # This might be a header or section marker
                            text_parts.append(f"  SECTION: {category}")
                            previous_category = category
                    elif amount and amount != "nan" and previous_category:
                        # Handle case where amount is in a row without a category
                        # This might be a continuation of the previous category
                        cleaned_amount = amount.replace('$', '').replace(',', '').strip()
                        text_parts.append(f"  {previous_category}: {cleaned_amount}")
            else:
                # Standard table format with clear column headers
                text_parts.append("[TABLE_FORMAT]")
                text_parts.append("COLUMN HEADERS: " + " | ".join(str(col) for col in df.columns))
                text_parts.append("")
                text_parts.append("DATA ROWS:")
                # Format as a clean table
                table_text = df.to_string(index=False, na_rep='[EMPTY]', max_colwidth=30)
                # Add indentation for clarity
                for line in table_text.split('\n'):
                    text_parts.append(f"  {line}")
        else:
            text_parts.append("[EMPTY_SHEET]")
        
        # Add sheet end marker
        text_parts.append("")
        text_parts.append("[SHEET_END]")
        text_parts.append("")
    
    # Add document end marker
    text_parts.append("[DOCUMENT_END]")
    
    result = "\n".join(text_parts)
    return result if result.strip() else f"[Excel content from {file_name}]"

def create_test_excel_file():
    """Create a test Excel file that mimics the structure from the logs"""
    # Based on the logs, it seems like we have a financial statement with specific structure
    # Let's make sure the first column has financial keywords
    data = {
        'Category': [
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

def test_excel_extraction():
    """Test the Excel extraction fix"""
    print("Creating test Excel file...")
    excel_file_path = create_test_excel_file()
    
    try:
        # Read the file content
        with open(excel_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Test Excel extraction
        print("\nTesting Excel extraction...")
        extracted_text = extract_text_from_excel_fixed(file_content, "financial_statement_september_2025_actual.xlsx")
        
        print("Extracted text length:", len(extracted_text))
        print("\nExtracted text:")
        print("=" * 60)
        print(extracted_text)
        print("=" * 60)
        
        # Analyze the structure
        print("\nANALYSIS:")
        has_financial_format = '[FINANCIAL_STATEMENT_FORMAT]' in extracted_text
        has_net_operating_income = 'Net Operating Income' in extracted_text
        has_actual_values = '30000.0' in extracted_text
        has_category_value_pairs = ':' in extracted_text and 'Rental Income' in extracted_text
        
        print(f"  Extracted text contains '[FINANCIAL_STATEMENT_FORMAT]': {'✅' if has_financial_format else '❌'}")
        print(f"  Extracted text contains 'Net Operating Income': {'✅' if has_net_operating_income else '❌'}")
        print(f"  Extracted text contains actual values (e.g., '30000.0'): {'✅' if has_actual_values else '❌'}")
        print(f"  Extracted text contains category:value pairs: {'✅' if has_category_value_pairs else '❌'}")
        
        # Success criteria
        success = has_financial_format and has_net_operating_income and has_actual_values and has_category_value_pairs
        print(f"\n{'SUCCESS' if success else 'FAILURE'}: Excel extraction {'works correctly' if success else 'still has issues'}")
        
        # Count how many financial values we extracted
        if success:
            value_lines = [line for line in extracted_text.split('\n') if ':' in line and not line.startswith('SECTION:')]
            print(f"\nExtracted {len(value_lines)} financial value lines:")
            for line in value_lines[:10]:  # Show first 10
                print(f"  {line}")
            if len(value_lines) > 10:
                print(f"  ... and {len(value_lines) - 10} more")
        
        return success
        
    finally:
        # Clean up
        os.unlink(excel_file_path)

if __name__ == "__main__":
    test_excel_extraction()