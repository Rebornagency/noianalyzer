"""
Debug Logger Integration Example

This module demonstrates how to integrate the DebugContextLogger with a FastAPI application.
It provides a sample application with endpoints that trigger errors for testing purposes.
"""

import os
import logging
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from utils.debug_logger import DebugContextLogger, DebugLoggerSettings, create_test_endpoint

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_integration")

# Create a FastAPI app
app = FastAPI(
    title="Debug Logger Demo",
    description="An example API to demonstrate the debug logger",
    version="1.0.0"
)

# Define custom settings for the debug logger if needed
# If not, it will use defaults
debug_settings = DebugLoggerSettings(
    LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
    LOG_DIR=os.getenv("LOG_DIR", "logs"),
    ENV_VARS_TO_CAPTURE=[
        "ENV", "DEBUG", "PORT", "LOG_LEVEL", "ENVIRONMENT", 
        "RENDER_EXTERNAL_URL", "RENDER_SERVICE_ID"
    ]
)

# Initialize the debug logger with our app and settings
debug_logger = DebugContextLogger(app, debug_settings)

# Create a test endpoint that raises an exception
create_test_endpoint(app)

# Define a model for request validation errors
class Item(BaseModel):
    name: str
    price: float
    quantity: int

@app.get("/")
async def root():
    """Return a welcome message"""
    return {"message": "Debug Logger Demo API - Try /raise-error to test error handling"}

@app.get("/http-error")
async def http_error():
    """Raise an HTTP exception"""
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/items")
async def create_item(item: Item):
    """
    Create a new item (will fail with validation error if invalid data sent)
    Test with: curl -X POST "http://localhost:8000/items" -H "Content-Type: application/json" -d '{"name":"test"}'
    """
    return {"item": item, "created": True}

@app.get("/env-vars")
async def get_env_vars():
    """
    Return some environment variables to show what's captured in logs
    This is just for demo - in a real app you wouldn't expose this endpoint
    """
    return {
        "ENV": os.getenv("ENV", "development"),
        "DEBUG": os.getenv("DEBUG", "true"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }

@app.get("/chained-exception")
async def chained_exception():
    """Demonstrate a chained exception with multiple causes"""
    try:
        try:
            try:
                result = {}
                # This will raise a KeyError
                value = result["nonexistent_key"]
            except KeyError as ke:
                # Wrap KeyError with ValueError
                raise ValueError("Could not find required key") from ke
        except ValueError as ve:
            # Wrap ValueError with TypeError
            raise TypeError("Processing error with input data") from ve
    except TypeError as te:
        # Final wrapper exception
        raise HTTPException(status_code=500, detail="An error occurred processing the request") from te

if __name__ == "__main__":
    """
    Run the app with uvicorn
    Command: python debug_integration.py
    """
    import uvicorn
    logger.info("Starting debug integration demo app")
    uvicorn.run(app, host="0.0.0.0", port=8000) 