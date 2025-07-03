#!/usr/bin/env python3
"""
Minimal NOI Analyzer API Server for Credit System
This version only handles credits, payments, and basic endpoints - no document processing
"""

import os
import logging
import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Import only the credit system
from pay_per_use.api import router as pay_per_use_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_server_minimal')

# Initialize FastAPI app
app = FastAPI(
    title="NOI Analyzer Credit API",
    description="Minimal API for credit system and payments",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "service": "NOI Analyzer Credit API",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "NOI Analyzer Credit API is running"}

# Payment success/cancel pages
@app.get("/payment-success", response_class=HTMLResponse)
async def payment_success():
    """Success page after payment"""
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
                <p>Thank you. Your purchase is confirmed and credits have been added to your account.</p>
                <p>You can now return to the NOI Analyzer app and use your credits.</p>
                <p><a href="javascript:window.close()">Close Window</a></p>
            </div>
        </body>
    </html>
    """

@app.get("/payment-cancel", response_class=HTMLResponse)
async def payment_cancel():
    """Cancel page if payment cancelled"""
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
                <p>You can close this window and try again later if needed.</p>
                <p><a href="javascript:window.close()">Close Window</a></p>
            </div>
        </body>
    </html>
    """

# Include the credit system routes
app.include_router(pay_per_use_router)

if __name__ == "__main__":
    # For local development
    uvicorn.run(
        "api_server_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 