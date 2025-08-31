#!/usr/bin/env python3
"""
Test script to check if Stripe library can be imported
"""

print("Testing Stripe import...")

try:
    import stripe
    print(f"✅ Stripe library imported successfully (version: {getattr(stripe, 'VERSION', 'Unknown')})")
    
    # Test if we can access the api_key attribute
    print(f"✅ Stripe.api_key attribute accessible: {hasattr(stripe, 'api_key')}")
    
    # Test environment variable
    import os
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_key:
        print(f"✅ STRIPE_SECRET_KEY environment variable is set (length: {len(stripe_key)} characters)")
        # Test setting the API key
        try:
            stripe.api_key = stripe_key
            print("✅ Stripe API key set successfully")
        except Exception as e:
            print(f"❌ Error setting Stripe API key: {e}")
    else:
        print("❌ STRIPE_SECRET_KEY environment variable is not set")
        
except ImportError as e:
    print(f"❌ Failed to import Stripe library: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("Test completed.")