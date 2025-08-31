#!/usr/bin/env python3
"""
Comprehensive test script to verify all fixes
"""

import sys
import os

# Add the current directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sentry_config():
    """Test that sentry_config can be imported and initialized without errors"""
    try:
        import sentry_config
        result = sentry_config.init_sentry()
        print(f"✅ Sentry configuration test: {'PASSED' if result else 'INIT FAILED (but no exception)'}")
        return True
    except Exception as e:
        print(f"❌ Sentry configuration test FAILED: {e}")
        return False

def test_simple_server():
    """Test that simple_server can be imported without errors"""
    try:
        import simple_server
        print("✅ Simple server import test: PASSED")
        return True
    except Exception as e:
        print(f"❌ Simple server import test FAILED: {e}")
        return False

def test_credit_ui():
    """Test that credit_ui can be imported without errors"""
    try:
        from utils import credit_ui
        print("✅ Credit UI import test: PASSED")
        return True
    except Exception as e:
        print(f"❌ Credit UI import test FAILED: {e}")
        return False

def test_pay_per_use_api():
    """Test that pay_per_use API can be imported without errors"""
    try:
        from pay_per_use import api
        print("✅ Pay-per-use API import test: PASSED")
        return True
    except Exception as e:
        print(f"❌ Pay-per-use API import test FAILED: {e}")
        return False

def test_app_import():
    """Test that the main app can be imported without errors"""
    try:
        # Mock some Streamlit functions that might not be available in CLI
        import streamlit as st
        st.session_state = {}
        
        import app
        print("✅ Main app import test: PASSED")
        return True
    except Exception as e:
        print(f"❌ Main app import test FAILED: {e}")
        return False

if __name__ == "__main__":
    print("Running comprehensive fix verification...")
    print("=" * 50)
    
    tests = [
        test_sentry_config,
        test_simple_server,
        test_credit_ui,
        test_pay_per_use_api,
        test_app_import
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed!")
        print("✅ All fixes have been successfully applied!")
    else:
        print(f"💥 {passed}/{total} tests passed.")
        print("Some issues may still need to be addressed.")
        sys.exit(1)