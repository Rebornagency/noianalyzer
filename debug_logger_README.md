# FastAPI Debug Context Logger

A comprehensive error logging utility for FastAPI applications deployed on Render or other cloud services.

## Features

- **Detailed Error Context Capture**:
  - Full stack trace including chained exceptions
  - Request details (path, method, headers, query params, body)
  - Environment variables
  - Timestamp and unique error ID

- **JSON Structured Logging**:
  - Logs to both stdout and rotating log files
  - Formatted for easy parsing and analysis

- **FastAPI Integration**:
  - Global exception handling via middleware
  - No need to modify existing endpoints
  - Easy integration with a few lines of code

- **Privacy Protection**:
  - Masks sensitive headers like Authorization tokens
  - Configurable maximum request body size

## Installation

```bash
# No additional installation needed - part of this codebase
# Just import the module and integrate with your FastAPI app
```

## Quick Start

```python
from fastapi import FastAPI
from utils.debug_logger import DebugContextLogger, DebugLoggerSettings

# Create your FastAPI app
app = FastAPI()

# Initialize the debug logger
debug_logger = DebugContextLogger(app)

# Your routes go here
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Add a test endpoint for verification
@app.get("/raise-error")
async def raise_error():
    # This will trigger the debug logger
    1 / 0  # ZeroDivisionError
```

## Configuration

You can customize the logger with `DebugLoggerSettings`:

```python
debug_settings = DebugLoggerSettings(
    LOG_LEVEL="DEBUG",  # Logging level
    LOG_DIR="custom_logs",  # Where log files are stored
    MASK_HEADERS=["authorization", "cookie", "x-api-key"],  # Headers to mask
    ENV_VARS_TO_CAPTURE=["ENV", "DEBUG", "PORT", "RENDER_SERVICE_ID"],  # Environment vars to log
    MAX_REQUEST_BODY_SIZE=20480  # Max size of request body to log (bytes)
)

debug_logger = DebugContextLogger(app, debug_settings)
```

## Sample Log Output

```json
{
  "timestamp": "2023-06-15T12:34:56.789012",
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "request": {
    "method": "POST",
    "url": "http://localhost:8000/api/v2/extraction/financials",
    "path": "/api/v2/extraction/financials",
    "path_params": {},
    "query_params": {"debug": "true"},
    "headers": {
      "content-type": "application/json",
      "authorization": "********",
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "client": {
      "host": "127.0.0.1",
      "port": 53312
    },
    "body": {
      "document_type": "income_statement",
      "property_id": "123"
    }
  },
  "exception": {
    "type": "ValueError",
    "message": "Invalid document type",
    "traceback": "Traceback (most recent call last):\n  File \"/app/api_server.py\"...",
    "cause_chain": [
      {
        "type": "KeyError",
        "message": "'document_type'",
        "traceback": "..."
      }
    ]
  },
  "environment": {
    "ENV": "production",
    "DEBUG": "false",
    "PORT": "8000",
    "RENDER_SERVICE_ID": "srv-123abc",
    "config.LOG_LEVEL": "INFO"
  }
}
```

## Testing the Logger

You can use the included debug integration module and test endpoints:

1. Run the demo app:
   ```
   python debug_integration.py
   ```

2. Trigger various exceptions:
   ```
   curl http://localhost:8000/raise-error
   curl http://localhost:8000/http-error
   curl -X POST "http://localhost:8000/items" -H "Content-Type: application/json" -d '{"name":"test"}'
   curl http://localhost:8000/chained-exception
   ```

3. Check the logs:
   ```
   cat logs/error_YYYYMMDD.json
   ```

## Integration with Existing FastAPI App

To integrate the debug logger with an existing FastAPI application, simply add these lines:

```python
from utils.debug_logger import DebugContextLogger

# At the beginning of your app, after creating the FastAPI instance:
debug_logger = DebugContextLogger(app)
```

## Why You Need This

- Render logs often lack full error context
- Get better insight into what caused errors, what requests triggered them, and the app state at the time
- Speed up debugging in production with comprehensive context data
- Track chained exceptions to identify root causes
- Maintain a history of errors in structured format for analysis 