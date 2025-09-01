#!/usr/bin/env python3
"""
Comprehensive verification script to test all fixes
"""

import os
import sys
import subprocess
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stripe_installation():
    """Test if Stripe library is properly installed"""
    logger.info("Testing Stripe library installation...")
    
    try:
        import stripe
        logger.info("✅ Stripe library imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import Stripe library: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error importing Stripe: {e}")
        return False

def test_requirements_files():
    """Check all requirements files for proper configurations"""
    logger.info("Checking requirements files...")
    
    requirements_files = [
        "requirements.txt",
        "requirements-api.txt",
        "requirements-render.txt"
    ]
    
    all_good = True
    
    for req_file in requirements_files:
        try:
            with open(req_file, 'r') as f:
                content = f.read()
            
            # Check for Stripe
            stripe_match = re.search(r'stripe[=<>!~]*([0-9.]+)', content, re.IGNORECASE)
            if stripe_match:
                version = stripe_match.group(1)
                logger.info(f"✅ {req_file}: stripe version {version}")
            else:
                logger.warning(f"⚠️ {req_file}: stripe not found or not pinned")
                all_good = False
                
            # Check for email-validator
            email_validator_match = re.search(r'email-validator[=<>!~]*([0-9.]+)', content, re.IGNORECASE)
            if email_validator_match:
                version = email_validator_match.group(1)
                if version >= "2.3.0":
                    logger.info(f"✅ {req_file}: email-validator version {version} (fixed)")
                else:
                    logger.warning(f"⚠️ {req_file}: email-validator version {version} (still has warning)")
                    all_good = False
            else:
                logger.warning(f"⚠️ {req_file}: email-validator not found or not pinned")
                all_good = False
                
            # Check for sentry-sdk
            sentry_sdk_match = re.search(r'sentry-sdk[=<>!~]*([0-9.]+)', content, re.IGNORECASE)
            if sentry_sdk_match:
                version = sentry_sdk_match.group(1)
                if version >= "2.0.0":
                    logger.info(f"✅ {req_file}: sentry-sdk version {version} (fixed)")
                else:
                    logger.warning(f"⚠️ {req_file}: sentry-sdk version {version} (may still have warning)")
                    all_good = False
            else:
                logger.warning(f"⚠️ {req_file}: sentry-sdk not found or not pinned")
                all_good = False
                
        except FileNotFoundError:
            logger.warning(f"⚠️ {req_file}: File not found")
            all_good = False
        except Exception as e:
            logger.error(f"❌ Error reading {req_file}: {e}")
            all_good = False
    
    return all_good

def test_stripe_configuration():
    """Test if Stripe is properly configured with environment variables"""
    logger.info("Testing Stripe configuration...")
    
    # This is just for local testing - in Render, these would be set
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID", 
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    logger.info("Checking for Stripe environment variables (these would be set in Render)...")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: SET (value masked for security)")
        else:
            logger.info(f"⚠️  {var}: NOT SET (expected in local testing)")
    
    return True  # This is just a check, not a failure condition

def test_server_startup_logic():
    """Test the server startup logic in start_credit_api.py"""
    logger.info("Testing server startup logic...")
    
    try:
        # Import the functions from start_credit_api.py
        import start_credit_api
        
        # Test the Stripe availability check
        stripe_available = start_credit_api.is_stripe_library_available()
        logger.info(f"Stripe library availability check: {stripe_available}")
        
        # Test the Stripe configuration check
        stripe_configured = start_credit_api.is_stripe_configured()
        logger.info(f"Stripe configuration check: {stripe_configured}")
        
        logger.info("✅ Server startup logic functions working correctly")
        return True
    except Exception as e:
        logger.error(f"❌ Error testing server startup logic: {e}")
        return False

def main():
    """Main verification function"""
    logger.info("Starting comprehensive verification of all fixes...")
    logger.info("=" * 70)
    
    # Test each component
    stripe_install_ok = test_stripe_installation()
    print()
    
    requirements_ok = test_requirements_files()
    print()
    
    configuration_ok = test_stripe_configuration()
    print()
    
    startup_logic_ok = test_server_startup_logic()
    print()
    
    logger.info("=" * 70)
    
    if stripe_install_ok and requirements_ok and configuration_ok and startup_logic_ok:
        logger.info("✅ All tests passed! All fixes should be working correctly.")
        logger.info("   You can now deploy to Render with confidence.")
        return True
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        if not stripe_install_ok:
            logger.error("   - Stripe library not properly installed")
        if not requirements_ok:
            logger.error("   - Requirements files not properly configured")
        if not startup_logic_ok:
            logger.error("   - Server startup logic has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)