#!/usr/bin/env python3
"""
Test script to check if the Stripe library availability check works
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_stripe_library_available() -> bool:
    """Check if the Stripe library is available for import."""
    try:
        import stripe
        logger.info("✅ Stripe library imported successfully")
        return True
    except ImportError as e:
        logger.warning(f"❌ Stripe library import failed: {e}")
        # Try to provide more specific debugging info
        try:
            import pip
            logger.info("Available packages:")
            installed_packages = [d.project_name for d in pip.get_installed_distributions()]
            if 'stripe' in [pkg.lower() for pkg in installed_packages]:
                logger.info("ℹ️  Stripe package appears to be installed")
            else:
                logger.info("ℹ️  Stripe package not found in installed packages")
        except Exception as pip_error:
            logger.info(f"Could not check installed packages: {pip_error}")
        return False

# Test the function
logger.info("Testing Stripe library availability...")
result = is_stripe_library_available()
logger.info(f"Stripe library available: {result}")

def is_stripe_configured():
    """Return True if a Stripe secret key and at least one price ID are configured."""
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        print("⚠️  STRIPE_SECRET_KEY is not set")
        return False
    
    print("✅ STRIPE_SECRET_KEY is set")
    
    # Check for at least one price ID
    price_ids = [
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID", 
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    found_price_id = False
    for var in price_ids:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} is set")
            found_price_id = True
        else:
            print(f"⚠️  {var} is not set")
    
    return found_price_id

if __name__ == "__main__":
    print("Testing Stripe configuration and library availability...")
    print("=" * 50)
    
    # Check if Stripe is configured
    configured = is_stripe_configured()
    
    # Check if Stripe library is available
    available = is_stripe_library_available()
    
    print("=" * 50)
    
    if configured and available:
        print("✅ Stripe is properly configured and the library is available")
    elif configured and not available:
        print("⚠️  Stripe is configured but the library is not available")
        print("   Try installing it with: pip install stripe")
    elif not configured and available:
        print("⚠️  Stripe library is available but not configured")
        print("   Set the STRIPE_SECRET_KEY and price ID environment variables")
    else:
        print("⚠️  Stripe is not configured and the library is not available")