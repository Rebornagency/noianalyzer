# 📊 Logging Configuration for NOI Analyzer

This document explains how logging is configured in the NOI Analyzer application and how to view logs on both Render and Sentry.

## 🏗️ Architecture Overview

The NOI Analyzer uses a centralized logging approach with the following components:

1. **Centralized Configuration**: `logging_config.py` provides a unified logging setup
2. **Render Integration**: Logs are sent to stdout/stderr which Render automatically captures
3. **Sentry Integration**: Error tracking and performance monitoring through Sentry
4. **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 📋 Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened but the application continues
- **ERROR**: A serious problem that needs attention
- **CRITICAL**: A very serious error that may cause the application to stop

## 🎯 Viewing Logs

### On Render

Render automatically captures all logs sent to stdout/stderr:

1. Go to your Render dashboard
2. Select your service (either the main app or API)
3. Click on the "Logs" tab
4. You'll see real-time logs as they're generated

Example Render log output:
```
2023-06-15T10:30:45.123456Z INFO - credit_ui - User credit check successful: 5 credits remaining
2023-06-15T10:30:46.789012Z ERROR - simple_server - Stripe payment processing failed: Invalid card number
```

### On Sentry

Sentry captures error-level logs and performance data:

1. Go to your Sentry dashboard (sentry.io)
2. Select the "NOI Analyzer" project
3. View issues in real-time as they occur

Sentry captures:
- Error stack traces with local variables
- Performance metrics for slow operations
- User context and breadcrumbs
- Environment information

## ⚙️ Configuration

### Environment Variables

Set these environment variables in your Render service:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Sentry configuration (optional but recommended)
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Customizing Log Format

The default log format is:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Which produces logs like:
```
2023-06-15 10:30:45,123 - credit_ui - INFO - User credit check successful: 5 credits remaining
```

## 🔧 Troubleshooting

### Missing Logs on Render

1. Ensure your application is sending logs to stdout/stderr (not to files)
2. Check that you're looking at the correct service in Render
3. Verify that your log level is set appropriately

### Missing Logs in Sentry

1. Confirm that `SENTRY_DSN` is set correctly
2. Check that the Sentry SDK is properly initialized
3. Verify that you're sending logs at ERROR level or above for events

## 🛠️ Development Tips

### Testing Logging Locally

```bash
# Set log level for more verbose output
export LOG_LEVEL=DEBUG
streamlit run app.py

# Or for just the API server
export LOG_LEVEL=DEBUG
python start_credit_api.py
```

### Adding Custom Logging

In your Python modules:

```python
from logging_config import get_logger

logger = get_logger(__name__)

def my_function():
    logger.info("Processing started")
    try:
        # Do something
        logger.debug("Detailed processing info")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise
```

## 📈 Best Practices

1. **Use appropriate log levels**: Don't log everything at ERROR level
2. **Include context**: Add relevant information to log messages
3. **Avoid sensitive data**: Never log passwords, API keys, or personal information
4. **Monitor regularly**: Check both Render logs and Sentry for issues
5. **Set up alerts**: Configure Sentry alerts for critical errors

## 🆘 Support

If you're having issues with logging:

1. Check that all environment variables are set correctly
2. Verify that the `logging_config.py` file is in the correct location
3. Ensure that your Render services are properly configured
4. Contact support with specific error messages and log excerpts