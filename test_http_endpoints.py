#!/usr/bin/env python3
"""
Test script to verify that the HTTP endpoints are working correctly
"""

import requests
import threading
import time
import os
import sys

def test_endpoints():
    """Test the HTTP endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing HTTP endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint working")
        else:
            print(f"✗ Health endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
    
    # Test packages endpoint
    try:
        response = requests.get(f"{base_url}/packages", timeout=5)
        if response.status_code == 200:
            packages = response.json()
            print(f"✓ Packages endpoint working, returned {len(packages)} packages")
        else:
            print(f"✗ Packages endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Packages endpoint failed: {e}")
    
    # Test admin endpoints with default key
    admin_key = "test_admin_key_change_me"
    
    # Test admin users endpoint
    try:
        response = requests.get(f"{base_url}/pay-per-use/admin/users?admin_key={admin_key}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Admin users endpoint working, returned {len(data.get('users', []))} users")
        elif response.status_code == 403:
            print("✗ Admin users endpoint failed: Unauthorized")
        else:
            print(f"✗ Admin users endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Admin users endpoint failed: {e}")
    
    # Test admin transactions endpoint
    try:
        response = requests.get(f"{base_url}/pay-per-use/admin/transactions?admin_key={admin_key}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Admin transactions endpoint working, returned {len(data.get('transactions', []))} transactions")
        elif response.status_code == 403:
            print("✗ Admin transactions endpoint failed: Unauthorized")
        else:
            print(f"✗ Admin transactions endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Admin transactions endpoint failed: {e}")
    
    # Test admin stats endpoint
    try:
        response = requests.get(f"{base_url}/pay-per-use/admin/stats?admin_key={admin_key}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Admin stats endpoint working, returned stats: {data.get('stats', {})}")
        elif response.status_code == 403:
            print("✗ Admin stats endpoint failed: Unauthorized")
        else:
            print(f"✗ Admin stats endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Admin stats endpoint failed: {e}")

def main():
    """Main test function"""
    print("=== Testing HTTP Endpoints ===")
    
    # Change to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Wait a moment for the server to start
    time.sleep(2)
    
    # Run the tests
    test_endpoints()
    
    print("\n✅ HTTP endpoint tests completed!")

if __name__ == "__main__":
    main()