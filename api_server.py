"""
Data Extraction AI API Server (Enhanced + Fixed FilePreprocessor + Health Check + Debug Logger)

This file contains the FastAPI server for the Data Extraction AI project.
It includes endpoints for extracting financial data from various document types.

Enhancements:
- Added proper FilePreprocessor class definition
- Added health check endpoint for Render
- Fixed data structure for NOI Analyzer compatibility
- Improved error handling and logging
- Added comprehensive debug logging middleware
- Added test endpoint to demonstrate error logging
"""

import io
import os
import sys
import json
import time
import logging
import tempfile
import datetime
import traceback
import shutil
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, validator
import magic

# Local imports
from pay_per_use.api import pay_per_use_router
from utils.helpers import format_for_noi_comparison
from preprocessing_module import FilePreprocessor
from ai_extraction import GPTDataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API version
API_VERSION = "1.0.0"

# Create FastAPI app
app = FastAPI(
    title="Data Extraction AI API",
    description="API for extracting financial data from documents",
    version=API_VERSION
)

def validate_pdf_file(content: bytes) -> bool:
    """
    Validate PDF file with multiple checks:
    1. Magic bytes (%PDF-)
    2. Lightweight parsing of first page
    
    Args:
        content: PDF file content as bytes
        
    Returns:
        bool: True if valid PDF, False otherwise
    """
    try:
        # Check magic bytes
        if not content.startswith(b'%PDF-'):
            logger.warning("PDF validation failed: Invalid magic bytes")
            return False
        
        # Try lightweight parsing of first page
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                # Just check if we can access the first page
                if len(pdf.pages) > 0:
                    # Try to extract text from first page (lightweight operation)
                    first_page = pdf.pages[0]
                    first_page.extract_text()
        except Exception as e:
            logger.warning(f"PDF validation failed: Cannot parse first page - {str(e)}")
            return False
            
        return True
    except Exception as e:
        logger.warning(f"PDF validation failed: {str(e)}")
        return False

class ExtractionRequest(BaseModel):
    document_type: Optional[str] = None
    property_id: Optional[str] = None
    period: Optional[str] = None
    
    @validator('document_type')
    def validate_document_type(cls, v):
        if v is not None:
            valid_types = ['profit_loss', 'balance_sheet', 'rent_roll', 'operating_statement']
            if v.lower() not in [t.lower() for t in valid_types]:
                raise ValueError(f"Invalid document type: {v}. Must be one of: {', '.join(valid_types)}")
        return v
    
    @validator('period')
    def validate_period(cls, v):
        if v is not None:
            # Basic period format validation (YYYY-MM or YYYY-MM-DD)
            import re
            if not re.match(r'^\d{4}-\d{2}(-\d{2})?$', v):
                raise ValueError("Period must be in YYYY-MM or YYYY-MM-DD format")
        return v

@app.post("/api/v2/extraction/financials")
async def extract_financials_v2(
    file: UploadFile = File(...),
    request: ExtractionRequest = Depends()
):
    """
    Enhanced endpoint for financial data extraction
    """
    # Validate file size (50MB limit)
    max_file_size = 50 * 1024 * 1024  # 50MB
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    content = b''
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content += chunk
        file_size += len(chunk)
        
        # Check file size limit
        if file_size > max_file_size:
            raise HTTPException(status_code=413, detail=f"File too large (max {max_file_size / (1024*1024):.0f}MB)")
    
    # Reset file position
    file.file = io.BytesIO(content)
    
    # Check file type
    try:
        file_type = magic.from_buffer(content[:1024], mime=True)
        is_pdf = file_type == 'application/pdf'
        
        # Validate supported file types
        supported_types = (
            'application/pdf',
            'application/vnd.ms-excel', 
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv', 
            'text/plain'
        )
        
        if file_type not in supported_types:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {file_type}")
        
        # Additional PDF validation
        if is_pdf:
            if not validate_pdf_file(content):
                raise HTTPException(status_code=415, detail="Invalid PDF file - file may be corrupted or not a valid PDF")
                
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error checking file type: {str(e)}")
        raise HTTPException(status_code=415, detail=f"Error validating file type: {str(e)}")
    
    # Process the extraction with enhanced error handling
    temp_path = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Preprocess file
        preprocessor = FilePreprocessor()
        preprocessed_data = preprocessor.preprocess(
            temp_path, 
            content_type=file.content_type or '', 
            filename=file.filename or ''
        )
        
        # Extract data
        extractor = GPTDataExtractor(api_key=None)
        extraction_result = extractor.extract_data(
            preprocessed_data, 
            document_type=request.document_type, 
            period=request.period
        )
        
        # Add metadata
        extraction_result['metadata'] = {
            'filename': file.filename,
            'document_type': request.document_type,
            'period': extraction_result.get('period'),
            'property_id': request.property_id,
            'extraction_time': datetime.datetime.now().isoformat()
        }
        
        # Format for NOI Analyzer
        formatted_result = format_for_noi_comparison(extraction_result)
        
        # Remove temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        # Remove temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

# Add health check endpoint for Render
@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {"message": "Data Extraction AI API is running"}

@app.post("/extract")
async def extract_data(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    api_key: Optional[str] = Header(None)
):
    """
    Extract data from uploaded document (V1 endpoint)
    
    Args:
        file: Uploaded file
        document_type: Optional document type label
        api_key: OpenAI API key (optional)
        
    Returns:
        Extracted and formatted data
    """
    logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}")
    
    # Create temp directory for file processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded file to temp directory
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            # Create instances of the necessary classes
            preprocessor = FilePreprocessor()
            extractor = GPTDataExtractor(api_key=api_key)
            
            # Step 1: Preprocess the file
            preprocessed_data = preprocessor.preprocess(
                temp_file_path, 
                content_type=file.content_type, 
                filename=file.filename
            )
            
            # Step 2: Extract data using GPT
            extraction_result = extractor.extract_data(
                preprocessed_data,
                document_type=document_type,
            )
            
            # Step 3: Validate and format the extracted data
            final_result = validate_and_format_data(extraction_result)
            
            # Add metadata to the result
            final_result['metadata'] = {
                'filename': file.filename,
                'document_type': document_type,
                'period': extraction_result.get('period'),
                'classification_method': 'user_provided' if document_type else 'unknown'
            }
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Add test endpoints for the debug logger
@app.get("/debug/raise-error")
async def raise_error():
    """Test endpoint that raises an exception to demonstrate error logging"""
    # Create a chained exception
    try:
        # First level exception
        try:
            # Second level exception
            1 / 0
        except ZeroDivisionError as zde:
            # Wrap the zero division error
            raise ValueError("Invalid calculation during test") from zde
    except ValueError as ve:
        # Wrap the value error
        raise RuntimeError("Test exception to demonstrate error logging") from ve

@app.get("/debug/http-error")
async def http_error():
    """Test endpoint that raises an HTTP exception"""
    raise HTTPException(
        status_code=404, 
        detail="Resource not found - This is a test error to demonstrate logging"
    )

# -------------------------------------------------------------
# Simple success / cancel pages for Stripe Checkout redirects
# -------------------------------------------------------------

@app.get("/payment-success", response_class=HTMLResponse)
async def payment_success():
    """Minimal HTML page shown after a successful Stripe payment."""
    return """
    <html>
        <head>
            <title>Payment Successful</title>
            <meta charset='utf-8'/>
            <style>
                body {font-family: Arial, sans-serif; text-align: center; padding-top: 4rem;}
                .card {display: inline-block; padding: 2rem 3rem; border: 1px solid #e1e1e1; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);} 
                h1 {color: #28a745; margin-bottom: 1rem;}
                p {color: #444;}
                a {color: #0d6efd; text-decoration: none;}
            </style>
        </head>
        <body>
            <div class='card'>
                <h1>✅ Payment successful!</h1>
                <p>Thank you. Your purchase is confirmed and processing has started.</p>
                <p>Check your email for your report or updated credit balance.</p>
                <p><a href='/'>Return to app</a></p>
            </div>
            <script>
                // Auto-close tab after 5 s if it was opened in a new tab
                setTimeout(function(){ window.close(); }, 5000);
            </script>
        </body>
    </html>
    """

@app.get("/payment-cancel", response_class=HTMLResponse)
async def payment_cancel():
    """Minimal HTML page shown if the customer cancels at Stripe."""
    return """
    <html>
        <head>
            <title>Payment Cancelled</title>
            <meta charset='utf-8'/>
            <style>
                body {font-family: Arial, sans-serif; text-align: center; padding-top: 4rem;}
                .card {display: inline-block; padding: 2rem 3rem; border: 1px solid #e1e1e1; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);} 
                h1 {color: #dc3545; margin-bottom: 1rem;}
                p {color: #444;}
                a {color: #0d6efd; text-decoration: none;}
            </style>
        </head>
        <body>
            <div class='card'>
                <h1>❌ Payment cancelled</h1>
                <p>Your payment wasn't completed, so no charges were made.</p>
                <p>You can close this window or <a href='/'>return to the app</a> to try again.</p>
            </div>
        </body>
    </html>
    """

app.include_router(pay_per_use_router)

if __name__ == "__main__":
    import uvicorn
    # For local development
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
