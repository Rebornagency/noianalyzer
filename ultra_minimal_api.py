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
    "basic": {"credits": 10, "price": 500, "name": "Basic Pack"},
    "standard": {"credits": 25, "price": 1000, "name": "Standard Pack"},
    "premium": {"credits": 50, "price": 1800, "name": "Premium Pack"}
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
        """Get POST data from request"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                return json.loads(post_data.decode('utf-8'))
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
            
        else:
            self._send_error("Endpoint not found", 404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        data = self._get_post_data()
        
        if path == "/create-checkout" or path == "/pay-per-use/credits/purchase":
            # Simplified checkout creation (mock Stripe response)
            if path == "/pay-per-use/credits/purchase":
                # Form data (x-www-form-urlencoded) used by Streamlit call
                email = data.get('email')
                package = data.get('package_id')
            else:
                email = data.get('email')
                package = data.get('package')
            
            if not email or not package:
                self._send_error("Email and package required")
                return
            if package not in CREDIT_PACKAGES:
                self._send_error("Invalid package")
                return
            package_info = CREDIT_PACKAGES[package]
            transaction_id = self.db.create_transaction(
                email, package, package_info['credits'], package_info['price']
            )
            checkout_url = f"https://mock-checkout.example.com/pay/{transaction_id}"
            self._send_json_response({"checkout_url": checkout_url, "transaction_id": transaction_id})
        
        elif path == "/pay-per-use/init":
            # No-op initializer for frontend; just return OK
            self._send_json_response({"status": "initialized"})
            
        elif path == "/mock-payment-success":
            # Mock payment success (for testing)
            transaction_id = data.get('transaction_id')
            email = data.get('email')
            
            if not transaction_id or not email:
                self._send_error("Transaction ID and email required")
                return
            
            # In real implementation, this would be handled by Stripe webhooks
            # For now, just add credits directly
            package = data.get('package', 'basic')
            if package in CREDIT_PACKAGES:
                credits = CREDIT_PACKAGES[package]['credits']
                self.db.add_credits(email, credits)
                
                self._send_json_response({
                    "success": True,
                    "credits_added": credits,
                    "new_balance": self.db.get_credits(email)
                })
            else:
                self._send_error("Invalid package")
                
        else:
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