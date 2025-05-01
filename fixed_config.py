import os
import logging
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config')

# Hardcoded OpenAI API key (will be used as primary source)
HARDCODED_OPENAI_API_KEY = "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"

# OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Default extraction API URL
DEFAULT_EXTRACTION_API_URL = os.environ.get("EXTRACTION_API_URL", "https://dataextractionai.onrender.com")

# Default API key for the extraction API
DEFAULT_API_KEY = os.environ.get("API_KEY", "")

# Maximum retries for API calls
MAX_API_RETRIES = int(os.environ.get("MAX_API_RETRIES", "3"))

# API request timeout in seconds
API_TIMEOUT = int(os.environ.get("API_TIMEOUT", "120"))

def get_openai_api_key():
    """
    Get OpenAI API key from hardcoded value, environment or session state.
    
    Returns:
        OpenAI API key
    """
    # First priority: Use hardcoded API key
    if HARDCODED_OPENAI_API_KEY:
        logger.info("Using hardcoded OpenAI API key")
        return HARDCODED_OPENAI_API_KEY
        
    # Second priority: Check if API key is in session state (set via UI)
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        logger.info("Using OpenAI API key from session state")
        return st.session_state.openai_api_key
        
    # Third priority: Use environment variable
    if OPENAI_API_KEY:
        logger.info("Using OpenAI API key from environment variable")
        return OPENAI_API_KEY
        
    logger.warning("No OpenAI API key found in any source")
    return ""

def get_extraction_api_url():
    """
    Get extraction API URL from environment or session state.
    
    Returns:
        Extraction API URL
    """
    # Check if API URL is in session state (set via UI)
    if 'extraction_api_url' in st.session_state and st.session_state.extraction_api_url:
        logger.info(f"Using extraction API URL from session state: {st.session_state.extraction_api_url}")
        api_url = st.session_state.extraction_api_url
    else:
        # Otherwise use environment variable
        api_url = DEFAULT_EXTRACTION_API_URL
        logger.info(f"Using default extraction API URL: {api_url}")
    
    # Ensure URL doesn't end with /extract as we add the specific endpoint in the API call
    if api_url and api_url.endswith('/extract'):
        api_url = api_url[:-8]
    elif api_url and api_url.endswith('/'):
        api_url = api_url[:-1]
            
    logger.info(f"Final extraction API base URL: {api_url}")
    return api_url

def get_api_key():
    """
    Get API key for extraction API from environment or session state.
    
    Returns:
        API key
    """
    # Check if API key is in session state (set via UI)
    if 'extraction_api_key' in st.session_state and st.session_state.extraction_api_key:
        logger.info("Using extraction API key from session state")
        return st.session_state.extraction_api_key
        
    # Otherwise use environment variable
    if not DEFAULT_API_KEY:
        logger.warning("Extraction API key not found in environment variables")
    return DEFAULT_API_KEY

def get_max_retries():
    """
    Get maximum number of retries for API calls.
    
    Returns:
        Maximum number of retries
    """
    return MAX_API_RETRIES

def get_api_timeout():
    """
    Get timeout for API requests in seconds.
    
    Returns:
        Timeout in seconds
    """
    return API_TIMEOUT

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
