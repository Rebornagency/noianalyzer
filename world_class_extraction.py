"""
World-Class Data Extraction System for NOI Analyzer
This module provides enhanced data extraction capabilities with confidence scoring,
audit trails, and robust error handling for all document types.
"""

import os
import io
import json
import logging
import time
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import pdfplumber
from openai import OpenAI

from config import get_openai_api_key
from utils.openai_utils import chat_completion
from utils.error_handler import setup_logger

# Setup logger
logger = setup_logger(__name__)

class DocumentType(Enum):
    """Enumeration of supported document types"""
    ACTUAL_INCOME_STATEMENT = "Actual Income Statement"
    BUDGET = "Budget"
    PRIOR_YEAR_ACTUAL = "Prior Year Actual"
    UNKNOWN = "Unknown"

class ExtractionConfidence(Enum):
    """Enumeration of confidence levels for extractions"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"

@dataclass
class ExtractionResult:
    """Data class for extraction results with confidence and audit information"""
    data: Dict[str, Any]
    confidence: ExtractionConfidence
    confidence_scores: Dict[str, float]
    audit_trail: List[str]
    processing_time: float
    document_type: DocumentType
    extraction_method: str

class WorldClassExtractor:
    """
    World-class data extraction system with enhanced preprocessing,
    confidence scoring, and audit trails.
    """
    
    def __init__(self):
        """Initialize the extractor with OpenAI client"""
        self.openai_api_key = get_openai_api_key()
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Define the standard financial metrics structure
        self.financial_metrics = {
            # Revenue items
            "gross_potential_rent": 0.0,
            "vacancy_loss": 0.0,
            "concessions": 0.0,
            "bad_debt": 0.0,
            "other_income": 0.0,
            "effective_gross_income": 0.0,
            
            # Expense items
            "operating_expenses": 0.0,
            "property_taxes": 0.0,
            "insurance": 0.0,
            "repairs_maintenance": 0.0,
            "utilities": 0.0,
            "management_fees": 0.0,
            "parking_income": 0.0,
            "laundry_income": 0.0,
            "late_fees": 0.0,
            "pet_fees": 0.0,
            "application_fees": 0.0,
            "storage_fees": 0.0,
            "amenity_fees": 0.0,
            "utility_reimbursements": 0.0,
            "cleaning_fees": 0.0,
            "cancellation_fees": 0.0,
            "miscellaneous_income": 0.0,
            
            # Calculated totals
            "net_operating_income": 0.0,
            
            # Metadata fields (as strings)
            "file_name": "",
            "document_type_hint": "",
            "extraction_status": "",
            "requires_manual_entry": False
        }
    
    def extract_data(self, file_content: bytes, file_name: str, 
                    document_type_hint: Optional[str] = None) -> ExtractionResult:
        """
        Extract financial data from a document with confidence scoring and audit trail.
        
        Args:
            file_content: Document content as bytes
            file_name: Name of the file
            document_type_hint: Optional hint about document type
            
        Returns:
            ExtractionResult with data, confidence, and audit information
        """
        start_time = time.time()
        audit_trail = [f"Starting extraction for {file_name}"]
        
        try:
            # 1. Preprocess the document
            audit_trail.append("Preprocessing document")
            preprocessed_content = self._preprocess_document(file_content, file_name)
            audit_trail.append(f"Preprocessing completed. Content length: {len(preprocessed_content)}")
            
            # 2. Determine document type
            audit_trail.append("Determining document type")
            document_type = self._determine_document_type(file_name, document_type_hint, preprocessed_content)
            audit_trail.append(f"Document type determined: {document_type.value}")
            
            # 3. Extract text with enhanced structure
            audit_trail.append("Extracting structured text")
            structured_text = self._extract_structured_text(file_content, file_name, preprocessed_content)
            audit_trail.append(f"Structured text extracted. Length: {len(structured_text)}")
            
            # 4. Extract financial data using GPT-4 with enhanced prompt
            audit_trail.append("Extracting financial data with GPT-4")
            extracted_data, confidence_scores = self._extract_with_gpt(structured_text, document_type)
            audit_trail.append("GPT-4 extraction completed")
            
            # 5. Validate and enrich the extracted data
            audit_trail.append("Validating and enriching extracted data")
            validated_data = self._validate_and_enrich_data(extracted_data, confidence_scores)
            audit_trail.append("Data validation and enrichment completed")
            
            # 6. Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(confidence_scores)
            audit_trail.append(f"Overall confidence calculated: {overall_confidence.value}")
            
            processing_time = time.time() - start_time
            
            return ExtractionResult(
                data=validated_data,
                confidence=overall_confidence,
                confidence_scores=confidence_scores,
                audit_trail=audit_trail,
                processing_time=processing_time,
                document_type=document_type,
                extraction_method="gpt-4-enhanced"
            )
            
        except Exception as e:
            audit_trail.append(f"Error during extraction: {str(e)}")
            processing_time = time.time() - start_time
            
            # Create fallback result
            fallback_data = self._create_fallback_data(file_name, document_type_hint)
            
            return ExtractionResult(
                data=fallback_data,
                confidence=ExtractionConfidence.UNCERTAIN,
                confidence_scores={},
                audit_trail=audit_trail,
                processing_time=processing_time,
                document_type=DocumentType.UNKNOWN,
                extraction_method="fallback"
            )
    
    def _preprocess_document(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """
        Preprocess document to determine type and basic structure.
        
        Args:
            file_content: Document content as bytes
            file_name: Name of the file
            
        Returns:
            Dictionary with preprocessing information
        """
        _, ext = os.path.splitext(file_name)
        ext = ext.lower().lstrip('.')
        
        preprocessing_info = {
            "file_name": file_name,
            "file_extension": ext,
            "content_length": len(file_content),
            "detected_type": None,
            "structure_indicators": []
        }
        
        # Detect document type based on content
        if ext in ['xlsx', 'xls']:
            preprocessing_info["detected_type"] = "excel"
            preprocessing_info["structure_indicators"] = self._detect_excel_structure(file_content)
        elif ext == 'pdf':
            preprocessing_info["detected_type"] = "pdf"
            preprocessing_info["structure_indicators"] = self._detect_pdf_structure(file_content)
        elif ext == 'csv':
            preprocessing_info["detected_type"] = "csv"
        elif ext == 'txt':
            preprocessing_info["detected_type"] = "text"
            
        return preprocessing_info
    
    def _detect_excel_structure(self, file_content: bytes) -> List[str]:
        """
        Detect structure indicators in Excel files.
        
        Args:
            file_content: Excel file content as bytes
            
        Returns:
            List of structure indicators
        """
        indicators = []
        try:
            excel_file = io.BytesIO(file_content)
            xl = pd.ExcelFile(excel_file)
            
            for sheet_name in xl.sheet_names:
                excel_file.seek(0)
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Check for financial keywords in column names and first column
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
                            indicators.append(f"financial_keyword_in_columns:{keyword}")
                            break
                    
                    # Check first column data
                    for keyword in financial_keywords:
                        if first_column_data.str.contains(keyword, na=False).any():
                            indicators.append(f"financial_keyword_in_data:{keyword}")
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
                        indicators.append(f"numeric_columns:{numeric_columns}")
        
        except Exception as e:
            logger.warning(f"Error detecting Excel structure: {str(e)}")
        
        return indicators
    
    def _detect_pdf_structure(self, file_content: bytes) -> List[str]:
        """
        Detect structure indicators in PDF files.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            List of structure indicators
        """
        indicators = []
        try:
            pdf_file = io.BytesIO(file_content)
            with pdfplumber.open(pdf_file) as pdf:
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
            logger.warning(f"Error detecting PDF structure: {str(e)}")
        
        return indicators
    
    def _determine_document_type(self, file_name: str, document_type_hint: Optional[str], 
                                preprocessing_info: Dict[str, Any]) -> DocumentType:
        """
        Determine document type based on file name and content.
        
        Args:
            file_name: Name of the file
            document_type_hint: Optional hint about document type
            preprocessing_info: Preprocessing information
            
        Returns:
            DocumentType enum value
        """
        file_name_lower = file_name.lower()
        
        # First check document type hint
        if document_type_hint:
            document_type_hint_lower = document_type_hint.lower()
            if "budget" in document_type_hint_lower:
                return DocumentType.BUDGET
            elif "prior" in document_type_hint_lower:
                if "year" in document_type_hint_lower:
                    return DocumentType.PRIOR_YEAR_ACTUAL
                else:
                    return DocumentType.ACTUAL_INCOME_STATEMENT  # Prior month
            elif "actual" in document_type_hint_lower:
                return DocumentType.ACTUAL_INCOME_STATEMENT
        
        # Check file name
        if "budget" in file_name_lower:
            return DocumentType.BUDGET
        elif "prior" in file_name_lower:
            if "year" in file_name_lower:
                return DocumentType.PRIOR_YEAR_ACTUAL
            else:
                return DocumentType.ACTUAL_INCOME_STATEMENT  # Prior month
        elif "actual" in file_name_lower or "current" in file_name_lower:
            return DocumentType.ACTUAL_INCOME_STATEMENT
        
        # Check preprocessing indicators
        structure_indicators = preprocessing_info.get("structure_indicators", [])
        for indicator in structure_indicators:
            if "financial_keyword" in indicator:
                return DocumentType.ACTUAL_INCOME_STATEMENT
        
        return DocumentType.UNKNOWN
    
    def _extract_structured_text(self, file_content: bytes, file_name: str, 
                                preprocessing_info: Dict[str, Any]) -> str:
        """
        Extract structured text from document with clear formatting for AI parsing.
        
        Args:
            file_content: Document content as bytes
            file_name: Name of the file
            preprocessing_info: Preprocessing information
            
        Returns:
            Structured text representation of the document
        """
        _, ext = os.path.splitext(file_name)
        ext = ext.lower().lstrip('.')
        
        if ext in ['xlsx', 'xls']:
            return self._extract_excel_text(file_content, file_name)
        elif ext == 'pdf':
            return self._extract_pdf_text(file_content, file_name)
        elif ext == 'csv':
            return self._extract_csv_text(file_content, file_name)
        elif ext == 'txt':
            return self._extract_txt_text(file_content, file_name)
        else:
            # Fallback to basic text extraction
            try:
                return file_content.decode('utf-8', errors='ignore')
            except Exception:
                return f"[Content from {file_name}]"
    
    def _extract_excel_text(self, file_content: bytes, file_name: str) -> str:
        """
        Extract structured text from Excel files.
        
        Args:
            file_content: Excel file content as bytes
            file_name: Name of the file
            
        Returns:
            Structured text representation of the Excel file
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
                
                # Remove unnamed columns
                columns_to_drop = [col for col in df.columns if str(col).startswith('Unnamed:')]
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
                    
                    if has_financial_terms and len(df.columns) >= 2:
                        # Format as financial statement
                        text_parts.append("[FINANCIAL_STATEMENT_FORMAT]")
                        text_parts.append("LINE ITEMS:")
                        text_parts.append("")
                        
                        # Extract data with value identification
                        category_column_idx = 0
                        previous_category = ""
                        
                        for idx, row in df.iterrows():
                            category = str(row.iloc[category_column_idx]) if len(row) > category_column_idx and pd.notna(row.iloc[category_column_idx]) else ""
                            
                            # Find the best value from other columns
                            amount = ""
                            for col_idx in range(1, len(df.columns)):
                                if len(row) > col_idx:
                                    raw_amount = row.iloc[col_idx]
                                    if pd.notna(raw_amount):
                                        amount = str(raw_amount)
                                        break
                            
                            if category.strip() and not category.startswith('Unnamed'):
                                category = category.strip()
                                if amount and amount != "nan":
                                    cleaned_amount = amount.replace('$', '').replace(',', '').strip()
                                    text_parts.append(f"  {category}: {cleaned_amount}")
                                    previous_category = category
                                else:
                                    text_parts.append(f"  SECTION: {category}")
                                    previous_category = category
                            elif amount and amount != "nan" and previous_category:
                                cleaned_amount = amount.replace('$', '').replace(',', '').strip()
                                text_parts.append(f"  {previous_category}: {cleaned_amount}")
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
            logger.warning(f"Error extracting Excel text: {str(e)}")
            text_parts = [f"[Excel content from {file_name}]"]
        
        return "\n".join(text_parts)
    
    def _extract_pdf_text(self, file_content: bytes, file_name: str) -> str:
        """
        Extract structured text from PDF files.
        
        Args:
            file_content: PDF file content as bytes
            file_name: Name of the file
            
        Returns:
            Structured text representation of the PDF file
        """
        text_parts = [f"PDF DOCUMENT: {file_name}", "=" * 60, ""]
        
        try:
            pdf_file = io.BytesIO(file_content)
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    text_parts.append(f"[PAGE_START] {i+1}")
                    text_parts.append("-" * 30)
                    
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        # Clean up text
                        cleaned_lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                        if cleaned_lines:
                            text_parts.append("[TEXT_CONTENT]")
                            text_parts.extend(cleaned_lines)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        text_parts.append("")
                        text_parts.append("[TABLES_FOUND]")
                        for j, table in enumerate(tables):
                            if table:
                                text_parts.append(f"[TABLE_{j+1}]")
                                for row in table:
                                    cleaned_row = [str(cell) if cell is not None else "[EMPTY]" for cell in row]
                                    text_parts.append("  |  ".join(cleaned_row))
                    
                    text_parts.append("")
                    text_parts.append("[PAGE_END]")
                    text_parts.append("")
            
            text_parts.append("[DOCUMENT_END]")
            
        except Exception as e:
            logger.warning(f"Error extracting PDF text: {str(e)}")
            text_parts = [f"[PDF content from {file_name}]"]
        
        return "\n".join(text_parts)
    
    def _extract_csv_text(self, file_content: bytes, file_name: str) -> str:
        """
        Extract structured text from CSV files.
        
        Args:
            file_content: CSV file content as bytes
            file_name: Name of the file
            
        Returns:
            Structured text representation of the CSV file
        """
        text_parts = [f"CSV DOCUMENT: {file_name}", "=" * 60, ""]
        
        try:
            # Try to detect encoding
            import chardet
            encoding_info = chardet.detect(file_content)
            encoding = encoding_info.get('encoding', 'utf-8') or 'utf-8'
            
            try:
                csv_text = file_content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                csv_text = file_content.decode('utf-8', errors='ignore')
            
            # Split into lines
            lines = [line.strip() for line in csv_text.splitlines() if line.strip()]
            if lines:
                text_parts.append("[CSV_CONTENT]")
                text_parts.extend(lines)
            
            text_parts.append("")
            text_parts.append("[DOCUMENT_END]")
            
        except Exception as e:
            logger.warning(f"Error extracting CSV text: {str(e)}")
            text_parts = [f"[CSV content from {file_name}]"]
        
        return "\n".join(text_parts)
    
    def _extract_txt_text(self, file_content: bytes, file_name: str) -> str:
        """
        Extract structured text from TXT files.
        
        Args:
            file_content: TXT file content as bytes
            file_name: Name of the file
            
        Returns:
            Structured text representation of the TXT file
        """
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
            
            # Add structure markers
            text_parts = [f"TEXT DOCUMENT: {file_name}", "=" * 60, ""]
            
            # Add section headers for common financial terms
            section_headers = {
                'REVENUE': '[REVENUE_SECTION]',
                'INCOME': '[INCOME_SECTION]', 
                'EXPENSE': '[EXPENSE_SECTION]',
                'OPERATING': '[OPERATING_SECTION]',
                'PROPERTY': '[PROPERTY_INFORMATION]',
                'TOTAL': '[SUMMARY_SECTION]',
                'FINANCIAL': '[FINANCIAL_STATEMENT]',
                'RESULT': '[FINANCIAL_RESULTS]'
            }
            
            lines = [line.strip() for line in text_content.splitlines() if line.strip()]
            for line in lines:
                text_parts.append(line)
                # Add section markers
                for keyword, header in section_headers.items():
                    if keyword in line.upper() and header not in line:
                        text_parts.append("")
                        text_parts.append(header)
                        text_parts.append("-" * 25)
            
            text_parts.append("")
            text_parts.append("[DOCUMENT_END]")
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"Error extracting TXT text: {str(e)}")
            return f"[Text content from {file_name}]"
    
    def _extract_with_gpt(self, document_text: str, document_type: DocumentType) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Extract financial data using GPT-4 with enhanced prompt and confidence scoring.
        
        Args:
            document_text: Structured text representation of the document
            document_type: Type of document
            
        Returns:
            Tuple of extracted data dictionary and confidence scores
        """
        # Truncate document text if too long
        max_length = 3000
        if len(document_text) > max_length:
            start_length = int(max_length * 0.7)
            end_length = max_length - start_length - 50
            document_text = document_text[:start_length] + "... [truncated] ..." + document_text[-end_length:]
        
        # Create enhanced prompt
        prompt = self._create_enhanced_prompt(document_text, document_type)
        
        # Prepare messages for chat completion
        messages = [
            {"role": "system", "content": "You are a world-class real estate financial analyst with expertise in extracting precise financial data from property income statements. You focus on accuracy, mathematical consistency, and providing confidence scores for each extracted value."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Call OpenAI API
            response_content = chat_completion(
                messages=messages,
                model="gpt-4",  # Use GPT-4 for better accuracy
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse the JSON response
            try:
                # Extract JSON from response if it's wrapped in other text
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_content[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Extract data and confidence scores
                    extracted_data = result.get("financial_data", {})
                    confidence_scores = result.get("confidence_scores", {})
                    
                    return extracted_data, confidence_scores
                else:
                    raise json.JSONDecodeError("No JSON found in response", response_content, 0)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
                logger.error(f"Response content: {response_content}")
                # Return empty result with low confidence
                return {}, {}
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            # Return empty result with low confidence
            return {}, {}
    
    def _create_enhanced_prompt(self, document_text: str, document_type: DocumentType) -> str:
        """
        Create an enhanced prompt for GPT-4 with confidence scoring instructions.
        
        Args:
            document_text: Structured text representation of the document
            document_type: Type of document
            
        Returns:
            Enhanced prompt string
        """
        # Document type specific instructions
        doc_type_instructions = ""
        if document_type == DocumentType.BUDGET:
            doc_type_instructions = """
Document Type Specific Instructions:
This is a BUDGET document. Focus on projected/forecasted values rather than actual results.
Look for terms like "Budget", "Forecast", "Projected", "Estimated" in the document.
"""
        elif document_type == DocumentType.PRIOR_YEAR_ACTUAL:
            doc_type_instructions = """
Document Type Specific Instructions:
This is a PRIOR YEAR ACTUAL document. Look for historical actual results from a previous year.
Focus on data from the prior year period.
"""
        elif document_type == DocumentType.ACTUAL_INCOME_STATEMENT:
            doc_type_instructions = """
Document Type Specific Instructions:
This is a CURRENT PERIOD ACTUAL document. Look for the most recent actual results.
Focus on current period data.
"""
        
        prompt = f"""
You are a world-class real estate financial analyst with expertise in extracting precise financial data from property income statements. 

DOCUMENT STRUCTURE GUIDE:
The document has been pre-processed with clear structural markers to help you parse it:
- [SHEET_START]/[SHEET_END]: Excel sheet boundaries
- [PAGE_START]/[PAGE_END]: PDF page boundaries  
- [FINANCIAL_STATEMENT_FORMAT]: Financial data in category: value format
- [TABLE_FORMAT]: Tabular data with headers
- [TEXT_CONTENT]: Plain text content
- SECTION markers: [REVENUE_SECTION], [EXPENSE_SECTION], etc.

Document Information:
- Document Type: {document_type.value}
{doc_type_instructions}

Document Content:
{document_text}

INSTRUCTIONS:
Extract all financial metrics from the document and return them in the exact JSON structure shown below. 

CRITICAL EXTRACTION STRATEGY:
1. FIRST, identify the document structure using the markers provided
2. LOOK for financial line items in [FINANCIAL_STATEMENT_FORMAT] sections first
3. FOR tabular data, examine column headers and row values systematically
4. IDENTIFY financial concepts by their meaning, not exact wording
5. HANDLE different formats: "Gross Potential Rent", "Potential Rent", "Scheduled Rent" are all GPR
6. RECOGNIZE negative values in formats: (1,234.50), -$1,234.50, -1,234.50
7. CALCULATE derived values when not explicitly provided:
   - Effective Gross Income = Gross Potential Rent - Vacancy Loss - Concessions - Bad Debt + Other Income
   - Net Operating Income = Effective Gross Income - Operating Expenses
8. NEVER leave fields empty - use 0.0 if truly unknown
9. CRITICALLY IMPORTANT: DO NOT return all zero values. If you cannot find specific values, make educated estimates based on context.
10. PROVIDE confidence scores (0.0 to 1.0) for each extracted value based on how certain you are about its accuracy.

REQUIRED JSON STRUCTURE:
{{
  "financial_data": {{
    "gross_potential_rent": 0.0,          // Gross Potential Rent (Total potential rental income)
    "vacancy_loss": 0.0,                  // Vacancy Loss (Lost income due to vacant units)
    "concessions": 0.0,                   // Concessions (Reduced rent given to tenants)
    "bad_debt": 0.0,                      // Bad Debt (Uncollected rent)
    "other_income": 0.0,                  // Other Income (Parking, laundry, etc.)
    "effective_gross_income": 0.0,        // Effective Gross Income (GPR - Vacancy - Concessions - Bad Debt + Other Income)
    "operating_expenses": 0.0,            // Total Operating Expenses (Sum of all operating expenses)
    "property_taxes": 0.0,                // Property Taxes
    "insurance": 0.0,                     // Insurance
    "repairs_maintenance": 0.0,           // Repairs & Maintenance
    "utilities": 0.0,                     // Utilities
    "management_fees": 0.0,               // Management Fees
    "parking_income": 0.0,                // Parking Income
    "laundry_income": 0.0,                // Laundry Income
    "late_fees": 0.0,                     // Late Fees
    "pet_fees": 0.0,                      // Pet Fees
    "application_fees": 0.0,              // Application Fees
    "storage_fees": 0.0,                  // Storage Fees
    "amenity_fees": 0.0,                  // Amenity Fees
    "utility_reimbursements": 0.0,        // Utility Reimbursements
    "cleaning_fees": 0.0,                 // Cleaning Fees
    "cancellation_fees": 0.0,             // Cancellation Fees
    "miscellaneous_income": 0.0,          // Miscellaneous Income
    "net_operating_income": 0.0           // Net Operating Income (EGI - OpEx)
  }},
  "confidence_scores": {{
    "gross_potential_rent": 0.0,          // Confidence in GPR value (0.0 to 1.0)
    "vacancy_loss": 0.0,                  // Confidence in Vacancy Loss value
    "concessions": 0.0,                   // Confidence in Concessions value
    "bad_debt": 0.0,                      // Confidence in Bad Debt value
    "other_income": 0.0,                  // Confidence in Other Income value
    "effective_gross_income": 0.0,        // Confidence in EGI value
    "operating_expenses": 0.0,            // Confidence in OpEx value
    "property_taxes": 0.0,                // Confidence in Property Taxes value
    "insurance": 0.0,                     // Confidence in Insurance value
    "repairs_maintenance": 0.0,           // Confidence in Repairs & Maintenance value
    "utilities": 0.0,                     // Confidence in Utilities value
    "management_fees": 0.0,               // Confidence in Management Fees value
    "parking_income": 0.0,                // Confidence in Parking Income value
    "laundry_income": 0.0,                // Confidence in Laundry Income value
    "late_fees": 0.0,                     // Confidence in Late Fees value
    "pet_fees": 0.0,                      // Confidence in Pet Fees value
    "application_fees": 0.0,              // Confidence in Application Fees value
    "storage_fees": 0.0,                  // Confidence in Storage Fees value
    "amenity_fees": 0.0,                  // Confidence in Amenity Fees value
    "utility_reimbursements": 0.0,        // Confidence in Utility Reimbursements value
    "cleaning_fees": 0.0,                 // Confidence in Cleaning Fees value
    "cancellation_fees": 0.0,             // Confidence in Cancellation Fees value
    "miscellaneous_income": 0.0,          // Confidence in Miscellaneous Income value
    "net_operating_income": 0.0           // Confidence in NOI value
  }}
}}

EXTENSIVE FIELD VARIATIONS TO LOOK FOR:
- Gross Potential Rent: Gross Potential Rent, Potential Rent, Scheduled Rent, Total Revenue, Revenue, Gross Income
- Vacancy Loss: Vacancy, Credit Loss, Vacancy and Credit Loss, Turnover Loss
- Concessions: Tenant Concessions, Leasing Concessions, Move-in Concessions, Free Rent
- Bad Debt: Uncollected Rent, Delinquent Rent, Write-offs, Account Receivable Write-offs
- Other Income: Additional Income, Miscellaneous Income, Parking Fees, Laundry Income
- Effective Gross Income: Effective Gross Income, Net Rental Income, Adjusted Gross Income
- Operating Expenses: Operating Expenses, Total Operating Expenses, Expenses, Operating Costs
- Net Operating Income: Net Operating Income, Net Income, Operating Income, Property Net Income

NEGATIVE VALUE FORMATS:
Convert these formats to negative numbers:
- (1,234.50) → -1234.50
- (1234.50) → -1234.50  
- -$1,234.50 → -1234.50
- -1,234.50 → -1234.50

CALCULATION RULES (Use if not explicitly provided):
- Effective Gross Income = Gross Potential Rent - Vacancy Loss - Concessions - Bad Debt + Other Income
- Net Operating Income = Effective Gross Income - Operating Expenses
- If you find individual expense items, sum them to calculate Operating Expenses
- If you find individual income items, sum them to calculate Gross Potential Rent

RETURN ONLY the JSON object with the extracted values and confidence scores. Do not include any other text, explanations, or formatting.
Make sure all fields are present with numeric values and confidence scores. DO NOT return all zero values - make educated estimates when needed.
"""
        
        return prompt
    
    def _validate_and_enrich_data(self, extracted_data: Dict[str, Any], 
                                 confidence_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate and enrich extracted data with calculations and defaults.
        
        Args:
            extracted_data: Raw extracted data
            confidence_scores: Confidence scores for each field
            
        Returns:
            Validated and enriched data
        """
        # Start with standard financial metrics structure
        validated_data = self.financial_metrics.copy()
        
        # Update with extracted data
        for key, value in extracted_data.items():
            if key in validated_data:
                try:
                    validated_data[key] = float(value)
                except (ValueError, TypeError):
                    validated_data[key] = 0.0
        
        # Perform financial calculations to ensure consistency
        # Calculate Effective Gross Income if not provided or low confidence
        gpr_confidence = confidence_scores.get("gross_potential_rent", 0.0)
        egi_confidence = confidence_scores.get("effective_gross_income", 0.0)
        
        if gpr_confidence > 0.5:  # We have reasonable confidence in GPR
            calculated_egi = (
                validated_data["gross_potential_rent"] - 
                validated_data["vacancy_loss"] - 
                validated_data["concessions"] - 
                validated_data["bad_debt"] + 
                validated_data["other_income"]
            )
            
            # If EGI confidence is low or calculated value is significantly different, use calculated value
            if egi_confidence < 0.5 or abs(calculated_egi - validated_data["effective_gross_income"]) > 1.0:
                validated_data["effective_gross_income"] = calculated_egi
                confidence_scores["effective_gross_income"] = max(egi_confidence, gpr_confidence * 0.9)
        
        # Calculate Net Operating Income if not provided or low confidence
        egi_confidence = confidence_scores.get("effective_gross_income", 0.0)
        opex_confidence = confidence_scores.get("operating_expenses", 0.0)
        noi_confidence = confidence_scores.get("net_operating_income", 0.0)
        
        if egi_confidence > 0.5 and opex_confidence > 0.5:  # We have reasonable confidence in both
            calculated_noi = validated_data["effective_gross_income"] - validated_data["operating_expenses"]
            
            # If NOI confidence is low or calculated value is significantly different, use calculated value
            if noi_confidence < 0.5 or abs(calculated_noi - validated_data["net_operating_income"]) > 1.0:
                validated_data["net_operating_income"] = calculated_noi
                confidence_scores["net_operating_income"] = max(
                    noi_confidence, 
                    min(egi_confidence, opex_confidence) * 0.9
                )
        
        return validated_data
    
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> ExtractionConfidence:
        """
        Calculate overall confidence based on individual field confidence scores.
        
        Args:
            confidence_scores: Confidence scores for each field
            
        Returns:
            Overall ExtractionConfidence level
        """
        if not confidence_scores:
            return ExtractionConfidence.UNCERTAIN
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
        
        # Determine overall confidence level
        if avg_confidence >= 0.8:
            return ExtractionConfidence.HIGH
        elif avg_confidence >= 0.6:
            return ExtractionConfidence.MEDIUM
        elif avg_confidence >= 0.4:
            return ExtractionConfidence.LOW
        else:
            return ExtractionConfidence.UNCERTAIN
    
    def _create_fallback_data(self, file_name: str, document_type_hint: Optional[str]) -> Dict[str, Any]:
        """
        Create fallback data when extraction fails.
        
        Args:
            file_name: Name of the file
            document_type_hint: Optional hint about document type
            
        Returns:
            Fallback data dictionary
        """
        fallback_data = self.financial_metrics.copy()
        fallback_data["file_name"] = file_name
        fallback_data["document_type_hint"] = document_type_hint or "unknown"
        fallback_data["extraction_status"] = "failed"
        fallback_data["requires_manual_entry"] = True
        
        return fallback_data

# Convenience function for backward compatibility
def extract_financial_data(file_content: bytes, file_name: str, 
                          document_type_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract financial data from document (backward compatibility function).
    
    Args:
        file_content: Document content as bytes
        file_name: Name of the file
        document_type_hint: Optional hint about document type
        
    Returns:
        Dictionary containing extracted financial data
    """
    extractor = WorldClassExtractor()
    result = extractor.extract_data(file_content, file_name, document_type_hint)
    return result.data