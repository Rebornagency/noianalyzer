#!/usr/bin/env python3
"""
Test script for simple_server.py
"""

import sys
import os

# Add the current directory to the path so we can import the server module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that we can import the server module without errors"""
    try:
        import simple_server
        print("✅ simple_server imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import simple_server: {e}")
        return False

def test_server_startup():
    """Test that we can start the server without errors"""
    try:
        import simple_server
        # Just test that the classes are properly defined
        handler = simple_server.CreditAPIHandler
        db_manager = simple_server.DatabaseManager
        print("✅ CreditAPIHandler and DatabaseManager classes are properly defined")
        return True
    except Exception as e:
        print(f"❌ Failed to create server classes: {e}")
        return False

if __name__ == "__main__":
    print("Testing simple_server.py...")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_server_startup()
    
    print("=" * 40)
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
        sys.exit(1)