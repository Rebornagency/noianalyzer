#!/usr/bin/env python3
"""
Simple Credit System Verification Script
Tests the core credit system functionality without external dependencies
"""

import os
import sys
import sqlite3
from datetime import datetime

def test_database_structure():
    """Test if the database has the expected structure"""
    print("🔍 Testing Database Structure...")
    
    db_path = os.getenv("DATABASE_PATH", "noi_analyzer.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if core tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'credit_transactions', 'credit_packages', 'ip_trial_usage']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print(f"✅ All required tables found: {required_tables}")
        
        # Check table structures
        for table in required_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"   📋 {table}: {len(columns)} columns")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_credit_system_imports():
    """Test if credit system modules can be imported"""
    print("\n🔍 Testing Credit System Imports...")
    
    try:
        from pay_per_use.database import db_service
        print("✅ Database service imported")
        
        from pay_per_use.credit_service import credit_service
        print("✅ Credit service imported")
        
        from pay_per_use.models import User, CreditTransaction, TransactionType
        print("✅ Models imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic credit system functionality"""
    print("\n🔍 Testing Basic Functionality...")
    
    try:
        from pay_per_use.database import db_service
        from pay_per_use.credit_service import credit_service
        
        # Test user creation
        test_email = "test@example.com"
        print(f"   Creating test user: {test_email}")
        
        user = db_service.get_or_create_user(test_email)
        print(f"✅ User created/retrieved: {user.email} with {user.credits} credits")
        
        # Test credit packages
        packages = db_service.get_active_packages()
        print(f"✅ Found {len(packages)} credit packages")
        
        if packages:
            for pkg in packages:
                print(f"   📦 {pkg.name}: {pkg.credits} credits for ${pkg.price_cents/100}")
        
        # Test credit check
        has_credits, current_credits, message = credit_service.check_user_credits(test_email)
        print(f"✅ Credit check: {has_credits}, {current_credits} credits")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

def test_environment_variables():
    """Test if required environment variables are set"""
    print("\n🔍 Testing Environment Variables...")
    
    critical_vars = [
        "OPENAI_API_KEY",
        "STRIPE_SECRET_KEY", 
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    
    optional_vars = [
        "DATABASE_PATH",
        "BACKEND_URL",
        "FREE_TRIAL_CREDITS"
    ]
    
    all_good = True
    
    for var in critical_vars:
        value = os.getenv(var)
        if value and not value.startswith("PLACEHOLDER"):
            print(f"✅ {var}: Set and not placeholder")
        elif value and value.startswith("PLACEHOLDER"):
            print(f"❌ {var}: Placeholder value detected - please update with real value")
            all_good = False
        else:
            print(f"❌ {var}: Missing or not set")
            all_good = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (using default)")
    
    if not all_good:
        print("\n📝 To fix missing environment variables:")
        print("   1. If running locally, create a .env file with your real values")
        print("   2. If running on Render, set the environment variables in your dashboard")
        print("   3. Required Stripe variables:")
        print("      - STRIPE_SECRET_KEY")
        print("      - STRIPE_STARTER_PRICE_ID")
        print("      - STRIPE_PROFESSIONAL_PRICE_ID")
        print("      - STRIPE_BUSINESS_PRICE_ID")
        print("      - STRIPE_WEBHOOK_SECRET")
    
    return all_good

def main():
    """Main verification function"""
    print("🚀 NOI Analyzer Credit System Verification")
    print("=" * 50)
    
    tests = [
        ("Database Structure", test_database_structure),
        ("System Imports", test_credit_system_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Environment Variables", test_environment_variables)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Credit system is ready!")
        print("\n📝 Next steps:")
        print("   1. Verify Render environment variables are correctly set")
        print("   2. Test with real Stripe credentials in production")
        print("   3. Set up monitoring and backups")
    else:
        print("⚠️  SOME TESTS FAILED - Fix issues before deployment")
        print("\n📝 Required actions:")
        print("   1. Check STRIPE_* environment variables in Render")
        print("   2. Ensure database is properly initialized")
        print("   3. Verify all imports work correctly")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)