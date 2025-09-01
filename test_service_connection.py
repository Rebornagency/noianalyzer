#!/usr/bin/env python3
"""
Test script to verify the connection between the main application and credit service
"""

import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_service_connection():
    """Test connection to the credit service"""
    # Get the backend URL
    backend_url = os.getenv("BACKEND_URL", "https://noianalyzer-1.onrender.com")
    logger.info(f"Testing connection to credit service at: {backend_url}")
    
    try:
        # Test health endpoint
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Health check successful")
            logger.info(f"Response: {response.json()}")
        else:
            logger.error(f"❌ Health check failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
        # Test packages endpoint
        response = requests.get(f"{backend_url}/pay-per-use/packages", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Packages endpoint accessible")
            logger.info(f"Found {len(response.json())} packages")
        else:
            logger.warning(f"⚠️ Packages endpoint returned status {response.status_code}")
            
        # Test credits endpoint with a test email
        test_email = "test@example.com"
        response = requests.get(f"{backend_url}/pay-per-use/credits/{test_email}", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Credits endpoint accessible")
            logger.info(f"Response: {response.json()}")
        else:
            logger.warning(f"⚠️ Credits endpoint returned status {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ Timeout error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting service connection test...")
    logger.info("=" * 50)
    
    success = test_service_connection()
    
    logger.info("=" * 50)
    if success:
        logger.info("✅ All tests passed! Services are properly connected.")
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        
    exit(0 if success else 1)