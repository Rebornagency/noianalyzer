#!/usr/bin/env python3
"""
Test script to verify logging configuration
"""

import os
import sys

# Add the current directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging_import():
    """Test that we can import logging_config without errors"""
    try:
        from logging_config import setup_logging, get_logger
        print("✅ logging_config imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import logging_config: {e}")
        return False

def test_logger_creation():
    """Test that we can create and use a logger"""
    try:
        from logging_config import setup_logging, get_logger
        
        # Setup logging
        setup_logging()
        
        # Get a logger
        logger = get_logger(__name__)
        
        # Test logging at different levels
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        
        print("✅ Logger creation and usage test passed")
        return True
    except Exception as e:
        print(f"❌ Failed to create/use logger: {e}")
        return False

def test_log_level_configuration():
    """Test that log level configuration works"""
    try:
        from logging_config import configure_logging, get_logger
        import logging
        
        # Test with DEBUG level
        configure_logging(log_level="DEBUG")
        logger = get_logger(__name__)
        
        # This should output since we're at DEBUG level
        logger.debug("Debug message at DEBUG level")
        
        print("✅ Log level configuration test passed")
        return True
    except Exception as e:
        print(f"❌ Failed to test log level configuration: {e}")
        return False

def test_sentry_availability():
    """Test if Sentry is available and can be configured"""
    try:
        from logging_config import configure_logging
        import logging
        
        # Try to configure with Sentry (will gracefully handle if not available)
        logger = configure_logging(enable_sentry=True)
        
        print("✅ Sentry configuration test completed (may or may not be available)")
        return True
    except Exception as e:
        print(f"❌ Failed to test Sentry configuration: {e}")
        return False

if __name__ == "__main__":
    print("Testing logging configuration...")
    print("=" * 40)
    
    success = True
    success &= test_logging_import()
    success &= test_logger_creation()
    success &= test_log_level_configuration()
    success &= test_sentry_availability()
    
    print("=" * 40)
    if success:
        print("🎉 All logging tests passed!")
    else:
        print("💥 Some logging tests failed!")
        sys.exit(1)