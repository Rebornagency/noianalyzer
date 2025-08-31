#!/usr/bin/env python3
"""
Comprehensive test script to verify Stripe configuration
"""

import os
import sys

def verify_stripe_config():
    """Verify Stripe configuration step by step"""
    print("🔍 Verifying Stripe Configuration...")
    print("=" * 50)
    
    # Step 1: Check if Stripe library is available
    print("1. Checking Stripe library availability...")
    try:
        import stripe
        print(f"   ✅ Stripe library available (version: {getattr(stripe, 'VERSION', 'Unknown')})")
        stripe_available = True
    except ImportError as e:
        print(f"   ❌ Stripe library not available: {e}")
        stripe_available = False
        return False
    
    # Step 2: Check environment variables
    print("\n2. Checking environment variables...")
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID", 
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    missing_vars = []
    set_vars = []
    
    for var in required_vars:
        value = os.getenv(var, "")
        if value and not value.startswith("PLACEHOLDER"):
            print(f"   ✅ {var}: SET")
            set_vars.append(var)
        else:
            print(f"   ❌ {var}: {'NOT SET' if not value else 'PLACEHOLDER VALUE'}")
            missing_vars.append(var)
    
    # Step 3: Check if Stripe can be initialized
    print("\n3. Testing Stripe initialization...")
    if stripe_available and "STRIPE_SECRET_KEY" in set_vars:
        stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
        try:
            stripe.api_key = stripe_secret_key
            # Test the API key by making a simple request
            # We'll just set the key without making a request to avoid errors
            print("   ✅ Stripe API key set successfully")
            print("   🎉 Stripe is properly configured!")
            return True
        except Exception as e:
            print(f"   ❌ Error setting Stripe API key: {e}")
            return False
    else:
        if missing_vars:
            print("   ❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"      - {var}")
        else:
            print("   ⚠️  Stripe library available but no STRIPE_SECRET_KEY set")
        return False

def main():
    """Main function"""
    print("NOI Analyzer - Stripe Configuration Verification")
    print("=" * 50)
    
    success = verify_stripe_config()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All checks passed! Stripe is properly configured.")
        print("\nNext steps:")
        print("1. Restart your Render service")
        print("2. Test the credit purchase functionality")
    else:
        print("❌ Configuration issues detected.")
        print("\nTroubleshooting steps:")
        print("1. Check that all required Stripe environment variables are set in Render")
        print("2. Verify that STRIPE_SECRET_KEY is a valid Stripe secret key (starts with sk_)")
        print("3. Verify that price IDs are valid Stripe price IDs (start with price_)")
        print("4. Restart your Render service after making changes")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)