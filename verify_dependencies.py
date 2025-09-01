#!/usr/bin/env python3
"""
Verification script to check if all required dependencies are available
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version < (3, 7):
        logger.error("Python 3.7+ is required")
        return False
    return True

def check_required_packages():
    """Check if all required packages are available"""
    required_packages = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("stripe", "Stripe payment processing"),
        ("sqlite3", "Database (built-in)"),
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            if package == "sqlite3":
                # sqlite3 is built-in, just check if it's available
                import sqlite3
                logger.info(f"✅ {description} (sqlite3) - Available")
            else:
                __import__(package)
                logger.info(f"✅ {description} ({package}) - Available")
        except ImportError:
            logger.warning(f"⚠️  {description} ({package}) - NOT AVAILABLE")
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Install missing packages with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_environment_variables():
    """Check if required environment variables are set"""
    required_env_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID",
    ]
    
    unset_vars = []
    
    for var in required_env_vars:
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
            unset_vars.append(var)
    
    if unset_vars:
        logger.warning(f"Unset environment variables: {', '.join(unset_vars)}")
        return False
    
    return True

def main():
    """Main verification function"""
    logger.info("Starting dependency verification...")
    logger.info("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check required packages
    packages_ok = check_required_packages()
    
    # Check environment variables
    env_vars_ok = check_environment_variables()
    
    logger.info("=" * 50)
    
    if packages_ok and env_vars_ok:
        logger.info("✅ All dependencies and environment variables are properly configured!")
        return True
    else:
        logger.warning("⚠️  Some dependencies or environment variables are missing or misconfigured")
        logger.info("Please check the warnings above and resolve any issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)