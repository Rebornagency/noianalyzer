#!/usr/bin/env python3
"""
Simple inline test to verify credit enforcement
"""

import requests
import time

def quick_test():
    """Quick test of credit enforcement"""
    print("🧪 Quick Credit Enforcement Test")
    print("=" * 40)
    
    # Test connection first
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print(f"✅ Backend is running: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test with a new user email
    test_email = f"test_{int(time.time())}@example.com"
    print(f"📧 Testing with email: {test_email}")
    
    try:
        # Get initial credits
        response = requests.get(f"http://localhost:8000/pay-per-use/credits/{test_email}", timeout=3)
        if response.status_code == 200:
            data = response.json()
            initial_credits = data.get("credits", 0)
            print(f"💰 Initial credits: {initial_credits}")
            
            if initial_credits <= 0:
                print("❌ FAIL: New user should get free trial credits")
                return False
            
            # Try to deduct credits
            deduct_response = requests.post(
                "http://localhost:8000/pay-per-use/use-credits",
                data={"email": test_email, "analysis_id": "test_123"},
                timeout=3
            )
            
            if deduct_response.status_code == 200:
                print("✅ PASS: Credit deduction works")
                
                # Check remaining credits
                final_response = requests.get(f"http://localhost:8000/pay-per-use/credits/{test_email}", timeout=3)
                if final_response.status_code == 200:
                    final_data = final_response.json()
                    final_credits = final_data.get("credits", 0)
                    print(f"💰 Final credits: {final_credits}")
                    
                    if final_credits == initial_credits - 1:
                        print("✅ PASS: Credits properly deducted")
                        return True
                    else:
                        print("❌ FAIL: Credits not properly deducted")
                        return False
                else:
                    print(f"❌ FAIL: Could not check final credits: {final_response.status_code}")
                    return False
            else:
                print(f"❌ FAIL: Credit deduction failed: {deduct_response.status_code}")
                return False
        else:
            print(f"❌ FAIL: Could not get initial credits: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Test error: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 Credit enforcement is working!")
    else:
        print("\n💥 Credit enforcement test failed!")