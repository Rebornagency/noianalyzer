import streamlit as st
import pandas as pd
import streamlit as st
import logging
import json
from typing import Dict, Any, Optional, List

from noi_calculations import calculate_noi_comparisons
from ai_insights_gpt import generate_insights_with_gpt
from insights_display import display_insights
from ai_extraction import extract_noi_data
from utils.helpers import format_for_noi_comparison

# Import the new core processing function
from utils.processing_helpers import process_single_document_core
from utils.error_handler import setup_logger # For logger setup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("noi_analyzer_enhanced.log"), # New log file name
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('noi_tool_batch_integration')

def collect_all_files() -> Dict[str, Any]:
    """
    Collect all files from session state
    
    Returns:
        Dictionary with document types as keys and file objects as values
    """
    logger.info("Collecting files from session state")
    
    files = {}
    
    # Check for current month actuals (required)
    logger.info(f"DEBUG: Checking session state for current_month_actuals: {'current_month_actuals' in st.session_state}")
    if 'current_month_actuals' in st.session_state:
        logger.info(f"DEBUG: current_month_actuals value: {st.session_state.current_month_actuals}")
        logger.info(f"DEBUG: current_month_actuals is not None: {st.session_state.current_month_actuals is not None}")
        if hasattr(st.session_state.current_month_actuals, 'name'):
            logger.info(f"DEBUG: current_month_actuals filename: {st.session_state.current_month_actuals.name}")
    if 'current_month_actuals' in st.session_state and st.session_state.current_month_actuals is not None:
        files["current_month_actuals"] = st.session_state.current_month_actuals
        logger.info(f"DEBUG: Added current_month_actuals to files collection")
    
    # Check for prior month actuals (optional)
    if 'prior_month_actuals' in st.session_state and st.session_state.prior_month_actuals is not None:
        files["prior_month_actuals"] = st.session_state.prior_month_actuals
        logger.info(f"DEBUG: Added prior_month_actuals to files collection")
    
    # Check for budget (optional)
    if 'current_month_budget' in st.session_state and st.session_state.current_month_budget is not None:
        files["current_month_budget"] = st.session_state.current_month_budget
        logger.info(f"DEBUG: Added current_month_budget to files collection")
    
    # Check for prior year actuals (optional)
    if 'prior_year_actuals' in st.session_state and st.session_state.prior_year_actuals is not None:
        files["prior_year_actuals"] = st.session_state.prior_year_actuals
        logger.info(f"DEBUG: Added prior_year_actuals to files collection")
    
    logger.info(f"Collected {len(files)} files: {list(files.keys())}")
    logger.info(f"DEBUG: Files collection summary: {[(k, bool(v), getattr(v, 'name', 'NO_NAME')) for k, v in files.items()]}")
    return files

def process_all_documents() -> Dict[str, Any]:
    """
    Process all uploaded documents using the core processing function 
    and return consolidated data ready for NOI calculation.
    This function will also update st.session_state.consolidated_data and st.session_state.raw_data.
    
    Returns:
        Dictionary containing formatted financial data for each document type, 
        or an error dictionary if critical errors occur (e.g., no current month data).
    """
    logger.info("Starting process_all_documents")
    
    files_to_process = collect_all_files()
    
    if not files_to_process or 'current_month_actuals' not in files_to_process:
        logger.warning("No files to process or current_month_actuals is missing.")
        st.session_state.consolidated_data = {}
        st.session_state.raw_data = {}
        return {
            'error': "No files to process or Current Month Actuals is missing. Please upload files and try again.",
            'details': "Current Month Actuals is mandatory."
        }
    
    processed_data_for_consolidation = {}
    raw_extraction_results = {}
    overall_has_error = False
    first_error_message = ""
    first_error_details = ""

    # Standard internal keys for consolidated_data
    doc_type_mapping = {
        "current_month_actuals": "current_month",
        "prior_month_actuals": "prior_month",
        "current_month_budget": "budget",
        "prior_year_actuals": "prior_year"
    }

    for doc_key, uploaded_file in files_to_process.items():
        if uploaded_file:
            logger.info(f"Processing document for key: {doc_key} - File: {getattr(uploaded_file, 'name', 'UnknownFile')}")
            # Call the core processing function
            core_result = process_single_document_core(uploaded_file, doc_key)
            internal_doc_type = doc_type_mapping.get(doc_key)

            if not internal_doc_type:
                logger.error(f"Unknown document key '{doc_key}' encountered. Skipping file {getattr(uploaded_file, 'name', 'UnknownFile')}")
                if not overall_has_error:
                    overall_has_error = True
                    first_error_message = f"Internal configuration error: Unknown document key '{doc_key}'"
                continue

            if 'error' in core_result:
                logger.error(f"Error processing {doc_key} ({getattr(uploaded_file, 'name', 'UnknownFile')}): {core_result['error']}")
                # Store a placeholder or error info in raw_data for this doc_type
                raw_extraction_results[internal_doc_type] = core_result 
                if not overall_has_error: # Capture first error for overall status
                    overall_has_error = True
                    first_error_message = core_result['error']
                    first_error_details = core_result.get('details', '')
                # Don't add to formatted data if core processing failed
            else:
                # Successfully processed
                processed_data_for_consolidation[internal_doc_type] = core_result.get("formatted_data")
                raw_extraction_results[internal_doc_type] = core_result.get("raw_extraction_result")
                logger.info(f"Successfully processed and formatted data for {internal_doc_type} from {doc_key}")
    
    # Update session state
    st.session_state.consolidated_data = processed_data_for_consolidation
    st.session_state.raw_data = raw_extraction_results
    logger.info(f"Updated st.session_state.consolidated_data with keys: {list(st.session_state.consolidated_data.keys())}")
    logger.info(f"Updated st.session_state.raw_data with keys: {list(st.session_state.raw_data.keys())}")

    # Check if we have the minimum required data (current_month)
    if "current_month" not in processed_data_for_consolidation or not processed_data_for_consolidation["current_month"]:
        logger.error("Critical error: Current month data is missing or failed to process after attempting all files.")
        final_error_message = first_error_message if overall_has_error else "Current month data is required but missing or failed to process."
        final_error_details = first_error_details if overall_has_error else "Please upload Current Month Actuals file and try again."
        return {
            'error': final_error_message,
            'details': final_error_details
        }
    
    if overall_has_error:
        logger.warning(f"process_all_documents completed with some errors. First error: {first_error_message}")
        # Return the consolidated data but also indicate partial success / errors
        # The main app can then decide how to message this to the user
        return {
            "warning": "Some documents could not be processed.",
            "details": first_error_message, # Provide the first error encountered as a sample
            "consolidated_output": processed_data_for_consolidation # Return data processed so far
        }
    
    logger.info("Successfully processed all documents. Consolidated data is ready.")
    return processed_data_for_consolidation # This is the dict like {"current_month": data, ...}

def validate_formatted_data(data: Dict[str, Any], doc_type_label: str) -> Dict[str, Any]:
    """
    Validate formatted data to ensure it contains all required fields and basic consistency.
    
    Args:
        data: Formatted data dictionary for a single document type.
        doc_type_label: Label for logging/error messages (e.g., "Current Month").
        
    Returns:
        Dictionary with validation status: {"valid": bool, "message": str, "warnings": List[str]}
    """
    if not isinstance(data, dict):
        return {"valid": False, "message": f"Invalid data format for {doc_type_label}: Expected dict, got {type(data).__name__}", "warnings": []}

    required_fields = ["gpr", "egi", "opex", "noi"] # Core fields for any financial report
    warnings = [] 
    
    # Check for missing required fields (basic check, format_for_noi_comparison should ensure these with defaults)
    missing_fields = [field for field in required_fields if field not in data or data[field] is None] # Check for None too
    if missing_fields:
        warnings.append(f"Missing or null core financial fields in {doc_type_label}: {', '.join(missing_fields)}. Defaults may have been used.")

    # Basic consistency checks (can be expanded)
    # EGI = GPR - Vacancy Loss - Concessions - Bad Debt + Other Income
    # NOI = EGI - OpEx
    # These are illustrative; format_for_noi_comparison should ideally calculate/verify these.
    # If format_for_noi_comparison guarantees these, these checks here are redundant or become deeper validation.

    gpr = data.get("gpr", 0.0)
    vacancy_loss = data.get("vacancy_loss", 0.0)
    concessions = data.get("concessions", 0.0)
    bad_debt = data.get("bad_debt", 0.0)
    other_income_total = data.get("other_income", 0.0)
    egi_reported = data.get("egi", 0.0)
    opex_total = data.get("opex", 0.0)
    noi_reported = data.get("noi", 0.0)

    calculated_egi = gpr - vacancy_loss - concessions - bad_debt + other_income_total
    if abs(egi_reported - calculated_egi) > 0.01: # Tolerance for float comparisons
        warnings.append(f"EGI inconsistency in {doc_type_label}: Reported EGI {egi_reported:.2f} vs Calculated EGI {calculated_egi:.2f}.")

    calculated_noi = egi_reported - opex_total # Use reported EGI for NOI calc to avoid cascading EGI error here
    if abs(noi_reported - calculated_noi) > 0.01:
        warnings.append(f"NOI inconsistency in {doc_type_label}: Reported NOI {noi_reported:.2f} vs Calculated NOI {calculated_noi:.2f} (from reported EGI)." )

    if not warnings and not missing_fields: # If no missing fields found earlier and no new warnings
        return {"valid": True, "message": f"Data for {doc_type_label} appears valid and consistent.", "warnings": []}
    else:
        return {"valid": False, "message": f"Validation issues found for {doc_type_label}.", "warnings": warnings}
