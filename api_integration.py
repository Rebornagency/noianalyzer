import streamlit as st
import requests
import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple

from config import get_extraction_api_url, get_api_key, get_max_retries, get_api_timeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api_integration')

def call_extraction_api(
    file: Any,
    document_type_hint: Optional[str] = None,
    progress_callback=None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Call the extraction API with improved retry logic and enhanced error handling.
    
    Args:
        file: Uploaded file object (from Streamlit)
        document_type_hint: Optional hint for document type
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Tuple of (result, error_message)
    """
    # Validate input parameters
    if file is None:
        logger.error("No file provided for extraction")
        return None, "No file provided for extraction"
        
    # Get API configuration
    api_url = get_extraction_api_url()
    api_key = get_api_key()
    max_retries = get_max_retries()
    timeout = get_api_timeout()
    
    if not api_url:
        logger.error("Extraction API URL is not configured")
        return None, "Extraction API URL is not configured"
        
    if not api_key:
        logger.error("Extraction API key is not configured")
        return None, "Extraction API key is not configured"
    
    # Prepare request data
    files_payload = {"file": (file.name, file.getvalue(), file.type)}
    data_payload = {}
    if document_type_hint:
        data_payload['document_type'] = document_type_hint
        
    # Prepare headers
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    
    # Initialize retry counter
    retry_count = 0
    last_error = None
    base_wait_time = 1  # Start with 1 second wait time
    
    # Retry loop with exponential backoff
    while retry_count < max_retries:
        try:
            if progress_callback:
                progress_callback(f"API call attempt {retry_count + 1}/{max_retries}", (retry_count / max_retries) * 30)
                
            logger.info(f"Sending request to {api_url} (attempt {retry_count + 1}/{max_retries})")
            
            # Send request
            response = requests.post(
                api_url,
                files=files_payload,
                data=data_payload,
                headers=headers,
                timeout=timeout
            )
            
            if progress_callback:
                progress_callback("Processing API response", 50)
                
            # Check response status
            if response.status_code == 200:
                # Success
                try:
                    result = response.json()
                    if progress_callback:
                        progress_callback("API call successful", 70)
                    
                    # Validate response structure
                    if "error" in result:
                        logger.error(f"API returned error: {result['error']}")
                        return None, f"API Error: {result['error']}"
                    
                    return result, None
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse API response: {str(e)}")
                    last_error = f"Invalid response format: {str(e)}"
            elif response.status_code == 429:
                # Rate limit - exponential backoff
                wait_time = base_wait_time * (2 ** retry_count)
                logger.warning(f"Rate limit exceeded (attempt {retry_count + 1}/{max_retries}), waiting {wait_time}s")
                if progress_callback:
                    progress_callback(f"Rate limit exceeded, retrying in {wait_time} seconds", 30)
                time.sleep(wait_time)
            elif response.status_code >= 500:
                # Server error - exponential backoff
                wait_time = base_wait_time * (2 ** retry_count)
                logger.warning(f"Server error {response.status_code} (attempt {retry_count + 1}/{max_retries}), waiting {wait_time}s")
                if progress_callback:
                    progress_callback(f"Server error, retrying in {wait_time} seconds", 30)
                time.sleep(wait_time)
            else:
                # Client error - no retry
                try:
                    error_detail = response.json().get("detail", response.text)
                except json.JSONDecodeError:
                    error_detail = response.text
                    
                error_message = f"API Error ({response.status_code}): {error_detail}"
                logger.error(error_message)
                return None, error_message
                
        except requests.exceptions.Timeout:
            # Timeout - exponential backoff
            wait_time = base_wait_time * (2 ** retry_count)
            logger.warning(f"Request timeout (attempt {retry_count + 1}/{max_retries}), waiting {wait_time}s")
            if progress_callback:
                progress_callback(f"Request timeout, retrying", 30)
            time.sleep(wait_time)
            last_error = "Request timed out"
            
        except requests.exceptions.ConnectionError:
            # Connection error - exponential backoff
            wait_time = base_wait_time * (2 ** retry_count)
            logger.warning(f"Connection error (attempt {retry_count + 1}/{max_retries}), waiting {wait_time}s")
            if progress_callback:
                progress_callback(f"Connection error, retrying", 30)
            time.sleep(wait_time)
            last_error = "Connection error"
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None, f"Unexpected error: {str(e)}"
            
        # Increment retry counter
        retry_count += 1
        
    # If we get here, all retries failed
    logger.error(f"All {max_retries} API call attempts failed")
    return None, f"All {max_retries} API call attempts failed. Last error: {last_error}"

def extract_data_from_documents(files, document_type_hint=None, progress_callback=None):
    """
    Extract data from multiple documents.
    Maintains the original function signature for compatibility.
    
    Args:
        files: List of uploaded files
        document_type_hint: Optional hint for document type
        progress_callback: Optional callback function for progress updates
        
    Returns:
        List of extraction results or error messages
    """
    results = []
    
    for file in files:
        if progress_callback:
            progress_callback(f"Processing {file.name}...", 10)
            
        result, error = call_extraction_api(file, document_type_hint, progress_callback)
        
        if result:
            results.append(result)
        elif error:
            results.append({"error": error, "filename": file.name})
            
    return results

def check_api_health():
    """
    Check if the extraction API is healthy.
    New utility function that doesn't affect existing code.
    
    Returns:
        True if API is healthy, False otherwise
    """
    try:
        api_url = get_extraction_api_url()
        if not api_url:
            return False
            
        health_url = f"{api_url}/health"
        response = requests.get(health_url, timeout=5)
        
        return response.status_code == 200
    except:
        return False
