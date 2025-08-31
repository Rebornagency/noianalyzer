#!/usr/bin/env python3
"""
Diagnostic script to check Stripe environment variables
"""

import os

def check_stripe_environment():
    """Check Stripe environment variables and configuration"""
    print("🔍 Checking Stripe Environment Variables")
    print("=" * 50)
    
    # Check if we're in the right directory
    print(f"Current working directory: {os.getcwd()}")
    
    # List all environment variables with "STRIPE" in the name
    print("\n1. All STRIPE-related environment variables:")
    stripe_vars = {k: v for k, v in os.environ.items() if 'STRIPE' in k.upper()}
    if stripe_vars:
        for k, v in stripe_vars.items():
            # Mask sensitive values
            if 'KEY' in k.upper() or 'SECRET' in k.upper():
                masked_value = f"{v[:3]}...{v[-4:]}" if len(v) > 7 else "Too short"
                print(f"   {k}: {masked_value}")
            else:
                print(f"   {k}: {v[:20]}{'...' if len(v) > 20 else ''}")
    else:
        print("   No STRIPE-related environment variables found")
    
    # Check specific required variables
    print("\n2. Required Stripe variables:")
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID", 
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ SET" if value else "❌ NOT SET"
        print(f"   {var}: {status}")
        if value and ('KEY' in var or 'SECRET' in var):
            masked_value = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
            print(f"     Value (masked): {masked_value}")
    
    # Check if Stripe library is available
    print("\n3. Stripe library availability:")
    try:
        import stripe
        print(f"   ✅ Stripe library available (version: {getattr(stripe, 'VERSION', 'Unknown')})")
        # Try to initialize with environment variable
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if stripe_key:
            try:
                stripe.api_key = stripe_key
                print("   ✅ Stripe API key can be set")
            except Exception as e:
                print(f"   ❌ Error setting Stripe API key: {e}")
        else:
            print("   ⚠️  No STRIPE_SECRET_KEY to test with")
    except ImportError:
        print("   ❌ Stripe library not available")
        print("   💡 Install with: pip install stripe")
    
    # Check start_credit_api.py logic
    print("\n4. Server selection logic check:")
    stripe_env_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID", 
        "STRIPE_BUSINESS_PRICE_ID",
    ]
    
    def is_stripe_configured():
        """Return True if a Stripe secret key and at least one price ID are configured (non-placeholder)."""
        secret_key = os.getenv("STRIPE_SECRET_KEY")
        if not secret_key:
            return False
        # At least one non-placeholder price ID
        for var in stripe_env_vars[1:]:
            val = os.getenv(var, "").strip()
            if val and not val.startswith("PLACEHOLDER"):
                return True
        return False
    
    def is_stripe_library_available():
        """Check if the Stripe library is available for import."""
        try:
            import stripe
            return True
        except ImportError:
            return False
    
    stripe_configured = is_stripe_configured()
    stripe_available = is_stripe_library_available()
    
    print(f"   Stripe configured (secret key + price ID): {'✅ YES' if stripe_configured else '❌ NO'}")
    print(f"   Stripe library available: {'✅ YES' if stripe_available else '❌ NO'}")
    
    if stripe_configured and stripe_available:
        print("   🎯 Server should start with Stripe integration")
    else:
        print("   🚫 Server will fall back to ultra minimal version")
        if not stripe_configured:
            print("      Reason: Missing Stripe configuration")
        if not stripe_available:
            print("      Reason: Stripe library not installed")

if __name__ == "__main__":
    check_stripe_environment()