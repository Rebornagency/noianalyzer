import os
import logging
import requests
import json
import tempfile
import time
from typing import Dict, Any, List, Optional, BinaryIO, Union
import streamlit as st
from config import get_extraction_api_url, get_api_key
from constants import ERROR_MESSAGES, DEFAULT_API_CONFIG, FILE_UPLOAD_CONFIG, MAIN_METRICS, OPEX_COMPONENTS
from utils.error_handler import setup_logger, handle_errors, graceful_degradation, APIError
from utils.common import safe_float, safe_string, create_fallback_financial_data, normalize_field_names

# Setup logger
logger = setup_logger(__name__)

@graceful_degradation(
    fallback_value={"error": "Data extraction service temporarily unavailable. Please try manual entry or check back later."},
    operation_name="document data extraction"
)
@handle_errors(default_return={"error": "Failed to extract data from document"})
def extract_noi_data(file: Any, document_type_hint: Optional[str] = None, 
                    api_url: Optional[str] = None, api_key: Optional[str] = None,
                    max_retries: int = None, retry_delay: int = 5) -> Dict[str, Any]:
    """
    Extract NOI data from a document using the extraction API with enhanced error handling.
    
    Args:
        file: Document file to process
        document_type_hint: Optional hint about document type
        api_url: Optional API URL override
        api_key: Optional API key override
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
        f"Starting data extraction",
        extra={
            "file_name": file_name,
            "document_type_hint": document_type_hint,
            "max_retries": max_retries
        }
    )
    
    # Get API URL and API key from config if not provided
    if api_url is None:
        api_url = get_extraction_api_url()
    # Normalise URL: remove trailing slashes and ensure single /extract suffix
    if api_url:
        api_url = api_url.rstrip('/')
        if not api_url.endswith('/extract'):
            api_url = f"{api_url}/extract"
    
    if api_key is None:
        api_key = get_api_key()
    
    # Validate API configuration
    if not api_url:
        logger.error("Extraction API URL not configured")
        raise APIError(ERROR_MESSAGES["API_CONFIGURATION_MISSING"])
    
    if not api_key:
        logger.error("Extraction API key not configured")
        raise APIError(ERROR_MESSAGES["API_KEY_MISSING"])
    
    logger.info(
        f"API configuration validated",
        extra={
            "api_url": api_url,
            "api_key_length": len(api_key)
        }
    )
    
    # Prepare files for API request with validation
    try:
        file_content = file.getvalue()
        # Size guardrail (bytes)
        max_size_bytes = FILE_UPLOAD_CONFIG.get("MAX_FILE_SIZE", 200) * 1024 * 1024
        if len(file_content) > max_size_bytes:
            logger.error(f"Uploaded file exceeds size limit: {len(file_content)} bytes")
            raise APIError("Uploaded file too large (limit {} MB)".format(FILE_UPLOAD_CONFIG.get("MAX_FILE_SIZE", 200)))
        file_type = getattr(file, 'type', 'application/octet-stream')
        files = {"file": (file_name, file_content, file_type)}
        
        logger.info(
            f"File prepared for upload",
            extra={
                "file_size": len(file_content),
                "file_type": file_type
            }
        )
    except Exception as e:
        logger.error(f"Error preparing file for upload: {str(e)}")
        raise APIError(f"Failed to prepare file for upload: {str(e)}")
    
    # Prepare headers with API key
    headers = {"x-api-key": api_key, "Accept": "application/json"}
    
    # Prepare data with document type hint if provided
    data = {}
    if document_type_hint:
        data["document_type"] = safe_string(document_type_hint)
    
    # Retry logic with enhanced error handling
    last_error = None
    for attempt in range(max_retries):
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
            spinner_message = f"Extracting data from {file_name} (attempt {attempt+1}/{max_retries})..."
            
            if hasattr(st, 'spinner'):
                with st.spinner(spinner_message):
                    response = requests.post(
                        api_url, 
                        files=files, 
                        data=data, 
                        headers=headers, 
                        timeout=DEFAULT_API_CONFIG["TIMEOUT"]
                    )
            else:
                response = requests.post(
                    api_url, 
                    files=files, 
                    data=data, 
                    headers=headers, 
                    timeout=DEFAULT_API_CONFIG["TIMEOUT"]
                )
            
            attempt_time = time.time() - attempt_start_time
            logger.info(
                f"API request completed",
                extra={
                    "status_code": response.status_code,
                    "response_time": f"{attempt_time:.3f}s",
                    "attempt": attempt + 1
                }
            )
            
            # Handle successful response
            if response.status_code == 200:
                try:
                    result = response.json()
                    
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
                    
                except json.JSONDecodeError as e:
                    logger.error(f"API returned invalid JSON: {str(e)}")
                    last_error = APIError("API returned invalid JSON response")
                    
                    # Don't retry JSON decode errors
                    if attempt == max_retries - 1:
                        # Return fallback data for invalid JSON
                        return create_fallback_extraction_result(file_name, document_type_hint, "Invalid API response format")
                    
            elif response.status_code == 502:
                # Bad Gateway - temporary server issue, definitely retry
                error_msg = f"Server temporarily unavailable (502)"
                logger.warning(
                    error_msg,
                    extra={
                        "file_name": file_name,
                        "response_text": response.text[:200]
                    }
                )
                last_error = APIError(error_msg)
                
            elif response.status_code >= 500:
                # Server error, might be temporary
                error_msg = f"Server error (status {response.status_code})"
                logger.error(
                    error_msg,
                    extra={
                        "file_name": file_name,
                        "status_code": response.status_code,
                        "response_text": response.text[:200]
                    }
                )
                last_error = APIError(error_msg)
                
            else:
                # Client error or other error, don't retry
                error_msg = f"API request failed (status {response.status_code})"
                logger.error(
                    error_msg,
                    extra={
                        "file_name": file_name,
                        "status_code": response.status_code,
                        "response_text": response.text[:200]
                    }
                )
                
                # Return fallback for client errors
                return create_fallback_extraction_result(file_name, document_type_hint, error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out (attempt {attempt+1})"
            logger.warning(error_msg, extra={"file_name": file_name})
            last_error = APIError("Request timeout")
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error (attempt {attempt+1})"
            logger.warning(error_msg, extra={"file_name": file_name})
            last_error = APIError("Connection error")
            
        except Exception as e:
            error_msg = f"Unexpected error during extraction: {str(e)}"
            logger.error(error_msg, exc_info=True, extra={"file_name": file_name})
            last_error = APIError(error_msg)
        
        # Wait before retry (except on last attempt)
        if attempt < max_retries - 1:
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
        calculated_egi = enriched_result["gpr"] - enriched_result["vacancy_loss"] + enriched_result["other_income"]
        if abs(calculated_egi - enriched_result["egi"]) > 1.0:
            logger.warning(f"EGI calculation mismatch detected, using calculated value")
            enriched_result["egi"] = calculated_egi
            
        calculated_noi = enriched_result["egi"] - enriched_result["opex"]
        if abs(calculated_noi - enriched_result["noi"]) > 1.0:
            logger.warning(f"NOI calculation mismatch detected, using calculated value")
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
