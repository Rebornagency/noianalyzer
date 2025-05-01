import os
import logging
import json
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
        "url": "http://localhost:8000/api/v2/extraction/financials",
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
