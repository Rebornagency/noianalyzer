#!/usr/bin/env python3
"""
Test script to check Stripe configuration
"""

import os

def test_stripe_config():
    """Test if Stripe is properly configured"""
    print("🔍 Testing Stripe configuration...")
    
    # Check environment variables
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
    starter_price_id = os.getenv("STRIPE_STARTER_PRICE_ID")
    professional_price_id = os.getenv("STRIPE_PROFESSIONAL_PRICE_ID")
    business_price_id = os.getenv("STRIPE_BUSINESS_PRICE_ID")
    
    print(f"STRIPE_SECRET_KEY: {'SET' if stripe_secret_key else 'NOT SET'}")
    print(f"STRIPE_STARTER_PRICE_ID: {'SET' if starter_price_id else 'NOT SET'}")
    print(f"STRIPE_PROFESSIONAL_PRICE_ID: {'SET' if professional_price_id else 'NOT SET'}")
    print(f"STRIPE_BUSINESS_PRICE_ID: {'SET' if business_price_id else 'NOT SET'}")
    
    # Check if Stripe library is available
    try:
        import stripe
        print(f"✅ Stripe library available (version: {stripe.VERSION})")
        stripe_available = True
    except ImportError:
        print("❌ Stripe library not available")
        stripe_available = False
    
    # Check if Stripe is properly configured
    if stripe_secret_key and stripe_available:
        print("✅ Stripe is properly configured")
        return True
    else:
        print("❌ Stripe is not properly configured")
        return False

if __name__ == "__main__":
    test_stripe_config()