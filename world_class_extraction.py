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
import hashlib

import pandas as pd
import pdfplumber
from openai import OpenAI

from config import get_openai_api_key
from utils.openai_utils import chat_completion
from utils.error_handler import setup_logger
from preprocessing_module import FilePreprocessor

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
        
        # Initialize the file preprocessor
        self.preprocessor = FilePreprocessor()
        
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
        audit_trail = [f"Starting extraction for {file_name} at {time.strftime('%Y-%m-%d %H:%M:%S')}"]
        
        try:
            # 1. Preprocess the document with validation
            audit_trail.append("Preprocessing document")
            preprocessed_content = self._preprocess_document(file_content, file_name)
            audit_trail.append(f"Preprocessing completed. Content length: {len(str(preprocessed_content))}")
            
            # 2. Validate that document contains actual financial data
            audit_trail.append("Validating financial content")
            has_financial_data = self.preprocessor.validate_financial_content(preprocessed_content['content'])
            audit_trail.append(f"Financial content validation result: {has_financial_data}")
            
            if not has_financial_data:
                audit_trail.append("Document identified as template without financial data")
                # Create a result indicating no financial data
                empty_result = self._create_empty_financial_result()
                processing_time = time.time() - start_time
                
                return ExtractionResult(
                    data=empty_result,
                    confidence=ExtractionConfidence.UNCERTAIN,
                    confidence_scores={},
                    audit_trail=audit_trail,
                    processing_time=processing_time,
                    document_type=DocumentType.UNKNOWN,
                    extraction_method="template-validation"
                )
            
            # 3. Determine document type
            audit_trail.append("Determining document type")
            document_type = self._determine_document_type(file_name, document_type_hint, preprocessed_content)
            audit_trail.append(f"Document type determined: {document_type.value}")
            
            # 4. Extract structured text with multi-modal approach
            audit_trail.append("Extracting structured text with multi-modal approach")
            structured_text = self._extract_structured_text(file_content, file_name, preprocessed_content)
            audit_trail.append(f"Structured text extracted. Length: {len(structured_text)}")
            
            # 5. Extract financial data using GPT-4 with enhanced prompt and retry mechanism
            audit_trail.append("Extracting financial data with GPT-4 (with retry mechanism)")
            extracted_data, confidence_scores = self._extract_with_gpt_with_retry(structured_text, document_type)
            audit_trail.append("GPT-4 extraction completed")
            
            # 6. Validate and enrich the extracted data
            audit_trail.append("Validating and enriching extracted data")
            validated_data = self._validate_and_enrich_data(extracted_data, confidence_scores)
            audit_trail.append("Data validation and enrichment completed")
            
            # 7. Add enhanced validation for zero values
            audit_trail.append("Performing zero value validation")
            validated_data = self._validate_zero_values(validated_data)
            audit_trail.append("Zero value validation completed")
            
            # 8. Add enhanced consistency checks
            audit_trail.append("Performing consistency checks")
            validated_data = self._perform_consistency_checks(validated_data)
            audit_trail.append("Consistency checks completed")
            
            # 9. Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(confidence_scores)
            audit_trail.append(f"Overall confidence calculated: {overall_confidence.value}")
            
            # 10. Add document hash for audit trail
            document_hash = hashlib.md5(file_content).hexdigest()
            audit_trail.append(f"Document hash: {document_hash}")
            
            processing_time = time.time() - start_time
            
            # Add metadata to the result
            validated_data["file_name"] = file_name
            validated_data["document_hash"] = document_hash
            validated_data["processing_timestamp"] = time.time()
            
            return ExtractionResult(
                data=validated_data,
                confidence=overall_confidence,
                confidence_scores=confidence_scores,
                audit_trail=audit_trail,
                processing_time=processing_time,
                document_type=document_type,
                extraction_method="gpt-4-enhanced-with-validation"
            )
            
        except Exception as e:
            audit_trail.append(f"Error during extraction: {str(e)}")
            processing_time = time.time() - start_time
            
            # Create fallback result with enhanced fallback data
            fallback_data = self._create_enhanced_fallback_data(file_name, document_type_hint)
            
            return ExtractionResult(
                data=fallback_data,
                confidence=ExtractionConfidence.UNCERTAIN,
                confidence_scores={},
                audit_trail=audit_trail,
                processing_time=processing_time,
                document_type=DocumentType.UNKNOWN,
                extraction_method="enhanced-fallback"
            )
    
    def _preprocess_document(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """
        Preprocess document to determine type and basic structure with enhanced error handling.
        
        Args:
            file_content: Document content as bytes
            file_name: Name of the file
            
        Returns:
            Dictionary with preprocessing information
        """
        try:
            # Create a temporary file for preprocessing
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Use the FilePreprocessor to handle all file types
                preprocessed = self.preprocessor.preprocess(tmp_file_path, filename=file_name)
                return preprocessed
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
        except Exception as e:
            logger.error(f"Error preprocessing document {file_name}: {str(e)}")
            # Return a minimal structure if preprocessing fails
            return {
                'content': {},
                'metadata': {
                    'filename': file_name,
                    'error': str(e)
                }
            }
    
    def _extract_structured_text(self, file_content: bytes, file_name: str, preprocessed_content: Dict[str, Any]) -> str:
        """
        Extract structured text from preprocessed content using hierarchical approach.
        
        Args:
            file_content: Original file content
            file_name: Name of the file
            preprocessed_content: Preprocessed content from FilePreprocessor
            
        Returns:
            Structured text for GPT processing
        """
        try:
            # Use hierarchical approach for text input
            # 1. Prefer 'combined_text' when available
            if 'content' in preprocessed_content and 'combined_text' in preprocessed_content['content']:
                text = preprocessed_content['content']['combined_text']
                if text and len(text.strip()) > 0:
                    return self._format_structured_text(text, file_name, preprocessed_content)
            
            # 2. Fall back to 'text_representation' for structured documents like Excel
            if 'content' in preprocessed_content and 'text_representation' in preprocessed_content['content']:
                text_rep = preprocessed_content['content']['text_representation']
                if isinstance(text_rep, list) and len(text_rep) > 0:
                    text = "\n\n".join(text_rep)
                    if text and len(text.strip()) > 0:
                        return self._format_structured_text(text, file_name, preprocessed_content)
                elif isinstance(text_rep, str) and len(text_rep.strip()) > 0:
                    return self._format_structured_text(text_rep, file_name, preprocessed_content)
            
            # 3. Use simple 'text' content as final fallback
            if 'content' in preprocessed_content and 'text' in preprocessed_content['content']:
                text_content = preprocessed_content['content']['text']
                if isinstance(text_content, list) and len(text_content) > 0:
                    # For PDF content with multiple pages
                    pages_text = []
                    for page in text_content:
                        if isinstance(page, dict) and 'content' in page:
                            pages_text.append(page['content'])
                    text = "\n\n".join(pages_text)
                    if text and len(text.strip()) > 0:
                        return self._format_structured_text(text, file_name, preprocessed_content)
                elif isinstance(text_content, str) and len(text_content.strip()) > 0:
                    return self._format_structured_text(text_content, file_name, preprocessed_content)
            
            # If we still don't have text, convert the entire content to string
            return self._format_structured_text(str(preprocessed_content), file_name, preprocessed_content)
            
        except Exception as e:
            logger.error(f"Error extracting structured text from {file_name}: {str(e)}")
            return f"Error extracting text from document: {str(e)}"
    
    def _format_structured_text(self, text: str, file_name: str, preprocessed_content: Dict[str, Any]) -> str:
        """
        Format text with clear section headers and structural markers.
        
        Args:
            text: Raw text content
            file_name: Name of the file
            preprocessed_content: Preprocessed content
            
        Returns:
            Formatted structured text
        """
        # Add document metadata as headers
        formatted_text = f"DOCUMENT_FILE_NAME: {file_name}\n"
        formatted_text += f"DOCUMENT_PROCESSING_TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Add metadata if available
        if 'metadata' in preprocessed_content:
            metadata = preprocessed_content['metadata']
            if 'extension' in metadata:
                formatted_text += f"DOCUMENT_FILE_TYPE: {metadata['extension']}\n"
            if 'file_type' in metadata:
                formatted_text += f"DOCUMENT_MIME_TYPE: {metadata['file_type']}\n"
        
        # Add structure indicators if available
        if 'content' in preprocessed_content and 'structure_indicators' in preprocessed_content['content']:
            indicators = preprocessed_content['content']['structure_indicators']
            if indicators and len(indicators) > 0:
                formatted_text += f"DOCUMENT_STRUCTURE_INDICATORS: {', '.join(indicators)}\n"
        
        # Add separator and the actual content
        formatted_text += "\n" + "="*50 + "\n"
        formatted_text += "DOCUMENT_CONTENT_START\n"
        formatted_text += "="*50 + "\n\n"
        formatted_text += text
        formatted_text += "\n\n" + "="*50 + "\n"
        formatted_text += "DOCUMENT_CONTENT_END\n"
        formatted_text += "="*50 + "\n"
        
        return formatted_text
    
    def _determine_document_type(self, file_name: str, document_type_hint: Optional[str], 
                                preprocessed_content: Dict[str, Any]) -> DocumentType:
        """
        Determine document type from file name, hint, or content.
        
        Args:
            file_name: Name of the file
            document_type_hint: Hint about document type
            preprocessed_content: Preprocessed content
            
        Returns:
            DocumentType enum value
        """
        # Use hint if provided
        if document_type_hint:
            if "actual" in document_type_hint.lower() and "income" in document_type_hint.lower():
                return DocumentType.ACTUAL_INCOME_STATEMENT
            elif "budget" in document_type_hint.lower():
                return DocumentType.BUDGET
            elif "prior" in document_type_hint.lower() and "year" in document_type_hint.lower():
                return DocumentType.PRIOR_YEAR_ACTUAL
        
        # Try to determine from file name
        file_name_lower = file_name.lower()
        if "actual" in file_name_lower and "income" in file_name_lower:
            return DocumentType.ACTUAL_INCOME_STATEMENT
        elif "budget" in file_name_lower:
            return DocumentType.BUDGET
        elif "prior" in file_name_lower and "year" in file_name_lower:
            return DocumentType.PRIOR_YEAR_ACTUAL
        
        # Try to determine from content
        if 'content' in preprocessed_content:
            content_str = str(preprocessed_content['content']).lower()
            if "actual" in content_str and "income" in content_str:
                return DocumentType.ACTUAL_INCOME_STATEMENT
            elif "budget" in content_str:
                return DocumentType.BUDGET
            elif "prior" in content_str and "year" in content_str:
                return DocumentType.PRIOR_YEAR_ACTUAL
        
        return DocumentType.UNKNOWN
    
    def _extract_with_gpt_with_retry(self, structured_text: str, document_type: DocumentType, 
                                    max_retries: int = 3) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Extract financial data using GPT-4 with retry mechanism and progressive prompting.
        
        Args:
            structured_text: Formatted text for GPT processing
            document_type: Type of document
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of extracted data and confidence scores
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                    # For retry attempts, use a more explicit prompt
                    prompt = self._create_enhanced_extraction_prompt(structured_text, document_type, attempt)
                else:
                    # First attempt with standard prompt
                    prompt = self._create_extraction_prompt(structured_text, document_type)
                
                # Extract data using GPT
                response = self._extract_with_gpt(prompt)
                
                # Validate response structure
                if isinstance(response, dict) and 'financial_data' in response and 'confidence_scores' in response:
                    return response['financial_data'], response['confidence_scores']
                else:
                    raise ValueError("Invalid response structure from GPT")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"GPT extraction attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    # Wait before retry
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        # If all retries failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise Exception("GPT extraction failed after all retries")
    
    def _create_extraction_prompt(self, text: str, document_type: DocumentType) -> str:
        """
        Create extraction prompt based on document type with enhanced context.
        
        Args:
            text: Preprocessed text from the document
            document_type: Type of document
            
        Returns:
            Extraction prompt for GPT
        """
        # Prepare a sample of the text for GPT (first 3000 characters to leave room for prompt)
        text_sample = text[:3000]
        
        # Create document type specific context
        doc_type_context = ""
        if document_type == DocumentType.ACTUAL_INCOME_STATEMENT:
            doc_type_context = """This is an Actual Income Statement showing real financial results for a specific property.

Important notes for Actual Income Statements:
- These are ACTUAL results, not projections or budgets
- Look for sections labeled "Income", "Revenue", "Expenses", or "Operating Expenses"
- The document may use terms like "YTD", "Month-to-Date", or specific month names
- Focus on the most recent or relevant period if multiple periods are shown
- Ensure mathematical consistency in your extraction
- Be precise with negative values which may be shown in parentheses e.g. (1,234.50)"""
            
        elif document_type == DocumentType.BUDGET:
            doc_type_context = """This is a Budget document showing projected financial figures for a specific property.

Important notes for Budget documents:
- These are PROJECTED figures, not actual results
- Look for sections labeled "Budget", "Forecast", "Plan", or "Projected"
- The document may include comparisons to actual results
- Focus on the budget figures, not the actual or variance columns
- Ensure mathematical consistency in your extraction
- Be precise with negative values which may be shown in parentheses e.g. (1,234.50)"""
            
        elif document_type == DocumentType.PRIOR_YEAR_ACTUAL:
            doc_type_context = """This is a Prior Year Actual statement showing historical financial results for a specific property.

Important notes for Prior Year Actual statements:
- These are HISTORICAL results from a previous period
- Look for sections labeled with previous year indicators
- The document may include comparisons to current year or budget
- Focus on the prior year figures, not current year or budget columns
- Ensure mathematical consistency in your extraction
- Be precise with negative values which may be shown in parentheses e.g. (1,234.50)"""
        else:
            doc_type_context = """This is a financial document of unknown type. Please identify the document type and extract accordingly."""
        
        # Create the full prompt with explicit instructions
        prompt = f"""You are a world-class real estate financial analyst. Extract financial data and return ONLY a JSON object.

Document Type: {document_type.value}
Instructions: {doc_type_context}

Document Content:
{text_sample}

Extract these financial metrics and provide confidence scores (0.0 to 1.0):
REQUIRED JSON FORMAT:
{{
  "financial_data": {{
    "gross_potential_rent": 0.0,
    "vacancy_loss": 0.0,
    "concessions": 0.0,
    "bad_debt": 0.0,
    "other_income": 0.0,
    "effective_gross_income": 0.0,
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
    "net_operating_income": 0.0
  }},
  "confidence_scores": {{
    "gross_potential_rent": 0.0,
    "vacancy_loss": 0.0,
    "concessions": 0.0,
    "bad_debt": 0.0,
    "other_income": 0.0,
    "effective_gross_income": 0.0,
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
    "net_operating_income": 0.0
  }}
}}

FINANCIAL TERM MAPPINGS:
- Gross Potential Rent: Rent, Revenue, Income, Gross Rent
- Vacancy Loss: Vacancy, Credit Loss
- Concessions: Free Rent, Tenant Concessions
- Bad Debt: Uncollected Rent, Delinquent Rent
- Other Income: Parking, Laundry, Fees
- Operating Expenses: Expenses, OpEx
- Net Operating Income: NOI

IMPORTANT:
1. Return ONLY the JSON object, nothing else
2. All values must be numbers, not strings
3. If a value is not found, use 0.0
4. Provide confidence scores based on how certain you are (1.0 = very certain, 0.0 = guessing)
5. Calculate derived values when needed:
   - Effective Gross Income = Gross Potential Rent - Vacancy Loss - Concessions - Bad Debt + Other Income
   - Net Operating Income = Effective Gross Income - Operating Expenses
6. Be precise with negative values which may be shown in parentheses e.g. (1,234.50) should be -1234.50
7. Handle currency formatting (e.g., $1,234.50 should be 1234.50)
"""
        
        return prompt
    
    def _create_enhanced_extraction_prompt(self, text: str, document_type: DocumentType, attempt: int) -> str:
        """
        Create an enhanced extraction prompt for retry attempts.
        
        Args:
            text: Preprocessed text from the document
            document_type: Type of document
            attempt: Retry attempt number
            
        Returns:
            Enhanced extraction prompt for GPT
        """
        # For retry attempts, be more explicit and provide examples
        base_prompt = self._create_extraction_prompt(text, document_type)
        
        # Add retry-specific instructions
        retry_instructions = f"""
        
ADDITIONAL INSTRUCTIONS FOR ATTEMPT #{attempt + 1}:
- Pay extra attention to number formatting and currency symbols
- Look for values in tables, lists, and structured sections
- If you see ranges or multiple values, use the most relevant one
- For missing values, use 0.0 but set confidence score accordingly
- Double-check that all required fields are present in your response
- Ensure your JSON is properly formatted with no syntax errors
"""
        
        return base_prompt + retry_instructions
    
    def _extract_with_gpt(self, prompt: str) -> Dict[str, Any]:
        """
        Extract data using GPT with proper error handling.
        
        Args:
            prompt: Prompt for GPT
            
        Returns:
            Extracted data as dictionary
        """
        try:
            # Use chat completion with appropriate parameters
            response = chat_completion(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a world-class real estate financial analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=2000
            )
            
            # Extract content from response using safe attribute access
            content = ""
            try:
                # Safely navigate the response structure using getattr
                choices = getattr(response, 'choices', None)
                if choices and len(choices) > 0:
                    choice = choices[0]
                    message = getattr(choice, 'message', None)
                    if message:
                        content = getattr(message, 'content', str(message))
                    else:
                        content = str(choice)
                else:
                    # Try to convert response to dict and access choices
                    if hasattr(response, '__dict__'):
                        response_dict = response.__dict__
                        choices = response_dict.get('choices', [])
                        if choices and len(choices) > 0:
                            choice = choices[0]
                            message = getattr(choice, 'message', choice)
                            if hasattr(message, '__dict__'):
                                message_dict = message.__dict__
                                content = message_dict.get('content', str(message))
                            else:
                                content = str(message)
                        else:
                            content = str(response_dict)
                    else:
                        content = str(response)
            except Exception as e:
                # Fallback to string conversion
                logger.warning(f"Error navigating response structure: {str(e)}")
                content = str(response)
            
            # Parse JSON response
            parsed_data = self._parse_gpt_response(content)
            # Return the full parsed data (which includes financial_data and confidence_scores)
            return parsed_data
                
        except Exception as e:
            logger.error(f"Error in GPT extraction: {str(e)}")
            raise
    
    @staticmethod
    def _parse_gpt_response(response_content: str) -> Dict[str, Any]:
        """
        Parse GPT response content and extract JSON data.
        
        Args:
            response_content: String content from GPT response
            
        Returns:
            Dictionary containing financial_data and confidence_scores
        """
        # Parse JSON response
        # Try to extract JSON from the response content
        json_start = response_content.find('{')
        json_end = response_content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_content[json_start:json_end]
            try:
                parsed_data = json.loads(json_str)
                return parsed_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                raise ValueError(f"Failed to parse JSON from GPT response: {str(e)}")
        else:
            raise ValueError("No JSON object found in GPT response")

    def _validate_and_enrich_data(self, extracted_data: Dict[str, Any], 
                                 confidence_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate and enrich extracted data with calculations and formatting.
        
        Args:
            extracted_data: Raw extracted data
            confidence_scores: Confidence scores for each field
            
        Returns:
            Validated and enriched data
        """
        # Start with a copy of the extracted data
        validated_data = extracted_data.copy() if extracted_data else {}
        
        # Ensure all required fields are present
        for field in self.financial_metrics.keys():
            if field not in validated_data:
                validated_data[field] = 0.0
        
        # Convert all values to float and handle string representations
        for field, value in validated_data.items():
            if isinstance(value, str):
                # Handle currency formatting and parentheses for negative values
                cleaned_value = value.strip().replace('$', '').replace(',', '')
                if cleaned_value.startswith('(') and cleaned_value.endswith(')'):
                    cleaned_value = '-' + cleaned_value[1:-1]
                try:
                    validated_data[field] = float(cleaned_value)
                except (ValueError, TypeError):
                    validated_data[field] = 0.0
            elif not isinstance(value, (int, float)):
                validated_data[field] = 0.0
            else:
                validated_data[field] = float(value)
        
        # Calculate derived metrics if not provided
        self._calculate_derived_metrics(validated_data)
        
        return validated_data
    
    def _calculate_derived_metrics(self, data: Dict[str, Any]) -> None:
        """
        Calculate derived financial metrics.
        
        Args:
            data: Financial data dictionary to update
        """
        # Calculate Effective Gross Income if not provided or if confidence is low
        if data.get("effective_gross_income", 0.0) == 0.0:
            egi = (data.get("gross_potential_rent", 0.0) - 
                  data.get("vacancy_loss", 0.0) - 
                  data.get("concessions", 0.0) - 
                  data.get("bad_debt", 0.0) + 
                  data.get("other_income", 0.0))
            data["effective_gross_income"] = egi
        
        # Calculate Net Operating Income if not provided or if confidence is low
        if data.get("net_operating_income", 0.0) == 0.0:
            noi = (data.get("effective_gross_income", 0.0) - 
                  data.get("operating_expenses", 0.0))
            data["net_operating_income"] = noi
    
    def _validate_zero_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that zero values in extraction results are legitimate.
        
        Args:
            data: Financial data dictionary
            
        Returns:
            Validated data dictionary
        """
        validated_data = data.copy()
        
        # Key financial metrics that should not be zero in most cases
        key_metrics = ["gross_potential_rent", "effective_gross_income", "net_operating_income"]
        
        for metric in key_metrics:
            if validated_data.get(metric, 0.0) == 0.0:
                # Log warning for zero values in key metrics
                logger.warning(f"Zero value detected for key metric '{metric}' in extraction result - this may indicate extraction issues")
        
        return validated_data
    
    def _perform_consistency_checks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform consistency checks on extracted financial data.
        
        Args:
            data: Financial data dictionary
            
        Returns:
            Data dictionary with consistency flags
        """
        # Add consistency check results to the data
        data["consistency_checks"] = {}
        
        # Check EGI calculation consistency
        calculated_egi = (data.get("gross_potential_rent", 0.0) - 
                         data.get("vacancy_loss", 0.0) - 
                         data.get("concessions", 0.0) - 
                         data.get("bad_debt", 0.0) + 
                         data.get("other_income", 0.0))
        
        reported_egi = data.get("effective_gross_income", 0.0)
        
        # Allow for small rounding differences
        if abs(calculated_egi - reported_egi) <= 1.0:
            data["consistency_checks"]["egi_calculation"] = "consistent"
        else:
            data["consistency_checks"]["egi_calculation"] = "inconsistent"
            logger.warning(f"EGI calculation inconsistency: calculated={calculated_egi}, reported={reported_egi}")
        
        # Check NOI calculation consistency
        calculated_noi = reported_egi - data.get("operating_expenses", 0.0)
        reported_noi = data.get("net_operating_income", 0.0)
        
        # Allow for small rounding differences
        if abs(calculated_noi - reported_noi) <= 1.0:
            data["consistency_checks"]["noi_calculation"] = "consistent"
        else:
            data["consistency_checks"]["noi_calculation"] = "inconsistent"
            logger.warning(f"NOI calculation inconsistency: calculated={calculated_noi}, reported={reported_noi}")
        
        return data
    
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> ExtractionConfidence:
        """
        Calculate overall confidence based on individual field confidence scores.
        
        Args:
            confidence_scores: Dictionary of field confidence scores
            
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
    
    def _create_empty_financial_result(self) -> Dict[str, Any]:
        """
        Create a result structure for documents without financial data.
        
        Returns:
            Empty financial result with appropriate flags
        """
        empty_result = self.financial_metrics.copy()
        empty_result["extraction_status"] = "no_financial_data"
        empty_result["requires_manual_entry"] = True
        empty_result["error_message"] = "Document appears to be a template without actual financial data. Please upload a document containing real financial figures."
        return empty_result
    
    def _create_enhanced_fallback_data(self, file_name: str, 
                                      document_type_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Create enhanced fallback data with better error handling.
        
        Args:
            file_name: Name of the file
            document_type_hint: Hint about document type
            
        Returns:
            Enhanced fallback data
        """
        fallback_data = self.financial_metrics.copy()
        fallback_data["file_name"] = file_name
        fallback_data["document_type_hint"] = document_type_hint or ""
        fallback_data["extraction_status"] = "failed"
        fallback_data["requires_manual_entry"] = True
        return fallback_data


def extract_financial_data(file_content: bytes, file_name: str, 
                          document_type_hint: Optional[str] = None) -> ExtractionResult:
    """
    Convenience function to extract financial data from a document.
    
    Args:
        file_content: Document content as bytes
        file_name: Name of the file
        document_type_hint: Optional hint about document type
        
    Returns:
        ExtractionResult with data, confidence, and audit information
    """
    extractor = WorldClassExtractor()
    return extractor.extract_data(file_content, file_name, document_type_hint)