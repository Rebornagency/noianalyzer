import logging
from typing import Dict, Any, Optional
import json

from ai_extraction import extract_noi_data # Assumes extract_noi_data is accessible
from utils.helpers import format_for_noi_comparison # Assumes format_for_noi_comparison is accessible
from utils.error_handler import setup_logger, NOIAnalyzerError, FileProcessingError

logger = setup_logger(__name__) # Use the centralized logger setup

def process_single_document_core(uploaded_file: Any, document_key: str) -> Dict[str, Any]:
    """
    Core function to process a single uploaded financial document.
    It extracts data, formats it for NOI comparison, and handles errors.

    Args:
        uploaded_file: The uploaded file object (e.g., from Streamlit file_uploader).
        document_key: A string key representing the document type (e.g., 'current_month_actuals').

    Returns:
        A dictionary containing the formatted financial data if successful,
        or an error dictionary if processing fails.
    """
    if not uploaded_file:
        logger.warning(f"process_single_document_core called for {document_key} with no file.")
        return {"error": "No file provided for processing.", "details": f"Document key: {document_key}"}

    file_name = getattr(uploaded_file, 'name', 'UnknownFile')
    logger.info(f"Starting core processing for {document_key}: {file_name}")

    try:
        # Step 1: Extract data using AI service
        # Pass document_key to extract_noi_data if it can use it for context or logging
        extraction_result = extract_noi_data(uploaded_file, document_key) 

        if not extraction_result:
            logger.error(f"Data extraction returned empty result for {document_key}: {file_name}")
            raise FileProcessingError(f"Data extraction failed to return any result for {file_name}.")

        # Step 2: Check for errors from extraction_result
        if isinstance(extraction_result, dict) and 'error' in extraction_result:
            error_message = extraction_result['error']
            error_details = extraction_result.get('details', '')
            logger.error(f"Error extracting data from {document_key} ({file_name}): {error_message}. Details: {error_details}")
            # Return the error structure directly as it might be informative
            return {"error": error_message, "details": error_details, "file_name": file_name, "document_key": document_key}
        
        # Log raw extraction result (snippet for brevity)
        try:
            loggable_extraction_snippet = {k: (type(v).__name__ if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v) for k, v in extraction_result.items() if k in ['financials', 'metadata', 'document_type', 'confidence_score']}
            logger.info(f"Raw extraction result snippet for {document_key} ({file_name}): {json.dumps(loggable_extraction_snippet, default=str)}")
        except Exception as log_e:
            logger.warning(f"Could not log raw extraction snippet for {document_key}: {log_e}")

        # Step 3: Format data for NOI comparison
        # format_for_noi_comparison expects the full extraction_result which might contain more than just 'financials'
        formatted_data = format_for_noi_comparison(extraction_result)

        if not formatted_data:
            logger.error(f"Formatting returned empty result for {document_key}: {file_name}")
            raise FileProcessingError(f"Data formatting failed to return any result for {file_name} after successful extraction.")
        
        # Log formatted data (snippet)
        try:
            loggable_formatted_snippet = {k: v for i, (k, v) in enumerate(formatted_data.items()) if i < 5} # Log first 5 items
            logger.info(f"Formatted data snippet for {document_key} ({file_name}): {json.dumps(loggable_formatted_snippet, default=str)}")
        except Exception as log_e:
            logger.warning(f"Could not log formatted data snippet for {document_key}: {log_e}")

        logger.info(f"Successfully processed {document_key}: {file_name}")
        # Return the formatted data, and also include the raw extraction result for potential use by the caller
        return {"formatted_data": formatted_data, "raw_extraction_result": extraction_result}

    except FileProcessingError as fpe:
        logger.error(f"FileProcessingError for {document_key} ({file_name}): {fpe}")
        return {"error": str(fpe), "details": "File processing stage error.", "file_name": file_name, "document_key": document_key}
    except NOIAnalyzerError as nae:
        logger.error(f"NOIAnalyzerError for {document_key} ({file_name}): {nae}")
        return {"error": str(nae), "details": "Application specific error during processing.", "file_name": file_name, "document_key": document_key}
    except Exception as e:
        logger.error(f"Unexpected error processing {document_key} ({file_name}): {str(e)}", exc_info=True)
        return {"error": "An unexpected error occurred during document processing.", "details": str(e), "file_name": file_name, "document_key": document_key} 