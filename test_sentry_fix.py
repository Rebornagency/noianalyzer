#!/usr/bin/env python3
"""
Test script to verify the Sentry configuration fix
"""

import sys
import os

# Add the current directory to the path so we can import the sentry_config module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sentry_import():
    """Test that we can import sentry_config without errors"""
    try:
        import sentry_config
        print("✅ sentry_config imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import sentry_config: {e}")
        return False

def test_sentry_initialization():
    """Test that we can initialize Sentry without errors"""
    try:
        import sentry_config
        result = sentry_config.init_sentry()
        print(f"✅ Sentry initialization result: {result}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Sentry: {e}")
        return False

if __name__ == "__main__":
    print("Testing Sentry configuration fix...")
    print("=" * 40)
    
    success = True
    success &= test_sentry_import()
    success &= test_sentry_initialization()
    
    print("=" * 40)
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
        sys.exit(1)