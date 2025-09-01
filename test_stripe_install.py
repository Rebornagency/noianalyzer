#!/usr/bin/env python3
"""
Test script to verify Stripe installation and configuration
"""

import os
import sys
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
        
        # Check if we can access the version
        try:
            version = getattr(stripe, 'VERSION', 'Unknown')
            logger.info(f"✅ Stripe version: {version}")
        except AttributeError:
            logger.info("✅ Stripe library version not accessible (this is OK)")
            
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import Stripe library: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error importing Stripe: {e}")
        return False

def test_stripe_configuration():
    """Test if Stripe is properly configured with environment variables"""
    logger.info("Testing Stripe configuration...")
    
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID", 
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values for logging
            if "KEY" in var or "SECRET" in var:
                masked_value = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
                logger.info(f"✅ {var}: {masked_value} (SET)")
            else:
                logger.info(f"✅ {var}: {value[:20]}{'...' if len(value) > 20 else ''} (SET)")
        else:
            logger.warning(f"⚠️  {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        logger.info("✅ All required Stripe environment variables are set")
        return True

def test_requirements_file():
    """Check if Stripe is listed in requirements file"""
    logger.info("Checking requirements file...")
    
    try:
        with open('requirements-api.txt', 'r') as f:
            content = f.read()
            
        if 'stripe' in content.lower():
            logger.info("✅ Stripe found in requirements-api.txt")
            
            # Check for specific version
            import re
            stripe_match = re.search(r'stripe[=<>!~]*[0-9.]+', content, re.IGNORECASE)
            if stripe_match:
                logger.info(f"✅ Stripe version specified: {stripe_match.group()}")
            else:
                logger.info("✅ Stripe listed without specific version")
                
            return True
        else:
            logger.error("❌ Stripe not found in requirements-api.txt")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error reading requirements file: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting Stripe installation and configuration test...")
    logger.info("=" * 60)
    
    # Test each component
    installation_ok = test_stripe_installation()
    print()
    
    configuration_ok = test_stripe_configuration()
    print()
    
    requirements_ok = test_requirements_file()
    print()
    
    logger.info("=" * 60)
    
    if installation_ok and configuration_ok and requirements_ok:
        logger.info("✅ All tests passed! Stripe should work correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        if not installation_ok:
            logger.error("   - Stripe library not installed")
        if not configuration_ok:
            logger.error("   - Stripe not properly configured")
        if not requirements_ok:
            logger.error("   - Stripe not in requirements file")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)