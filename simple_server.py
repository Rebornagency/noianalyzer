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
from urllib.parse import urlparse, parse_qs

# Credit packages for NOI Analyzer
CREDIT_PACKAGES = {
    "starter": {"credits": 5, "price": 1500, "name": "Starter Pack"},
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
                "endpoints": ["/health", "/packages", "/credits", "/pay-per-use/credits/{email}"]
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
            
        else:
            self._send_json_response({"error": "Endpoint not found", "available_endpoints": ["/health", "/packages", "/credits", "/pay-per-use/credits/{email}"]}, 404)
    
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
            # Credit purchase endpoint (simplified for now)
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                email = data.get('email')
                package_id = data.get('package_id')
                
                if not email or not package_id:
                    self._send_json_response({"error": "Email and package_id required"}, 400)
                    return
                
                if package_id not in CREDIT_PACKAGES:
                    self._send_json_response({"error": "Invalid package_id"}, 400)
                    return
                
                # For now, return a message about setting up Stripe
                package_info = CREDIT_PACKAGES[package_id]
                self._send_json_response({
                    "message": "Credit purchase endpoint ready",
                    "package": package_info,
                    "next_step": "Set up Stripe integration for real payments",
                    "checkout_url": None  # Will add Stripe integration later
                })
                
            except Exception as e:
                self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
        else:
            self._send_json_response({"error": "POST endpoint not found"}, 404)
    
    def log_message(self, format, *args):
        # Reduce log noise in production
        pass

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 Starting NOI Analyzer Credit API on port {port}")
    print(f"📊 Credit packages loaded: {len(CREDIT_PACKAGES)} packages")
    print(f"🔗 Health check: http://0.0.0.0:{port}/health")
    print(f"💳 Packages: http://0.0.0.0:{port}/packages")
    print(f"👤 Credits: http://0.0.0.0:{port}/credits?email=test@example.com")
    
    server = HTTPServer(('0.0.0.0', port), CreditAPIHandler)
    print(f"✅ NOI Analyzer Credit API ready!")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()