import os
import logging
import requests
import json
import tempfile
from typing import Dict, Any, List, Optional, BinaryIO, Union
import streamlit as st
from config import get_extraction_api_url, get_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_extraction')

def extract_noi_data(file: Any, document_type_hint: Optional[str] = None, 
                    api_url: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract NOI data from a document using the extraction API.
    
    Args:
        file: Document file to process
        document_type_hint: Optional hint about document type
        api_url: Optional API URL override
        api_key: Optional API key override
        
    Returns:
        Dictionary containing extracted financial data
    """
    logger.info(f"Extracting data from document: {getattr(file, 'name', 'unknown')}")
    logger.info(f"Document type hint: {document_type_hint}")
    
    # Get API URL and API key from config if not provided
    if api_url is None:
        api_url = get_extraction_api_url()
        # Ensure the URL ends with /extract
        if api_url.endswith('/'):
            api_url = f"{api_url}extract"
        else:
            api_url = f"{api_url}/extract"
    
    if api_key is None:
        api_key = get_api_key()
    
    logger.info(f"Using extraction API URL: {api_url}")
    
    # Check if we have valid API credentials
    if not api_url:
        logger.error("Extraction API URL not configured")
        return {"error": "Extraction API URL not configured"}
    
    if not api_key:
        logger.error("Extraction API key not configured")
        return {"error": "Extraction API key not configured"}
    
    try:
        # Prepare files for API request
        files = {"file": (file.name, file.getvalue(), file.type)}
        
        # Prepare headers with API key
        headers = {"x-api-key": api_key}
        
        # Prepare data with document type hint if provided
        data = {}
        if document_type_hint:
            data["document_type"] = document_type_hint
        
        # Make API request
        logger.info(f"Sending request to extraction API: {api_url}")
        response = requests.post(api_url, files=files, data=data, headers=headers)
        
        # Check response status
        if response.status_code == 200:
            logger.info("Extraction API request successful")
            result = response.json()
            logger.debug(f"Extraction API response structure: {list(result.keys())}")
            return result
        else:
            logger.error(f"Extraction API request failed with status code {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return {
                'error': f"Extraction API request failed with status code {response.status_code}",
                'details': response.text
            }
    
    except Exception as e:
        logger.error(f"Error extracting data from document: {str(e)}")
        return {
            'error': f"Error extracting data from document: {str(e)}"
        }

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
