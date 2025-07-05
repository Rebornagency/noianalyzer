#!/usr/bin/env python3
"""
Debug script to test Stripe backend configuration
This will help identify why credits are being added for free instead of going through Stripe
"""

import requests
import json
import os

def test_backend_stripe_config():
    """Test the backend Stripe configuration"""
    
    print("🔍 NOI Analyzer - Stripe Backend Debug")
    print("=" * 50)
    
    # Test different backend URLs
    backend_urls = [
        "https://noianalyzer-1.onrender.com",
        "http://localhost:8000", 
        "http://localhost:10000"
    ]
    
    test_email = "test@example.com"
    test_package = "standard"  # or "professional-15" depending on your packages
    
    for backend_url in backend_urls:
        print(f"\n🌐 Testing: {backend_url}")
        print("-" * 30)
        
        # Test 1: Health check
        try:
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health check: OK")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                continue
        except Exception as e:
            print(f"❌ Cannot connect: {e}")
            continue
        
        # Test 2: Get packages
        try:
            response = requests.get(f"{backend_url}/pay-per-use/packages", timeout=5)
            if response.status_code == 200:
                packages = response.json()
                print(f"✅ Packages loaded: {len(packages)} packages")
                
                # Show package details
                for pkg in packages:
                    stripe_id = pkg.get('stripe_price_id', 'N/A')
                    is_placeholder = stripe_id.startswith('PLACEHOLDER') or 'PLACEHOLDER' in stripe_id
                    status = "❌ PLACEHOLDER" if is_placeholder else "✅ REAL"
                    print(f"   {status} {pkg.get('name', 'Unknown')}: {stripe_id}")
            else:
                print(f"❌ Packages failed: {response.status_code}")
                continue
        except Exception as e:
            print(f"❌ Package request failed: {e}")
            continue
            
        # Test 3: Test purchase request
        try:
            print(f"\n🛒 Testing purchase request...")
            response = requests.post(
                f"{backend_url}/pay-per-use/credits/purchase",
                data={"email": test_email, "package_id": test_package},
                timeout=10,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                checkout_url = result.get('checkout_url', 'No URL')
                print(f"   Checkout URL: {checkout_url}")
                
                # Analyze the URL type
                if 'stripe.com' in checkout_url:
                    print("   🎉 REAL STRIPE URL - This should work!")
                elif 'localhost' in checkout_url or 'mock-checkout' in checkout_url:
                    print("   ⚠️  MOCK/LOCALHOST URL - This will auto-complete for free")
                    print("   🔧 This means Stripe isn't properly configured on backend")
                else:
                    print(f"   ❓ UNKNOWN URL TYPE: {checkout_url}")
                    
            else:
                print(f"   ❌ Purchase failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Purchase request failed: {e}")
        
        print(f"\n{'='*50}")
    
    print(f"\n💡 DIAGNOSIS:")
    print("If you see 'MOCK/LOCALHOST URL', then:")
    print("1. Backend doesn't have proper Stripe environment variables")
    print("2. Stripe integration is failing and falling back to mock")
    print("3. The environment variables need to be added to your production server")
    
    print(f"\n🔧 NEXT STEPS:")
    print("1. Add Stripe environment variables to your backend server")
    print("2. Redeploy the backend")
    print("3. Run this script again to verify")

def test_local_stripe_config():
    """Test local Stripe configuration"""
    print(f"\n🏠 Local Environment Check:")
    print("-" * 30)
    
    stripe_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID", 
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    for var in stripe_vars:
        value = os.getenv(var)
        if value and not value.startswith("PLACEHOLDER"):
            print(f"✅ {var}: {value[:20]}...")
        else:
            print(f"❌ {var}: Not set or placeholder")
    
    print(f"\n📝 If local variables are set but backend still returns mock URLs,")
    print(f"   then the backend server needs the same environment variables.")

if __name__ == "__main__":
    test_backend_stripe_config()
    test_local_stripe_config() 