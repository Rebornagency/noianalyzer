#!/usr/bin/env python3
"""
Test script for the credit API system
Run this to verify the API server is working correctly
"""

import requests
import json
import sys
import os

def test_api_server(base_url="http://localhost:8000"):
    """Test the credit API server endpoints"""
    print(f"Testing API server at: {base_url}")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        return False
    
    # Test 2: Get packages
    print("\n2. Testing packages endpoint...")
    try:
        response = requests.get(f"{base_url}/pay-per-use/packages", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            packages = response.json()
            print(f"   Found {len(packages)} packages:")
            for pkg in packages:
                print(f"     - {pkg['name']}: {pkg['credits']} credits for ${pkg['price_dollars']}")
            print("   ✅ Packages endpoint working")
        else:
            print(f"   ❌ Packages endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Packages request failed: {e}")
    
    # Test 3: Test user credits (with test email)
    test_email = "test@example.com"
    print(f"\n3. Testing user credits endpoint with email: {test_email}")
    try:
        response = requests.get(f"{base_url}/pay-per-use/credits/{test_email}", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            credits_data = response.json()
            print(f"   Credits: {credits_data.get('credits', 0)}")
            print("   ✅ User credits endpoint working")
        else:
            print(f"   ❌ User credits failed: {response.text}")
    except Exception as e:
        print(f"   ❌ User credits request failed: {e}")
    
    # Test 4: Test purchase endpoint (simulation)
    print(f"\n4. Testing purchase endpoint with test data...")
    try:
        # Use form data like the UI does
        response = requests.post(
            f"{base_url}/pay-per-use/credits/purchase",
            data={"email": test_email, "package_id": "basic"},
            timeout=10,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Checkout URL received: {result.get('checkout_url', 'N/A')}")
            print("   ✅ Purchase endpoint working")
        else:
            print(f"   ❌ Purchase failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Purchase request failed: {e}")
    
    print("\n" + "=" * 50)
    print("API test completed!")
    return True

def start_ultra_minimal_server():
    """Start the ultra minimal API server"""
    print("Starting ultra minimal API server...")
    try:
        import ultra_minimal_api
        print("Ultra minimal API module loaded successfully")
        print("Starting server on port 10000...")
        ultra_minimal_api.run_server()
    except ImportError as e:
        print(f"Failed to import ultra_minimal_api: {e}")
    except Exception as e:
        print(f"Failed to start server: {e}")

def main():
    """Main test function"""
    print("NOI Analyzer Credit API Test")
    print("=" * 50)
    
    # First, try to test the default API endpoint
    if test_api_server("http://localhost:8000"):
        print("✅ API server at localhost:8000 is working!")
        return
    
    # If that fails, try the ultra minimal server port
    print("\nTrying ultra minimal server port...")
    if test_api_server("http://localhost:10000"):
        print("✅ API server at localhost:10000 is working!")
        return
    
    # If both fail, show instructions
    print("\n❌ No API server found running.")
    print("\nTo fix this, run one of these commands in a separate terminal:")
    print("1. python api_server_minimal.py")
    print("2. python ultra_minimal_api.py")
    print("3. python api_server.py")
    
    print("\nOr set the BACKEND_URL environment variable to point to your API server.")

if __name__ == "__main__":
    main() 