#!/usr/bin/env python3
"""
Debug script to run directly on Render to diagnose Stripe installation issues
"""

import os
import sys
import subprocess
import importlib.util

def check_python_info():
    """Check Python version and environment"""
    print("🔍 Python Environment Info")
    print("=" * 40)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print()

def check_requirements_file():
    """Check if requirements-api.txt exists and its contents"""
    print("🔍 Checking requirements-api.txt")
    print("=" * 40)
    
    if os.path.exists('requirements-api.txt'):
        print("✅ requirements-api.txt found")
        try:
            with open('requirements-api.txt', 'r') as f:
                content = f.read()
                print("Contents:")
                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        print(f"  {line}")
        except Exception as e:
            print(f"❌ Error reading requirements-api.txt: {e}")
    else:
        print("❌ requirements-api.txt NOT found")
    print()

def check_installed_packages():
    """Check what packages are installed"""
    print("🔍 Checking installed packages")
    print("=" * 40)
    
    try:
        # Try to use pip to list installed packages
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("Installed packages:")
            for line in result.stdout.split('\n'):
                if 'stripe' in line.lower():
                    print(f"  🎯 {line}")
                elif any(pkg in line.lower() for pkg in ['fastapi', 'uvicorn', 'python-dotenv']):
                    print(f"  ✅ {line}")
        else:
            print(f"Error running pip list: {result.stderr}")
    except Exception as e:
        print(f"Error checking installed packages: {e}")
    print()

def test_stripe_import():
    """Test importing Stripe"""
    print("🔍 Testing Stripe import")
    print("=" * 40)
    
    try:
        import stripe
        print("✅ Stripe imported successfully!")
        print(f"   Version: {getattr(stripe, 'VERSION', 'Unknown')}")
        
        # Test setting API key
        test_key = "sk_test_placeholder"
        stripe.api_key = test_key
        print("✅ Stripe API key can be set")
        
        return True
    except ImportError as e:
        print(f"❌ Stripe import failed: {e}")
        
        # Try to install stripe manually
        print("🔧 Trying to install stripe manually...")
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'stripe==10.10.0'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("✅ Stripe installed successfully!")
                # Try importing again
                try:
                    import stripe
                    print("✅ Stripe imported successfully after manual installation!")
                    print(f"   Version: {getattr(stripe, 'VERSION', 'Unknown')}")
                    return True
                except ImportError as e2:
                    print(f"❌ Still can't import stripe after installation: {e2}")
            else:
                print(f"❌ Failed to install stripe: {result.stderr}")
        except Exception as install_error:
            print(f"❌ Error during manual installation: {install_error}")
            
        return False
    except Exception as e:
        print(f"❌ Unexpected error with Stripe: {e}")
        return False

def check_environment_variables():
    """Check environment variables"""
    print("🔍 Checking environment variables")
    print("=" * 40)
    
    stripe_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID", 
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    for var in stripe_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                masked = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
                print(f"✅ {var}: {masked} (SET)")
            else:
                print(f"✅ {var}: SET")
        else:
            print(f"❌ {var}: NOT SET")
    print()

def main():
    """Main debug function"""
    print("🚀 Render Deployment Debug Script")
    print("=" * 50)
    print()
    
    check_python_info()
    check_requirements_file()
    check_installed_packages()
    check_environment_variables()
    stripe_works = test_stripe_import()
    
    print("=" * 50)
    if stripe_works:
        print("🎉 SUCCESS: Stripe is working properly!")
    else:
        print("💥 ISSUE: Stripe is not working properly")
        print()
        print("🔧 Suggested fixes:")
        print("   1. Check Render build logs for pip install errors")
        print("   2. Ensure buildCommand in render.yaml is: pip install -r requirements-api.txt")
        print("   3. Add these environment variables to Render:")
        print("      - DISABLE_POETRY=1")
        print("      - UV_INSTALL_PURELIB=0")
        print("   4. Clear Render build cache and redeploy")
    
    return stripe_works

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)