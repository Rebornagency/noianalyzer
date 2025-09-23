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
    Extract financial data from document content using GPT.
    
    Args:
        file_content: The content of the file as bytes
        file_name: Name of the file
        document_type_hint: Hint about document type
        openai_api_key: OpenAI API key
        
    Returns:
        Dictionary containing extracted financial data
    """
    text_content = None
    
    # Try to use the preprocessing module if available
    try:
        # Import the preprocessing module here to avoid circular imports
        from preprocessing_module import FilePreprocessor
        
        # Create a temporary file to process with the preprocessing module
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1] or '.tmp') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Use the preprocessing module to extract text content
            preprocessor = FilePreprocessor()
            preprocessed_data = preprocessor.preprocess(temp_file_path, filename=file_name)
            
            # Extract text content from preprocessed data
            if 'combined_text' in preprocessed_data:
                text_content = preprocessed_data['combined_text']
            elif 'content' in preprocessed_data and isinstance(preprocessed_data['content'], dict):
                content = preprocessed_data['content']
                if 'combined_text' in content:
                    text_content = content['combined_text']
                elif 'text' in content:
                    if isinstance(content['text'], list):
                        # Handle PDF text extraction
                        text_content = '\n\n'.join([page.get('content', '') for page in content['text']])
                    else:
                        text_content = content['text']
                elif 'text_representation' in content:
                    # Handle Excel/CSV text representation
                    if isinstance(content['text_representation'], list):
                        text_content = '\n\n'.join(content['text_representation'])
                    else:
                        text_content = str(content['text_representation'])
                else:
                    text_content = str(content)
            else:
                text_content = str(preprocessed_data.get('content', ''))
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
                
    except ImportError as e:
        # If preprocessing module is not available, log and continue with basic text decoding
        logger.warning(f"Preprocessing module not available: {str(e)}")
    except Exception as e:
        # If preprocessing fails, log and fall back to simple text decoding
        logger.warning(f"Preprocessing failed, falling back to text decoding: {str(e)}")
    
    # If we couldn't extract text content through preprocessing, try basic text decoding
    if text_content is None:
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
        except Exception:
            text_content = f"[Document content from {file_name}]"
    
    # If text content is still empty, fall back to file name
    if not text_content.strip():
        text_content = f"[Document content from {file_name}]"
    
    # Create the prompt for GPT
    prompt = create_gpt_extraction_prompt(text_content, file_name, document_type_hint)
    
    # Prepare messages for chat completion
    messages = [
        {"role": "system", "content": "You are a senior real estate financial analyst specializing in extracting financial data from property management documents. You are meticulous and accurate."},
        {"role": "user", "content": prompt}
    ]
    
    logger.info(f"Sending extraction prompt to GPT (length: {len(prompt)} chars)")
    
    try:
        # Call OpenAI API
        response_content = chat_completion(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=2000
        )
        
        logger.info(f"Received response from GPT (length: {len(response_content)} chars)")
        
        # Parse the JSON response
        try:
            # Extract JSON from response if it's wrapped in other text
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
            logger.error(f"Response content: {response_content}")
            raise APIError("GPT returned invalid JSON response")
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise APIError(f"Failed to extract data using GPT: {str(e)}")


def create_gpt_extraction_prompt(document_text: str, file_name: str, document_type_hint: Optional[str]) -> str:
    """
    Create a prompt for GPT to extract financial data from document text.
    
    Args:
        document_text: The text content of the document
        file_name: Name of the file
        document_type_hint: Hint about document type
        
    Returns:
        Formatted prompt string
    """
    # Truncate document text if too long
    max_length = 3000  # Limit to prevent token overflow
    if len(document_text) > max_length:
        document_text = document_text[:max_length] + "... [truncated]"
    
    prompt = f"""
Extract financial data from the following property management document and return it as a JSON object.

Document Information:
- File Name: {file_name}
- Document Type: {document_type_hint or 'Unknown'}

Document Content:
{document_text}

Instructions:
1. Extract all financial metrics and return them in the exact JSON structure shown below
2. All monetary values must be numeric (no currency symbols, commas, or text)
3. If a value is not found, use 0.0
4. Ensure all field names match exactly as specified
5. Calculate derived values (EGI, NOI) if not explicitly provided
6. Be flexible with field names - look for synonyms and variations

Required JSON Structure:
{{
  "file_name": "{file_name}",
  "document_type": "{document_type_hint or 'unknown'}",
  "gpr": 0.0,              // Gross Potential Rent
  "vacancy_loss": 0.0,     // Vacancy Loss
  "concessions": 0.0,      // Concessions
  "bad_debt": 0.0,         // Bad Debt
  "other_income": 0.0,     // Other Income
  "egi": 0.0,              // Effective Gross Income (calculate if not provided)
  "opex": 0.0,             // Total Operating Expenses
  "noi": 0.0,              // Net Operating Income (calculate if not provided)
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

Common Field Variations to Look For:
- GPR: Gross Potential Rent, Potential Rent, Scheduled Rent, Total Revenue, Revenue, Gross Income
- Vacancy Loss: Vacancy, Credit Loss, Vacancy and Credit Loss
- Other Income: Additional Income, Miscellaneous Income
- OpEx: Operating Expenses, Total Operating Expenses, Expenses
- NOI: Net Operating Income, Net Income, Operating Income

Calculation Rules:
- EGI = GPR - Vacancy Loss - Concessions - Bad Debt + Other Income
- NOI = EGI - OpEx

Return ONLY the JSON object with the extracted values. Do not include any other text, explanations, or formatting.
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
    financial_fields = MAIN_METRICS + OPEX_COMPONENTS
    
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
    
    # Validate financial calculations
    try:
        gpr = enriched_result["gpr"]
        vacancy_loss = enriched_result["vacancy_loss"]
        concessions = enriched_result["concessions"]
        bad_debt = enriched_result["bad_debt"]
        other_income = enriched_result["other_income"]
        calculated_egi = gpr - vacancy_loss - concessions - bad_debt + other_income
        
        # Always update EGI if we have meaningful GPR data, regardless of mismatch threshold
        if gpr > 0 or abs(calculated_egi - enriched_result["egi"]) > 1.0:
            if abs(calculated_egi - enriched_result["egi"]) > 1.0:
                logger.warning(f"EGI calculation mismatch detected: reported={enriched_result['egi']:.2f}, calculated={calculated_egi:.2f} (GPR={gpr:.2f} - Vacancy={vacancy_loss:.2f} - Concessions={concessions:.2f} - BadDebt={bad_debt:.2f} + OtherIncome={other_income:.2f})")
            enriched_result["egi"] = calculated_egi
            
        egi = enriched_result["egi"]
        opex = enriched_result["opex"]
        calculated_noi = egi - opex
        
        # Always validate and correct NOI calculation, especially when it's negative operating expenses
        if gpr > 0 or egi != 0 or opex > 0 or abs(calculated_noi - enriched_result["noi"]) > 1.0:
            # Special check for the case where NOI is reported as negative operating expenses
            if abs(enriched_result["noi"] + opex) < 1.0 and egi > 0:
                logger.warning(f"NOI appears to be reported as negative operating expenses: reported={enriched_result['noi']:.2f}, should be EGI-OpEx={calculated_noi:.2f}")
                enriched_result["noi"] = calculated_noi
            elif abs(calculated_noi - enriched_result["noi"]) > 1.0:
                logger.warning(f"NOI calculation mismatch detected: reported={enriched_result['noi']:.2f}, calculated={calculated_noi:.2f} (EGI={egi:.2f} - OpEx={opex:.2f})")
                enriched_result["noi"] = calculated_noi
            
    except Exception as e:
        logger.warning(f"Error validating financial calculations: {str(e)}")
    
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
