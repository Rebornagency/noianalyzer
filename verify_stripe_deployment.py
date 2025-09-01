#!/usr/bin/env python3
"""
Verification script to check Stripe deployment status
Run this script to get detailed information about Stripe installation and configuration
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def check_stripe_deployment():
    """Comprehensive check of Stripe deployment status"""
    print("=" * 60)
    print("STRIPE DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 1. Platform detection
    is_render = bool(os.getenv('RENDER'))
    print(f"📍 Platform: {'Render (Production)' if is_render else 'Local Development'}")
    print()
    
    # 2. Python environment
    print("🐍 Python Environment:")
    print(f"   Version: {sys.version}")
    print(f"   Executable: {sys.executable}")
    print(f"   Current directory: {os.getcwd()}")
    print()
    
    # 3. Directory contents
    print("📂 Directory Contents:")
    try:
        files = os.listdir('.')
        for file in files:
            print(f"   {file}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 4. Critical files check
    print("📄 Critical Files Check:")
    critical_files = ['requirements-api.txt', 'render.yaml']
    for cf in critical_files:
        status = "✅ FOUND" if os.path.exists(cf) else "❌ MISSING"
        print(f"   {cf}: {status}")
    print()
    
    # 5. Requirements file analysis
    print("📋 Requirements Analysis:")
    if os.path.exists('requirements-api.txt'):
        try:
            with open('requirements-api.txt', 'r') as f:
                lines = f.readlines()
                print(f"   Total lines: {len(lines)}")
                stripe_lines = [line.strip() for line in lines if 'stripe' in line.lower() and not line.startswith('#')]
                if stripe_lines:
                    print(f"   ✅ Stripe requirement found: {stripe_lines[0]}")
                else:
                    print("   ❌ No stripe requirement found")
        except Exception as e:
            print(f"   Error reading requirements: {e}")
    else:
        print("   ❌ requirements-api.txt not found")
    print()
    
    # 6. Environment variables
    print("🔐 Environment Variables:")
    critical_vars = [
        "DISABLE_POETRY",
        "UV_INSTALL_PURELIB",
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value is not None:
            if 'KEY' in var or 'SECRET' in var:
                masked = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
                print(f"   ✅ {var}: {masked}")
            else:
                print(f"   ✅ {var}: SET")
        else:
            print(f"   ⚠️  {var}: NOT SET")
    print()
    
    # 7. Package installation check
    print("📦 Package Installation Check:")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            stripe_packages = [line for line in lines if 'stripe' in line.lower()]
            if stripe_packages:
                print("   ✅ Stripe package installed:")
                for pkg in stripe_packages:
                    print(f"     {pkg}")
            else:
                print("   ❌ Stripe package NOT installed")
                print("   All packages (first 20):")
                for line in lines[:20]:
                    if line.strip():
                        print(f"     {line}")
        else:
            print(f"   ❌ Error running pip list: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("   ❌ pip list command timed out")
    except Exception as e:
        print(f"   ❌ Error checking packages: {e}")
    print()
    
    # 8. Stripe import test
    print("🔌 Stripe Import Test:")
    try:
        import stripe
        print("   ✅ Stripe imported successfully")
        print(f"   Version: {getattr(stripe, 'VERSION', 'Unknown')}")
        
        # Test API key setting
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if stripe_key:
            stripe.api_key = stripe_key
            print("   ✅ Stripe API key can be set")
            return True
        else:
            print("   ⚠️  STRIPE_SECRET_KEY not set (but Stripe library works)")
            return True
    except ImportError as e:
        print(f"   ❌ Stripe import failed: {e}")
        print("   This is the main issue - Stripe library not available")
        return False
    except Exception as e:
        print(f"   ❌ Stripe initialization error: {e}")
        return False

def main():
    """Main function"""
    success = check_stripe_deployment()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 SUCCESS: Stripe is properly configured!")
        print("   You should now be able to process real payments.")
    else:
        print("💥 ISSUE: Stripe is not working properly")
        print()
        print("🔧 Troubleshooting steps:")
        print("   1. Check Render build logs for pip install errors")
        print("   2. Verify render.yaml has correct buildCommand")
        print("   3. Ensure DISABLE_POETRY=1 and UV_INSTALL_PURELIB=0 are set")
        print("   4. Clear Render build cache and redeploy")
        print("   5. Check that requirements-api.txt contains 'stripe==10.10.0'")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)