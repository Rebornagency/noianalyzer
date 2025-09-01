#!/usr/bin/env python3
"""
Test script that mimics the Stripe import in simple_server.py
"""

import logging

# Configure logging to match simple_server.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import Stripe, but handle gracefully if not available
try:
    import stripe
    STRIPE_AVAILABLE = True
    logger.info("✅ Stripe imported successfully")
    logger.info(f"   Stripe version: {getattr(stripe, 'VERSION', 'Unknown')}")
    logger.info(f"   Stripe file location: {stripe.__file__}")
except ImportError as e:
    STRIPE_AVAILABLE = False
    logger.warning("⚠️  Stripe library not available - Stripe integration disabled")
    logger.info("   Run 'pip install stripe' to enable Stripe integration")
    logger.info(f"   Import error details: {str(e)}")
except Exception as e:
    STRIPE_AVAILABLE = False
    logger.error(f"❌ Unexpected error during Stripe initialization: {str(e)}")
    logger.info("   Stripe integration will be disabled")

print(f"\nSTRIPE_AVAILABLE: {STRIPE_AVAILABLE}")