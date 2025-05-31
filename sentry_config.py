"""
Sentry Configuration for NOI Analyzer
Handles error tracking, performance monitoring, and debugging
"""

import os
import sentry_sdk
from sentry_sdk.integrations.streamlit import StreamlitIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.pandas import PandasIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from datetime import datetime
import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

def init_sentry():
    """
    Initialize Sentry with comprehensive error tracking and performance monitoring.
    Call this function at the start of your application.
    """
    
    # Get DSN from environment variable
    sentry_dsn = os.getenv("SENTRY_DSN")
    
    if not sentry_dsn:
        logger.warning("SENTRY_DSN environment variable not set. Sentry will not be initialized.")
        return False
    
    # Get environment info
    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    release = os.getenv("SENTRY_RELEASE", f"noi-analyzer@{datetime.now().strftime('%Y.%m.%d')}")
    
    try:
        # Configure Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            
            # Environment and release info
            environment=environment,
            release=release,
            
            # Integrations for better error tracking
            integrations=[
                StreamlitIntegration(
                    # Capture form submissions and button clicks
                    auto_enabling=True,
                ),
                LoggingIntegration(
                    # Capture logging statements as breadcrumbs
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
                PandasIntegration(
                    # Track pandas dataframe operations
                    auto_enabling=True,
                ),
                FastApiIntegration(
                    # For any FastAPI endpoints in your app
                    auto_enabling=True,
                    transaction_style="endpoint",
                ),
            ],
            
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
            
            # Debug mode (only in development)
            debug=environment == "development",
        )
        
        # Set user context and tags
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("app.name", "NOI Analyzer")
            scope.set_tag("app.version", release)
            scope.set_tag("python.version", os.sys.version.split()[0])
            
        logger.info(f"Sentry initialized successfully for environment: {environment}")
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
        user_id: Unique identifier for the user (optional)
        property_name: Current property being analyzed (optional)
        session_id: Session identifier (optional)
    """
    
    with sentry_sdk.configure_scope() as scope:
        scope.set_user({
            "id": user_id or "anonymous",
            "session_id": session_id,
        })
        
        if property_name:
            scope.set_tag("property.name", property_name[:50])  # Limit length
        
        logger.debug(f"Updated Sentry user context: user_id={user_id}, property={property_name}")


def add_breadcrumb(message, category="info", level="info", data=None):
    """
    Add a breadcrumb to track user actions and application flow.
    
    Args:
        message: Description of the action
        category: Category of the breadcrumb (navigation, file_upload, processing, etc.)
        level: Severity level (debug, info, warning, error)
        data: Additional data (optional)
    """
    
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def capture_exception_with_context(exception, context=None, tags=None):
    """
    Capture an exception with additional context.
    
    Args:
        exception: The exception to capture
        context: Additional context dictionary
        tags: Additional tags dictionary
    """
    
    with sentry_sdk.configure_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, str(value))
        
        sentry_sdk.capture_exception(exception)


def capture_message_with_context(message, level="info", context=None, tags=None):
    """
    Capture a message with additional context.
    
    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        context: Additional context dictionary
        tags: Additional tags dictionary
    """
    
    with sentry_sdk.configure_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, str(value))
        
        sentry_sdk.capture_message(message, level)


def monitor_performance(operation_name):
    """
    Context manager for monitoring performance of operations.
    
    Usage:
        with monitor_performance("document_processing"):
            # Your code here
            process_documents()
    """
    
    return sentry_sdk.start_transaction(
        op="function",
        name=operation_name,
        sampled=True
    ) 