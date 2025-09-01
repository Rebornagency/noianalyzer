#!/usr/bin/env python3
"""
Test script to check the /pay-per-use/credits/{email} endpoint
"""

import requests
import time

def test_endpoint():
    """Test the /pay-per-use/credits/{email} endpoint"""
    try:
        print("Testing /pay-per-use/credits/test@example.com endpoint...")
        response = requests.get('http://localhost:10000/pay-per-use/credits/test@example.com', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Headers: {response.headers}")
        
        if response.status_code == 200:
            print("✅ Endpoint is working correctly!")
            return True
        else:
            print(f"❌ Endpoint returned status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_endpoint()