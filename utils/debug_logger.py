"""
Debug Context Logger for FastAPI

This module provides comprehensive error logging capabilities for FastAPI applications.
It captures detailed context information about exceptions including request details,
environment variables, and stack traces, and logs them in a structured format.
"""

import os
import sys
import json
import traceback
import logging
from datetime import datetime
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import inspect

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from pydantic import BaseSettings, Field

# Setup logger
logger = logging.getLogger("debug_context_logger")


class DebugLoggerSettings(BaseSettings):
    """Settings for the debug logger"""
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR") 
    MASK_HEADERS: List[str] = Field(
        default=["authorization", "cookie", "x-api-key", "api-key"],
        env="MASK_HEADERS"
    )
    ENV_VARS_TO_CAPTURE: List[str] = Field(
        default=["ENV", "DEBUG", "PORT", "LOG_LEVEL", "ENVIRONMENT", "APP_ENV"],
        env="ENV_VARS_TO_CAPTURE"
    )
    MAX_REQUEST_BODY_SIZE: int = Field(default=10240, env="MAX_REQUEST_BODY_SIZE")  # 10KB default
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class DebugContextLogger:
    """
    Debug Context Logger captures detailed error context from FastAPI applications.
    
    It logs:
    - Full exception details with stack trace
    - Request information (method, path, headers, query params, body)
    - Environment variables
    - Timestamp and request ID
    
    Logs are output in JSON format to both stdout and rotating log files.
    """
    
    def __init__(self, app: FastAPI, settings: Optional[DebugLoggerSettings] = None):
        """
        Initialize the debug context logger.
        
        Args:
            app: The FastAPI application
            settings: Optional DebugLoggerSettings object. If not provided, defaults will be used.
        """
        self.app = app
        self.settings = settings or DebugLoggerSettings()
        self._setup_logger()
        self._setup_exception_handlers()
        self._setup_middleware()
        
        # Create log directory if it doesn't exist
        Path(self.settings.LOG_DIR).mkdir(exist_ok=True)
        
        logger.info(f"Debug Context Logger initialized with log_dir={self.settings.LOG_DIR}")
    
    def _setup_logger(self) -> None:
        """Configure the logger with appropriate handlers and formatters"""
        log_level = getattr(logging, self.settings.LOG_LEVEL)
        
        # Clear any existing handlers
        logger.handlers = []
        
        # Configure logger
        logger.setLevel(log_level)
        logger.propagate = False
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
        
        # File handler (daily rotating logs)
        log_file = Path(self.settings.LOG_DIR) / f"error_{datetime.now().strftime('%Y%m%d')}.json"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    def _setup_exception_handlers(self) -> None:
        """Register exception handlers with the FastAPI app"""
        # Handle validation errors
        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return await self._handle_exception(request, exc, status_code=422)
        
        # Handle HTTP exceptions
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return await self._handle_exception(request, exc, status_code=exc.status_code)
        
        # Handle all other exceptions
        @self.app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            return await self._handle_exception(request, exc, status_code=500)
    
    def _setup_middleware(self) -> None:
        """Add middleware to capture exceptions that might be missed by exception handlers"""
        class DebugContextMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: Callable):
                try:
                    return await call_next(request)
                except Exception as exc:
                    # This will catch exceptions that might be missed by the exception handlers
                    return await self._handle_exception(request, exc, status_code=500)
        
        self.app.add_middleware(DebugContextMiddleware)
    
    async def _handle_exception(
        self, 
        request: Request, 
        exc: Exception, 
        status_code: int = 500
    ) -> JSONResponse:
        """
        Handle an exception by logging it with context and returning an appropriate response.
        
        Args:
            request: The FastAPI request
            exc: The exception
            status_code: HTTP status code to return
            
        Returns:
            JSONResponse with error details
        """
        # Generate a unique ID for this error
        error_id = str(uuid.uuid4())
        
        # Get request details
        request_info = await self._get_request_info(request)
        
        # Get environment variables
        env_vars = self._get_environment_vars()
        
        # Format the exception
        exception_info = self._format_exception(exc)
        
        # Build the log data
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "error_id": error_id,
            "request": request_info,
            "exception": exception_info,
            "environment": env_vars,
        }
        
        # Log it
        logger.error(json.dumps(log_data))
        
        # Return an appropriate response
        return JSONResponse(
            status_code=status_code,
            content={
                "error": True,
                "message": str(exc),
                "error_id": error_id,
                "type": exception_info["type"]
            }
        )
        
    async def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """
        Extract relevant information from the request.
        
        Args:
            request: The FastAPI request
            
        Returns:
            Dictionary containing request details
        """
        headers = dict(request.headers)
        
        # Mask sensitive headers
        for header in self.settings.MASK_HEADERS:
            if header.lower() in headers:
                headers[header.lower()] = "********"
        
        # Basic request info
        info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "path_params": dict(request.path_params),
            "query_params": dict(request.query_params),
            "headers": headers,
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None,
            }
        }
        
        # Try to get the request body, but don't crash if it's not available
        try:
            body = await request.body()
            if len(body) <= self.settings.MAX_REQUEST_BODY_SIZE:
                try:
                    # Try to parse as JSON
                    info["body"] = json.loads(body)
                except:
                    # If not JSON, store as string if it's text
                    try:
                        info["body"] = body.decode("utf-8")
                    except:
                        info["body"] = f"<binary data of length {len(body)}>"
            else:
                info["body"] = f"<body too large: {len(body)} bytes>"
        except:
            info["body"] = "<body unavailable>"
            
        return info
        
    def _get_environment_vars(self) -> Dict[str, Any]:
        """
        Extract relevant environment variables.
        
        Returns:
            Dictionary of environment variables
        """
        env_vars = {}
        for var in self.settings.ENV_VARS_TO_CAPTURE:
            if var in os.environ:
                env_vars[var] = os.environ[var]
                
        # Get loaded Pydantic settings if available
        for frame_info in inspect.stack():
            frame = frame_info.frame
            for var_name, var_val in frame.f_locals.items():
                if isinstance(var_val, BaseSettings):
                    for key, value in var_val.dict().items():
                        if not isinstance(value, (dict, list)):
                            env_vars[f"config.{key}"] = str(value)
        
        return env_vars
        
    def _format_exception(self, exc: Exception) -> Dict[str, Any]:
        """
        Format exception details including the stack trace.
        
        Args:
            exc: The exception to format
            
        Returns:
            Dictionary with exception details
        """
        exc_type = type(exc).__name__
        exc_msg = str(exc)
        exc_traceback = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        
        # Handle chained exceptions
        cause_chain = []
        cause = exc.__cause__
        while cause:
            cause_info = {
                "type": type(cause).__name__,
                "message": str(cause),
                "traceback": "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
            }
            cause_chain.append(cause_info)
            cause = cause.__cause__
            
        return {
            "type": exc_type,
            "message": exc_msg,
            "traceback": exc_traceback,
            "cause_chain": cause_chain
        }


def create_test_endpoint(app: FastAPI) -> None:
    """
    Create a test endpoint that raises an exception.
    
    Args:
        app: The FastAPI application
    """
    @app.get("/raise-error")
    async def raise_error():
        """Test endpoint that raises an exception"""
        # Create a chained exception
        try:
            # First level exception
            try:
                # Second level exception
                1 / 0
            except ZeroDivisionError as zde:
                # Wrap the zero division error
                raise ValueError("Invalid calculation") from zde
        except ValueError as ve:
            # Wrap the value error
            raise RuntimeError("Something went wrong in the test endpoint") from ve 