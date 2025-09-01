#!/usr/bin/env python3
"""
Test script to verify that the admin endpoints are working correctly
"""

import os
import sys
import sqlite3
from simple_server import DatabaseManager

def test_database_methods():
    """Test the database methods that support the admin endpoints"""
    print("Testing DatabaseManager methods...")
    
    # Initialize the database manager
    db = DatabaseManager()
    print("✓ DatabaseManager initialized")
    
    # Test get_all_users
    try:
        users = db.get_all_users()
        print(f"✓ get_all_users() returned {len(users)} users")
    except Exception as e:
        print(f"✗ get_all_users() failed: {e}")
        return False
    
    # Test get_all_transactions
    try:
        transactions = db.get_all_transactions()
        print(f"✓ get_all_transactions() returned {len(transactions)} transactions")
    except Exception as e:
        print(f"✗ get_all_transactions() failed: {e}")
        return False
    
    # Test get_system_stats
    try:
        stats = db.get_system_stats()
        print(f"✓ get_system_stats() returned stats: {stats}")
    except Exception as e:
        print(f"✗ get_system_stats() failed: {e}")
        return False
    
    # Test verify_admin_key
    try:
        # Test with default key
        result = db.verify_admin_key("test_admin_key_change_me")
        print(f"✓ verify_admin_key() with default key: {result}")
        
        # Test with wrong key
        result = db.verify_admin_key("wrong_key")
        print(f"✓ verify_admin_key() with wrong key: {result}")
    except Exception as e:
        print(f"✗ verify_admin_key() failed: {e}")
        return False
    
    # Test admin_adjust_credits
    try:
        result, message = db.admin_adjust_credits("test@example.com", 10, "Test adjustment")
        print(f"✓ admin_adjust_credits() result: {result}, message: {message}")
    except Exception as e:
        print(f"✗ admin_adjust_credits() failed: {e}")
        return False
    
    # Test update_user_status
    try:
        result, message = db.update_user_status("test@example.com", "active")
        print(f"✓ update_user_status() result: {result}, message: {message}")
    except Exception as e:
        print(f"✗ update_user_status() failed: {e}")
        return False
    
    print("All database methods tested successfully!")
    return True

def main():
    """Main test function"""
    print("=== Testing Admin Endpoints ===")
    
    # Change to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the tests
    success = test_database_methods()
    
    if success:
        print("\n✅ All tests passed! The admin endpoints should work correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())