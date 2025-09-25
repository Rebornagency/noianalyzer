import os
import logging
import json
import tempfile
import time
from typing import Dict, Any, List, Optional, BinaryIO, Union
import streamlit as st
from config import get_extraction_api_url, get_api_key, get_openai_api_key
from constants import ERROR_MESSAGES, DEFAULT_API_CONFIG, FILE_UPLOAD_CONFIG, MAIN_METRICS, OPEX_COMPONENTS, INCOME_COMPONENTS
from utils.error_handler import setup_logger, handle_errors, graceful_degradation, APIError
from utils.common import safe_float, safe_string, create_fallback_financial_data, normalize_field_names
from utils.openai_utils import chat_completion

# Setup logger
logger = setup_logger(__name__)

@graceful_degradation(
    fallback_value={"error": "Data extraction service temporarily unavailable. Please try manual entry or check back later."},
    operation_name="document data extraction"
)
@handle_errors(default_return={"error": "Failed to extract data from document"})
def extract_noi_data(file: Any, document_type_hint: Optional[str] = None, 
                    api_url: Optional[str] = None, api_key: Optional[str] = None,
                    max_retries: Optional[int] = None, retry_delay: int = 5) -> Dict[str, Any]:
    """
    Extract NOI data from a document using GPT with enhanced error handling.
    
    Args:
        file: Document file to process
        document_type_hint: Optional hint about document type
        api_url: Not used in GPT implementation (kept for compatibility)
        api_key: Not used in GPT implementation (kept for compatibility)
        max_retries: Maximum number of retry attempts for API calls
        retry_delay: Delay in seconds between retry attempts
        
    Returns:
        Dictionary containing extracted financial data or fallback structure
    """
    # Use default configuration if not provided
    if max_retries is None:
        max_retries = DEFAULT_API_CONFIG["MAX_RETRIES"]
    
    file_name = getattr(file, 'name', 'unknown')
    logger.info(
        f"Starting GPT-based data extraction",
        extra={
            "file_name": file_name,
            "document_type_hint": document_type_hint,
            "max_retries": max_retries
        }
    )
    
    # Get OpenAI API key
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        logger.error("OpenAI API key not configured")
        raise APIError("OpenAI API key not configured. Please set your OpenAI API key.")
    
    # Prepare file content for processing
    try:
        file_content = file.getvalue()
        # Size guardrail (bytes)
        max_size_bytes = FILE_UPLOAD_CONFIG.get("MAX_FILE_SIZE", 200) * 1024 * 1024
        if len(file_content) > max_size_bytes:
            logger.error(f"Uploaded file exceeds size limit: {len(file_content)} bytes")
            raise APIError("Uploaded file too large (limit {} MB)".format(FILE_UPLOAD_CONFIG.get("MAX_FILE_SIZE", 200)))
        file_type = getattr(file, 'type', 'application/octet-stream')
        
        logger.info(
            f"File prepared for GPT processing",
            extra={
                "file_size": len(file_content),
                "file_type": file_type
            }
        )
    except Exception as e:
        logger.error(f"Error preparing file for processing: {str(e)}")
        raise APIError(f"Failed to prepare file for processing: {str(e)}")
    
    # Retry logic with enhanced error handling
    last_error = None
    for attempt in range(max_retries):  # type: ignore
        try:
            attempt_start_time = time.time()
            
            if attempt > 0:
                logger.info(
                    f"Retry attempt {attempt+1}/{max_retries}",
                    extra={
                        "file_name": file_name,
                        "previous_error": str(last_error) if last_error else None
                    }
                )
            
            # Create spinner in UI for better user feedback
            spinner_message = f"Extracting data from {file_name} using GPT (attempt {attempt+1}/{max_retries})..."
            
            if hasattr(st, 'spinner'):
                with st.spinner(spinner_message):
                    result = extract_financial_data_with_gpt(file_content, file_name, document_type_hint, openai_api_key)
            else:
                result = extract_financial_data_with_gpt(file_content, file_name, document_type_hint, openai_api_key)
            
            attempt_time = time.time() - attempt_start_time
            logger.info(
                f"GPT extraction completed",
                extra={
                    "file_name": file_name,
                    "response_time": f"{attempt_time:.3f}s",
                    "attempt": attempt + 1
                }
            )
            
            # Validate and enrich the response
            validated_result = validate_and_enrich_extraction_result(result, file_name, document_type_hint)
            
            logger.info(
                f"Data extraction successful",
                extra={
                    "file_name": file_name,
                    "response_keys": list(validated_result.keys()),
                    "total_time": f"{time.time() - (attempt_start_time - (attempt * retry_delay)):.3f}s"
                }
            )
            
            return validated_result
                    
        except Exception as e:
            error_msg = f"Unexpected error during GPT extraction: {str(e)}"
            logger.error(error_msg, exc_info=True, extra={"file_name": file_name})
            last_error = APIError(error_msg)
        
        # Wait before retry (except on last attempt)
        if attempt < max_retries - 1:  # type: ignore
            logger.info(f"Waiting {retry_delay} seconds before retry...")
            time.sleep(retry_delay)
            # Exponential backoff
            retry_delay = min(retry_delay * 2, 60)  # Cap at 60 seconds
    
    # All retries exhausted - return fallback
    logger.error(
        f"Data extraction failed after {max_retries} attempts",
        extra={
            "file_name": file_name,
            "last_error": str(last_error) if last_error else "Unknown error"
        }
    )
    
    return create_fallback_extraction_result(file_name, document_type_hint, f"Service unavailable after {max_retries} attempts")


def extract_financial_data_with_gpt(file_content: bytes, file_name: str, document_type_hint: Optional[str], openai_api_key: str) -> Dict[str, Any]:
    """
    Extract financial data from document content using GPT with enhanced robustness.
    
    Args:
        file_content: The content of the file as bytes
        file_name: Name of the file
        document_type_hint: Hint about document type
        openai_api_key: OpenAI API key
        
    Returns:
        Dictionary containing extracted financial data
    """
    text_content = None
    
    # Determine file extension
    _, ext = os.path.splitext(file_name)
    ext = ext.lower().lstrip('.')
    
    logger.info(f"Processing file with extension: {ext}", extra={"file_name": file_name})
    
    # Try to process based on file extension
    try:
        if ext in ['xlsx', 'xls']:
            # Handle Excel files
            logger.info("Processing as Excel file", extra={"file_name": file_name})
            text_content = extract_text_from_excel(file_content, file_name)
        elif ext == 'pdf':
            # Handle PDF files
            logger.info("Processing as PDF file", extra={"file_name": file_name})
            text_content = extract_text_from_pdf(file_content, file_name)
        elif ext == 'csv':
            # Handle CSV files
            logger.info("Processing as CSV file", extra={"file_name": file_name})
            text_content = extract_text_from_csv(file_content, file_name)
        elif ext == 'txt':
            # Handle text files with enhanced formatting
            logger.info("Processing as text file", extra={"file_name": file_name})
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
                # Enhance text formatting for better GPT parsing
                text_content = _format_text_content(text_content, file_name)
            except Exception as e:
                logger.warning(f"Text decoding failed: {str(e)}", extra={"file_name": file_name})
                text_content = f"[Text content from {file_name}]"
        else:
            # For unknown file types, try multiple approaches
            logger.info(f"Processing as unknown file type ({ext}), trying multiple approaches", extra={"file_name": file_name})
            
            # Try as text first
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
                # Enhance text formatting for better GPT parsing
                text_content = _format_text_content(text_content, file_name)
                logger.info("Successfully decoded as text", extra={"file_name": file_name})
            except Exception as e:
                logger.warning(f"Text decoding failed: {str(e)}", extra={"file_name": file_name})
                
            # If text didn't work well, try as Excel
            if not text_content or len(text_content.strip()) < 50:
                try:
                    logger.info("Trying Excel extraction for unknown file type", extra={"file_name": file_name})
                    text_content = extract_text_from_excel(file_content, file_name)
                except Exception as e:
                    logger.warning(f"Excel extraction failed for unknown file type: {str(e)}", extra={"file_name": file_name})
                    
            # If still no good content, try as CSV
            if not text_content or len(text_content.strip()) < 50:
                try:
                    logger.info("Trying CSV extraction for unknown file type", extra={"file_name": file_name})
                    text_content = extract_text_from_csv(file_content, file_name)
                except Exception as e:
                    logger.warning(f"CSV extraction failed for unknown file type: {str(e)}", extra={"file_name": file_name})
                
    except Exception as e:
        # If any processing fails, fall back to basic text decoding
        logger.warning(f"File processing failed for {file_name}, falling back to text decoding: {str(e)}")
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
            # Enhance text formatting for better GPT parsing
            text_content = _format_text_content(text_content, file_name)
        except Exception:
            text_content = f"[Document content from {file_name}]"
    
    # If text content is still empty or too short, fall back to file name
    if not text_content or not text_content.strip() or len(text_content.strip()) < 20:
        logger.warning("Text content is empty or too short, using file name as content", extra={"file_name": file_name})
        text_content = f"[Document content from {file_name}]"
    
    # Log the length and a sample of the text content for debugging
    logger.info(
        f"Extracted text content length: {len(text_content)} chars",
        extra={
            "file_name": file_name,
            "content_length": len(text_content)
        }
    )
    
    # For very long content, log a sample
    if len(text_content) > 1000:
        # Take a sample from the beginning, middle, and end
        sample_start = text_content[:300]
        sample_middle = text_content[len(text_content)//2:len(text_content)//2+300]
        sample_end = text_content[-300:]
        sample = f"{sample_start} ... {sample_middle} ... {sample_end}"
        logger.debug(
            f"Sample of extracted text content: {sample}",
            extra={"file_name": file_name}
        )
    else:
        logger.debug(
            f"Extracted text content: {text_content}",
            extra={"file_name": file_name}
        )
    
    # Create the prompt for GPT
    prompt = create_gpt_extraction_prompt(text_content, file_name, document_type_hint)
    
    # Prepare messages for chat completion
    messages = [
        {"role": "system", "content": "You are a world-class real estate financial analyst with expertise in extracting data from diverse financial documents. You are meticulous, accurate, and never leave fields empty."},
        {"role": "user", "content": prompt}
    ]
    
    logger.info(f"Sending extraction prompt to GPT (length: {len(prompt)} chars)")
    
    # Try multiple attempts with GPT
    max_gpt_attempts = 3
    for attempt in range(max_gpt_attempts):
        try:
            # Call OpenAI API
            response_content = chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=2000
            )
            
            logger.info(f"Received response from GPT (length: {len(response_content)} chars)")
            logger.debug(f"Raw GPT response: {response_content}")
            
            # Parse the JSON response
            try:
                # Extract JSON from response if it's wrapped in other text
                json_start = response_content.find('{{')
                json_end = response_content.rfind('}}') + 2
                if json_start >= 0 and json_end > json_start:
                    # Handle double braces from GPT formatting
                    json_str = response_content[json_start:json_end].replace('{{', '{').replace('}}', '}')
                    result = json.loads(json_str)
                    logger.info(f"Successfully parsed JSON from GPT response with brace correction")
                else:
                    json_start = response_content.find('{')
                    json_end = response_content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response_content[json_start:json_end]
                        result = json.loads(json_str)
                        logger.info(f"Successfully parsed JSON from GPT response")
                    else:
                        result = json.loads(response_content)
                        logger.info(f"Successfully parsed direct JSON response")
                
                # Validate that we have the required structure AND meaningful data
                required_fields = ['gpr', 'vacancy_loss', 'concessions', 'bad_debt', 'other_income', 
                                 'egi', 'opex', 'noi', 'property_taxes', 'insurance', 'repairs_maintenance',
                                 'utilities', 'management_fees', 'parking', 'laundry', 'late_fees']
                
                # Check if we have the required fields in the response
                has_required_fields = all(field in result for field in required_fields)
                
                # Check if we have meaningful (non-zero) financial data
                has_meaningful_data = False
                key_metrics = ['gpr', 'egi', 'opex', 'noi']
                if has_required_fields:
                    # Check if at least some key financial metrics have non-zero values
                    meaningful_values = [result.get(metric, 0) for metric in key_metrics]
                    # At least one key metric should be non-zero for meaningful data
                    has_meaningful_data = any(float(value) != 0 for value in meaningful_values)
                
                # If we have the required structure and meaningful data, return it
                if has_required_fields and has_meaningful_data:
                    logger.info(f"GPT extraction successful with required financial fields and meaningful data")
                    # Log the keys in the result for debugging
                    logger.info(
                        f"GPT response keys: {list(result.keys())}",
                        extra={
                            "file_name": file_name,
                            "response_keys": list(result.keys())
                        }
                    )
                    return result
                elif has_required_fields:
                    logger.warning(f"GPT response has required fields but no meaningful data (attempt {attempt + 1}/{max_gpt_attempts})")
                    # Log what fields we have for debugging
                    available_fields = [key for key in result.keys() if key not in ['file_name', 'document_type']]
                    logger.debug(f"Available fields: {available_fields}")
                    # Log key metric values
                    key_metrics_values = {metric: result.get(metric, 0) for metric in key_metrics}
                    logger.debug(f"Key metrics values: {key_metrics_values}")
                else:
                    logger.warning(f"GPT response missing required financial fields (attempt {attempt + 1}/{max_gpt_attempts})")
                    # Log what fields we do have for debugging
                    available_fields = [key for key in result.keys() if key not in ['file_name', 'document_type']]
                    logger.debug(f"Available fields: {available_fields}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
                logger.error(f"Response content: {response_content}")
                # Try to extract any financial data that might be in the response
                result = _extract_financial_data_from_text(response_content, file_name, document_type_hint)
                if result and len(result) > 2:
                    logger.info("Successfully extracted financial data from text response")
                    return result
                else:
                    logger.warning(f"Text extraction from GPT response failed (attempt {attempt + 1}/{max_gpt_attempts})")
                    
        except Exception as e:
            logger.error(f"Error calling OpenAI API (attempt {attempt + 1}/{max_gpt_attempts}): {str(e)}")
            
        # If we get here, the attempt failed. Try again with a modified prompt for subsequent attempts
        if attempt < max_gpt_attempts - 1:
            logger.info(f"Retrying GPT extraction (attempt {attempt + 2}/{max_gpt_attempts})")
            # Add a note to be more explicit on retry
            retry_note = f"\n\nIMPORTANT: This is retry attempt {attempt + 2}. Please be extremely thorough and extract ALL financial data, even if you're unsure. Make educated estimates when needed. DO NOT return all zero values."
            messages[1]["content"] = prompt + retry_note
    
    # If all GPT attempts fail, try to extract data directly from the document text
    logger.warning("All GPT attempts failed, trying direct text extraction")
    direct_result = _extract_financial_data_from_text(text_content, file_name, document_type_hint)
    if direct_result and len(direct_result) > 2:
        logger.info("Successfully extracted financial data directly from document text")
        return direct_result
    
    # If everything fails, return a fallback result
    logger.error("All extraction methods failed, returning fallback result")
    return {
        "file_name": file_name,
        "document_type": document_type_hint or "unknown",
        "gpr": 0.0,
        "vacancy_loss": 0.0,
        "concessions": 0.0,
        "bad_debt": 0.0,
        "other_income": 0.0,
        "egi": 0.0,
        "opex": 0.0,
        "noi": 0.0,
        "property_taxes": 0.0,
        "insurance": 0.0,
        "repairs_maintenance": 0.0,
        "utilities": 0.0,
        "management_fees": 0.0,
        "parking": 0.0,
        "laundry": 0.0,
        "late_fees": 0.0,
        "pet_fees": 0.0,
        "application_fees": 0.0,
        "storage_fees": 0.0,
        "amenity_fees": 0.0,
        "utility_reimbursements": 0.0,
        "cleaning_fees": 0.0,
        "cancellation_fees": 0.0,
        "miscellaneous": 0.0
    }


def _extract_financial_data_from_text(text: str, file_name: str, document_type_hint: Optional[str]) -> Dict[str, Any]:
    """
    Extract financial data from text response when JSON parsing fails.
    
    Args:
        text: Text response from GPT
        file_name: Name of the file
        document_type_hint: Hint about document type
        
    Returns:
        Dictionary containing extracted financial data or empty dict if none found
    """
    try:
        # Try to find financial values using regex patterns
        import re
        
        # Create a basic result structure
        result: Dict[str, Any] = {
            "file_name": file_name,
            "document_type": document_type_hint or "unknown"
        }
        
        # Normalize the text for better matching
        normalized_text = text.lower()
        
        # Common financial terms and their field mappings with more variations
        financial_terms = {
            r'(?:gross\s+potential\s+rent|gpr|potential\s+rent|scheduled\s+rent|total\s+rental\s+income|gross\s+rental\s+income)': 'gpr',
            r'(?:vacancy\s+loss|vacancy|credit\s+loss|vacancy\s+and\s+credit\s+loss|turnover\s+loss)': 'vacancy_loss',
            r'(?:concession|concessions|tenant\s+concessions|leasing\s+concessions|move-in\s+concessions|free\s+rent)': 'concessions',
            r'(?:bad\s+debt|uncollected\s+rent|delinquent\s+rent|write-offs|account\s+receivable\s+write-offs)': 'bad_debt',
            r'(?:other\s+income|additional\s+income|miscellaneous\s+income|parking\s+(?:fees?|income)|laundry\s+(?:fees?|income)|application\s+fees?|late\s+fees?|pet\s+fees?|storage\s+fees?|amenity\s+fees?|utility\s+reimbursements?|cleaning\s+fees?|cancellation\s+fees?)': 'other_income',
            r'(?:effective\s+gross\s+income|egi|net\s+rental\s+income|adjusted\s+gross\s+income)': 'egi',
            r'(?:operating\s+expenses?|opex|total\s+operating\s+expenses|expenses|operating\s+costs|property\s+operating\s+expenses)': 'opex',
            r'(?:net\s+operating\s+income|noi|net\s+income|operating\s+income|property\s+net\s+income)': 'noi',
            r'(?:property\s+tax)': 'property_taxes',
            r'(?:insurance)': 'insurance',
            r'(?:repairs?\s+(?:&|and)\s+maintenance|repairs?|maintenance)': 'repairs_maintenance',
            r'(?:utilit(?:y|ies))': 'utilities',
            r'(?:management\s+fees?)': 'management_fees',
            r'(?:parking)': 'parking',
            r'(?:laundry)': 'laundry',
            r'(?:late\s+fees?)': 'late_fees'
        }
        
        # Look for monetary values in the text with more flexible patterns
        for pattern, field in financial_terms.items():
            # Look for pattern followed by a value with more flexible matching
            # This pattern matches various formats: $1,234.50, 1,234.50, (1,234.50), -$1,234.50
            matches = re.findall(rf'{pattern}.*?[\$:€£¥]?\s*(-?\(?[\d,]+\.?\d*\)?)', normalized_text, re.IGNORECASE)
            if matches:
                # Take the first match and convert to float
                try:
                    value_str = matches[0]
                    # Handle parentheses for negative values
                    if value_str.startswith('(') and value_str.endswith(')'):
                        value = -float(value_str[1:-1].replace(',', ''))
                    else:
                        value = float(value_str.replace(',', '').replace('$', '').replace('€', '').replace('£', '').replace('¥', ''))
                    result[field] = value
                except ValueError:
                    pass  # Skip if conversion fails
        
        # If we found some financial data, return it
        if len(result) > 2:  # More than just file_name and document_type
            logger.info(f"Extracted {len(result) - 2} financial fields from text response")
            return result
        
        # Try a more aggressive approach - look for any monetary values near financial terms
        financial_categories = {
            'gpr': ['gross potential rent', 'potential rent', 'scheduled rent', 'total revenue', 'gross income'],
            'vacancy_loss': ['vacancy', 'credit loss'],
            'concessions': ['concession', 'free rent'],
            'bad_debt': ['bad debt', 'uncollected rent'],
            'other_income': ['other income', 'parking', 'laundry', 'application fee', 'late fee'],
            'egi': ['effective gross income'],
            'opex': ['operating expense', 'operating cost'],
            'noi': ['net operating income', 'net income']
        }
        
        # Split text into lines for better processing
        lines = normalized_text.split('\n')
        for category, terms in financial_categories.items():
            for term in terms:
                for i, line in enumerate(lines):
                    if term in line:
                        # Look for monetary values in this line and nearby lines
                        search_lines = lines[max(0, i-1):min(len(lines), i+2)]
                        for search_line in search_lines:
                            # Find monetary values
                            money_matches = re.findall(r'(-?\(?[\d,]+\.?\d*\)?)', search_line)
                            for match in money_matches:
                                try:
                                    # Handle parentheses for negative values
                                    if match.startswith('(') and match.endswith(')'):
                                        value = -float(match[1:-1].replace(',', ''))
                                    else:
                                        value = float(match.replace(',', ''))
                                    if category not in result or result[category] == 0.0:
                                        result[category] = value
                                        break
                                except ValueError:
                                    continue
                        if category in result:
                            break
                if category in result:
                    break
        
        # If we found some financial data, return it
        if len(result) > 2:  # More than just file_name and document_type
            logger.info(f"Aggressively extracted {len(result) - 2} financial fields from text response")
            return result
        
        return {}  # Return empty dict if no data found
    except Exception as e:
        logger.warning(f"Error extracting financial data from text: {str(e)}")
        return {}


def extract_text_from_excel(file_content: bytes, file_name: str) -> str:
    """
    Extract text content from Excel file bytes with enhanced structure preservation.
    
    Args:
        file_content: Excel file content as bytes
        file_name: Name of the file
        
    Returns:
        Extracted text content with clear structure for AI parsing
    """
    import pandas as pd
    import io
    
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
                
                # Find the column with numeric values
                numeric_column_idx = -1
                for col_idx in range(len(df.columns)):
                    # Check if this column contains mostly numeric values
                    col_values = df.iloc[:, col_idx]
                    numeric_count = 0
                    total_count = 0
                    for val in col_values:
                        if pd.notna(val):
                            total_count += 1
                            try:
                                float(str(val).replace('$', '').replace(',', '').replace('(', '-').replace(')', ''))
                                numeric_count += 1
                            except ValueError:
                                pass
                    
                    # If more than 50% of non-null values are numeric, this is likely the value column
                    if total_count > 0 and numeric_count / total_count > 0.5:
                        numeric_column_idx = col_idx
                        break
                
                # If we couldn't find a clear numeric column, use the last column
                if numeric_column_idx == -1 and len(df.columns) > 1:
                    numeric_column_idx = len(df.columns) - 1
                
                # Extract data using the identified columns
                category_column_idx = 0  # Assume first column has categories
                
                for idx, row in df.iterrows():
                    # Get values from identified columns
                    category = str(row.iloc[category_column_idx]) if len(row) > category_column_idx and pd.notna(row.iloc[category_column_idx]) else ""
                    
                    # Get amount from the numeric column if available
                    amount = ""
                    if numeric_column_idx != -1 and len(row) > numeric_column_idx:
                        raw_amount = row.iloc[numeric_column_idx]
                        if pd.notna(raw_amount):
                            amount = str(raw_amount)
                    
                    # If no amount in numeric column, try other columns
                    if not amount and numeric_column_idx != -1:
                        for col_idx in range(len(df.columns)):
                            if col_idx != category_column_idx and len(row) > col_idx:
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
                        else:
                            # This might be a header or section marker
                            text_parts.append(f"  SECTION: {category}")
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
    
    # If the result is empty or too short, try a different approach
    if len(result.strip()) < 50:
        # Reset file pointer and try reading with different parameters
        excel_file.seek(0)
        try:
            # Try reading all sheets with header=None to get raw data
            xl = pd.ExcelFile(excel_file)
            sheet_names = xl.sheet_names
            
            text_parts = [f"EXCEL DOCUMENT: {file_name}", "=" * 60, ""]
            for sheet_name in sheet_names:
                excel_file.seek(0)
                # Read without assuming header structure
                df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                text_parts.append(f"[SHEET_START] {sheet_name}")
                text_parts.append("-" * 40)
                text_parts.append("[RAW_DATA_FORMAT]")
                # Format raw data
                table_text = df_raw.to_string(index=False, na_rep='[EMPTY]', max_colwidth=30)
                for line in table_text.split('\n'):
                    text_parts.append(f"  {line}")
                text_parts.append("")
                text_parts.append("[SHEET_END]")
                text_parts.append("")
            
            text_parts.append("[DOCUMENT_END]")
            result = "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"Alternative Excel extraction also failed: {str(e)}")
    
    return result if result.strip() else f"[Excel content from {file_name}]"


def extract_text_from_pdf(file_content: bytes, file_name: str) -> str:
    """
    Extract text content from PDF file bytes with enhanced structure preservation.
    
    Args:
        file_content: PDF file content as bytes
        file_name: Name of the file
        
    Returns:
        Extracted text content with clear structure for AI parsing
    """
    try:
        import pdfplumber
        import io
        
        # Create a temporary file-like object
        pdf_file = io.BytesIO(file_content)
        
        text_parts = [f"PDF DOCUMENT: {file_name}", "=" * 60, ""]
        
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages):
                text_parts.append(f"[PAGE_START] {i+1}")
                text_parts.append("-" * 30)
                
                # Try to extract both text and tables
                page_text = page.extract_text()
                tables = page.extract_tables()
                
                # Add page text if available
                if page_text:
                    # Clean up the text to remove excessive whitespace
                    cleaned_lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                    if cleaned_lines:
                        text_parts.append("[TEXT_CONTENT]")
                        text_parts.extend(cleaned_lines)
                
                # Add tables if found
                if tables:
                    text_parts.append("")
                    text_parts.append("[TABLES_FOUND]")
                    for j, table in enumerate(tables):
                        if table:
                            text_parts.append(f"[TABLE_{j+1}]")
                            for row in table:
                                # Filter out None values and join with clear separators
                                cleaned_row = [str(cell) if cell is not None else "[EMPTY]" for cell in row]
                                text_parts.append("  |  ".join(cleaned_row))
                
                text_parts.append("")
                text_parts.append("[PAGE_END]")
                text_parts.append("")
        
        text_parts.append("[DOCUMENT_END]")
        result = "\n".join(text_parts)
        
        # If result is empty, try alternative extraction method
        if not result.strip():
            pdf_file.seek(0)
            try:
                # Try with different parameters
                text_parts = [f"PDF DOCUMENT: {file_name}", "=" * 60, ""]
                with pdfplumber.open(pdf_file) as pdf:
                    for i, page in enumerate(pdf.pages):
                        text_parts.append(f"[PAGE_START] {i+1}")
                        # Try extracting tables as well
                        tables = page.extract_tables()
                        page_text = page.extract_text()
                        
                        if page_text:
                            # Clean up the text
                            cleaned_lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                            if cleaned_lines:
                                text_parts.append("[TEXT_CONTENT]")
                                text_parts.extend(cleaned_lines)
                        
                        # Add tables if found
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
                text_parts.append("[DOCUMENT_END]")
                result = "\n".join(text_parts)
            except Exception as e:
                logger.warning(f"Alternative PDF extraction also failed: {str(e)}")
        
        return result if result.strip() else f"[PDF content from {file_name}]"
    except Exception as e:
        logger.warning(f"PDF extraction failed, returning placeholder: {str(e)}")
        return f"[PDF content from {file_name}]"


def extract_text_from_csv(file_content: bytes, file_name: str) -> str:
    """
    Extract text content from CSV file bytes with enhanced structure preservation.
    
    Args:
        file_content: CSV file content as bytes
        file_name: Name of the file
        
    Returns:
        Extracted text content with clear structure for AI parsing
    """
    import pandas as pd
    import io
    
    try:
        # Try to detect encoding
        import chardet
        encoding_info = chardet.detect(file_content)
        encoding = encoding_info.get('encoding', 'utf-8') or 'utf-8'  # Ensure we have a valid encoding
        
        # Create a temporary file-like object with detected encoding
        try:
            csv_file = io.StringIO(file_content.decode(encoding))
        except (UnicodeDecodeError, LookupError):
            # Fallback to utf-8 with error handling
            csv_file = io.StringIO(file_content.decode('utf-8', errors='ignore'))
        
        # Read CSV with more flexible parameters
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            # Try with different parameters
            csv_file.seek(0)
            df = pd.read_csv(csv_file, sep=None, engine='python')  # Auto-detect separator
        
        # Format with clear structure
        text_parts = [f"CSV DOCUMENT: {file_name}", "=" * 60, ""]
        
        # Improve DataFrame formatting for better GPT understanding
        if not df.empty:
            # Remove unnamed columns that are typically artifacts
            columns_to_drop = [col for col in df.columns if str(col).startswith('Unnamed:')]
            if columns_to_drop:
                df = df.drop(columns=columns_to_drop)
            
            # Check if this looks like financial data
            first_column_data = df.iloc[:, 0].astype(str).str.lower() if len(df.columns) > 0 else pd.Series([])
            financial_keywords = ['rent', 'income', 'revenue', 'expense', 'tax', 'insurance', 'maintenance', 
                                'utilities', 'management', 'parking', 'laundry', 'fee', 'noi', 'egi', 'operating']
            has_financial_terms = any(
                first_column_data.str.contains(keyword, na=False).any() 
                for keyword in financial_keywords
            )
            
            if has_financial_terms and len(df.columns) >= 2:
                # Format as financial statement
                text_parts.append("[FINANCIAL_STATEMENT_FORMAT]")
                text_parts.append("LINE ITEMS:")
                text_parts.append("")
                
                # Find the column with numeric values
                numeric_column_idx = -1
                for col_idx in range(len(df.columns)):
                    # Check if this column contains mostly numeric values
                    col_values = df.iloc[:, col_idx]
                    numeric_count = 0
                    total_count = 0
                    for val in col_values:
                        if pd.notna(val):
                            total_count += 1
                            try:
                                float(str(val).replace('$', '').replace(',', '').replace('(', '-').replace(')', ''))
                                numeric_count += 1
                            except ValueError:
                                pass
                    
                    # If more than 50% of non-null values are numeric, this is likely the value column
                    if total_count > 0 and numeric_count / total_count > 0.5:
                        numeric_column_idx = col_idx
                        break
                
                # If we couldn't find a clear numeric column, use the last column
                if numeric_column_idx == -1 and len(df.columns) > 1:
                    numeric_column_idx = len(df.columns) - 1
                
                # Extract data using the identified columns
                category_column_idx = 0  # Assume first column has categories
                
                for idx, row in df.iterrows():
                    # Get values from identified columns
                    category = str(row.iloc[category_column_idx]) if len(row) > category_column_idx and pd.notna(row.iloc[category_column_idx]) else ""
                    
                    # Get amount from the numeric column if available
                    amount = ""
                    if numeric_column_idx != -1 and len(row) > numeric_column_idx:
                        raw_amount = row.iloc[numeric_column_idx]
                        if pd.notna(raw_amount):
                            amount = str(raw_amount)
                    
                    # If no amount in numeric column, try other columns
                    if not amount and numeric_column_idx != -1:
                        for col_idx in range(len(df.columns)):
                            if col_idx != category_column_idx and len(row) > col_idx:
                                val = row.iloc[col_idx]
                                if pd.notna(val):
                                    val_str = str(val)
                                    # Check if this looks like a monetary value
                                    if any(char.isdigit() for char in val_str):
                                        amount = val_str
                                        break
                    
                    # Only include rows that have meaningful data
                    if category.strip() and not category.startswith('Unnamed'):
                        category = category.strip()
                        if amount and amount != "nan":
                            # Clean the amount string
                            cleaned_amount = amount.replace('$', '').replace(',', '').strip()
                            text_parts.append(f"  {category}: {cleaned_amount}")
                        else:
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
            text_parts.append("[EMPTY_CSV_FILE]")
        
        text_parts.append("")
        text_parts.append("[DOCUMENT_END]")
        result = "\n".join(text_parts)
        
        return result
    except Exception as e:
        logger.warning(f"CSV extraction failed, falling back to basic decoding: {str(e)}")
        try:
            decoded_text = file_content.decode('utf-8', errors='ignore')
            if decoded_text.strip():
                # Add structure to plain text CSV
                lines = [line.strip() for line in decoded_text.strip().split('\n') if line.strip()]
                if len(lines) > 1:
                    result_parts = [f"CSV DOCUMENT: {file_name}", "=" * 60, ""]
                    result_parts.append("[TEXT_FORMAT]")
                    result_parts.extend(lines)
                    result_parts.append("")
                    result_parts.append("[DOCUMENT_END]")
                    return "\n".join(result_parts)
            return decoded_text if decoded_text.strip() else f"[CSV content from {file_name}]"
        except Exception:
            return f"[CSV content from {file_name}]"


def _format_text_content(text_content: str, file_name: str) -> str:
    """
    Format text content for better GPT parsing with clear structure markers.
    
    Args:
        text_content: Raw text content
        file_name: Name of the file
        
    Returns:
        Formatted text content with structure markers
    """
    if not text_content or not text_content.strip():
        return f"[Text content from {file_name}]"
    
    # Clean up excessive whitespace while preserving structure
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    
    # Add clear document structure
    result_parts = [f"TEXT DOCUMENT: {file_name}", "=" * 60, ""]
    
    # Add section headers for common financial statement sections
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
    
    for line in lines:
        result_parts.append(line)
        # Add section markers for better structure
        for keyword, header in section_headers.items():
            if keyword in line.upper() and header not in line:
                result_parts.append("")
                result_parts.append(header)
                result_parts.append("-" * 25)
    
    result_parts.append("")
    result_parts.append("[DOCUMENT_END]")
    
    # Join lines with appropriate spacing
    formatted_text = "\n".join(result_parts)
    
    return formatted_text


def create_gpt_extraction_prompt(document_text: str, file_name: str, document_type_hint: Optional[str]) -> str:
    """
    Create an enhanced prompt for GPT to extract financial data from structured documents.
    
    Args:
        document_text: The text content of the document
        file_name: Name of the file
        document_type_hint: Hint about document type
        
    Returns:
        Formatted prompt string with enhanced structure recognition
    """
    # Truncate document text if too long
    max_length = 3000  # Limit to prevent token overflow
    if len(document_text) > max_length:
        # Try to preserve the beginning and end which are more likely to contain important info
        start_length = int(max_length * 0.7)
        end_length = max_length - start_length - 50  # 50 for "..."
        document_text = document_text[:start_length] + "... [truncated] ..." + document_text[-end_length:]
    
    # Document type specific instructions
    doc_type_instructions = ""
    if document_type_hint:
        if "budget" in document_type_hint.lower():
            doc_type_instructions = """
Document Type Specific Instructions:
This is a BUDGET document. Focus on projected/forecasted values rather than actual results.
Look for terms like "Budget", "Forecast", "Projected", "Estimated" in the document.
"""
        elif "prior" in document_type_hint.lower():
            doc_type_instructions = """
Document Type Specific Instructions:
This is a PRIOR PERIOD document. Look for historical actual results.
Focus on data from previous months or years.
"""
        else:
            doc_type_instructions = """
Document Type Specific Instructions:
This is a CURRENT PERIOD document. Look for the most recent actual results.
Focus on current month or year data.
"""
    
    prompt = f"""
You are a world-class real estate financial analyst with expertise in extracting data from diverse financial documents. 
Your task is to intelligently extract financial data from the provided property management document, regardless of its format or structure.

DOCUMENT STRUCTURE GUIDE:
The document has been pre-processed with clear structural markers to help you parse it:
- [SHEET_START]/[SHEET_END]: Excel sheet boundaries
- [PAGE_START]/[PAGE_END]: PDF page boundaries  
- [[FINANCIAL_STATEMENT_FORMAT]: Financial data in category: value format
- [TABLE_FORMAT]: Tabular data with headers
- [TEXT_CONTENT]: Plain text content
- SECTION markers: [REVENUE_SECTION], [EXPENSE_SECTION], etc.

Document Information:
- File Name: {file_name}
- Document Type: {document_type_hint or 'Unknown'}
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
   - EGI = GPR - Vacancy Loss - Concessions - Bad Debt + Other Income
   - NOI = EGI - OpEx
8. NEVER leave fields empty - use 0.0 if truly unknown
9. CRITICALLY IMPORTANT: DO NOT return all zero values. If you cannot find specific values, make educated estimates based on context.

REQUIRED JSON STRUCTURE:
{{
  "file_name": "{file_name}",
  "document_type": "{document_type_hint or 'unknown'}",
  "gpr": 0.0,              // Gross Potential Rent (Total potential rental income)
  "vacancy_loss": 0.0,     // Vacancy Loss (Lost income due to vacant units)
  "concessions": 0.0,      // Concessions (Reduced rent given to tenants)
  "bad_debt": 0.0,         // Bad Debt (Uncollected rent)
  "other_income": 0.0,     // Other Income (Parking, laundry, etc.)
  "egi": 0.0,              // Effective Gross Income (GPR - Vacancy - Concessions - Bad Debt + Other Income)
  "opex": 0.0,             // Total Operating Expenses (Sum of all operating expenses)
  "noi": 0.0,              // Net Operating Income (EGI - OpEx)
  "property_taxes": 0.0,   // Property Taxes
  "insurance": 0.0,        // Insurance
  "repairs_maintenance": 0.0,  // Repairs & Maintenance
  "utilities": 0.0,        // Utilities
  "management_fees": 0.0,  // Management Fees
  "parking": 0.0,          // Parking Income
  "laundry": 0.0,          // Laundry Income
  "late_fees": 0.0,        // Late Fees
  "pet_fees": 0.0,         // Pet Fees
  "application_fees": 0.0, // Application Fees
  "storage_fees": 0.0,     // Storage Fees
  "amenity_fees": 0.0,     // Amenity Fees
  "utility_reimbursements": 0.0,  // Utility Reimbursements
  "cleaning_fees": 0.0,    // Cleaning Fees
  "cancellation_fees": 0.0, // Cancellation Fees
  "miscellaneous": 0.0     // Miscellaneous Income
}}

EXTENSIVE FIELD VARIATIONS TO LOOK FOR:
- GPR: Gross Potential Rent, Potential Rent, Scheduled Rent, Total Revenue, Revenue, Gross Income
- Vacancy Loss: Vacancy, Credit Loss, Vacancy and Credit Loss, Turnover Loss
- Concessions: Tenant Concessions, Leasing Concessions, Move-in Concessions, Free Rent
- Bad Debt: Uncollected Rent, Delinquent Rent, Write-offs, Account Receivable Write-offs
- Other Income: Additional Income, Miscellaneous Income, Parking Fees, Laundry Income
- EGI: Effective Gross Income, Net Rental Income, Adjusted Gross Income
- OpEx: Operating Expenses, Total Operating Expenses, Expenses, Operating Costs
- NOI: Net Operating Income, Net Income, Operating Income, Property Net Income

NEGATIVE VALUE FORMATS:
Convert these formats to negative numbers:
- (1,234.50) → -1234.50
- (1234.50) → -1234.50  
- -$1,234.50 → -1234.50
- -1,234.50 → -1234.50

CALCULATION RULES (Use if not explicitly provided):
- EGI = GPR - Vacancy Loss - Concessions - Bad Debt + Other Income
- NOI = EGI - OpEx
- If you find individual expense items, sum them to calculate OpEx
- If you find individual income items, sum them to calculate GPR

RETURN ONLY the JSON object with the extracted values. Do not include any other text, explanations, or formatting.
Make sure all fields are present with numeric values. DO NOT return all zero values - make educated estimates when needed.
"""
    
    return prompt


def validate_and_enrich_extraction_result(result: Dict[str, Any], file_name: str, document_type: Optional[str]) -> Dict[str, Any]:
    """
    Validate and enrich extraction results with fallback values for missing data.
    
    Args:
        result: Raw extraction result from API
        file_name: Name of the processed file
        document_type: Type of document processed
        
    Returns:
        Validated and enriched extraction result
    """
    logger.info(f"Validating extraction result for {file_name}")
    
    # Normalise field names first so downstream logic is consistent
    result = normalize_field_names(result)
    
    # Ensure required fields exist with safe defaults
    enriched_result = {
        "file_name": safe_string(file_name),
        "document_type": safe_string(document_type) or determine_document_type(file_name, result),
        "extraction_timestamp": time.time(),
        "extraction_method": "api",
        **result  # Include all original data
    }
    
    # Validate financial fields and provide safe defaults
    financial_fields = MAIN_METRICS + OPEX_COMPONENTS + INCOME_COMPONENTS
    
    missing_fields = []
    for field in financial_fields:
        if field not in enriched_result or enriched_result[field] is None:
            enriched_result[field] = 0.0
            missing_fields.append(field)
        else:
            # Ensure numeric fields are properly converted
            enriched_result[field] = safe_float(enriched_result[field])
    
    if missing_fields:
        logger.warning(
            f"Missing financial fields filled with defaults",
            extra={
                "file_name": file_name,
                "missing_fields": missing_fields
            }
        )
        # Log the actual fields that were returned
        logger.info(
            f"Fields actually returned by GPT: {list(result.keys())}",
            extra={
                "file_name": file_name
            }
        )
    
    # Validate financial calculations with more robust logic
    try:
        # Get individual income components
        gpr = enriched_result["gpr"]
        vacancy_loss = enriched_result["vacancy_loss"]
        concessions = enriched_result["concessions"]
        bad_debt = enriched_result["bad_debt"]
        other_income = enriched_result["other_income"]
        
        # Calculate EGI
        calculated_egi = gpr - vacancy_loss - concessions - bad_debt + other_income
        
        # Always update EGI if we have meaningful GPR data
        if gpr > 0 or abs(calculated_egi - enriched_result["egi"]) > 1.0:
            if abs(calculated_egi - enriched_result["egi"]) > 1.0:
                logger.info(f"EGI calculation updated: reported={enriched_result['egi']:.2f}, calculated={calculated_egi:.2f} (GPR={gpr:.2f} - Vacancy={vacancy_loss:.2f} - Concessions={concessions:.2f} - BadDebt={bad_debt:.2f} + OtherIncome={other_income:.2f})")
            enriched_result["egi"] = calculated_egi
            
        egi = enriched_result["egi"]
        opex = enriched_result["opex"]
        calculated_noi = egi - opex
        
        # Always validate and correct NOI calculation
        if gpr > 0 or egi != 0 or opex > 0 or abs(calculated_noi - enriched_result["noi"]) > 1.0:
            # Special check for the case where NOI is reported as negative operating expenses
            if abs(enriched_result["noi"] + opex) < 1.0 and egi > 0:
                logger.info(f"NOI calculation corrected: reported={enriched_result['noi']:.2f}, should be EGI-OpEx={calculated_noi:.2f}")
                enriched_result["noi"] = calculated_noi
            elif abs(calculated_noi - enriched_result["noi"]) > 1.0:
                logger.info(f"NOI calculation updated: reported={enriched_result['noi']:.2f}, calculated={calculated_noi:.2f} (EGI={egi:.2f} - OpEx={opex:.2f})")
                enriched_result["noi"] = calculated_noi
            
    except Exception as e:
        logger.warning(f"Error validating financial calculations: {str(e)}")
    
    # Log the final result structure for debugging
    logger.info(
        f"Final extraction result keys: {list(enriched_result.keys())}",
        extra={
            "file_name": file_name
        }
    )
    
    return enriched_result


def create_fallback_extraction_result(file_name: str, document_type: Optional[str], error_reason: str) -> Dict[str, Any]:
    """
    Create a fallback extraction result when API extraction fails.
    
    Args:
        file_name: Name of the file that failed to process
        document_type: Type of document
        error_reason: Reason for the fallback
        
    Returns:
        Fallback extraction result with empty financial data
    """
    logger.info(
        f"Creating fallback extraction result",
        extra={
            "file_name": file_name,
            "document_type": document_type,
            "error_reason": error_reason
        }
    )
    
    fallback_result = create_fallback_financial_data()
    fallback_result.update({
        "file_name": safe_string(file_name),
        "document_type": safe_string(document_type) or determine_document_type(file_name, {}),
        "extraction_timestamp": time.time(),
        "extraction_method": "fallback",
        "extraction_status": "failed",
        "fallback_reason": safe_string(error_reason),
        "requires_manual_entry": True,
        "user_message": f"Automatic extraction failed for {file_name}. Please enter data manually or try uploading again."
    })
    
    return fallback_result

# Define determine_document_type locally to avoid circular imports
def determine_document_type(filename: str, result: Dict[str, Any]) -> str:
    """
    Determine the document type based on filename and content

    Args:
        filename: Name of the file
        result: Extraction result

    Returns:
        Document type (current_month, prior_month, budget, prior_year)
    """
    filename = filename.lower()

    # Try to determine from filename first
    if "budget" in filename:
        return "budget"
    elif "prior" in filename or "previous" in filename:
        if "year" in filename:
            return "prior_year"
        else:
            return "prior_month"
    elif "current" in filename or "actual" in filename:
        return "current_month"

    # If not determined from filename, try to use document_type from result
    doc_type = result.get("document_type", "").lower()
    if "budget" in doc_type:
        return "budget"
    elif "prior year" in doc_type or "previous year" in doc_type:
        return "prior_year"
    elif "prior" in doc_type or "previous" in doc_type:
        return "prior_month"
    elif "current" in doc_type or "actual" in doc_type:
        return "current_month"

    # Default to current_month if can't determine
    return "current_month"

def extract_data_from_documents(
    current_month_file: Optional[BinaryIO] = None,
    prior_month_file: Optional[BinaryIO] = None,
    budget_file: Optional[BinaryIO] = None,
    prior_year_file: Optional[BinaryIO] = None
) -> Dict[str, Any]:
    """
    Extract data from financial documents using the extraction API.
    
    Args:
        current_month_file: Current month actuals file
        prior_month_file: Prior month actuals file
        budget_file: Budget file
        prior_year_file: Prior year actuals file
        
    Returns:
        Dictionary with extracted data
    """
    logger.info("Extracting data from multiple documents")
    
    results = {}
    
    # Process current month file (required)
    if current_month_file:
        logger.info(f"Processing current month file: {getattr(current_month_file, 'name', 'unknown')}")
        current_result = extract_noi_data(current_month_file, "current_month_actuals")
        if "error" not in current_result:
            results["current_month"] = current_result
        else:
            logger.error(f"Error processing current month file: {current_result.get('error')}")
            results["error"] = current_result.get('error')
    
    # Process prior month file (optional)
    if prior_month_file:
        logger.info(f"Processing prior month file: {getattr(prior_month_file, 'name', 'unknown')}")
        prior_result = extract_noi_data(prior_month_file, "prior_month_actuals")
        if "error" not in prior_result:
            results["prior_month"] = prior_result
        else:
            logger.warning(f"Error processing prior month file: {prior_result.get('error')}")
    
    # Process budget file (optional)
    if budget_file:
        logger.info(f"Processing budget file: {getattr(budget_file, 'name', 'unknown')}")
        budget_result = extract_noi_data(budget_file, "current_month_budget")
        if "error" not in budget_result:
            results["budget"] = budget_result
        else:
            logger.warning(f"Error processing budget file: {budget_result.get('error')}")
    
    # Process prior year file (optional)
    if prior_year_file:
        logger.info(f"Processing prior year file: {getattr(prior_year_file, 'name', 'unknown')}")
        prior_year_result = extract_noi_data(prior_year_file, "prior_year_actuals")
        if "error" not in prior_year_result:
            results["prior_year"] = prior_year_result
        else:
            logger.warning(f"Error processing prior year file: {prior_year_result.get('error')}")
    
    return results

def process_uploaded_files(
    current_month_file: Optional[BinaryIO] = None,
    prior_month_file: Optional[BinaryIO] = None,
    budget_file: Optional[BinaryIO] = None,
    prior_year_file: Optional[BinaryIO] = None
) -> Dict[str, Any]:
    """
    Process uploaded files and extract data.
    
    Args:
        current_month_file: Current month actuals file
        prior_month_file: Prior month actuals file
        budget_file: Budget file
        prior_year_file: Prior year actuals file
        
    Returns:
        Dictionary with extracted data
    """
    logger.info("Processing uploaded files")
    
    # Check if current month file is provided
    if not current_month_file:
        logger.warning("Current month file is required but not provided")
        return {
            'error': "Current month file is required"
        }
    
    # Create temporary files to ensure file-like objects with proper names
    temp_files = {}
    file_mapping = {
        'current_month_actuals': current_month_file,
        'prior_month_actuals': prior_month_file,
        'current_month_budget': budget_file,
        'prior_year_actuals': prior_year_file
    }
    
    try:
        # Create temporary files
        for key, file in file_mapping.items():
            if file is not None:
                # Get file extension
                file_name = getattr(file, 'name', '')
                _, ext = os.path.splitext(file_name)
                
                # Create temporary file with proper extension
                temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                temp_file.write(file.read())
                temp_file.flush()
                temp_file.close()
                
                # Reopen file for reading
                temp_files[key] = open(temp_file.name, 'rb')
                logger.info(f"Created temporary file for {key}: {temp_file.name}")
        
        # Extract data from documents
        result = extract_data_from_documents(
            current_month_file=temp_files.get('current_month_actuals'),
            prior_month_file=temp_files.get('prior_month_actuals'),
            budget_file=temp_files.get('current_month_budget'),
            prior_year_file=temp_files.get('prior_year_actuals')
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing uploaded files: {str(e)}")
        return {
            'error': f"Error processing uploaded files: {str(e)}"
        }
    
    finally:
        # Close and remove temporary files
        for file in temp_files.values():
            try:
                file_path = file.name
                file.close()
                os.unlink(file_path)
                logger.info(f"Removed temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Error removing temporary file: {str(e)}")




