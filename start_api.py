#!/usr/bin/env python3
"""
Simple script to start the NOI Analyzer API server
"""

import uvicorn
import os

if __name__ == "__main__":
    # Set default port
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    
    print(f"🚀 Starting NOI Analyzer API server on {host}:{port}")
    print(f"📋 Health check will be available at: http://{host}:{port}/health")
    print(f"💳 Credit endpoints will be available at: http://{host}:{port}/pay-per-use/")
    print("🛑 Press Ctrl+C to stop")
    
    # Start the server
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    ) 