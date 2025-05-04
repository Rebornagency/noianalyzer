import os
import logging
import json
import streamlit as st
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config')

# Default configuration
DEFAULT_CONFIG = {
    "extraction_api": {
        "url": "https://dataextractionai.onrender.com",
        "timeout": 60,
        "max_retries": 3,
        "batch_size": 5
    },
    "data_formats": {
        "date_format": "%Y-%m-%d",
        "currency_format": "USD"
    },
    "field_mapping": {
        "gpr": ["gross_potential_rent", "potential_rent", "scheduled_rent"],
        "opex": ["operating_expenses", "total_operating_expenses", "expenses_total"],
        "noi": ["net_operating_income", "noi", "net_income"],
        "egi": ["effective_gross_income", "adjusted_income", "effective_income"]
    }
}

# Hardcoded OpenAI API key - removed for security
HARDCODED_OPENAI_API_KEY = ""

# Move this function outside to make it globally available
def safe_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration with fallback to environment variables and defaults"""
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Update our config with file values (deep merge)
                deep_update(config, file_config)
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
            except Exception as e:
                logger.warning(f"Error setting config from env var {key}: {str(e)}")
    
    return config

def deep_update(target, source):
    """Deep update target dict with source data"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    return target

# Global config instance
_config = None

def get_config() -> Dict[str, Any]:
    """Get the global configuration singleton"""
    global _config
    if _config is None:
        _config = load_config()
    return _config

def get_extraction_api_url() -> str:
    """Get the extraction API URL"""
    return os.environ.get('EXTRACTION_API_URL') or get_config()['extraction_api']['url']

def get_api_key() -> Optional[str]:
    """Get the API key with improved security"""
    return os.environ.get('EXTRACTION_API_KEY')

def get_max_retries() -> int:
    """Get the maximum number of retries"""
    return int(os.environ.get('API_MAX_RETRIES') or get_config()['extraction_api']['max_retries'])

def get_api_timeout() -> int:
    """Get the API timeout in seconds"""
    return int(os.environ.get('API_TIMEOUT') or get_config()['extraction_api']['timeout'])

def get_openai_api_key() -> str:
    """
    Get OpenAI API key from environment or session state.
    
    Returns:
        OpenAI API key
    """
    # First priority: Use environment variable
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        logger.info("Using OpenAI API key from environment variable")
        return openai_key
        
    # Second priority: Check if API key is in session state (set via UI)
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        logger.info("Using OpenAI API key from session state")
        return st.session_state.openai_api_key
        
    # Third priority: Use hardcoded API key (empty in production)
    if HARDCODED_OPENAI_API_KEY:
        logger.info("Using hardcoded OpenAI API key")
        return HARDCODED_OPENAI_API_KEY
    
    logger.warning("No OpenAI API key found in any source")
    return ""

def save_api_settings(openai_key=None, extraction_url=None, extraction_key=None):
    """
    Save API settings to session state.
    
    Args:
        openai_key: OpenAI API key
        extraction_url: Extraction API URL
        extraction_key: Extraction API key
    """
    if openai_key:
        st.session_state.openai_api_key = openai_key
        logger.info("Saved OpenAI API key to session state")
        
    if extraction_url:
        # Ensure URL doesn't end with /extract as we add that in get_extraction_api_url
        if extraction_url.endswith('/extract'):
            extraction_url = extraction_url[:-8]
        elif extraction_url.endswith('/'):
            extraction_url = extraction_url[:-1]
            
        st.session_state.extraction_api_url = extraction_url
        logger.info(f"Saved extraction API URL to session state: {extraction_url}")
        
    if extraction_key:
        st.session_state.extraction_api_key = extraction_key
        logger.info("Saved extraction API key to session state")
