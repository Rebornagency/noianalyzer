"""
Sentry Configuration for NOI Analyzer
Handles error tracking, performance monitoring, and debugging
"""

import os
import sentry_sdk
from datetime import datetime
import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

# Try to import integrations, but make them optional
try:
    from sentry_sdk.integrations.streamlit import StreamlitIntegration
    HAS_STREAMLIT_INTEGRATION = True
except ImportError:
    HAS_STREAMLIT_INTEGRATION = False

# Try to import Starlette integration as fallback for Streamlit
try:
    from sentry_sdk.integrations.starlette import StarletteIntegration
    HAS_STARLETTE_INTEGRATION = True
except (ImportError, Exception) as e:
    # Catch both ImportError and DidNotEnable exceptions
    HAS_STARLETTE_INTEGRATION = False

try:
    from sentry_sdk.integrations.logging import LoggingIntegration
    HAS_LOGGING_INTEGRATION = True
except ImportError:
    HAS_LOGGING_INTEGRATION = False

try:
    from sentry_sdk.integrations.pandas import PandasIntegration
    HAS_PANDAS_INTEGRATION = True
except ImportError:
    HAS_PANDAS_INTEGRATION = False

try:
    # Only try to import FastAPI integration if starlette is available
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    HAS_FASTAPI_INTEGRATION = True
except (ImportError, Exception) as e:
    # Catch both ImportError and DidNotEnable exceptions
    HAS_FASTAPI_INTEGRATION = False

DEFAULT_SENTRY_DSN = "https://79cb707e8d1573757f94b1afcd1bd7bf@o4509419524653056.ingest.us.sentry.io/4509419570462720"

def init_sentry():
    """
    Initialize Sentry with comprehensive error tracking and performance monitoring.
    Call this function at the start of your application.
    """
    
    # Get DSN from environment variable or fallback to default
    sentry_dsn = os.getenv("SENTRY_DSN", DEFAULT_SENTRY_DSN)
    
    if not sentry_dsn:
        logger.error("No Sentry DSN provided and DEFAULT_SENTRY_DSN is empty. Sentry will not be initialized.")
        return False
    
    # Warn if using fallback DSN (env var missing)
    if os.getenv("SENTRY_DSN") is None:
        logger.warning("SENTRY_DSN env var not set – using built-in fallback DSN.")
    
    # Get environment info
    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    release = os.getenv("SENTRY_RELEASE", f"noi-analyzer@{datetime.now().strftime('%Y.%m.%d')}")
    
    try:
        # Build integrations list based on what's available
        integrations = []
        
        # Use Streamlit integration if available, otherwise don't use any web framework integration
        if HAS_STREAMLIT_INTEGRATION:
            integrations.append(StreamlitIntegration())
            logger.info("Using Streamlit integration for Sentry")
        else:
            logger.info("Streamlit integration not available for Sentry - proceeding without web framework integration")
        
        if HAS_LOGGING_INTEGRATION:
            integrations.append(LoggingIntegration(
                level=logging.WARNING,  # Only capture warnings and above
                event_level=logging.ERROR,  # Only send errors as events
            ))
        
        if HAS_PANDAS_INTEGRATION:
            integrations.append(PandasIntegration())
        
        if HAS_FASTAPI_INTEGRATION:
            integrations.append(FastApiIntegration(
                transaction_style="endpoint",
            ))
        
        # Configure Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            
            # Environment and release info
            environment=environment,
            release=release,
            
            # Integrations for better error tracking (only what's available)
            integrations=integrations,
            
            # Performance monitoring
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),  # 10% of transactions
            
            # Session tracking
            auto_session_tracking=True,
            
            # User context and PII
            send_default_pii=False,  # Don't send PII by default for privacy
            
            # Additional options
            attach_stacktrace=True,
            include_source_context=True,
            include_local_variables=True,
            
            # Filter out sensitive information
            before_send=filter_sensitive_data,
            
            # Set max breadcrumbs
            max_breadcrumbs=100,
            
            # Debug mode - disabled to reduce log noise
            debug=False,
            
            # Enable log capture for breadcrumbs / events
            _experiments={
                "enable_logs": True,
            },
        )
        
        # Set user context and tags
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("app.name", "NOI Analyzer")
            scope.set_tag("app.version", release)
            scope.set_tag("python.version", os.sys.version.split()[0])
            
        logger.info(f"Sentry initialized successfully for environment: {environment}")
        logger.info(f"Available integrations: {[type(i).__name__ for i in integrations]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {str(e)}")
        return False


def filter_sensitive_data(event, hint):
    """
    Filter out sensitive data before sending to Sentry.
    Remove API keys, passwords, financial data, etc.
    """
    
    # Remove sensitive environment variables
    if 'environment' in event:
        env_vars = event.get('environment', {})
        sensitive_keys = [
            'OPENAI_API_KEY', 'SENTRY_DSN', 'PASSWORD', 'SECRET', 
            'TOKEN', 'KEY', 'CREDENTIAL'
        ]
        
        for key in list(env_vars.keys()):
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                env_vars[key] = '[Filtered]'
    
    # Filter sensitive data from request data
    if 'request' in event:
        request = event['request']
        if 'data' in request and isinstance(request['data'], dict):
            # Remove financial data and personal information
            sensitive_fields = [
                'property_name', 'financial_data', 'amount', 'revenue', 
                'expense', 'noi', 'cash_flow', 'api_key'
            ]
            
            for field in sensitive_fields:
                if field in request['data']:
                    request['data'][field] = '[Filtered]'
    
    # Filter extra context
    if 'extra' in event:
        extra = event['extra']
        for key in list(extra.keys()):
            if 'financial' in key.lower() or 'data' in key.lower():
                if isinstance(extra[key], dict) and len(str(extra[key])) > 1000:
                    extra[key] = '[Large dataset filtered]'
    
    return event


def set_user_context(user_id=None, property_name=None, session_id=None):
    """
    Set user context for better error tracking.
    
    Args:
        user_id (str, optional): Unique identifier for the user
        property_name (str, optional): Name of the property being analyzed
        session_id (str, optional): Session identifier
    """
    with sentry_sdk.configure_scope() as scope:
        if user_id:
            scope.user = {"id": user_id}
        if property_name:
            scope.set_tag("property.name", property_name)
        if session_id:
            scope.set_tag("session.id", session_id)


def capture_exception(error, message=None, **kwargs):
    """
    Capture an exception with additional context.
    
    Args:
        error (Exception): The exception to capture
        message (str, optional): Additional message to include
        **kwargs: Additional context to include
    """
    if message:
        logger.error(f"{message}: {str(error)}")
        sentry_sdk.set_context("custom", kwargs)
        sentry_sdk.capture_message(message)
    
    sentry_sdk.capture_exception(error)


def capture_message(message, level="info", **kwargs):
    """
    Capture a custom message with additional context.
    
    Args:
        message (str): The message to capture
        level (str): The level of the message (info, warning, error)
        **kwargs: Additional context to include
    """
    logger.log(getattr(logging, level.upper()), message)
    sentry_sdk.set_context("custom", kwargs)
    sentry_sdk.capture_message(message, level=level)