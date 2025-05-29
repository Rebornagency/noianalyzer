import os
import logging
import json
import streamlit as st
from typing import Dict, Any, List, Optional

from constants import (
    DEFAULT_API_CONFIG, ENV_VARS, ERROR_MESSAGES, SUCCESS_MESSAGES,
    FIELD_MAPPING, DATE_FORMAT, CURRENCY_FORMAT
)
from utils.error_handler import setup_logger, handle_errors, APIError, create_error_response
from utils.common import safe_float, deep_merge_dicts, validate_required_fields

# Setup logger
logger = setup_logger(__name__)

# Default configuration using constants
DEFAULT_CONFIG = {
    "extraction_api": DEFAULT_API_CONFIG,
    "data_formats": {
        "date_format": DATE_FORMAT,
        "currency_format": CURRENCY_FORMAT
    },
    "field_mapping": FIELD_MAPPING
}

# Global config instance
_config = None


@handle_errors(default_return=DEFAULT_CONFIG)
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration with fallback to environment variables and defaults.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Update our config with file values (deep merge)
                config = deep_merge_dicts(config, file_config)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
    
    # Override with environment variables
    env_prefix = "NOI_"
    for key in os.environ:
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix):].lower()
            parts = config_key.split('_')
            
            # Navigate to the right spot in the config
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value, attempting type conversion
            try:
                value = os.environ[key]
                # Try to convert to appropriate type
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)
                current[parts[-1]] = value
                logger.info(f"Set config from env var {key}")
            except Exception as e:
                logger.warning(f"Error setting config from env var {key}: {str(e)}")
    
    return config


def get_config() -> Dict[str, Any]:
    """Get the global configuration singleton"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


@handle_errors(default_return=DEFAULT_API_CONFIG["EXTRACTION_API_URL"])
def get_extraction_api_url() -> str:
    """
    Get the extraction API URL with improved error handling.
    
    Returns:
        Extraction API URL
    """
    # Priority: environment variable > session state > config
    url = (
        os.environ.get(ENV_VARS["EXTRACTION_API_URL"]) or
        getattr(st.session_state, 'extraction_api_url', None) or
        get_config()['extraction_api']['EXTRACTION_API_URL']
    )
    
    logger.info(f"Using extraction API URL: {url}")
    return url


@handle_errors(default_return=None)
def get_api_key() -> Optional[str]:
    """
    Get the extraction API key with improved security.
    
    Returns:
        API key or None if not found
    """
    key = (
        os.environ.get(ENV_VARS["EXTRACTION_API_KEY"]) or
        getattr(st.session_state, 'extraction_api_key', None)
    )
    
    if not key:
        logger.warning("No extraction API key found")
        return None
    
    logger.info("Found extraction API key")
    return key


@handle_errors(default_return=DEFAULT_API_CONFIG["MAX_RETRIES"])
def get_max_retries() -> int:
    """
    Get the maximum number of retries.
    
    Returns:
        Maximum retry count
    """
    retries = (
        os.environ.get(ENV_VARS["API_MAX_RETRIES"]) or
        get_config()['extraction_api']['MAX_RETRIES']
    )
    return int(retries)


@handle_errors(default_return=DEFAULT_API_CONFIG["TIMEOUT"])
def get_api_timeout() -> int:
    """
    Get the API timeout in seconds.
    
    Returns:
        Timeout in seconds
    """
    timeout = (
        os.environ.get(ENV_VARS["API_TIMEOUT"]) or
        get_config()['extraction_api']['TIMEOUT']
    )
    return int(timeout)


@handle_errors(default_return="")
def get_openai_api_key() -> str:
    """
    Get OpenAI API key from environment or session state with improved error handling.
    
    Returns:
        OpenAI API key
        
    Raises:
        APIError: If no API key is found in any source
    """
    # First priority: Use environment variable
    openai_key = os.environ.get(ENV_VARS["OPENAI_API_KEY"], "")
    if openai_key:
        logger.info("Using OpenAI API key from environment variable")
        return openai_key
        
    # Second priority: Check if API key is in session state (set via UI)
    if hasattr(st, 'session_state') and 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        logger.info("Using OpenAI API key from session state")
        return st.session_state.openai_api_key
    
    # If no key found, log warning but don't raise exception for backward compatibility
    logger.warning(ERROR_MESSAGES["API_KEY_MISSING"])
    return ""


@handle_errors()
def save_api_settings(openai_key=None, extraction_url=None, extraction_key=None):
    """
    Save API settings to session state with improved validation.
    
    Args:
        openai_key: OpenAI API key
        extraction_url: Extraction API URL
        extraction_key: Extraction API key
    """
    if openai_key:
        st.session_state.openai_api_key = openai_key
        logger.info("Saved OpenAI API key to session state")
        
    if extraction_url:
        # Clean and validate URL
        url = extraction_url.strip()
        if url.endswith('/extract'):
            url = url[:-8]
        elif url.endswith('/'):
            url = url[:-1]
            
        st.session_state.extraction_api_url = url
        logger.info(f"Saved extraction API URL to session state: {url}")
        
    if extraction_key:
        st.session_state.extraction_api_key = extraction_key
        logger.info("Saved extraction API key to session state")


@handle_errors(default_return=False)
def validate_api_configuration() -> bool:
    """
    Validate that required API configuration is available.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    required_config = {
        "extraction_api_url": get_extraction_api_url(),
        "openai_api_key": get_openai_api_key()
    }
    
    try:
        validate_required_fields(required_config, ["extraction_api_url"])
        
        # OpenAI key is optional for some operations, so just warn if missing
        if not required_config["openai_api_key"]:
            logger.warning("OpenAI API key not configured - some features may be unavailable")
        
        logger.info("API configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"API configuration validation failed: {str(e)}")
        return False


# Legacy function for backward compatibility
def safe_float(value: Any) -> float:
    """Legacy safe_float function - redirects to utils.common"""
    from utils.common import safe_float as common_safe_float
    return common_safe_float(value)
