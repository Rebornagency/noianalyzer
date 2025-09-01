#!/usr/bin/env python3
"""
Test script to check if Stripe library can be imported
"""

try:
    import stripe
    print("✅ Stripe library imported successfully")
    print(f"Stripe version: {stripe.__version__}")
    
    # Try to access the api_key attribute
    if hasattr(stripe, 'api_key'):
        print("✅ Stripe api_key attribute available")
    else:
        print("❌ Stripe api_key attribute not available")
        
except ImportError as e:
    print(f"❌ Failed to import Stripe library: {e}")
    
    # Try to check what's installed
    try:
        import pkg_resources
        installed_packages = [d.project_name for d in pkg_resources.working_set]
        if 'stripe' in [pkg.lower() for pkg in installed_packages]:
            print("ℹ️  Stripe package appears to be installed")
        else:
            print("ℹ️  Stripe package not found in installed packages")
    except Exception as pkg_error:
        print(f"❌ Could not check installed packages: {pkg_error}")

except Exception as e:
    print(f"❌ Unexpected error: {e}")