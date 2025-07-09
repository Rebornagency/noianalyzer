#!/usr/bin/env python3
"""
Ultra-Minimal Standalone Credit API Server
Zero external dependencies - uses only Python built-ins
"""

import os
import json
import logging
import sqlite3
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CREDIT_PACKAGES = {
    "starter": {"credits": 3, "price": 1500, "name": "Starter Pack"},
    "professional": {"credits": 10, "price": 3000, "name": "Professional Pack"},
    "business": {"credits": 40, "price": 7500, "name": "Business Pack"}
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
    
    def create_transaction(self, email, package_type, credits, amount):
        """Create a transaction record"""
        transaction_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (id, email, package_type, credits, amount, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (transaction_id, email, package_type, credits, amount))
        
        conn.commit()
        conn.close()
        
        return transaction_id

class CreditAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = DatabaseManager()
        super().__init__(*args, **kwargs)
    
    def _send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data)
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error(self, message, status=400):
        """Send error response"""
        self._send_json_response({"error": message}, status)
    
    def _get_post_data(self):
        """Get POST data from request - handle both JSON and form-encoded data"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                content_type = self.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    # Parse JSON data
                    return json.loads(post_data.decode('utf-8'))
                elif 'application/x-www-form-urlencoded' in content_type:
                    # Parse form-encoded data
                    from urllib.parse import parse_qs
                    parsed = parse_qs(post_data.decode('utf-8'))
                    # Convert lists to single values
                    return {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed.items()}
                else:
                    # Try to parse as JSON first, then as form data
                    try:
                        return json.loads(post_data.decode('utf-8'))
                    except json.JSONDecodeError:
                        from urllib.parse import parse_qs
                        parsed = parse_qs(post_data.decode('utf-8'))
                        return {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed.items()}
        except Exception as e:
            logger.error(f"Error parsing POST data: {e}")
        return {}
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
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
            self._send_json_response({"status": "healthy", "service": "credit-api"})
            
        elif path == "/packages" or path == "/pay-per-use/packages":
            # Convert CREDIT_PACKAGES dict into list with extra fields expected by UI
            packages_list = []
            for package_id, info in CREDIT_PACKAGES.items():
                per_credit = info['price'] / 100 / info['credits']
                packages_list.append({
                    "package_id": package_id,
                    "name": info['name'],
                    "credits": info['credits'],
                    "price_cents": info['price'],
                    "price_dollars": info['price'] / 100,
                    "per_credit_cost": per_credit,
                    "description": f"Top up {info['credits']} credits"
                })
            self._send_json_response(packages_list)
        
        elif path.startswith("/pay-per-use/credits/"):
            # Extract email from path
            email = path.split("/pay-per-use/credits/")[-1]
            if not email:
                self._send_error("Email required")
                return
            credits = self.db.get_credits(email)
            self._send_json_response({"email": email, "credits": credits, "recent_transactions": []})
        
        elif path == "/credits":
            email = query_params.get('email', [None])[0]
            if not email:
                self._send_error("Email parameter required")
                return
            credits = self.db.get_credits(email)
            self._send_json_response({"email": email, "credits": credits})
            
        elif path.startswith("/checkout/"):
            # Handle checkout page
            transaction_id = path.split("/checkout/")[-1]
            if not transaction_id:
                self._send_error("Transaction ID required", 404)
                return
            
            # For testing purposes, create a simple checkout page that auto-completes
            checkout_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Credit Purchase - NOI Analyzer</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 2rem; background: #f5f5f5; }}
                    .checkout-card {{ 
                        background: white; 
                        border-radius: 8px; 
                        padding: 2rem; 
                        max-width: 400px; 
                        margin: 2rem auto; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }}
                    .spinner {{ 
                        border: 4px solid #f3f3f3; 
                        border-top: 4px solid #3498db; 
                        border-radius: 50%; 
                        width: 40px; 
                        height: 40px; 
                        animation: spin 1s linear infinite; 
                        margin: 1rem auto;
                    }}
                    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                    .success {{ color: #28a745; }}
                    .processing {{ color: #6c757d; }}
                </style>
            </head>
            <body>
                <div class="checkout-card">
                    <h2>Credit Purchase</h2>
                    <div class="spinner"></div>
                    <p class="processing">Processing your payment...</p>
                    <p><small>Transaction ID: {transaction_id}</small></p>
                </div>
                
                <script>
                    // Simulate payment processing and auto-complete
                    setTimeout(function() {{
                        fetch('/complete-payment', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ transaction_id: '{transaction_id}' }})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                document.querySelector('.spinner').style.display = 'none';
                                document.querySelector('.processing').innerHTML = 
                                    '<div class="success">✅ Payment successful!<br/>' +
                                    data.credits_added + ' credits added to your account<br/>' +
                                    'Redirecting back to the app...</div>';
                                
                                // Redirect back to main app after 3 seconds
                                setTimeout(function() {{
                                    window.close(); // Try to close the tab first
                                    window.location.href = 'http://localhost:8501'; // Fallback redirect
                                }}, 3000);
                            }} else {{
                                document.querySelector('.processing').innerHTML = 
                                    '<div style="color: red;">❌ Payment failed: ' + data.error + '</div>';
                            }}
                        }})
                        .catch(error => {{
                            document.querySelector('.processing').innerHTML = 
                                '<div style="color: red;">❌ Payment processing error</div>';
                        }});
                    }}, 2000); // 2 second delay to simulate processing
                </script>
            </body>
            </html>
            """
            
            # Send HTML response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(checkout_html.encode('utf-8'))
        
        else:
            self._send_error("Endpoint not found", 404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        data = self._get_post_data()
        
        logger.info(f"POST request to {path}")
        logger.info(f"Request data: {data}")
        
        if path == "/create-checkout" or path == "/pay-per-use/credits/purchase":
            # Simplified checkout creation (mock Stripe response)
            if path == "/pay-per-use/credits/purchase":
                # Form data (x-www-form-urlencoded) used by Streamlit call
                email = data.get('email')
                package = data.get('package_id')
            else:
                email = data.get('email')
                package = data.get('package')
            
            logger.info(f"Purchase request - Email: {email}, Package: {package}")
            
            if not email:
                logger.error("Purchase failed: No email provided")
                self._send_error("Email is required")
                return
                
            if not package:
                logger.error("Purchase failed: No package_id provided")
                self._send_error("Package ID is required")
                return
                
            if package not in CREDIT_PACKAGES:
                logger.error(f"Purchase failed: Invalid package '{package}'. Available: {list(CREDIT_PACKAGES.keys())}")
                self._send_error(f"Invalid package '{package}'. Available packages: {', '.join(CREDIT_PACKAGES.keys())}")
                return
                
            package_info = CREDIT_PACKAGES[package]
            logger.info(f"Creating transaction for {email} - Package: {package_info['name']}")
            
            try:
                transaction_id = self.db.create_transaction(
                    email, package, package_info['credits'], package_info['price']
                )
                
                # Create a working local checkout URL instead of mock
                checkout_url = f"http://localhost:10000/checkout/{transaction_id}"
                
                logger.info(f"Transaction created successfully: {transaction_id}")
                
                response_data = {
                    "checkout_url": checkout_url, 
                    "transaction_id": transaction_id,
                    "package": package_info['name'],
                    "credits": package_info['credits'],
                    "price": package_info['price'] / 100
                }
                
                self._send_json_response(response_data)
                
            except Exception as e:
                logger.error(f"Failed to create transaction: {e}")
                self._send_error(f"Failed to create transaction: {str(e)}")
        
        elif path == "/pay-per-use/init":
            # No-op initializer for frontend; just return OK
            logger.info("System initialization requested")
            self._send_json_response({"status": "initialized", "packages": len(CREDIT_PACKAGES)})
            
        elif path == "/complete-payment":
            # Complete payment and add credits to user account
            transaction_id = data.get('transaction_id')
            
            logger.info(f"Completing payment for transaction: {transaction_id}")
            
            if not transaction_id:
                self._send_error("Transaction ID required")
                return
            
            try:
                # Get transaction details from database
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT email, package_type, credits, amount, status 
                    FROM transactions 
                    WHERE id = ?
                """, (transaction_id,))
                
                transaction = cursor.fetchone()
                
                if not transaction:
                    conn.close()
                    self._send_error("Transaction not found")
                    return
                
                email, package_type, credits, amount, status = transaction
                
                if status != 'pending':
                    conn.close()
                    self._send_error(f"Transaction already {status}")
                    return
                
                # Add credits to user account
                self.db.add_credits(email, credits)
                
                # Mark transaction as completed
                cursor.execute("""
                    UPDATE transactions 
                    SET status = 'completed' 
                    WHERE id = ?
                """, (transaction_id,))
                
                conn.commit()
                conn.close()
                
                new_balance = self.db.get_credits(email)
                
                logger.info(f"Payment completed successfully: {email} received {credits} credits, new balance: {new_balance}")
                
                self._send_json_response({
                    "success": True,
                    "credits_added": credits,
                    "new_balance": new_balance,
                    "email": email,
                    "package": package_type
                })
                
            except Exception as e:
                logger.error(f"Failed to complete payment: {e}")
                self._send_error(f"Payment completion failed: {str(e)}")
            
        elif path == "/mock-payment-success":
            # Mock payment success (for testing)
            transaction_id = data.get('transaction_id')
            email = data.get('email')
            
            logger.info(f"Mock payment success - Transaction: {transaction_id}, Email: {email}")
            
            if not transaction_id or not email:
                self._send_error("Transaction ID and email required")
                return
            
            # In real implementation, this would be handled by Stripe webhooks
            # For now, just add credits directly
            package = data.get('package', 'basic')
            if package in CREDIT_PACKAGES:
                credits = CREDIT_PACKAGES[package]['credits']
                self.db.add_credits(email, credits)
                
                logger.info(f"Added {credits} credits to {email}")
                
                self._send_json_response({
                    "success": True,
                    "credits_added": credits,
                    "new_balance": self.db.get_credits(email)
                })
            else:
                self._send_error("Invalid package")
                
        else:
            logger.warning(f"Unknown POST endpoint: {path}")
            self._send_error("Endpoint not found", 404)

def run_server():
    """Run the HTTP server"""
    port = int(os.environ.get('PORT', 10000))
    
    # Create custom handler class with database instance
    class Handler(CreditAPIHandler):
        def __init__(self, *args, **kwargs):
            self.db = DatabaseManager()
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
    
    server = HTTPServer(('0.0.0.0', port), Handler)
    
    logger.info(f"Starting credit API server on port {port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()

if __name__ == "__main__":
    run_server() 