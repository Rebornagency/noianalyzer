#!/usr/bin/env python3
"""
Standalone Credit API Server - Zero Dependencies on Local Modules
All credit functionality implemented inline to avoid any import issues
"""

import os
import sqlite3
import logging
import datetime
import json
from typing import Dict, Any, Optional
from uuid import uuid4
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import stripe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('credit_api')

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Database setup
DATABASE_PATH = "credits.db"

class TransactionType(Enum):
    purchase = "purchase"
    usage = "usage"
    bonus = "bonus"
    refund = "refund"

@dataclass
class User:
    user_id: str
    email: str
    credits: int
    total_credits_purchased: int
    total_credits_used: int
    created_at: datetime.datetime
    free_trial_used: bool

@dataclass
class CreditPackage:
    package_id: str
    name: str
    credits: int
    price_cents: int
    stripe_price_id: str
    description: str

@dataclass  
class Transaction:
    transaction_id: str
    user_id: str
    type: TransactionType
    amount: int
    description: str
    created_at: datetime.datetime

class DatabaseService:
    def __init__(self):
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        try:
            # Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    credits INTEGER DEFAULT 0,
                    total_credits_purchased INTEGER DEFAULT 0,
                    total_credits_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    free_trial_used BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Credit packages table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS credit_packages (
                    package_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    credits INTEGER NOT NULL,
                    price_cents INTEGER NOT NULL,
                    stripe_price_id TEXT NOT NULL,
                    description TEXT
                )
            ''')
            
            # Transactions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized")
            
            # Create default packages
            self.create_default_packages()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_default_packages(self):
        packages = [
            ("starter-3", "Starter Pack", 3, 1500, "price_starter", "Perfect for trying out"),
            ("professional-10", "Professional Pack", 10, 3000, "price_professional", "Great for regular users"),
            ("business-40", "Business Pack", 40, 7500, "price_business", "Best value for power users")
        ]
        
        conn = self.get_connection()
        try:
            for package in packages:
                conn.execute('''
                    INSERT OR IGNORE INTO credit_packages 
                    (package_id, name, credits, price_cents, stripe_price_id, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', package)
            conn.commit()
        except Exception as e:
            logger.error(f"Error creating packages: {e}")
        finally:
            conn.close()
    
    def get_or_create_user(self, email: str) -> User:
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    email=row['email'],
                    credits=row['credits'],
                    total_credits_purchased=row['total_credits_purchased'],
                    total_credits_used=row['total_credits_used'],
                    created_at=datetime.datetime.fromisoformat(row['created_at']),
                    free_trial_used=bool(row['free_trial_used'])
                )
            else:
                # Create new user with free trial
                user_id = uuid4().hex
                free_credits = int(os.getenv("FREE_TRIAL_CREDITS", "3"))
                
                conn.execute('''
                    INSERT INTO users (user_id, email, credits, free_trial_used, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, email, free_credits, True, datetime.datetime.now()))
                
                conn.commit()
                
                return User(
                    user_id=user_id,
                    email=email,
                    credits=free_credits,
                    total_credits_purchased=0,
                    total_credits_used=0,
                    created_at=datetime.datetime.now(),
                    free_trial_used=True
                )
        except Exception as e:
            logger.error(f"Error with user {email}: {e}")
            raise
        finally:
            conn.close()
    
    def get_packages(self):
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM credit_packages ORDER BY credits ASC')
            packages = []
            for row in cursor.fetchall():
                packages.append(CreditPackage(
                    package_id=row['package_id'],
                    name=row['name'],
                    credits=row['credits'],
                    price_cents=row['price_cents'],
                    stripe_price_id=row['stripe_price_id'],
                    description=row['description']
                ))
            return packages
        finally:
            conn.close()
    
    def get_package_by_id(self, package_id: str):
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM credit_packages WHERE package_id = ?', (package_id,))
            row = cursor.fetchone()
            if row:
                return CreditPackage(
                    package_id=row['package_id'],
                    name=row['name'],
                    credits=row['credits'],
                    price_cents=row['price_cents'],
                    stripe_price_id=row['stripe_price_id'],
                    description=row['description']
                )
            return None
        finally:
            conn.close()
    
    def update_user_credits(self, user_id: str, credit_change: int, tx_type: TransactionType, description: str):
        conn = self.get_connection()
        try:
            # Get current credits
            cursor = conn.execute('SELECT credits FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            new_credits = row['credits'] + credit_change
            if new_credits < 0:
                return False
            
            # Update credits
            conn.execute('UPDATE users SET credits = ? WHERE user_id = ?', (new_credits, user_id))
            
            # Add transaction
            conn.execute('''
                INSERT INTO transactions (transaction_id, user_id, type, amount, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (uuid4().hex, user_id, tx_type.value, credit_change, description, datetime.datetime.now()))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating credits: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# Initialize services
db = DatabaseService()

# Initialize FastAPI app
app = FastAPI(
    title="Credit API",
    description="Standalone Credit System API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/")
async def root():
    return {"message": "Credit API is running"}

@app.get("/credits/{email}")
async def get_user_credits(email: str):
    try:
        user = db.get_or_create_user(email)
        return {
            "email": email,
            "credits": user.credits,
            "total_purchased": user.total_credits_purchased,
            "total_used": user.total_credits_used,
            "free_trial_used": user.free_trial_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/packages")
async def get_packages():
    try:
        packages = db.get_packages()
        return [
            {
                "package_id": pkg.package_id,
                "name": pkg.name,
                "credits": pkg.credits,
                "price_cents": pkg.price_cents,
                "price_dollars": pkg.price_cents / 100,
                "description": pkg.description
            } for pkg in packages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/credits/purchase")
async def purchase_credits(email: str = Form(...), package_id: str = Form(...)):
    try:
        user = db.get_or_create_user(email)
        package = db.get_package_by_id(package_id)
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Create Stripe checkout (simplified)
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=email,
            line_items=[{"price": package.stripe_price_id, "quantity": 1}],
            success_url="https://your-site.com/success",
            cancel_url="https://your-site.com/cancel",
            metadata={"user_id": user.user_id, "package_id": package_id, "email": email}
        )
        
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/credits/check")
async def check_credits(email: str = Form(...)):
    try:
        user = db.get_or_create_user(email)
        credits_needed = 1  # 1 credit per analysis
        
        return {
            "has_credits": user.credits >= credits_needed,
            "current_credits": user.credits,
            "needed_credits": credits_needed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/credits/use")
async def use_credits(email: str = Form(...), analysis_id: str = Form(...)):
    try:
        user = db.get_or_create_user(email)
        credits_needed = 1
        
        if user.credits < credits_needed:
            raise HTTPException(status_code=400, detail="Insufficient credits")
        
        success = db.update_user_credits(user.user_id, -credits_needed, TransactionType.usage, f"Analysis {analysis_id}")
        
        if success:
            return {"success": True, "message": "Credits deducted", "credits_deducted": credits_needed}
        else:
            raise HTTPException(status_code=400, detail="Failed to deduct credits")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment-success", response_class=HTMLResponse)
async def payment_success():
    return """
    <html>
        <head><title>Payment Successful</title></head>
        <body>
            <h1>✅ Payment successful!</h1>
            <p>Your credits have been added to your account.</p>
        </body>
    </html>
    """

@app.get("/payment-cancel", response_class=HTMLResponse)
async def payment_cancel():
    return """
    <html>
        <head><title>Payment Cancelled</title></head>
        <body>
            <h1>❌ Payment cancelled</h1>
            <p>No charges were made.</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run("api_server_credit_only:app", host="0.0.0.0", port=8000, reload=True) 