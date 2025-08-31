#!/usr/bin/env python3
"""
Test Script for Admin Dashboard Endpoints
Verifies all admin functionality is working correctly
"""

import os
import requests
import json
from datetime import datetime

# Configuration
API_URL = os.getenv("CREDIT_API_URL", "http://localhost:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "test_admin_key_change_me")

def test_endpoint(endpoint, method="GET", data=None, params=None):
    """Test an API endpoint"""
    try:
        url = f"{API_URL}{endpoint}"
        
        if method == "GET":
            if params is None:
                params = {}
            params["admin_key"] = ADMIN_API_KEY
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            if data is None:
                data = {}
            data["admin_key"] = ADMIN_API_KEY
            response = requests.post(url, data=data, timeout=10)
        
        return response.status_code, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return 0, str(e)

def main():
    """Test all admin endpoints"""
    print("🧪 Testing Admin Dashboard Endpoints")
    print("=" * 50)
    
    tests = [
        # Basic endpoints
        ("Health Check", "/health", "GET", None, None),
        ("Packages", "/packages", "GET", None, None),
        
        # Admin endpoints
        ("System Stats", "/pay-per-use/admin/stats", "GET", None, None),
        ("All Users", "/pay-per-use/admin/users", "GET", None, {"limit": 10}),
        ("All Transactions", "/pay-per-use/admin/transactions", "GET", None, {"limit": 10}),
        ("Suspicious IPs", "/pay-per-use/admin/suspicious-ips", "GET", None, {"min_trials": 2}),
    ]
    
    results = []
    
    for test_name, endpoint, method, data, params in tests:
        print(f"\n🔍 Testing: {test_name}")
        status, response = test_endpoint(endpoint, method, data, params)
        
        if status == 200:
            print(f"✅ {test_name}: SUCCESS")
            if isinstance(response, dict):
                # Print relevant info
                if 'stats' in response:
                    stats = response['stats']
                    print(f"   📊 Users: {stats.get('total_users', 0)}")
                    print(f"   💳 Outstanding Credits: {stats.get('total_outstanding_credits', 0)}")
                elif 'users' in response:
                    users = response['users']
                    print(f"   👥 Found {len(users)} users")
                elif 'transactions' in response:
                    transactions = response['transactions']
                    print(f"   📄 Found {len(transactions)} transactions")
                elif 'suspicious_ips' in response:
                    ips = response['suspicious_ips']
                    print(f"   🚨 Found {len(ips)} suspicious IPs")
                else:
                    print(f"   📋 Response: {type(response)}")
            results.append((test_name, True, status))
        elif status == 403:
            print(f"🔒 {test_name}: UNAUTHORIZED (check ADMIN_API_KEY)")
            results.append((test_name, False, "Unauthorized"))
        else:
            print(f"❌ {test_name}: FAILED (Status: {status})")
            print(f"   Error: {response}")
            results.append((test_name, False, status))
    
    # Test manual credit adjustment with a fake user
    print(f"\n🔍 Testing: Manual Credit Adjustment")
    test_data = {
        "email": "test@example.com",
        "credit_change": 5,
        "reason": "Test credit adjustment"
    }
    status, response = test_endpoint("/pay-per-use/admin/adjust-credits", "POST", test_data)
    
    if status == 200:
        print(f"✅ Manual Credit Adjustment: SUCCESS")
        print(f"   💳 Response: {response}")
        results.append(("Manual Credit Adjustment", True, status))
    elif status == 400:
        print(f"ℹ️ Manual Credit Adjustment: Expected failure (user doesn't exist)")
        results.append(("Manual Credit Adjustment", True, "Expected failure"))
    else:
        print(f"❌ Manual Credit Adjustment: FAILED (Status: {status})")
        print(f"   Error: {response}")
        results.append(("Manual Credit Adjustment", False, status))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, status in results:
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}: {status}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Admin dashboard is ready to use.")
        print("\nNext steps:")
        print("1. Set your ADMIN_API_KEY environment variable")
        print("2. Start your API server: python api_server_minimal.py")
        print("3. Start your admin dashboard: streamlit run admin_dashboard.py")
    else:
        print("⚠️ Some tests failed. Check your configuration.")
        print("\nTroubleshooting:")
        print("1. Ensure API server is running")
        print("2. Check ADMIN_API_KEY matches between client and server")
        print("3. Verify database is accessible")

if __name__ == "__main__":
    main()