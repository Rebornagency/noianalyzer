"""
Centralized Error Handling for NOI Analyzer

This module provides consistent error handling patterns, logging utilities,
and exception classes for the NOI Analyzer application.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple, Union, Callable
from functools import wraps
from datetime import datetime

from constants import ERROR_MESSAGES, SUCCESS_MESSAGES, LOG_FORMAT, LOG_LEVEL


class NOIAnalyzerError(Exception):
    """Base exception class for NOI Analyzer errors"""
    
    def __init__(self, message: str, error_type: str = "GENERAL_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)


class DataValidationError(NOIAnalyzerError):
    """Exception for data validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, expected: Optional[Any] = None, actual: Optional[Any] = None):
        details = {
            "field": field,
            "expected": expected,
            "actual": actual
        }
        super().__init__(message, "DATA_VALIDATION_ERROR", details)


class APIError(NOIAnalyzerError):
    """Exception for API-related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[str] = None):
        details = {
            "status_code": status_code,
            "response": response
        }
        super().__init__(message, "API_ERROR", details)


class FileProcessingError(NOIAnalyzerError):
    """Exception for file processing errors"""
    
    def __init__(self, message: str, filename: Optional[str] = None, file_type: Optional[str] = None):
        details = {
            "filename": filename,
            "file_type": file_type
        }
        super().__init__(message, "FILE_PROCESSING_ERROR", details)


def setup_logger(name: str, level: str = LOG_LEVEL) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # File handler
    file_handler = logging.FileHandler('noi_analyzer.log')
    file_handler.setLevel(getattr(logging, level.upper()))
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def handle_errors(
    default_return: Any = None,
    reraise: bool = False,
    log_errors: bool = True,
    custom_message: Optional[str] = None
) -> Callable:
    """
    Decorator for consistent error handling across functions.
    
    Args:
        default_return: Default value to return on error
        reraise: Whether to reraise the exception after logging
        log_errors: Whether to log errors
        custom_message: Custom error message prefix
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                return result
                
            except NOIAnalyzerError as e:
                if log_errors:
                    logger.error(
                        f"NOI Analyzer error in {func.__name__}: {e.message}",
                        extra={
                            "error_type": e.error_type,
                            "details": e.details,
                            "function": func.__name__,
                            "timestamp": e.timestamp.isoformat()
                        }
                    )
                
                if reraise:
                    raise
                
                return {
                    "error": e.message,
                    "error_type": e.error_type,
                    "details": e.details
                } if default_return is None else default_return
                
            except Exception as e:
                error_msg = custom_message or f"Error in {func.__name__}"
                full_error_msg = f"{error_msg}: {str(e)}"
                
                if log_errors:
                    logger.error(
                        full_error_msg,
                        exc_info=True,
                        extra={
                            "function": func.__name__,
                            "error_type": type(e).__name__
                        }
                    )
                
                if reraise:
                    raise
                
                return {
                    "error": str(e),
                    "error_type": type(e).__name__
                } if default_return is None else default_return
                
        return wrapper
    return decorator


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls with parameters and execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with call logging
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = setup_logger(func.__module__)
        start_time = datetime.now()
        
        # Log function call (be careful with sensitive data)
        logger.info(
            f"Calling {func.__name__}",
            extra={
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
        )
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Completed {func.__name__} in {execution_time:.2f}s",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"Failed {func.__name__} after {execution_time:.2f}s: {str(e)}",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "success": False,
                    "error": str(e)
                }
            )
            raise
            
    return wrapper


def validate_financial_data(data: Dict[str, Any], tolerance: float = 1.0) -> Tuple[bool, str]:
    """
    Validate financial data for consistency with improved error handling.
    
    Args:
        data: Dictionary containing financial data
        tolerance: Tolerance for floating point comparisons
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Raises:
        DataValidationError: If validation fails with detailed information
    """
    logger = setup_logger(__name__)
    
    try:
        # Check if EGI = GPR - Vacancy Loss + Other Income
        gpr = float(data.get("gpr", 0))
        vacancy_loss = float(data.get("vacancy_loss", 0))
        other_income = float(data.get("other_income", 0))
        egi = float(data.get("egi", 0))
        
        expected_egi = gpr - vacancy_loss + other_income
        
        if abs(expected_egi - egi) > tolerance:
            error_msg = f"EGI inconsistency: Expected {expected_egi:.2f}, got {egi:.2f}"
            raise DataValidationError(
                error_msg,
                field="egi",
                expected=expected_egi,
                actual=egi
            )
        
        # Check if NOI = EGI - OpEx
        opex = float(data.get("opex", 0))
        noi = float(data.get("noi", 0))
        
        expected_noi = egi - opex
        
        if abs(expected_noi - noi) > tolerance:
            error_msg = f"NOI inconsistency: Expected {expected_noi:.2f}, got {noi:.2f}"
            raise DataValidationError(
                error_msg,
                field="noi", 
                expected=expected_noi,
                actual=noi
            )
        
        logger.info("Financial data validation passed", extra={"data_keys": list(data.keys())})
        return True, SUCCESS_MESSAGES["VALIDATION_PASSED"]
        
    except DataValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
        raise DataValidationError(f"Validation failed: {str(e)}")


def graceful_degradation(fallback_value: Any = None, operation_name: str = "operation") -> Callable:
    """
    Decorator for graceful degradation of non-critical operations.
    
    Args:
        fallback_value: Value to return if operation fails
        operation_name: Name of the operation for logging
        
    Returns:
        Decorated function that gracefully degrades on failure
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Non-critical {operation_name} failed, using fallback: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "operation": operation_name,
                        "fallback_used": True
                    }
                )
                return fallback_value
                
        return wrapper
    return decorator


def create_error_response(
    error: Union[str, Exception],
    error_type: str = "GENERAL_ERROR",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: Error message or exception
        error_type: Type of error
        details: Additional error details
        
    Returns:
        Standardized error response dictionary
    """
    if isinstance(error, Exception):
        error_message = str(error)
        if hasattr(error, 'error_type'):
            error_type = error.error_type
        if hasattr(error, 'details'):
            details = error.details
    else:
        error_message = error
    
    return {
        "error": error_message,
        "error_type": error_type,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
        "success": False
    }


def create_success_response(
    data: Any,
    message: str = SUCCESS_MESSAGES["DATA_LOADED"],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        metadata: Additional metadata
        
    Returns:
        Standardized success response dictionary
    """
    return {
        "data": data,
        "message": message,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
        "success": True
    } 