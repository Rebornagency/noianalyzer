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
    property_id: Optional[str] = None,
    period: Optional[str] = None,
    progress_callback=None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Enhanced API integration with better error handling and retry logic
    """
    if file is None:
        return None, "No file provided for extraction"
    
    # Get configuration with defaults
    api_url = get_extraction_api_url() or "http://localhost:8000/api/v2/extraction/financials"
    api_key = get_api_key()
    max_retries = get_max_retries() or 3
    timeout = get_api_timeout() or 30
    
    if not api_key:
        logger.error("API key not configured")
        return None, "API key not configured"
    
    # Prepare request data
    files_payload = {"file": (file.name, file.getvalue(), file.type)}
    data_payload = {
        k: v for k, v in {
            "document_type": document_type_hint,
            "property_id": property_id,
            "period": period
        }.items() if v is not None
    }
    
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    
    # Initialize retry with exponential backoff
    retry_count = 0
    base_wait_time = 1  # Start with 1 second
    
    while retry_count < max_retries:
        try:
            if progress_callback:
                progress_callback(
                    f"API call attempt {retry_count + 1}/{max_retries}",
                    (retry_count / max_retries) * 30
                )
            
            response = requests.post(
                api_url,
                files=files_payload,
                data=data_payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if progress_callback:
                        progress_callback("Processing response", 70)
                    
                    # Validate response structure
                    if "financials" not in result:
                        logger.warning("Response missing financials object")
                        result = {"financials": result}
                    
                    return result, None
                    
                except json.JSONDecodeError as e:
                    return None, f"Invalid JSON response: {str(e)}"
                    
            elif response.status_code == 429:  # Rate limit
                wait_time = base_wait_time * (2 ** retry_count)  # Exponential backoff
                if progress_callback:
                    progress_callback(f"Rate limit exceeded, waiting {wait_time}s", 30)
                time.sleep(wait_time)
                
            elif response.status_code >= 500:  # Server error
                wait_time = base_wait_time * (2 ** retry_count)
                if progress_callback:
                    progress_callback(f"Server error, waiting {wait_time}s", 30)
                time.sleep(wait_time)
                
            else:  # Other client errors
                error_detail = "Unknown error"
                try:
                    error_response = response.json()
                    error_detail = error_response.get("detail", response.text)
                except:
                    error_detail = response.text
                
                return None, f"API Error ({response.status_code}): {error_detail}"
                
        except requests.exceptions.Timeout:
            wait_time = base_wait_time * (2 ** retry_count)
            logger.warning(f"Request timeout, waiting {wait_time}s")
            time.sleep(wait_time)
            
        except requests.exceptions.ConnectionError:
            wait_time = base_wait_time * (2 ** retry_count)
            logger.warning(f"Connection error, waiting {wait_time}s")
            time.sleep(wait_time)
            
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
            
        retry_count += 1
    
    return None, f"All {max_retries} API call attempts failed"
