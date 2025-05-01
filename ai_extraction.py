import os
import logging
import requests
import json
import tempfile
from typing import Dict, Any, List, Optional, BinaryIO, Union
import streamlit as st
from config import get_extraction_api_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_extraction')

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
    logger.info("Extracting data from documents")
    
    # Get the extraction API URL with proper endpoint
    api_url = get_extraction_api_url()
    logger.info(f"Using extraction API URL: {api_url}")
    
    # Prepare files for API request
    files = {}
    if current_month_file:
        files['current_month_actuals'] = current_month_file
        logger.info(f"Including current month actuals file: {getattr(current_month_file, 'name', 'unknown')}")
    
    if prior_month_file:
        files['prior_month_actuals'] = prior_month_file
        logger.info(f"Including prior month actuals file: {getattr(prior_month_file, 'name', 'unknown')}")
    
    if budget_file:
        files['current_month_budget'] = budget_file
        logger.info(f"Including budget file: {getattr(budget_file, 'name', 'unknown')}")
    
    if prior_year_file:
        files['prior_year_actuals'] = prior_year_file
        logger.info(f"Including prior year actuals file: {getattr(prior_year_file, 'name', 'unknown')}")
    
    # Return empty result if no files provided
    if not files:
        logger.warning("No files provided for extraction")
        return {}
    
    try:
        # Make API request
        logger.info(f"Sending request to extraction API: {api_url}")
        response = requests.post(api_url, files=files)
        
        # Check response status
        if response.status_code == 200:
            logger.info("Extraction API request successful")
            result = response.json()
            logger.debug(f"Extraction API response: {json.dumps(result, indent=2)}")
            return result
        else:
            logger.error(f"Extraction API request failed with status code {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return {
                'error': f"Extraction API request failed with status code {response.status_code}",
                'details': response.text
            }
    
    except Exception as e:
        logger.error(f"Error extracting data from documents: {str(e)}")
        return {
            'error': f"Error extracting data from documents: {str(e)}"
        }

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
