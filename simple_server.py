#!/usr/bin/env python3
"""
NOI Analyzer Credit API - Production Ready
Zero external dependencies - uses only Python built-ins
Includes full credit system for financial analysis tool
"""

import os
import json
import sqlite3
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote

# Try to import Stripe, but handle gracefully if not available
try:
    import stripe
    STRIPE_AVAILABLE = True
    # Initialize Stripe with environment variable
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        STRIPE_AVAILABLE = False
        print("⚠️  Stripe secret key not found - Stripe integration disabled")
except ImportError:
    STRIPE_AVAILABLE = False
    print("⚠️  Stripe library not available - Stripe integration disabled")

# Credit packages for NOI Analyzer
CREDIT_PACKAGES = {
    "starter": {"credits": 5, "price": 1500, "name": "Starter Pack"},
    "professional": {"credits": 10, "price": 3000, "name": "Professional Pack"},
    "business": {"credits": 40, "price": 7500, "name": "Business Pack"}
}

# Map package IDs to environment variable names for Stripe price IDs
STRIPE_PRICE_ID_ENV_MAP = {
    "starter": "STRIPE_STARTER_PRICE_ID",
    "professional": "STRIPE_PROFESSIONAL_PRICE_ID",
    "business": "STRIPE_BUSINESS_PRICE_ID"
}

class DatabaseManager:
    def __init__(self, db_path="credits.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                email TEXT,
                package_type TEXT,
                credits INTEGER,
                amount INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_credits(self, email):
        """Get user's credit balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT credits FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else 0
    
    def add_credits(self, email, credits):
        """Add credits to user account"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (email, credits) 
            VALUES (?, COALESCE((SELECT credits FROM users WHERE email = ?), 0) + ?)
        ''', (email, email, credits))
        
        conn.commit()
        conn.close()
    
    def deduct_credits(self, email, credits=1):
        """Deduct credits from user account (for NOI analysis)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check current balance
        cursor.execute("SELECT credits FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        current_credits = result[0] if result else 0
        
        if current_credits < credits:
            conn.close()
            return False  # Insufficient credits
        
        # Deduct credits
        new_balance = current_credits - credits
        cursor.execute("UPDATE users SET credits = ? WHERE email = ?", (new_balance, email))
        
        conn.commit()
        conn.close()
        return True
    
    # ADMIN FUNCTIONS
    def get_all_users(self):
        """Get all users (admin function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT email, credits, created_at FROM users ORDER BY created_at DESC")
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0][:8] + '...',  # Simplified ID
                'email': row[0],
                'credits': row[1],
                'total_credits_purchased': row[1],  # Simplified
                'total_credits_used': 0,  # Simplified
                'status': 'active',
                'created_at': row[2],
                'last_active': row[2],
                'free_trial_used': row[1] > 0
            })
        
        conn.close()
        return users
    
    def get_all_transactions(self):
        """Get all transactions (admin function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, package_type, credits, amount, status, created_at 
            FROM transactions 
            ORDER BY created_at DESC
        ''')
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'transaction_id': row[0],
                'user_id': row[1][:8] + '...',
                'email': row[1],
                'type': row[2] or 'manual',
                'amount': row[3],
                'description': f"{row[2] or 'Manual adjustment'}: {row[3]} credits",
                'stripe_session_id': None,
                'created_at': row[6]
            })
        
        conn.close()
        return transactions
    
    def get_user_details(self, email):
        """Get detailed user information (admin function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT email, credits, created_at FROM users WHERE email = ?", (email,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return None
        
        # Get user transactions
        cursor.execute('''
            SELECT id, package_type, credits, amount, status, created_at 
            FROM transactions 
            WHERE email = ? 
            ORDER BY created_at DESC
        ''', (email,))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'transaction_id': row[0],
                'type': row[1] or 'manual',
                'amount': row[2],
                'description': f"{row[1] or 'Manual adjustment'}: {row[2]} credits",
                'stripe_session_id': None,
                'created_at': row[5]
            })
        
        conn.close()
        
        return {
            'user': {
                'user_id': user_row[0][:8] + '...',
                'email': user_row[0],
                'credits': user_row[1],
                'total_credits_purchased': user_row[1],
                'total_credits_used': 0,
                'status': 'active',
                'created_at': user_row[2],
                'last_active': user_row[2],
                'free_trial_used': user_row[1] > 0
            },
            'transactions': transactions
        }
    
    def admin_adjust_credits(self, email, credit_change, reason):
        """Admin function to manually adjust user credits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current credits
            cursor.execute("SELECT credits FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            
            if not result:
                # Create user if doesn't exist
                cursor.execute("INSERT INTO users (email, credits) VALUES (?, ?)", (email, max(0, credit_change)))
                new_balance = max(0, credit_change)
            else:
                current_credits = result[0]
                new_balance = max(0, current_credits + credit_change)
                cursor.execute("UPDATE users SET credits = ? WHERE email = ?", (new_balance, email))
            
            # Add transaction record
            transaction_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO transactions (id, email, package_type, credits, amount, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, email, 'admin_adjustment', credit_change, 0, 'completed'))
            
            conn.commit()
            conn.close()
            return True, new_balance
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
    
    def get_system_stats(self):
        """Get system statistics (admin function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # User stats
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(credits) FROM users")
        result = cursor.fetchone()[0]
        stats['total_outstanding_credits'] = result if result else 0
        
        cursor.execute("SELECT SUM(credits) FROM users")
        result = cursor.fetchone()[0]
        stats['total_credits_purchased'] = result if result else 0
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE credits = 0")
        used_credits_users = cursor.fetchone()[0]
        stats['total_credits_used'] = used_credits_users  # Simplified
        
        # Transaction stats
        cursor.execute("SELECT COUNT(*) FROM transactions")
        stats['total_transactions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE created_at > datetime('now', '-30 days')")
        stats['purchases_last_30_days'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-7 days')")
        stats['new_users_last_7_days'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def verify_admin_key(self, provided_key):
        """Verify admin API key"""
        admin_key = os.getenv("ADMIN_API_KEY", "test_admin_key_change_me")
        return provided_key == admin_key

class CreditAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = DatabaseManager()
        super().__init__(*args, **kwargs)
    
    def _send_json_response(self, data, status=200):
        """Send JSON response with CORS headers"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data)
        self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if path == "/health":
            self._send_json_response({
                "status": "healthy", 
                "message": "NOI Analyzer Credit API running successfully!",
                "server": "credit_api",
                "version": "1.0",
                "endpoints": ["/health", "/packages", "/credits", "/pay-per-use/credits/{email}"],
                "admin_endpoints": [
                    "/pay-per-use/admin/users",
                    "/pay-per-use/admin/transactions", 
                    "/pay-per-use/admin/user/{email}",
                    "/pay-per-use/admin/stats",
                    "/pay-per-use/admin/adjust-credits",
                    "/pay-per-use/admin/user-status"
                ]
            })
            
        elif path == "/packages":
            # Convert packages for frontend consumption
            packages_list = []
            for package_id, info in CREDIT_PACKAGES.items():
                per_credit = info['price'] / 100 / info['credits']
                packages_list.append({
                    "package_id": package_id,
                    "name": info['name'],
                    "credits": info['credits'],
                    "price_cents": info['price'],
                    "price_dollars": info['price'] / 100,
                    "per_credit_cost": round(per_credit, 2),
                    "description": f"Get {info['credits']} NOI analysis credits"
                })
            self._send_json_response(packages_list)
        
        elif path == "/credits":
            email = query_params.get('email', [None])[0]
            if not email:
                self._send_json_response({"error": "Email parameter required"}, 400)
                return
            
            credits = self.db.get_credits(email)
            self._send_json_response({
                "email": email, 
                "credits": credits,
                "message": f"User has {credits} NOI analysis credits"
            })
            
        elif path.startswith("/pay-per-use/credits/"):
            # RESTful endpoint
            email = path.split("/pay-per-use/credits/")[-1]
            if not email:
                self._send_json_response({"error": "Email required in URL"}, 400)
                return
                
            credits = self.db.get_credits(email)
            self._send_json_response({
                "email": email, 
                "credits": credits,
                "recent_transactions": []
            })
            
        elif path == "/pay-per-use/packages":
            # Main website expects this endpoint for packages
            packages_list = []
            for package_id, info in CREDIT_PACKAGES.items():
                per_credit = info['price'] / 100 / info['credits']
                packages_list.append({
                    "package_id": package_id,
                    "name": info['name'],
                    "credits": info['credits'],
                    "price_cents": info['price'],
                    "price_dollars": info['price'] / 100,
                    "per_credit_cost": round(per_credit, 2),
                    "description": f"Get {info['credits']} NOI analysis credits"
                })
            self._send_json_response(packages_list)
        
        # ADMIN ENDPOINTS
        elif path.startswith("/pay-per-use/admin/"):
            # Check admin authentication
            admin_key = query_params.get('admin_key', [None])[0]
            if not self.db.verify_admin_key(admin_key):
                self._send_json_response({"error": "Unauthorized"}, 403)
                return
            
            if path == "/pay-per-use/admin/users":
                users = self.db.get_all_users()
                self._send_json_response({"users": users})
            
            elif path == "/pay-per-use/admin/transactions":
                transactions = self.db.get_all_transactions()
                self._send_json_response({"transactions": transactions})
            
            elif path.startswith("/pay-per-use/admin/user/"):
                email = path.split("/pay-per-use/admin/user/")[-1]
                if not email:
                    self._send_json_response({"error": "Email required"}, 400)
                    return
                
                user_details = self.db.get_user_details(email)
                if user_details:
                    self._send_json_response(user_details)
                else:
                    self._send_json_response({"error": "User not found"}, 404)
            
            elif path == "/pay-per-use/admin/stats":
                stats = self.db.get_system_stats()
                self._send_json_response({"stats": stats})
            
            else:
                self._send_json_response({"error": "Admin endpoint not found"}, 404)
            
        else:
            self._send_json_response({
                "error": "Endpoint not found", 
                "available_endpoints": ["/health", "/packages", "/credits", "/pay-per-use/credits/{email}"],
                "admin_endpoints": [
                    "/pay-per-use/admin/users",
                    "/pay-per-use/admin/transactions",
                    "/pay-per-use/admin/user/{email}",
                    "/pay-per-use/admin/stats",
                    "/pay-per-use/admin/adjust-credits",
                    "/pay-per-use/admin/user-status"
                ]
            }, 404)
    
    def do_POST(self):
        """Handle POST requests for credit operations"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/deduct-credit":
            # For NOI analysis usage
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                email = data.get('email')
                if not email:
                    self._send_json_response({"error": "Email required"}, 400)
                    return
                
                success = self.db.deduct_credits(email, 1)
                if success:
                    remaining_credits = self.db.get_credits(email)
                    self._send_json_response({
                        "success": True,
                        "message": "Credit deducted for NOI analysis",
                        "remaining_credits": remaining_credits
                    })
                else:
                    self._send_json_response({
                        "success": False,
                        "error": "Insufficient credits",
                        "remaining_credits": 0
                    }, 402)
                    
            except Exception as e:
                self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
                
        elif path == "/pay-per-use/use-credits":
            # Main website expects this endpoint
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Handle both JSON and form data
                if 'application/json' in self.headers.get('Content-Type', ''):
                    data = json.loads(post_data.decode('utf-8'))
                else:
                    # Parse form data
                    from urllib.parse import parse_qs
                    parsed_data = parse_qs(post_data.decode('utf-8'))
                    data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed_data.items()}
                
                email = data.get('email')
                if not email:
                    self._send_json_response({"error": "Email required"}, 400)
                    return
                
                success = self.db.deduct_credits(email, 1)
                if success:
                    remaining_credits = self.db.get_credits(email)
                    self._send_json_response({
                        "success": True,
                        "message": "Credit deducted for NOI analysis",
                        "credits_remaining": remaining_credits,
                        "analysis_id": data.get('analysis_id', 'unknown')
                    })
                else:
                    self._send_json_response({
                        "success": False,
                        "error": "Insufficient credits",
                        "credits_remaining": 0
                    }, 402)
                    
            except Exception as e:
                self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
                
        elif path == "/pay-per-use/credits/purchase":
            # Credit purchase endpoint - now with proper Stripe integration
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Handle both JSON and form data (like the /pay-per-use/use-credits endpoint)
                if 'application/json' in self.headers.get('Content-Type', ''):
                    data = json.loads(post_data.decode('utf-8'))
                else:
                    # Parse form data
                    from urllib.parse import parse_qs
                    parsed_data = parse_qs(post_data.decode('utf-8'))
                    data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed_data.items()}
                
                email = data.get('email')
                package_id = data.get('package_id')
                
                if not email or not package_id:
                    self._send_json_response({"error": "Email and package_id required"}, 400)
                    return
                
                if package_id not in CREDIT_PACKAGES:
                    self._send_json_response({"error": "Invalid package_id"}, 400)
                    return
                
                # Check if Stripe is available and properly configured
                if STRIPE_AVAILABLE and stripe.api_key:
                    # Get the appropriate Stripe price ID directly from environment variables
                    env_var_name = STRIPE_PRICE_ID_ENV_MAP.get(package_id)
                    stripe_price_id = os.getenv(env_var_name) if env_var_name else None
                    
                    if not stripe_price_id:
                        self._send_json_response({
                            "error": "Stripe price ID not configured for this package",
                            "message": "Missing Stripe configuration - contact administrator",
                            "package": CREDIT_PACKAGES[package_id]
                        }, 500)
                        return
                    
                    # Build success URL with email parameter
                    base_success_url = os.getenv("CREDIT_SUCCESS_URL")
                    
                    if base_success_url:
                        # If environment variable is set, use it but ensure email is included
                        if "email=" not in base_success_url and "{email}" not in base_success_url:
                            separator = "&" if "?" in base_success_url else "?"
                            success_url_with_email = f"{base_success_url}{separator}email={quote(email)}"
                        elif "{email}" in base_success_url:
                            # Replace {email} placeholder with actual email
                            success_url_with_email = base_success_url.replace("{email}", quote(email))
                        else:
                            success_url_with_email = base_success_url
                    else:
                        # Default URL with both session_id and email
                        success_url_with_email = f"https://noianalyzer-1.onrender.com/credit-success?session_id={{CHECKOUT_SESSION_ID}}&email={quote(email)}"
                    
                    # Create Stripe checkout session
                    try:
                        session = stripe.checkout.Session.create(
                            payment_method_types=["card"],
                            mode="payment",
                            customer_email=email,
                            line_items=[{"price": stripe_price_id, "quantity": 1}],
                            success_url=success_url_with_email,
                            cancel_url=os.getenv("CREDIT_CANCEL_URL", "https://noianalyzer-1.onrender.com/payment-cancel"),
                            metadata={
                                "type": "credit_purchase",
                                "package_id": package_id,
                                "email": email
                            },
                        )
                        
                        # Return the checkout URL
                        self._send_json_response({
                            "checkout_url": session.url,
                            "package": CREDIT_PACKAGES[package_id]
                        })
                        
                    except stripe.error.StripeError as e:
                        self._send_json_response({
                            "error": "Stripe error",
                            "message": str(e),
                            "package": CREDIT_PACKAGES[package_id]
                        }, 500)
                    except Exception as e:
                        self._send_json_response({
                            "error": "Failed to create Stripe checkout session",
                            "message": str(e),
                            "package": CREDIT_PACKAGES[package_id]
                        }, 500)
                else:
                    # Stripe not available - return placeholder response with clear instructions
                    package_info = CREDIT_PACKAGES[package_id]
                    self._send_json_response({
                        "message": "Credit purchase endpoint ready",
                        "package": package_info,
                        "next_step": "Set up Stripe integration for real payments",
                        "checkout_url": None,
                        "setup_instructions": [
                            "1. Create a Stripe account at https://stripe.com",
                            "2. Create products in Stripe Dashboard for each credit package",
                            "3. Copy the price IDs from each product",
                            "4. Set STRIPE_SECRET_KEY and STRIPE_*_PRICE_ID environment variables",
                            "5. Restart the server"
                        ]
                    })
                
            except Exception as e:
                self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
        
        # ADMIN POST ENDPOINTS
        elif path.startswith("/pay-per-use/admin/"):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Parse form data
                from urllib.parse import parse_qs
                parsed_data = parse_qs(post_data.decode('utf-8'))
                data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed_data.items()}
                
                # Check admin authentication
                admin_key = data.get('admin_key')
                if not self.db.verify_admin_key(admin_key):
                    self._send_json_response({"error": "Unauthorized"}, 403)
                    return
                
                if path == "/pay-per-use/admin/adjust-credits":
                    email = data.get('email')
                    credit_change = data.get('credit_change')
                    reason = data.get('reason')
                    
                    if not email or not reason or credit_change is None:
                        self._send_json_response({"error": "Email, credit_change, and reason are required"}, 400)
                        return
                    
                    try:
                        credit_change = int(credit_change)
                    except ValueError:
                        self._send_json_response({"error": "credit_change must be a number"}, 400)
                        return
                    
                    if credit_change == 0:
                        self._send_json_response({"error": "Credit change cannot be zero"}, 400)
                        return
                    
                    success, result = self.db.admin_adjust_credits(email, credit_change, reason)
                    
                    if success:
                        self._send_json_response({
                            "success": True,
                            "message": f"Credits adjusted for {email}",
                            "credit_change": credit_change,
                            "new_balance": result,
                            "reason": reason
                        })
                    else:
                        self._send_json_response({"error": f"Failed to adjust credits: {result}"}, 400)
                
                elif path == "/pay-per-use/admin/user-status":
                    email = data.get('email')
                    status = data.get('status')
                    
                    if not email or not status:
                        self._send_json_response({"error": "Email and status are required"}, 400)
                        return
                    
                    # Implementation would go here
                    self._send_json_response({"message": "User status updated (placeholder)"})
                
                else:
                    self._send_json_response({"error": "Admin endpoint not found"}, 404)
            
            except Exception as e:
                self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
        
        else:
            self._send_json_response({"error": "Endpoint not found"}, 404)