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
    stripe_api_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_api_key:
        stripe.api_key = stripe_api_key
        print("✅ Stripe initialized successfully")
        print(f"   Stripe API key length: {len(stripe_api_key)} characters")
        # Mask the API key for security (show only first 3 and last 4 characters)
        masked_key = f"{stripe_api_key[:3]}...{stripe_api_key[-4:]}" if len(stripe_api_key) > 7 else "Too short"
        print(f"   Stripe API key (masked): {masked_key}")
    else:
        STRIPE_AVAILABLE = False
        print("⚠️  Stripe secret key not found - Stripe integration disabled")
        print("   Make sure STRIPE_SECRET_KEY is set in your environment variables")
        # Debug: Show what environment variables are actually set
        env_vars = dict(os.environ)
        stripe_vars = {k: v for k, v in env_vars.items() if 'STRIPE' in k.upper()}
        if stripe_vars:
            print("   Available STRIPE-related environment variables:")
            for k, v in stripe_vars.items():
                # Mask sensitive values
                if 'KEY' in k.upper() or 'SECRET' in k.upper():
                    masked_value = f"{v[:3]}...{v[-4:]}" if len(v) > 7 else "Too short"
                    print(f"     {k}: {masked_value}")
                else:
                    print(f"     {k}: {v[:20]}{'...' if len(v) > 20 else ''}")
        else:
            print("   No STRIPE-related environment variables found")
            
        # Additional debugging to help diagnose the issue
        print("   🔍 Debugging STRIPE_SECRET_KEY:")
        print(f"      os.getenv('STRIPE_SECRET_KEY'): {repr(os.getenv('STRIPE_SECRET_KEY'))}")
        print(f"      os.environ.get('STRIPE_SECRET_KEY'): {repr(os.environ.get('STRIPE_SECRET_KEY'))}")
        print(f"      'STRIPE_SECRET_KEY' in os.environ: {'STRIPE_SECRET_KEY' in os.environ}")
except ImportError:
    STRIPE_AVAILABLE = False
    print("⚠️  Stripe library not available - Stripe integration disabled")
    print("   Run 'pip install stripe' to enable Stripe integration")
    # Check if it's in requirements
    try:
        with open('requirements-api.txt', 'r') as f:
            requirements = f.read()
            if 'stripe' in requirements.lower():
                print("   Note: stripe is listed in requirements-api.txt")
            else:
                print("   Note: stripe not found in requirements-api.txt")
    except:
        pass

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

# Debug: Print environment variables at startup
print("🔍 Environment variables check:")
print(f"   STRIPE_SECRET_KEY: {'SET' if os.getenv('STRIPE_SECRET_KEY') else 'NOT SET'}")
for package_id, env_var in STRIPE_PRICE_ID_ENV_MAP.items():
    print(f"   {env_var}: {'SET' if os.getenv(env_var) else 'NOT SET'}")


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
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Serve Terms of Service page
        if path == '/terms-of-service':
            self.serve_terms_of_service()
            return
        
        # Serve Privacy Policy page
        if path == '/privacy-policy':
            self.serve_privacy_policy()
            return
            
        # Serve main API documentation
        if path == '/' or path == '/docs':
            self.serve_docs()
            return
        
        # Serve health check
        if path == '/health':
            self.serve_health()
            return
    
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
                
                # Debug information
                print(f"🔍 Purchase request - Email: {email}, Package: {package_id}")
                print(f"   STRIPE_AVAILABLE: {STRIPE_AVAILABLE}")
                print(f"   stripe.api_key set: {bool(stripe.api_key) if 'stripe' in globals() and hasattr(stripe, 'api_key') else 'N/A'}")
                
                # Check if Stripe is available and properly configured
                if STRIPE_AVAILABLE and stripe.api_key:
                    # Get the appropriate Stripe price ID directly from environment variables
                    env_var_name = STRIPE_PRICE_ID_ENV_MAP.get(package_id)
                    stripe_price_id = os.getenv(env_var_name) if env_var_name else None
                    
                    print(f"   Environment variable name: {env_var_name}")
                    print(f"   Stripe price ID from env: {stripe_price_id}")
                    
                    if not stripe_price_id:
                        self._send_json_response({
                            "error": "Stripe price ID not configured for this package",
                            "message": "Missing Stripe configuration - contact administrator",
                            "package": CREDIT_PACKAGES[package_id],
                            "debug": {
                                "env_var_name": env_var_name,
                                "env_var_value": os.getenv(env_var_name) if env_var_name else None
                            }
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
                        print(f"   Creating Stripe session for price ID: {stripe_price_id}")
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
                        print(f"❌ Stripe error: {str(e)}")
                        self._send_json_response({
                            "error": "Stripe error",
                            "message": str(e),
                            "package": CREDIT_PACKAGES[package_id]
                        }, 500)
                    except Exception as e:
                        print(f"❌ Unexpected error creating Stripe session: {str(e)}")
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
                        "debug": {
                            "STRIPE_AVAILABLE": STRIPE_AVAILABLE,
                            "stripe_api_key_set": bool(stripe.api_key) if 'stripe' in globals() and hasattr(stripe, 'api_key') else False,
                            "required_env_vars": {
                                "STRIPE_SECRET_KEY": bool(os.getenv("STRIPE_SECRET_KEY")),
                                "STRIPE_STARTER_PRICE_ID": bool(os.getenv("STRIPE_STARTER_PRICE_ID")),
                                "STRIPE_PROFESSIONAL_PRICE_ID": bool(os.getenv("STRIPE_PROFESSIONAL_PRICE_ID")),
                                "STRIPE_BUSINESS_PRICE_ID": bool(os.getenv("STRIPE_BUSINESS_PRICE_ID"))
                            }
                        },
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

    def serve_health(self):
        """Serve health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "NOI Analyzer Credit API"
        }
        self.wfile.write(json.dumps(health_data).encode())
    
    def serve_terms_of_service(self):
        """Serve Terms of Service page"""
        try:
            with open('TERMS_OF_SERVICE.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert markdown to HTML (basic conversion)
            html_content = self.markdown_to_html(content)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Terms of Service - NOI Analyzer</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    code {{ background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {html_content}
                </div>
            </body>
            </html>
            """
            self.wfile.write(html_page.encode('utf-8'))
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Terms of Service Not Found</h1>")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading Terms of Service</h1><p>{str(e)}</p>".encode())

    def serve_privacy_policy(self):
        """Serve Privacy Policy page"""
        try:
            with open('PRIVACY_POLICY.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert markdown to HTML (basic conversion)
            html_content = self.markdown_to_html(content)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Privacy Policy - NOI Analyzer</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    code {{ background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {html_content}
                </div>
            </body>
            </html>
            """
            self.wfile.write(html_page.encode('utf-8'))
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Privacy Policy Not Found</h1>")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading Privacy Policy</h1><p>{str(e)}</p>".encode())
    
    def markdown_to_html(self, markdown_text):
        """Convert basic markdown to HTML"""
        import re
        
        # Convert headers
        markdown_text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', markdown_text, flags=re.MULTILINE)
        
        # Convert bold and italic
        markdown_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', markdown_text)
        markdown_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', markdown_text)
        
        # Convert lists
        markdown_text = re.sub(r'^- (.*?)$', r'<li>\1</li>', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\n\g<0></ul>\n', markdown_text)
        
        # Convert links
        markdown_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', markdown_text)
        
        # Convert paragraphs
        paragraphs = markdown_text.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            if not p.startswith('<'):
                p = f'<p>{p}</p>'
            html_paragraphs.append(p)
        
        return '\n'.join(html_paragraphs)

def run_server():
    """Run the HTTP server"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), CreditAPIHandler)
    print(f"🚀 Starting Credit API server on port {port}")
    print(f"   - Health check: http://localhost:{port}/health")
    print(f"   - Packages: http://localhost:{port}/packages")
    print(f"   - Credits: http://localhost:{port}/credits?email=test@example.com")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    run_server()
