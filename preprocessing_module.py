"""
Preprocessing Module for Real Estate NOI Analyzer
Extracts text and data from various file formats (PDF, Excel, CSV, TXT)
"""

import os
import io
import magic
import chardet
import pandas as pd
import pdfplumber
import time
import re
from typing import Dict, Any, List, Tuple, Optional
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('preprocessing_module')

class FilePreprocessor:
    """Main class for preprocessing different file types"""
    
    def __init__(self):
        """Initialize the preprocessor"""
        self.supported_extensions = {
            'pdf': self._process_pdf,
            'xlsx': self._process_excel,
            'xls': self._process_excel,
            'csv': self._process_csv,
            'txt': self._process_txt
        }
    
    def preprocess(self, file_path: str, content_type: Optional[str] = None, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to preprocess a file
        
        Args:
            file_path: Path to the file to preprocess
            content_type: Content type of the file (optional)
            filename: Original filename (optional)
            
        Returns:
            Dict containing extracted text/data and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file extension from filename if provided, otherwise from file_path
        if filename and '.' in filename:
            _, ext = os.path.splitext(filename)
        else:
            _, ext = os.path.splitext(file_path)
        
        ext = ext.lower().lstrip('.')
        
        # Determine file type from content_type if provided
        detected_type = None
        if content_type:
            # Map content types to extensions
            content_type_map = {
                'application/pdf': 'pdf',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
                'application/vnd.ms-excel': 'xls',
                'text/csv': 'csv',
                'text/plain': 'txt'
            }
            
            # Check if content_type is in our map
            for ct, extension in content_type_map.items():
                if ct in content_type:
                    detected_type = extension
                    break
        
        # Use detected type if available, otherwise use extension
        if detected_type:
            ext = detected_type
            logger.info(f"Using file type from content_type: {ext}")
        
        # Check if file type is supported
        if ext not in self.supported_extensions:
            # Fallback to Excel processor for spreadsheet content types
            if content_type and ('spreadsheet' in content_type or 'excel' in content_type.lower()):
                logger.info(f"Unsupported extension {ext} but content type {content_type} indicates Excel, using Excel processor")
                processor = self._process_excel
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        else:
            # Process the file based on its extension
            processor = self.supported_extensions[ext]
        
        # Get file type using magic
        file_type = magic.from_file(file_path, mime=True)
        file_size = os.path.getsize(file_path)
        
        logger.info(f"Processing file: {file_path} ({file_type}, {file_size} bytes)")
        
        # Extract content
        extracted_content = processor(file_path)
        
        # Add enhanced metadata
        result = {
            'metadata': {
                'filename': filename or os.path.basename(file_path),
                'file_type': file_type,
                'file_size': file_size,
                'extension': ext,
                'content_type': content_type,
                'processing_timestamp': time.time(),
                'processing_method': 'enhanced_preprocessing'
            },
            'content': extracted_content
        }
        
        return result
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF files using pdfplumber with enhanced structure detection
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing extracted text and tables
        """
        logger.info(f"Extracting content from PDF: {file_path}")
        result: Dict[str, Any] = {
            'text': [],
            'tables': [],
            'structure_indicators': []
        }
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        result['text'].append({
                            'page': i + 1,
                            'content': self._clean_text(page_text)
                        })
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for j, table in enumerate(tables):
                        if table:
                            # Convert table to DataFrame for easier processing
                            df = pd.DataFrame(table)
                            
                            # Clean up DataFrame - remove empty rows and columns
                            df = df.dropna(how='all').dropna(axis=1, how='all')
                            
                            # Use first row as header if it looks like a header
                            if len(df) > 0 and self._is_header_row(df.iloc[0]):
                                df.columns = df.iloc[0]
                                df = df.iloc[1:]
                            
                            # Remove unnamed columns
                            columns_to_drop = [col for col in df.columns if str(col).startswith('Unnamed:')]
                            if columns_to_drop:
                                df = df.drop(columns=columns_to_drop)
                            
                            # Only add non-empty tables
                            if not df.empty:
                                result['tables'].append({
                                    'page': i + 1,
                                    'table_index': j,
                                    'data': df.to_dict(orient='records')
                                })
                
                # Add structure indicators
                result['structure_indicators'] = self._detect_pdf_structure_indicators(pdf)
        
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
        
        # Combine all text for easier processing
        all_text = "\n\n".join([page['content'] for page in result['text']])
        result['combined_text'] = all_text
        
        return result
    
    def _detect_pdf_structure_indicators(self, pdf) -> List[str]:
        """
        Detect structure indicators in PDF files.
        
        Args:
            pdf: pdfplumber PDF object
            
        Returns:
            List of structure indicators
        """
        indicators = []
        
        try:
            total_pages = len(pdf.pages)
            indicators.append(f"pages:{total_pages}")
            
            # Check first few pages for structure
            for i, page in enumerate(pdf.pages[:3]):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    # Check for financial keywords
                    text_lower = page_text.lower()
                    financial_keywords = [
                        'rent', 'income', 'revenue', 'expense', 'tax', 'insurance', 
                        'maintenance', 'utilities', 'management', 'parking', 'laundry', 
                        'fee', 'noi', 'egi', 'operating', 'total'
                    ]
                    
                    for keyword in financial_keywords:
                        if keyword in text_lower:
                            indicators.append(f"page_{i}_financial_keyword:{keyword}")
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    indicators.append(f"page_{i}_tables:{len(tables)}")
        
        except Exception as e:
            logger.warning(f"Error detecting PDF structure indicators: {str(e)}")
        
        return indicators
    
    def _process_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Process Excel files using pandas with enhanced structure detection
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dict containing extracted sheets and data
        """
        logger.info(f"Extracting content from Excel: {file_path}")
        result: Dict[str, Any] = {
            'sheets': [],
            'text_representation': [],
            'structure_indicators': []
        }
        
        try:
            # Get list of sheet names
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            
            for sheet_name in sheet_names:
                # Read the sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Remove unnamed columns that are typically artifacts of merged cells
                columns_to_drop = [col for col in df.columns if str(col).startswith('Unnamed:')]
                if columns_to_drop:
                    df = df.drop(columns=columns_to_drop)
                
                # Store sheet data
                result['sheets'].append({
                    'name': sheet_name,
                    'data': df.to_dict(orient='records')
                })
                
                # Create text representation of the sheet with better formatting
                text_rep = f"Sheet: {sheet_name}\n"
                text_rep += df.to_string(index=False, na_rep='')
                result['text_representation'].append(text_rep)
                
                # Add structure indicators for this sheet
                sheet_indicators = self._detect_excel_sheet_structure(df, sheet_name)
                result['structure_indicators'].extend(sheet_indicators)
            
            # Combine all text representations
            result['combined_text'] = "\n\n".join(result['text_representation'])
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            raise
        
        return result
    
    def _detect_excel_sheet_structure(self, df, sheet_name: str) -> List[str]:
        """
        Detect structure indicators in Excel sheets.
        
        Args:
            df: DataFrame representing the sheet
            sheet_name: Name of the sheet
            
        Returns:
            List of structure indicators
        """
        indicators = [f"sheet:{sheet_name}"]
        
        try:
            if len(df.columns) > 0:
                column_names = [str(col).lower() for col in df.columns]
                first_column_data = df.iloc[:, 0].astype(str).str.lower() if len(df.columns) > 0 else pd.Series([])
                
                financial_keywords = [
                    'rent', 'income', 'revenue', 'expense', 'tax', 'insurance', 
                    'maintenance', 'utilities', 'management', 'parking', 'laundry', 
                    'fee', 'noi', 'egi', 'operating', 'total'
                ]
                
                # Check column names
                for keyword in financial_keywords:
                    if any(keyword in col for col in column_names):
                        indicators.append(f"sheet_{sheet_name}_financial_keyword_in_columns:{keyword}")
                        break
                
                # Check first column data
                for keyword in financial_keywords:
                    if first_column_data.str.contains(keyword, na=False).any():
                        indicators.append(f"sheet_{sheet_name}_financial_keyword_in_data:{keyword}")
                        break
                
                # Check for numeric columns
                numeric_columns = 0
                for col in df.columns:
                    numeric_count = 0
                    total_count = 0
                    for val in df[col]:
                        if pd.notna(val):
                            total_count += 1
                            try:
                                float(str(val).replace('$', '').replace(',', '').replace('(', '-').replace(')', ''))
                                numeric_count += 1
                            except ValueError:
                                pass
                    if total_count > 0 and numeric_count / total_count > 0.5:
                        numeric_columns += 1
                
                if numeric_columns > 0:
                    indicators.append(f"sheet_{sheet_name}_numeric_columns:{numeric_columns}")
        
        except Exception as e:
            logger.warning(f"Error detecting Excel sheet structure: {str(e)}")
        
        return indicators
    
    def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Process CSV files using pandas
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dict containing extracted data
        """
        logger.info(f"Extracting content from CSV: {file_path}")
        result: Dict[str, Any] = {}
        
        try:
            # Detect encoding
            encoding = self._detect_encoding(file_path)
            
            # Read CSV file
            df = pd.read_csv(file_path, encoding=encoding)
            
            # Store data
            result['data'] = df.to_dict(orient='records')
            
            # Create text representation with better formatting
            result['text_representation'] = df.to_string(index=False, na_rep='')
            result['combined_text'] = result['text_representation']
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise
        
        return result
    
    def _process_txt(self, file_path: str) -> Dict[str, Any]:
        """
        Process TXT files
        
        Args:
            file_path: Path to the TXT file
            
        Returns:
            Dict containing extracted text
        """
        logger.info(f"Extracting content from TXT: {file_path}")
        result: Dict[str, Any] = {}
        
        try:
            # Detect encoding
            encoding = self._detect_encoding(file_path)
            
            # Read text file
            with open(file_path, 'r', encoding=encoding) as f:
                text = f.read()
            
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Store data
            result['text'] = cleaned_text
            result['combined_text'] = cleaned_text
            
        except Exception as e:
            logger.error(f"Error processing TXT file: {str(e)}")
            raise
        
        return result
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10000 bytes
        
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        
        return encoding
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Replace multiple spaces with a single space
        text = ' '.join(text.split())
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive line breaks
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        # Standardize number formats (e.g., 1,000.00 → 1000.00)
        # This is a simplified approach; a more robust solution would use regex
        
        return text

    def validate_financial_content(self, content_data: Dict[str, Any]) -> bool:
        """
        Validate that extracted content contains actual financial data
        
        Args:
            content_data: The content extracted from the file
            
        Returns:
            True if the content contains financial data, False otherwise
        """
        try:
            # Count meaningful numerical values (non-zero, non-trivial)
            meaningful_numerical_count = 0
            total_entries = 0
            financial_indicators = 0
            
            # For CSV/Excel files with 'data' key
            if 'data' in content_data and isinstance(content_data['data'], list):
                for row in content_data['data']:
                    if isinstance(row, dict):
                        for key, value in row.items():
                            total_entries += 1
                            # Check for financial keywords in column names
                            if isinstance(key, str) and self._is_financial_term(key):
                                financial_indicators += 1
                            
                            if isinstance(value, (int, float)) and value != 0 and abs(value) >= 1:
                                meaningful_numerical_count += 1
                            elif isinstance(value, str) and value.strip():
                                # Check if string contains meaningful numerical data
                                cleaned_value = str(value).strip().replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
                                if cleaned_value and cleaned_value not in ['-', '']:
                                    try:
                                        num_value = float(cleaned_value)
                                        if num_value != 0 and abs(num_value) >= 1:
                                            meaningful_numerical_count += 1
                                    except ValueError:
                                        # Check for financial keywords in values
                                        if self._is_financial_term(value):
                                            financial_indicators += 1
            
            # For Excel files with 'sheets' key
            elif 'sheets' in content_data and isinstance(content_data['sheets'], list):
                for sheet in content_data['sheets']:
                    if isinstance(sheet, dict) and 'data' in sheet:
                        sheet_data = sheet['data']
                        if isinstance(sheet_data, list):
                            for row in sheet_data:
                                if isinstance(row, dict):
                                    for key, value in row.items():
                                        total_entries += 1
                                        # Check for financial keywords in column names
                                        if isinstance(key, str) and self._is_financial_term(key):
                                            financial_indicators += 1
                                            
                                        if isinstance(value, (int, float)) and value != 0 and abs(value) >= 1:
                                            meaningful_numerical_count += 1
                                        elif isinstance(value, str) and value.strip():
                                            # Check if string contains meaningful numerical data
                                            cleaned_value = str(value).strip().replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
                                            if cleaned_value and cleaned_value not in ['-', '']:
                                                try:
                                                    num_value = float(cleaned_value)
                                                    if num_value != 0 and abs(num_value) >= 1:
                                                        meaningful_numerical_count += 1
                                                except ValueError:
                                                    # Check for financial keywords in values
                                                    if self._is_financial_term(value):
                                                        financial_indicators += 1
            
            # For text content
            elif 'combined_text' in content_data:
                text = content_data['combined_text']
                # Find meaningful numerical patterns (currency amounts, significant numbers)
                meaningful_patterns = re.findall(r'\$[0-9,]+\.?\d*|[0-9,]+\.?\d*\s*(?:dollars|usd)', text, re.IGNORECASE)
                # Also look for plain numbers that are significant (> 100)
                plain_numbers = re.findall(r'\b\d{3,}\.?\d*\b', text)
                
                # Filter plain numbers to only include significant values
                significant_plain_numbers = [n for n in plain_numbers if float(n) >= 100]
                
                meaningful_numerical_count = len(meaningful_patterns) + len(significant_plain_numbers)
                total_entries = len(text.split())
                
                # Check for financial terms
                financial_terms = ['income', 'expense', 'revenue', 'tax', 'insurance', 'rent', 'fee', 'noi', 
                                 'operating', 'property', 'maintenance', 'utilities', 'management']
                text_lower = text.lower()
                for term in financial_terms:
                    if term in text_lower:
                        financial_indicators += 1
            
            # For PDF content with text
            elif 'text' in content_data and isinstance(content_data['text'], list):
                total_text = ""
                for page in content_data['text']:
                    if isinstance(page, dict) and 'content' in page:
                        total_text += page['content']
                
                # Apply same logic as text content
                meaningful_patterns = re.findall(r'\$[0-9,]+\.?\d*|[0-9,]+\.?\d*\s*(?:dollars|usd)', total_text, re.IGNORECASE)
                plain_numbers = re.findall(r'\b\d{3,}\.?\d*\b', total_text)
                significant_plain_numbers = [n for n in plain_numbers if float(n) >= 100]
                
                meaningful_numerical_count = len(meaningful_patterns) + len(significant_plain_numbers)
                total_entries = len(total_text.split())
                
                # Check for financial terms
                financial_terms = ['income', 'expense', 'revenue', 'tax', 'insurance', 'rent', 'fee', 'noi', 
                                 'operating', 'property', 'maintenance', 'utilities', 'management']
                text_lower = total_text.lower()
                for term in financial_terms:
                    if term in text_lower:
                        financial_indicators += 1
            
            # Determine if content has sufficient financial data
            logger.info(f"Financial content validation: {meaningful_numerical_count} meaningful numerical values, {financial_indicators} financial indicators out of {total_entries} entries")
            
            # For a document to be considered as having financial data, it should have:
            # 1. At least 3 meaningful numerical values, OR
            # 2. At least 5 financial indicators, OR
            # 3. At least 1% of entries being meaningful numerical values (for larger documents)
            has_sufficient_data = (meaningful_numerical_count >= 3 or 
                                 financial_indicators >= 5 or
                                 (total_entries > 0 and meaningful_numerical_count / total_entries >= 0.01))
            
            return has_sufficient_data
                
        except Exception as e:
            logger.warning(f"Error validating financial content: {str(e)}")
            # If validation fails, assume content might have data
            return True
    
    def _is_financial_term(self, term: str) -> bool:
        """
        Check if a term is a financial term.
        
        Args:
            term: Term to check
            
        Returns:
            True if the term is a financial term, False otherwise
        """
        financial_terms = [
            'income', 'expense', 'revenue', 'tax', 'insurance', 'rent', 'fee', 'noi', 
            'operating', 'property', 'maintenance', 'utilities', 'management', 'egi',
            'concessions', 'vacancy', 'debt', 'parking', 'laundry', 'total'
        ]
        
        term_lower = term.lower()
        return any(fin_term in term_lower for fin_term in financial_terms)

    def _is_header_row(self, row: pd.Series) -> bool:
        """
        Check if a row looks like a header row
        
        Args:
            row: DataFrame row to check
            
        Returns:
            True if the row looks like a header, False otherwise
        """
        # Convert all values to strings
        values = [str(v).lower() for v in row]
        
        # Check if any values contain typical header keywords
        header_keywords = ['total', 'income', 'expense', 'revenue', 'cost', 
                          'date', 'period', 'month', 'year', 'budget', 'actual']
        
        for value in values:
            for keyword in header_keywords:
                if keyword in value:
                    return True
        
        return False


def preprocess_file(file_path: str, content_type: Optional[str] = None, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to preprocess a file
    
    Args:
        file_path: Path to the file to preprocess
        content_type: Content type of the file (optional)
        filename: Original filename (optional)
        
    Returns:
        Dict containing extracted text/data and metadata
    """
    preprocessor = FilePreprocessor()
    return preprocessor.preprocess(file_path, content_type, filename)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python preprocessing_module.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        result = preprocess_file(file_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
