"""
Validation and Output Formatting Module for Real Estate NOI Analyzer
Validates extracted financial data and formats it according to the required JSON structure
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from constants import MAIN_METRICS, OPEX_COMPONENTS, INCOME_COMPONENTS, FINANCIAL_TOLERANCE, ERROR_MESSAGES
from utils.error_handler import setup_logger, handle_errors, DataValidationError
from utils.common import safe_float, safe_string, format_currency, clean_financial_data

# Setup logger
logger = setup_logger(__name__)

class ValidationFormatter:
    """
    Enhanced validation and formatting for extracted financial data with improved error handling.
    """
    
    def __init__(self):
        """Initialize the ValidationFormatter with enhanced logging."""
        logger.info("ValidationFormatter initialized with enhanced error handling")
    
    @handle_errors(default_return=({"error": "Validation failed"}, []))
    def validate_and_format_financial_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate and format extracted financial data with comprehensive error handling.
        
        Args:
            data: Extracted financial data dictionary
            
        Returns:
            Tuple of (formatted_data, validation_warnings)
            
        Raises:
            DataValidationError: If critical validation errors occur
        """
        logger.info(
            "Starting financial data validation and formatting",
            extra={
                "input_keys": list(data.keys()) if data else [],
                "input_size": len(data) if data else 0
            }
        )
        
        if not data or not isinstance(data, dict):
            error_msg = "Invalid input data: expected dictionary"
            logger.error(error_msg)
            raise DataValidationError(error_msg)
        
        # Clean the input data first
        cleaned_data = clean_financial_data(data)
        
        # Initialize formatted data and warnings
        formatted_data = {}
        warnings = []
        
        # Validate and format main metrics
        main_metric_warnings = self._validate_main_metrics(cleaned_data, formatted_data)
        warnings.extend(main_metric_warnings)
        
        # Validate and format OpEx components
        opex_warnings = self._validate_opex_components(cleaned_data, formatted_data)
        warnings.extend(opex_warnings)
        
        # Validate and format income components
        income_warnings = self._validate_income_components(cleaned_data, formatted_data)
        warnings.extend(income_warnings)
        
        # Validate financial calculations
        calculation_warnings = self._validate_financial_calculations(formatted_data)
        warnings.extend(calculation_warnings)
        
        # Ensure all required fields are present
        completeness_warnings = self._ensure_data_completeness(formatted_data)
        warnings.extend(completeness_warnings)
        
        # Log validation summary
        logger.info(
            "Financial data validation completed",
            extra={
                "output_keys": list(formatted_data.keys()),
                "warning_count": len(warnings),
                "warnings": warnings[:3] if len(warnings) > 3 else warnings  # Log first 3 warnings
            }
        )
        
        return formatted_data, warnings
    
    @handle_errors(default_return=[])
    def _validate_main_metrics(self, data: Dict[str, Any], formatted_data: Dict[str, Any]) -> List[str]:
        """
        Validate and format main financial metrics.
        
        Args:
            data: Input financial data
            formatted_data: Output formatted data (modified in place)
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        logger.info("Validating main financial metrics")
        
        for metric in MAIN_METRICS:
            try:
                # Extract and clean the value
                raw_value = data.get(metric)
                cleaned_value = safe_float(raw_value)
                formatted_data[metric] = cleaned_value
                
                # Check for potential data quality issues
                if raw_value is not None and cleaned_value == 0.0:
                    if isinstance(raw_value, str) and raw_value.strip():
                        warnings.append(f"Could not parse {metric} value: '{raw_value}' - defaulted to 0")
                        logger.warning(f"Parse error for {metric}: '{raw_value}'")
                
                # Validate metric-specific business rules
                if metric in ["gpr", "egi", "noi"] and cleaned_value < 0:
                    warnings.append(f"{metric.upper()} is negative ({format_currency(cleaned_value)}) - please verify")
                    logger.warning(f"Negative value for {metric}: {cleaned_value}")
                
            except Exception as e:
                error_msg = f"Error processing {metric}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                formatted_data[metric] = 0.0
                warnings.append(f"Error processing {metric} - defaulted to 0")
        
        return warnings
    
    @handle_errors(default_return=[])
    def _validate_opex_components(self, data: Dict[str, Any], formatted_data: Dict[str, Any]) -> List[str]:
        """
        Validate and format operating expense components.
        
        Args:
            data: Input financial data
            formatted_data: Output formatted data (modified in place)
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        logger.info("Validating OpEx components")
        
        opex_total = 0.0
        component_sum = 0.0
        
        for component in OPEX_COMPONENTS:
            try:
                raw_value = data.get(component)
                cleaned_value = safe_float(raw_value)
                formatted_data[component] = cleaned_value
                component_sum += cleaned_value
                
                # Check for negative OpEx components
                if cleaned_value < 0:
                    warnings.append(f"Negative {component} ({format_currency(cleaned_value)}) - please verify")
                    logger.warning(f"Negative OpEx component {component}: {cleaned_value}")
                
            except Exception as e:
                logger.error(f"Error processing OpEx component {component}: {str(e)}", exc_info=True)
                formatted_data[component] = 0.0
                warnings.append(f"Error processing {component} - defaulted to 0")
        
        # Validate total OpEx consistency
        opex_total = formatted_data.get("opex", 0.0)
        if opex_total > 0 and component_sum > 0:
            difference = abs(opex_total - component_sum)
            if difference > FINANCIAL_TOLERANCE:
                warnings.append(
                    f"OpEx total mismatch: total={format_currency(opex_total)}, "
                    f"components sum={format_currency(component_sum)}, "
                    f"difference={format_currency(difference)}"
                )
                logger.warning(
                    f"OpEx total mismatch",
                    extra={
                        "total_opex": opex_total,
                        "component_sum": component_sum,
                        "difference": difference
                    }
                )
                
                # Auto-correct if components sum is reasonable
                if component_sum > 0:
                    formatted_data["opex"] = component_sum
                    warnings.append(f"Auto-corrected OpEx total to {format_currency(component_sum)}")
        
        return warnings
    
    @handle_errors(default_return=[])
    def _validate_income_components(self, data: Dict[str, Any], formatted_data: Dict[str, Any]) -> List[str]:
        """
        Validate and format other income components.
        
        Args:
            data: Input financial data
            formatted_data: Output formatted data (modified in place)
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        logger.info("Validating income components")
        
        other_income_total = 0.0
        component_sum = 0.0
        
        for component in INCOME_COMPONENTS:
            try:
                raw_value = data.get(component)
                cleaned_value = safe_float(raw_value)
                formatted_data[component] = cleaned_value
                component_sum += cleaned_value
                
                # Income components should generally be positive
                if cleaned_value < 0:
                    warnings.append(f"Negative {component} ({format_currency(cleaned_value)}) - unusual but allowed")
                    logger.warning(f"Negative income component {component}: {cleaned_value}")
                
            except Exception as e:
                logger.error(f"Error processing income component {component}: {str(e)}", exc_info=True)
                formatted_data[component] = 0.0
                warnings.append(f"Error processing {component} - defaulted to 0")
        
        # Validate other income consistency
        other_income_total = formatted_data.get("other_income", 0.0)
        if other_income_total > 0 and component_sum > 0:
            difference = abs(other_income_total - component_sum)
            if difference > FINANCIAL_TOLERANCE:
                warnings.append(
                    f"Other income mismatch: total={format_currency(other_income_total)}, "
                    f"components sum={format_currency(component_sum)}, "
                    f"difference={format_currency(difference)}"
                )
                logger.warning(
                    f"Other income mismatch",
                    extra={
                        "total_other_income": other_income_total,
                        "component_sum": component_sum,
                        "difference": difference
                    }
                )
                
                # Auto-correct if components sum is reasonable
                if component_sum >= 0:
                    formatted_data["other_income"] = component_sum
                    warnings.append(f"Auto-corrected other income total to {format_currency(component_sum)}")
        
        return warnings
    
    @handle_errors(default_return=[])
    def _validate_financial_calculations(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate financial calculation consistency (EGI, NOI).
        
        Args:
            data: Formatted financial data
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        logger.info("Validating financial calculations")
        
        try:
            # Validate EGI calculation: EGI = GPR - Vacancy Loss + Other Income
            gpr = data.get("gpr", 0.0)
            vacancy_loss = data.get("vacancy_loss", 0.0)
            other_income = data.get("other_income", 0.0)
            reported_egi = data.get("egi", 0.0)
            
            calculated_egi = gpr - vacancy_loss + other_income
            egi_difference = abs(calculated_egi - reported_egi)
            
            if egi_difference > FINANCIAL_TOLERANCE:
                warnings.append(
                    f"EGI calculation mismatch: reported={format_currency(reported_egi)}, "
                    f"calculated={format_currency(calculated_egi)} "
                    f"(GPR {format_currency(gpr)} - Vacancy {format_currency(vacancy_loss)} + Other Income {format_currency(other_income)})"
                )
                logger.warning(
                    f"EGI calculation mismatch",
                    extra={
                        "reported_egi": reported_egi,
                        "calculated_egi": calculated_egi,
                        "gpr": gpr,
                        "vacancy_loss": vacancy_loss,
                        "other_income": other_income,
                        "difference": egi_difference
                    }
                )
                
                # Auto-correct EGI if calculation is reasonable
                data["egi"] = calculated_egi
                warnings.append(f"Auto-corrected EGI to {format_currency(calculated_egi)}")
            
            # Validate NOI calculation: NOI = EGI - OpEx
            egi = data.get("egi", 0.0)
            opex = data.get("opex", 0.0)
            reported_noi = data.get("noi", 0.0)
            
            calculated_noi = egi - opex
            noi_difference = abs(calculated_noi - reported_noi)
            
            if noi_difference > FINANCIAL_TOLERANCE:
                warnings.append(
                    f"NOI calculation mismatch: reported={format_currency(reported_noi)}, "
                    f"calculated={format_currency(calculated_noi)} "
                    f"(EGI {format_currency(egi)} - OpEx {format_currency(opex)})"
                )
                logger.warning(
                    f"NOI calculation mismatch",
                    extra={
                        "reported_noi": reported_noi,
                        "calculated_noi": calculated_noi,
                        "egi": egi,
                        "opex": opex,
                        "difference": noi_difference
                    }
                )
                
                # Auto-correct NOI if calculation is reasonable
                data["noi"] = calculated_noi
                warnings.append(f"Auto-corrected NOI to {format_currency(calculated_noi)}")
        
        except Exception as e:
            error_msg = f"Error validating financial calculations: {str(e)}"
            logger.error(error_msg, exc_info=True)
            warnings.append("Could not validate financial calculations")
        
        return warnings
    
    @handle_errors(default_return=[])
    def _ensure_data_completeness(self, data: Dict[str, Any]) -> List[str]:
        """
        Ensure all required fields are present with default values.
        
        Args:
            data: Financial data (modified in place)
            
        Returns:
            List of warnings about missing data
        """
        warnings = []
        missing_fields = []
        
        # Check for missing main metrics
        for metric in MAIN_METRICS:
            if metric not in data:
                data[metric] = 0.0
                missing_fields.append(metric)
        
        # Check for missing OpEx components
        for component in OPEX_COMPONENTS:
            if component not in data:
                data[component] = 0.0
                missing_fields.append(component)
        
        # Check for missing income components
        for component in INCOME_COMPONENTS:
            if component not in data:
                data[component] = 0.0
                missing_fields.append(component)
        
        if missing_fields:
            warnings.append(f"Missing fields filled with defaults: {', '.join(missing_fields[:5])}")
            if len(missing_fields) > 5:
                warnings.append(f"... and {len(missing_fields) - 5} more fields")
            
            logger.info(
                f"Data completeness check completed",
                extra={
                    "missing_field_count": len(missing_fields),
                    "missing_fields": missing_fields[:10]  # Log first 10
                }
            )
        
        return warnings


def validate_and_format_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Convenience function to validate and format extracted financial data
    
    Args:
        data: Extracted financial data
        
    Returns:
        Tuple containing:
            - Formatted data in the required JSON structure
            - List of validation warnings
    """
    validator = ValidationFormatter()
    return validator.validate_and_format_financial_data(data)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validation_formatter.py <json_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        formatted_data, warnings = validate_and_format_data(data)
        
        print("Formatted Data:")
        print(json.dumps(formatted_data, indent=2))
        
        if warnings:
            print("\nValidation Warnings:")
            for warning in warnings:
                print(f"- {warning}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
