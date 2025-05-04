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

def process_all_documents() -> Dict[str, Any]:
    """
    Process all uploaded documents using the enhanced extraction API.

    Returns:
        Consolidated data dictionary with the DETAILED structure for each document type.
    """
    # Initialize consolidated data structure
    consolidated_data = {
        "current_month": None,
        "prior_month": None,
        "budget": None,
        "prior_year": None
    }
    processed_ok = True # Flag to track if all essential processing worked
    processing_results = [] # Track processing results for summary

    # Process current month actuals (required)
    if st.session_state.current_month_actuals:
        with st.status(f"Processing Current Month: {st.session_state.current_month_actuals.name}...", expanded=True) as status:
            status.update(label="Extracting data...", state="running")
            result = extract_noi_data(st.session_state.current_month_actuals, "current_month_actuals")
            
            if result:
                status.update(label="Formatting data...", state="running")
                # Use the enhanced formatter
                formatted_data = format_for_noi_comparison(result)
                
                # Validate the formatted data
                validation_result = validate_formatted_data(formatted_data, "current_month")
                if validation_result["valid"]:
                    consolidated_data["current_month"] = formatted_data
                    status.update(label=f"✅ Processed Current Month: {st.session_state.current_month_actuals.name}", state="complete")
                    processing_results.append({
                        "file": st.session_state.current_month_actuals.name,
                        "type": "Current Month",
                        "status": "Success",
                        "details": f"Extracted {len(formatted_data)} data points"
                    })
                else:
                    status.update(label=f"⚠️ Processed Current Month with warnings: {validation_result['message']}", state="complete")
                    st.warning(validation_result["message"])
                    consolidated_data["current_month"] = formatted_data
                    processing_results.append({
                        "file": st.session_state.current_month_actuals.name,
                        "type": "Current Month",
                        "status": "Warning",
                        "details": validation_result["message"]
                    })
            else:
                status.update(label=f"❌ Failed to process Current Month: {st.session_state.current_month_actuals.name}", state="error")
                processed_ok = False # Mark failure
                processing_results.append({
                    "file": st.session_state.current_month_actuals.name,
                    "type": "Current Month",
                    "status": "Failed",
                    "details": "Extraction failed"
                })

    # Process prior month actuals (optional)
    if st.session_state.prior_month_actuals:
        with st.status(f"Processing Prior Month: {st.session_state.prior_month_actuals.name}...", expanded=True) as status:
            status.update(label="Extracting data...", state="running")
            result = extract_noi_data(st.session_state.prior_month_actuals, "prior_month_actuals")
            
            if result:
                status.update(label="Formatting data...", state="running")
                formatted_data = format_for_noi_comparison(result)
                
                # Validate the formatted data
                validation_result = validate_formatted_data(formatted_data, "prior_month")
                if validation_result["valid"]:
                    consolidated_data["prior_month"] = formatted_data
                    status.update(label=f"✅ Processed Prior Month: {st.session_state.prior_month_actuals.name}", state="complete")
                    processing_results.append({
                        "file": st.session_state.prior_month_actuals.name,
                        "type": "Prior Month",
                        "status": "Success",
                        "details": f"Extracted {len(formatted_data)} data points"
                    })
                else:
                    status.update(label=f"⚠️ Processed Prior Month with warnings: {validation_result['message']}", state="complete")
                    st.warning(validation_result["message"])
                    consolidated_data["prior_month"] = formatted_data
                    processing_results.append({
                        "file": st.session_state.prior_month_actuals.name,
                        "type": "Prior Month",
                        "status": "Warning",
                        "details": validation_result["message"]
                    })
            else:
                status.update(label=f"❌ Failed to process Prior Month: {st.session_state.prior_month_actuals.name}", state="error")
                processing_results.append({
                    "file": st.session_state.prior_month_actuals.name,
                    "type": "Prior Month",
                    "status": "Failed",
                    "details": "Extraction failed"
                })
                # Allow continuing even if optional files fail

    # Process budget files (optional)
    if st.session_state.current_month_budget:
        with st.status(f"Processing Budget: {st.session_state.current_month_budget.name}...", expanded=True) as status:
            status.update(label="Extracting data...", state="running")
            result = extract_noi_data(st.session_state.current_month_budget, "current_month_budget")
            
            if result:
                status.update(label="Formatting data...", state="running")
                formatted_data = format_for_noi_comparison(result)
                
                # Validate the formatted data
                validation_result = validate_formatted_data(formatted_data, "budget")
                if validation_result["valid"]:
                    consolidated_data["budget"] = formatted_data
                    status.update(label=f"✅ Processed Budget: {st.session_state.current_month_budget.name}", state="complete")
                    processing_results.append({
                        "file": st.session_state.current_month_budget.name,
                        "type": "Budget",
                        "status": "Success",
                        "details": f"Extracted {len(formatted_data)} data points"
                    })
                else:
                    status.update(label=f"⚠️ Processed Budget with warnings: {validation_result['message']}", state="complete")
                    st.warning(validation_result["message"])
                    consolidated_data["budget"] = formatted_data
                    processing_results.append({
                        "file": st.session_state.current_month_budget.name,
                        "type": "Budget",
                        "status": "Warning",
                        "details": validation_result["message"]
                    })
            else:
                status.update(label=f"❌ Failed to process Budget: {st.session_state.current_month_budget.name}", state="error")
                processing_results.append({
                    "file": st.session_state.current_month_budget.name,
                    "type": "Budget",
                    "status": "Failed",
                    "details": "Extraction failed"
                })

    # Process prior year actuals (optional)
    if st.session_state.prior_year_actuals:
        with st.status(f"Processing Prior Year: {st.session_state.prior_year_actuals.name}...", expanded=True) as status:
            status.update(label="Extracting data...", state="running")
            result = extract_noi_data(st.session_state.prior_year_actuals, "prior_year_actuals")
            
            if result:
                status.update(label="Formatting data...", state="running")
                formatted_data = format_for_noi_comparison(result)
                
                # Validate the formatted data
                validation_result = validate_formatted_data(formatted_data, "prior_year")
                if validation_result["valid"]:
                    consolidated_data["prior_year"] = formatted_data
                    status.update(label=f"✅ Processed Prior Year: {st.session_state.prior_year_actuals.name}", state="complete")
                    processing_results.append({
                        "file": st.session_state.prior_year_actuals.name,
                        "type": "Prior Year",
                        "status": "Success",
                        "details": f"Extracted {len(formatted_data)} data points"
                    })
                else:
                    status.update(label=f"⚠️ Processed Prior Year with warnings: {validation_result['message']}", state="complete")
                    st.warning(validation_result["message"])
                    consolidated_data["prior_year"] = formatted_data
                    processing_results.append({
                        "file": st.session_state.prior_year_actuals.name,
                        "type": "Prior Year",
                        "status": "Warning",
                        "details": validation_result["message"]
                    })
            else:
                status.update(label=f"❌ Failed to process Prior Year: {st.session_state.prior_year_actuals.name}", state="error")
                processing_results.append({
                    "file": st.session_state.prior_year_actuals.name,
                    "type": "Prior Year",
                    "status": "Failed",
                    "details": "Extraction failed"
                })

    # Display processing summary
    if processing_results:
        st.subheader("Processing Summary")
        summary_df = pd.DataFrame(processing_results)
        st.dataframe(summary_df, use_container_width=True)

    # Store in session state
    st.session_state.consolidated_data = consolidated_data
    st.session_state.processing_completed = processed_ok # Store completion status
    
    # Log the final consolidated structure
    logger.info(f"Consolidated data structure: {list(consolidated_data.keys())}")
    for doc_type, data in consolidated_data.items():
        if data:
            logger.info(f"{doc_type} data keys: {list(data.keys())}")

    return consolidated_data

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
