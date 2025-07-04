#!/usr/bin/env python3
"""
Simple script to start the credit API server
This will try different server options and start the first one that works
"""

import sys
import os

def start_ultra_minimal():
    """Start the ultra minimal API server (most reliable)"""
    print("🚀 Starting Ultra Minimal Credit API Server...")
    print("   - Port: 10000")
    print("   - No external dependencies")
    print("   - Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Import and run the ultra minimal server
        from ultra_minimal_api import run_server
        run_server()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start ultra minimal server: {e}")
        return False
    
    return True

def start_minimal():
    """Start the minimal FastAPI server"""
    print("🚀 Starting Minimal FastAPI Credit Server...")
    print("   - Port: 8000")
    print("   - Requires FastAPI and uvicorn")
    print("   - Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        import uvicorn
        from api_server_minimal import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError as e:
        print(f"❌ Missing dependencies for FastAPI server: {e}")
        print("💡 Try the ultra minimal server instead")
        return False
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start minimal server: {e}")
        return False
    
    return True

def main():
    """Main function to start the credit API"""
    print("NOI Analyzer Credit API Starter")
    print("=" * 50)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        server_type = sys.argv[1].lower()
        if server_type == "ultra":
            start_ultra_minimal()
            return
        elif server_type == "minimal":
            start_minimal()
            return
        else:
            print(f"❌ Unknown server type: {server_type}")
            print("Valid options: ultra, minimal")
            return
    
    # Try to start servers in order of reliability
    print("🔍 Auto-selecting best server option...")
    
    # First try ultra minimal (most reliable)
    print("\n1️⃣ Trying ultra minimal server...")
    if start_ultra_minimal():
        return
    
    # Then try minimal FastAPI
    print("\n2️⃣ Trying minimal FastAPI server...")
    if start_minimal():
        return
    
    # If all fail, show instructions
    print("\n❌ Could not start any server.")
    print("\n💡 Manual options:")
    print("   python start_credit_api.py ultra    # Start ultra minimal server")
    print("   python start_credit_api.py minimal  # Start FastAPI server")
    print("\n🔧 If you're still having issues:")
    print("   1. Check that you have Python installed")
    print("   2. Check that the required files exist")
    print("   3. For FastAPI server, install: pip install fastapi uvicorn")

if __name__ == "__main__":
    main() 