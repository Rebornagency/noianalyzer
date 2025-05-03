import requests
import json
import logging
import time
import traceback
import streamlit as st
from typing import Dict, Any, Optional, Tuple, List

from config import get_extraction_api_url, get_api_key
from utils.helpers import format_for_noi_comparison

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ai_extraction')


def extract_single_document(
        file: Any,
        document_type_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Extract DETAILED NOI data from a single file using the ENHANCED extraction API.

    Args:
        file: Uploaded file object (from Streamlit).
        document_type_hint: Optional hint from the UI (e.g., 'current_month_actuals').

    Returns:
        Extracted detailed data structure or None if extraction failed.
    """
    # Validate input parameters
    if file is None:
        st.error("No file provided for extraction.")
        logger.error("extract_single_document called with None file parameter")
        return None
        
    # Use direct API URL from config and append /extract endpoint
    base_api_url = get_extraction_api_url()
    if not base_api_url:
        api_url = "https://dataextractionai.onrender.com/extract"
        logger.warning(f"No API URL configured, using default: {api_url}")
    else:
        # Ensure the URL ends with /extract
        if base_api_url.endswith('/'):
            api_url = f"{base_api_url}extract"
        else:
            api_url = f"{base_api_url}/extract"
        logger.info(f"Using extraction API URL: {api_url}")
    
    api_key = get_api_key()
    if not api_key or len(api_key) < 5:
        st.error("Extraction API Key is not configured correctly in settings.")
        logger.error("Missing or invalid extraction API key.")
        return None

    logger.info(
        f"Extracting detailed data from {file.name} using API: {api_url}")
    logger.info(f"Document type hint provided: {document_type_hint}")

    # Initialize UI elements
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text(f"🚀 Sending {file.name} for detailed extraction...")

    try:
        # Validate file type
        valid_extensions = ['.pdf', '.xlsx', '.xls', '.csv']
        file_extension = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
        if file_extension not in valid_extensions:
            error_msg = f"Unsupported file type: {file_extension}. Please upload PDF, XLSX, XLS, or CSV files."
            status_text.error(f"❌ {error_msg}")
            progress_bar.empty()
            st.error(error_msg)
            logger.error(f"Invalid file type: {file_extension} for file {file.name}")
            return None

        # Prepare form data
        files_payload = {"file": (file.name, file.getvalue(), file.type)}
        data_payload = {}
        if document_type_hint:
            data_payload['document_type'] = document_type_hint

        # Prepare headers with correct API key format
        headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }

        # Send request to API with proper error handling
        response, error = send_api_request(
            api_url=api_url,
            files_payload=files_payload,
            data_payload=data_payload,
            headers=headers,
            file_name=file.name,
            progress_bar=progress_bar,
            status_text=status_text
        )
        
        if error:
            return None
            
        # Process successful response
        progress_bar.progress(100)
        status_text.success(f"✅ Detailed extraction complete for {file.name}!")
        time.sleep(1)  # Allow user to see success message
        status_text.empty()  # Clear status text
        progress_bar.empty()  # Clear progress bar

        result = response.json()
        logger.info(f"Successfully extracted detailed data from {file.name}")
        
        # Validate response structure
        if not isinstance(result, dict):
            st.error(f"Invalid response format for {file.name}: expected dictionary, got {type(result)}")
            logger.error(f"Invalid response format: {type(result)}")
            return None
            
        # Check for error in response
        if 'error' in result and result['error']:
            st.error(f"Extraction error for {file.name}: {result['error']}")
            logger.error(f"Extraction error in response: {result['error']}")
            return None
            
        # Log warnings from backend if present
        if 'validation_warnings' in result:
            logger.warning(
                f"Backend validation warnings for {file.name}: {result['validation_warnings']}"
            )
            # Check if validation_warnings is an iterable before joining
            if isinstance(result['validation_warnings'], list):
                st.warning(
                    f"Data validation warnings for {file.name}: {'; '.join(result['validation_warnings'])}"
                )
            else:
                # Handle case where validation_warnings is not a list
                st.warning(
                    f"Data validation warnings for {file.name}: {result['validation_warnings']}"
                )
                
        # Log detailed response structure for debugging
        logger.info(f"Response keys: {list(result.keys())}")
        if 'financials' in result:
            logger.info(f"Financials keys: {list(result['financials'].keys())}")
            
        return result

    except Exception as e:
        handle_extraction_exception(e, file.name, progress_bar, status_text)
        return None
    finally:
        # Ensure UI elements are cleaned up
        if 'progress_bar' in locals() and progress_bar is not None:
            progress_bar.empty()
        if 'status_text' in locals() and status_text is not None:
            status_text.empty()


def send_api_request(
        api_url: str,
        files_payload: Dict,
        data_payload: Dict,
        headers: Dict,
        file_name: str,
        progress_bar: Any,
        status_text: Any
) -> Tuple[Optional[requests.Response], Optional[str]]:
    """
    Send request to extraction API with proper error handling.
    
    Args:
        api_url: URL of the extraction API
        files_payload: Files to upload
        data_payload: Additional form data
        headers: Request headers
        file_name: Name of the file being processed
        progress_bar: Streamlit progress bar
        status_text: Streamlit text element for status updates
        
    Returns:
        Tuple of (response, error_message)
    """
    try:
        progress_bar.progress(30)
        # Log request details for debugging
        logger.info(
            f"Sending POST to {api_url} with headers: {list(headers.keys())}, data_payload: {data_payload.keys() if data_payload else 'empty'}"
        )

        response = requests.post(
            api_url,
            files=files_payload,
            data=data_payload,  # Send type hint as form data
            headers=headers,
            timeout=120  # Increase timeout for potentially longer AI processing
        )
        progress_bar.progress(70)
        status_text.text("Processing API response...")

        # Check if request was successful
        if response.status_code == 200:
            return response, None
        else:
            logger.error(
                f"API error ({file_name}): {response.status_code} - {response.text}"
            )
            try:
                # Try to parse error detail from JSON response
                error_detail = response.json().get("detail", response.text)
            except json.JSONDecodeError:
                error_detail = response.text
                
            error_message = f"API Error ({response.status_code}) for {file_name}: {error_detail}"
            st.error(error_message)
            status_text.error(f"❌ Extraction failed for {file_name}.")
            progress_bar.empty()
            
            # Provide more helpful error messages based on status code
            if response.status_code == 401 or response.status_code == 403:
                st.error("Authentication error: Please check your API key in the settings.")
            elif response.status_code == 404:
                st.error("API endpoint not found: Please check the extraction API URL in the settings.")
            elif response.status_code == 413:
                st.error("File too large: Please try with a smaller file or contact support.")
            elif response.status_code >= 500:
                st.error("Server error: The extraction service is experiencing issues. Please try again later.")
                
            return None, error_message
            
    except requests.exceptions.Timeout:
        error_message = f"Request timed out processing {file_name}. The server might be busy or the file too complex."
        logger.error(f"Request timed out while processing {file_name}")
        st.error(error_message)
        status_text.error(f"❌ Timeout during extraction for {file_name}.")
        progress_bar.empty()
        return None, error_message
        
    except requests.exceptions.ConnectionError:
        error_message = f"Connection Error: Could not connect to the API at {api_url}. Is the backend running?"
        logger.error(f"Connection error. Could not connect to the extraction API at {api_url}")
        st.error(error_message)
        status_text.error(f"❌ Connection error for {file_name}.")
        progress_bar.empty()
        return None, error_message
        
    except Exception as e:
        error_message = f"An unexpected error occurred during API request for {file_name}: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        st.error(error_message)
        status_text.error(f"❌ Error during API request for {file_name}.")
        progress_bar.empty()
        return None, error_message


def handle_extraction_exception(
        exception: Exception,
        file_name: str,
        progress_bar: Any,
        status_text: Any
) -> None:
    """
    Handle exceptions during extraction process.
    
    Args:
        exception: The exception that occurred
        file_name: Name of the file being processed
        progress_bar: Streamlit progress bar
        status_text: Streamlit text element for status updates
    """
    error_message = f"Error extracting data ({file_name}): {str(exception)}"
    error_type = type(exception).__name__
    
    logger.error(error_message)
    logger.error(traceback.format_exc())
    
    # Provide more specific error messages based on exception type
    if error_type == "JSONDecodeError":
        user_message = f"Invalid response format from API. The extraction service returned an invalid response."
    elif error_type == "FileNotFoundError":
        user_message = f"File not found: {file_name}. Please try uploading again."
    elif error_type == "PermissionError":
        user_message = f"Permission error accessing file: {file_name}."
    elif error_type == "MemoryError":
        user_message = f"Out of memory processing file: {file_name}. The file may be too large."
    else:
        user_message = f"An unexpected error occurred during extraction for {file_name}: {str(exception)}"
    
    st.error(user_message)
    status_text.error(f"❌ Error during extraction for {file_name}.")
    
    if progress_bar is not None:
        progress_bar.empty()

# THIS IS THE FUNCTION NEEDED TO FIX THE IMPORT ERROR
# We renamed the original function to extract_single_document to avoid recursion
def extract_noi_data(document_files: List[Any], api_url: Optional[str] = None, 
                    api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract NOI data from multiple documents using the extraction API.
    
    Args:
        document_files: List of document files to process
        api_url: Optional API URL override
        api_key: Optional API key override
        
    Returns:
        Dictionary containing extracted financial data for each file
    """
    logger.info(f"Extracting NOI data from {len(document_files)} documents")
    
    results = {}
    
    for doc_file in document_files:
        # Process each document using the single document function
        result = extract_single_document(doc_file)
        
        if result:
            logger.info(f"Successfully extracted data from {doc_file.name}")
            results[doc_file.name] = result
        else:
            logger.warning(f"Failed to extract data from {doc_file.name}")
            results[doc_file.name] = {"error": "Extraction failed"}
    
    return results
