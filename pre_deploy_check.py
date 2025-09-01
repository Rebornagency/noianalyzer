#!/usr/bin/env python3
"""
Pre-deployment verification script to ensure all dependencies are properly installed
"""

import sys
import os
import importlib.util

def check_stripe_installation():
    """Check if Stripe library is properly installed"""
    print("🔍 Checking Stripe installation...")
    
    try:
        # Try to import stripe
        import stripe
        print("✅ Stripe library imported successfully")
        print(f"   Version: {getattr(stripe, 'VERSION', 'Unknown')}")
        
        # Try to set API key
        stripe.api_key = "sk_test_placeholder"
        print("✅ Stripe API key can be set")
        
        return True
    except ImportError as e:
        print(f"❌ Stripe import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Stripe initialization failed: {e}")
        return False

def check_required_packages():
    """Check if all required packages are installed"""
    required_packages = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("stripe", "Stripe payment processing"),
        ("python-dotenv", "Environment variable management"),
        ("email-validator", "Email validation"),
    ]
    
    missing_packages = []
    
    for package_name, description in required_packages:
        try:
            # Special handling for packages with different import names
            if package_name == "python-dotenv":
                importlib.import_module("dotenv")
            elif package_name == "email-validator":
                importlib.import_module("email_validator")
            else:
                importlib.import_module(package_name)
            print(f"✅ {description} ({package_name}) - Available")
        except ImportError:
            print(f"❌ {description} ({package_name}) - NOT AVAILABLE")
            missing_packages.append(package_name)
    
    return len(missing_packages) == 0

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\n🔍 Checking environment variables...")
    
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID",
    ]
    
    all_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                masked_value = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
                print(f"✅ {var}: {masked_value} (SET)")
            else:
                print(f"✅ {var}: SET")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def main():
    """Main verification function"""
    print("🚀 Pre-deployment Verification Script")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check required packages
    print("\n📦 Checking required packages...")
    packages_ok = check_required_packages()
    
    # Check Stripe installation specifically
    print("\n💳 Checking Stripe installation...")
    stripe_ok = check_stripe_installation()
    
    # Check environment variables
    env_vars_ok = check_environment_variables()
    
    print("\n" + "=" * 50)
    
    if packages_ok and stripe_ok and env_vars_ok:
        print("✅ All checks passed! Ready for deployment.")
        return True
    else:
        print("❌ Some checks failed. Please review the issues above.")
        if not packages_ok:
            print("   - Missing required packages")
        if not stripe_ok:
            print("   - Stripe installation issues")
        if not env_vars_ok:
            print("   - Missing environment variables")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)