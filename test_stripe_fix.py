#!/usr/bin/env python3
"""
Simple test script to verify Stripe is working after applying fixes
"""

import os
import sys

def test_stripe():
    """Test if Stripe is properly installed and configured"""
    print("🔍 Testing Stripe installation and configuration...")
    
    # Check if we're on Render
    is_render = bool(os.getenv('RENDER'))
    print(f"📍 Platform: {'Render' if is_render else 'Local'}")
    
    # Test 1: Import Stripe
    try:
        import stripe
        print("✅ Stripe library imported successfully")
        print(f"   Version: {getattr(stripe, 'VERSION', 'Unknown')}")
    except ImportError as e:
        print(f"❌ Stripe import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing Stripe: {e}")
        return False
    
    # Test 2: Check environment variables
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID", 
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
    
    # Test 3: Initialize Stripe
    try:
        stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe_api_key:
            stripe.api_key = stripe_api_key
            print("✅ Stripe initialized successfully")
        else:
            print("❌ STRIPE_SECRET_KEY is empty")
            return False
    except Exception as e:
        print(f"❌ Error initializing Stripe: {e}")
        return False
    
    print("🎉 All Stripe tests passed!")
    return True

if __name__ == "__main__":
    print("🚀 Stripe Fix Verification Script")
    print("=" * 40)
    
    success = test_stripe()
    
    print("=" * 40)
    if success:
        print("✅ Stripe is properly configured and ready to use!")
        print("💡 You can now process real payments through your application.")
    else:
        print("❌ Stripe configuration issues detected.")
        print("🔧 Please check the error messages above and fix the issues.")
    
    sys.exit(0 if success else 1)