#!/usr/bin/env python3
"""
Test script to check if the Stripe library and configuration work correctly
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add helper to detect Stripe config
STRIPE_ENV_VARS = [
    "STRIPE_SECRET_KEY",
    "STRIPE_STARTER_PRICE_ID",
    "STRIPE_PROFESSIONAL_PRICE_ID",
    "STRIPE_BUSINESS_PRICE_ID",
]

def is_stripe_configured() -> bool:
    """Return True if a Stripe secret key and at least one price ID are configured (non-placeholder)."""
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        return False
    # At least one non-placeholder price ID
    for var in STRIPE_ENV_VARS[1:]:
        val = os.getenv(var, "").strip()
        if val and not val.startswith("PLACEHOLDER"):
            return True
    return False

def is_stripe_library_available() -> bool:
    """Check if the Stripe library is available for import."""
    try:
        import stripe
        logger.info("✅ Stripe library imported successfully")
        return True
    except ImportError as e:
        logger.warning(f"❌ Stripe library import failed: {e}")
        return False

# Test both functions
logger.info("Testing Stripe library and configuration...")
logger.info("=" * 50)

# Check library availability
library_available = is_stripe_library_available()
logger.info(f"Stripe library available: {library_available}")

# Check configuration
configured = is_stripe_configured()
logger.info(f"Stripe configured: {configured}")

# Check environment variables
logger.info("Environment variables check:")
for var in STRIPE_ENV_VARS:
    value = os.getenv(var, "NOT SET")
    if var == "STRIPE_SECRET_KEY" and value != "NOT SET":
        # Mask the secret key for security
        masked_value = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
        logger.info(f"  {var}: {masked_value}")
    else:
        logger.info(f"  {var}: {value}")

logger.info("=" * 50)
if library_available and configured:
    logger.info("✅ Stripe is ready for use")
elif library_available and not configured:
    logger.info("⚠️  Stripe library is available but not configured")
    logger.info("   Set the STRIPE_SECRET_KEY and price ID environment variables")
elif not library_available and configured:
    logger.info("❌ Stripe is configured but library is not available")
    logger.info("   Install the Stripe library: pip install stripe")
else:
    logger.info("⚠️  Stripe is not available and not configured")
    logger.info("   To enable Stripe:")
    logger.info("   1. Install the Stripe library: pip install stripe")
    logger.info("   2. Set the STRIPE_SECRET_KEY and price ID environment variables")