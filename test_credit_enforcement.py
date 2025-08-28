#!/usr/bin/env python3
"""
Test script to verify credit enforcement is working properly.
Tests that users cannot process documents after their free trial is exhausted.
"""

import requests
import json
import time
from typing import Dict, Any

# Backend URL
BACKEND_URL = "http://localhost:8000"

def test_backend_connection() -> bool:
    """Test if backend is running"""
    try:
        print(f"Testing connection to {BACKEND_URL}/health...")
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text[:200]}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
        return False
    except Exception as e:
        print(f"Other error: {e}")
        return False

def get_user_credits(email: str) -> Dict[str, Any]:
    """Get user credit data"""
    try:
        print(f"Getting credits for {email}...")
        response = requests.get(f"{BACKEND_URL}/pay-per-use/credits/{email}", timeout=5)
        print(f"Credits response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Credits response data: {data}")
            return data
        else:
            print(f"Error response: {response.text}")
            return {}
    except Exception as e:
        print(f"Error getting credits: {e}")
        return {}

def deduct_credits(email: str) -> tuple[bool, str]:
    """Try to deduct credits"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/pay-per-use/use-credits",
            data={
                "email": email,
                "analysis_id": "test_analysis_123"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Credits deducted successfully"
        else:
            return False, f"Failed: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Error: {e}"

def run_credit_enforcement_test():
    """Run comprehensive credit enforcement test"""
    print("🧪 Starting Credit Enforcement Test")
    print("=" * 50)
    
    # Test 1: Check backend connection
    print("\n1️⃣ Testing backend connection...")
    if not test_backend_connection():
        print("❌ FAIL: Backend API is not running!")
        print("Please start the API server first: python api_server_minimal.py")
        return False
    print("✅ PASS: Backend API is running")
    
    # Test 2: New user gets free trial credits
    test_email = f"test_user_{int(time.time())}@example.com"
    print(f"\n2️⃣ Testing free trial credits for new user: {test_email}")
    
    initial_credits = get_user_credits(test_email)
    print(f"Initial credit data: {json.dumps(initial_credits, indent=2)}")
    
    if initial_credits.get("credits", 0) <= 0:
        print("❌ FAIL: New user did not receive free trial credits!")
        return False
    print(f"✅ PASS: New user received {initial_credits.get('credits', 0)} free trial credits")
    
    # Test 3: First credit deduction should work
    print(f"\n3️⃣ Testing first credit deduction...")
    success, message = deduct_credits(test_email)
    
    if not success:
        print(f"❌ FAIL: First credit deduction failed: {message}")
        return False
    print(f"✅ PASS: First credit deduction successful: {message}")
    
    # Test 4: Check remaining credits after deduction
    print(f"\n4️⃣ Checking remaining credits after deduction...")
    after_deduction = get_user_credits(test_email)
    remaining_credits = after_deduction.get("credits", 0)
    print(f"Credits after deduction: {remaining_credits}")
    
    if remaining_credits != (initial_credits.get("credits", 0) - 1):
        print(f"❌ FAIL: Credit balance not properly updated!")
        return False
    print(f"✅ PASS: Credit balance properly updated")
    
    # Test 5: Try to deduct credits when user has 0 credits (should fail)
    print(f"\n5️⃣ Testing credit deduction when user has 0 credits...")
    
    # If user still has credits, deduct them first
    while remaining_credits > 0:
        success, message = deduct_credits(test_email)
        if not success:
            print(f"❌ Unexpected error during credit depletion: {message}")
            return False
        remaining_credits -= 1
        print(f"Depleted 1 credit, remaining: {remaining_credits}")
    
    # Now try to deduct when user has 0 credits
    success, message = deduct_credits(test_email)
    
    if success:
        print(f"❌ FAIL: Credit deduction should have failed when user has 0 credits!")
        return False
    print(f"✅ PASS: Credit deduction properly failed when user has 0 credits: {message}")
    
    # Test 6: Verify user still has 0 credits
    print(f"\n6️⃣ Verifying final credit balance...")
    final_credits = get_user_credits(test_email)
    final_balance = final_credits.get("credits", 0)
    
    if final_balance != 0:
        print(f"❌ FAIL: User should have 0 credits but has {final_balance}")
        return False
    print(f"✅ PASS: User correctly has 0 credits remaining")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Credit enforcement is working correctly!")
    print("✅ Users cannot process documents after free trial is exhausted!")
    return True

if __name__ == "__main__":
    success = run_credit_enforcement_test()
    exit(0 if success else 1)