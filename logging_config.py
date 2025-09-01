"""
Comprehensive Logging Configuration for NOI Analyzer
This module provides centralized logging configuration that works well with both
Render's log capture and Sentry error tracking.
"""

import logging
import os
import sys
from typing import Optional

# Try to import sentry_sdk for integration
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None
    LoggingIntegration = None

def configure_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_sentry: bool = True
) -> logging.Logger:
    """
    Configure comprehensive logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        enable_sentry: Whether to enable Sentry integration
        
    Returns:
        logging.Logger: Configured root logger
    """
    
    # Determine log level from environment or parameter
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Default format that works well with Render and Sentry
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            # Stream handler for Render and console output
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Get root logger
    logger = logging.getLogger()
    
    # Configure Sentry integration if available and enabled
    if enable_sentry and SENTRY_AVAILABLE and sentry_sdk is not None and LoggingIntegration is not None:
        try:
            sentry_dsn = os.getenv('SENTRY_DSN')
            if sentry_dsn:
                # Configure Sentry logging integration
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                )
                
                # Initialize Sentry with logging integration
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[sentry_logging],
                    traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
                )
                
                logger.info(f"✅ Sentry logging integration enabled with DSN: {sentry_dsn[:20]}...")
            else:
                logger.warning("⚠️ Sentry DSN not found - Sentry integration disabled")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Sentry logging integration: {e}")
    
    # Log configuration details
    logger.info(f"📝 Logging configured with level: {log_level}")
    logger.info(f"📍 Running on platform: {get_platform_info()}")
    
    return logger

def get_platform_info() -> str:
    """
    Get information about the current platform/deployment environment.
    
    Returns:
        str: Platform information
    """
    if os.getenv('RENDER'):
        return "Render"
    elif os.getenv('DOCKER'):
        return "Docker"
    elif os.getenv('HEROKU'):
        return "Heroku"
    else:
        return "Local Development"

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name, properly configured.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        
    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)

# Convenience function for quick setup
def setup_logging():
    """
    Quick setup function for typical use cases.
    """
    return configure_logging()

# Initialize logging when module is imported
root_logger = configure_logging()