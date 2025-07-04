#!/usr/bin/env python3
"""
Minimal NOI Analyzer API Server for Credit System Only
This version ONLY handles credits and payments - no document processing whatsoever
"""

import os
import logging
import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import only the core credit system modules without pipeline dependencies
from pay_per_use.models import CreditPackage
from pay_per_use.stripe_integration import create_credit_checkout_session, verify_webhook
from pay_per_use.credit_service import credit_service
from pay_per_use.database import db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_server_minimal')

# Initialize FastAPI app
app = FastAPI(
    title="NOI Analyzer Credit API",
    description="Minimal API for credit system and payments only",
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

# CREDIT SYSTEM ENDPOINTS ONLY

@app.post("/pay-per-use/init")
async def initialize_system():
    """Initialize the credit system with default packages"""
    try:
        db_service.create_default_packages()
        return {"message": "System initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pay-per-use/credits/{email}")
async def get_user_credits(email: str, request: Request):
    """Get user's current credit balance and info"""
    try:
        # Get IP address and user agent for tracking
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Pass IP info when getting user data
        user = credit_service.get_user_by_email(email, ip_address, user_agent)
        dashboard_data = credit_service.get_user_dashboard_data(email)
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "email": email,
            "credits": dashboard_data["user"].credits,
            "total_purchased": dashboard_data["user"].total_credits_purchased,
            "total_used": dashboard_data["user"].total_credits_used,
            "free_trial_used": dashboard_data["user"].free_trial_used,
            "recent_transactions": [
                {
                    "type": tx.type.value,
                    "amount": tx.amount,
                    "description": tx.description,
                    "created_at": tx.created_at.isoformat()
                } for tx in dashboard_data["recent_transactions"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pay-per-use/packages")
async def get_credit_packages():
    """Get available credit packages"""
    try:
        packages = credit_service.get_credit_packages()
        return [
            {
                "package_id": pkg.package_id,
                "name": pkg.name,
                "credits": pkg.credits,
                "price_cents": pkg.price_cents,
                "price_dollars": pkg.price_cents / 100,
                "description": pkg.description,
                "per_credit_cost": pkg.price_cents / pkg.credits / 100
            } for pkg in packages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pay-per-use/credits/purchase")
async def purchase_credits(
    request: Request,
    email: str = Form(...),
    package_id: str = Form(...)
):
    """Create checkout session for credit purchase"""
    try:
        # Get IP address for tracking
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Verify package exists
        package = db_service.get_package_by_id(package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Create or get user (this will track IP if it's a new user)
        user = credit_service.get_user_by_email(email, ip_address, user_agent)
        
        checkout_url = create_credit_checkout_session(email, package_id)
        return {"checkout_url": checkout_url, "package": package.name}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pay-per-use/check-credits")
async def check_user_credits_for_analysis(
    request: Request,
    email: str = Form(...)
):
    """Check if user has enough credits for analysis"""
    try:
        # Get IP address for tracking
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Create or get user with IP tracking for abuse prevention
        user = credit_service.get_user_by_email(email, ip_address, user_agent)
        
        has_credits, current_credits, message = credit_service.check_user_credits(email)
        
        if has_credits:
            return {
                "has_credits": True,
                "current_credits": current_credits,
                "needed_credits": credit_service.credits_per_analysis,
                "message": message
            }
        else:
            # Insufficient credits - return info for user to buy more
            packages = credit_service.get_credit_packages()
            return {
                "has_credits": False,
                "current_credits": current_credits,
                "needed_credits": credit_service.credits_per_analysis,
                "message": message,
                "available_packages": [
                    {
                        "package_id": pkg.package_id,
                        "name": pkg.name,
                        "credits": pkg.credits,
                        "price_dollars": pkg.price_cents / 100
                    } for pkg in packages
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pay-per-use/use-credits")
async def use_credits_for_analysis(
    email: str = Form(...),
    analysis_id: str = Form(...)
):
    """Deduct credits for an analysis"""
    try:
        success, message = credit_service.use_credits_for_analysis(email, analysis_id)
        if success:
            return {
                "success": True,
                "message": message,
                "credits_deducted": credit_service.credits_per_analysis
            }
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pay-per-use/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for credit purchases only"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = verify_webhook(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        session_type = metadata.get("type", "credit_purchase")
        
        if session_type == "credit_purchase":
            # Handle credit purchase
            user_id = metadata.get("user_id")
            package_id = metadata.get("package_id")
            email = metadata.get("email")
            
            if not user_id or not package_id:
                return JSONResponse(status_code=400, content={"error": "Missing credit purchase metadata"})
            
            # Add credits to user account
            success = credit_service.add_credits_from_purchase(user_id, package_id, session["id"])
            if success:
                return JSONResponse(status_code=200, content={"received": True, "credits_added": True})
            else:
                return JSONResponse(status_code=500, content={"error": "Failed to add credits"})

    return JSONResponse(status_code=200, content={"received": True})

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

# ADMIN ENDPOINTS FOR ABUSE PREVENTION
@app.get("/pay-per-use/admin/suspicious-ips")
async def get_suspicious_ips(min_trials: int = 3, admin_key: str = ""):
    """Get IP addresses with suspicious activity (admin only)"""
    # Simple admin authentication - in production use proper auth
    if admin_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        suspicious_ips = db_service.get_suspicious_ips(min_trials)
        return {"suspicious_ips": suspicious_ips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pay-per-use/admin/block-ip")
async def block_ip_address(
    ip_address: str = Form(...),
    reason: str = Form(...),
    admin_key: str = Form(...)
):
    """Block an IP address (admin only)"""
    # Simple admin authentication - in production use proper auth
    if admin_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        db_service.block_ip_address(ip_address, reason)
        return {"message": f"IP {ip_address} has been blocked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # For local development
    uvicorn.run(
        "api_server_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 