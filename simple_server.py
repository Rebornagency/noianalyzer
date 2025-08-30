#!/usr/bin/env python3
"""
Minimal HTTP Server - No External Dependencies
This is the simplest possible API server using only Python built-ins
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"status": "healthy", "message": "Render deployment successful!", "server": "minimal"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        # Override to reduce noise
        pass

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 Starting minimal server on port {port}")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ Server running at http://0.0.0.0:{port}/health")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()