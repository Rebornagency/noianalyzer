import streamlit as st
import pandas as pd
import logging
import json
from typing import Dict, Any, Optional, List

from noi_calculations import calculate_noi_comparisons
from ai_insights_gpt import generate_insights_with_gpt
from insights_display import display_insights
from ai_extraction import extract_noi_data
from utils.helpers import format_for_noi_comparison

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
    if 'current_month_actuals' in st.session_state and st.session_state.current_month_actuals is not None:
        files["current_month_actuals"] = st.session_state.current_month_actuals
    
    # Check for prior month actuals (optional)
    if 'prior_month_actuals' in st.session_state and st.session_state.prior_month_actuals is not None:
        files["prior_month_actuals"] = st.session_state.prior_month_actuals
    
    # Check for budget (optional)
    if 'current_month_budget' in st.session_state and st.session_state.current_month_budget is not None:
        files["current_month_budget"] = st.session_state.current_month_budget
    
    # Check for prior year actuals (optional)
    if 'prior_year_actuals' in st.session_state and st.session_state.prior_year_actuals is not None:
        files["prior_year_actuals"] = st.session_state.prior_year_actuals
    
    logger.info(f"Collected {len(files)} files: {list(files.keys())}")
    return files

def process_all_documents() -> Dict[str, Any]:
    """
    Process all uploaded documents and return consolidated data ready for NOI calculation
    
    Returns:
        Dictionary containing financial data for each document type
    """
    logger.info("Processing all documents")
    
    # Collect all files from session state
    files = collect_all_files()
    
    # Return empty data if no files
    if not files:
        logger.warning("No files to process")
        return {
            'error': "No files to process. Please upload at least the Current Month Actuals file."
        }
    
    # Extract data from each document
    results = {}
    has_error = False
    error_message = ""
    
    for doc_type, file in files.items():
        if file is not None:
            logger.info(f"Processing {doc_type}: {file.name}")
            
            # Process document and get extraction result
            extraction_result = extract_noi_data(file, doc_type)
            
            # Check for extraction errors
            if 'error' in extraction_result:
                logger.error(f"Error extracting data from {doc_type}: {extraction_result['error']}")
                has_error = True
                error_message = extraction_result['error']
                if 'details' in extraction_result:
                    error_message += f" Details: {extraction_result['details']}"
                continue
            
            # Log the raw extraction result for debugging
            logger.info(f"Raw extraction result structure for {doc_type}: {list(extraction_result.keys())}")
            
            # Handle nested structures in the extraction result
            if 'financials' in extraction_result:
                financials = extraction_result['financials']
                logger.info(f"Found 'financials' key in extraction result, keys: {list(financials.keys())}")
                
                # Log detailed structure of operating_expenses for debugging
                if 'operating_expenses' in financials and isinstance(financials['operating_expenses'], dict):
                    opex = financials['operating_expenses']
                    logger.info(f"operating_expenses is a dictionary with keys: {list(opex.keys())}")
                    if 'total_operating_expenses' in opex:
                        logger.info(f"Found total_operating_expenses: {opex['total_operating_expenses']}")
                
                # Log detailed structure of other_income for debugging
                if 'other_income' in financials and isinstance(financials['other_income'], dict):
                    other_income = financials['other_income']
                    logger.info(f"other_income is a dictionary with keys: {list(other_income.keys())}")
                    if 'total' in other_income:
                        logger.info(f"Found other_income.total: {other_income['total']}")
            
            # Format data for NOI calculation using our enhanced formatter
            formatted_data = format_for_noi_comparison(extraction_result)
            logger.info(f"Formatted data for {doc_type}: {formatted_data.keys()}")
            logger.info(f"Key metrics: gpr={formatted_data.get('gpr')}, opex={formatted_data.get('opex')}, noi={formatted_data.get('noi')}")
            
            # Add to results
            if doc_type == "current_month_actuals":
                results["current_month"] = formatted_data
            elif doc_type == "prior_month_actuals":
                results["prior_month"] = formatted_data
            elif doc_type == "current_month_budget":
                results["budget"] = formatted_data
            elif doc_type == "prior_year_actuals":
                results["prior_year"] = formatted_data
    
    # Check if we have the minimum required data
    if "current_month" not in results:
        logger.error("Current month data is required but missing or failed to process")
        return {
            'error': "Current month data is required but missing or failed to process",
            'details': error_message if has_error else "Please upload Current Month Actuals file and try again."
        }
    
    # Check if we have any errors but still have current month data
    if has_error:
        logger.warning("Some documents had extraction errors, but proceeding with available data")
        # We can still continue with partial data if at least current_month is available
    
    # Log structure of consolidated data
    logger.info(f"Consolidated data structure: {list(results.keys())}")
    
    # Check that current_month has the expected data
    if "current_month" in results:
        current_month = results["current_month"]
        logger.info(f"current_month data keys: {list(current_month.keys())}")
        logger.info(f"Key metrics: gpr={current_month.get('gpr')}, opex={current_month.get('opex')}, noi={current_month.get('noi')}")
    
    # Check other data elements if present
    for key in ["prior_month", "budget", "prior_year"]:
        if key in results:
            data = results[key]
            logger.info(f"{key} data keys: {list(data.keys())}")
            logger.info(f"Key metrics: gpr={data.get('gpr')}, opex={data.get('opex')}, noi={data.get('noi')}")
    
    # Verify data structure before returning
    for key in ["current_month", "prior_month", "budget", "prior_year"]:
        if key in results:
            # Ensure each entry has the required keys
            required_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]
            missing_keys = [req_key for req_key in required_keys if req_key not in results[key]]
            
            if missing_keys:
                logger.warning(f"Data for {key} is missing required keys: {missing_keys}")
                # Fill in missing keys with default values to prevent downstream errors
                for missing_key in missing_keys:
                    results[key][missing_key] = 0.0
                    logger.info(f"Added default value 0.0 for missing key {missing_key} in {key}")
            
            # Verify gpr_current is numeric
            for field in required_keys:
                if not isinstance(results[key].get(field), (int, float)):
                    try:
                        results[key][field] = float(results[key].get(field, 0))
                        logger.info(f"Converted {field} to float in {key}")
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert {field} to float in {key}, using default value 0.0")
                        results[key][field] = 0.0
    
    # All checks passed
    logger.info("Finished processing all documents, returning consolidated data")
    return results

def validate_formatted_data(data: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """
    Validate formatted data to ensure it contains all required fields.
    
    Args:
        data: Formatted data to validate
        doc_type: Type of document (current_month, prior_month, budget, prior_year)
        
    Returns:
        Dictionary with validation result
    """
    # Define required fields for each document type
    required_fields = ["gpr", "egi", "opex", "noi"]
    
    # Check for missing required fields
    missing_fields = [field for field in required_fields if field not in data or data[field] == 0]
    
    # Check for data consistency
    consistency_issues = []
    
    # Check if EGI is consistent with its components
    if "gpr" in data and "vacancy_loss" in data and "other_income" in data and "egi" in data:
        expected_egi = data["gpr"] - data["vacancy_loss"] + data["other_income"]
        if abs(data["egi"] - expected_egi) > 0.01:  # Allow small rounding differences
            consistency_issues.append(f"EGI ({data['egi']}) doesn't match calculated value ({expected_egi})")
    
    # Check if NOI is consistent with EGI and OpEx
    if "egi" in data and "opex" in data and "noi" in data:
        expected_noi = data["egi"] - data["opex"]
        if abs(data["noi"] - expected_noi) > 0.01:  # Allow small rounding differences
            consistency_issues.append(f"NOI ({data['noi']}) doesn't match calculated value ({expected_noi})")
    
    # Prepare validation result
    if not missing_fields and not consistency_issues:
        return {
            "valid": True,
            "message": f"All required fields present and consistent"
        }
    else:
        message_parts = []
        if missing_fields:
            message_parts.append(f"Missing fields: {', '.join(missing_fields)}")
        if consistency_issues:
            message_parts.append(f"Consistency issues: {'; '.join(consistency_issues)}")
        
        return {
            "valid": False,
            "message": ". ".join(message_parts)
        }
