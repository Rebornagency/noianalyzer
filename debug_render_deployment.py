#!/usr/bin/env python3
"""
Debug script to diagnose Render deployment issues
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check the deployment environment"""
    logger.info("🔍 Checking deployment environment...")
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check current directory
    logger.info(f"Current directory: {os.getcwd()}")
    
    # List files in current directory
    files = os.listdir('.')
    logger.info(f"Files in current directory: {files}")
    
    # Check environment variables
    render_vars = {k: v for k, v in os.environ.items() if 'RENDER' in k}
    if render_vars:
        logger.info("Render environment variables:")
        for k, v in render_vars.items():
            logger.info(f"  {k}: {v[:50]}{'...' if len(v) > 50 else ''}")
    else:
        logger.info("No Render environment variables found")

def check_requirements_file():
    """Check if requirements-api.txt exists and is readable"""
    logger.info("🔍 Checking requirements-api.txt...")
    
    if os.path.exists('requirements-api.txt'):
        logger.info("✅ requirements-api.txt found")
        try:
            with open('requirements-api.txt', 'r') as f:
                lines = f.readlines()
                logger.info(f"   File contains {len(lines)} lines")
                stripe_line = [line for line in lines if 'stripe' in line.lower()]
                if stripe_line:
                    logger.info(f"   Stripe requirement found: {stripe_line[0].strip()}")
                else:
                    logger.warning("   No stripe requirement found in file")
        except Exception as e:
            logger.error(f"   Error reading requirements-api.txt: {e}")
    else:
        logger.error("❌ requirements-api.txt NOT found")

def check_pip_install():
    """Try to install requirements manually"""
    logger.info("🔍 Testing pip install...")
    
    try:
        # Try to install requirements
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements-api.txt'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✅ pip install successful")
            logger.info(f"   Output: {result.stdout[:200]}{'...' if len(result.stdout) > 200 else ''}")
        else:
            logger.error("❌ pip install failed")
            logger.error(f"   Error: {result.stderr[:500]}{'...' if len(result.stderr) > 500 else ''}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ pip install timed out")
    except Exception as e:
        logger.error(f"❌ Error running pip install: {e}")

def check_stripe_import():
    """Check if stripe can be imported"""
    logger.info("🔍 Testing stripe import...")
    
    try:
        import stripe
        logger.info("✅ stripe imported successfully")
        logger.info(f"   Stripe version: {getattr(stripe, 'VERSION', 'Unknown')}")
        
        # Try to initialize with a dummy key
        try:
            stripe.api_key = "sk_test_dummy"
            logger.info("✅ stripe API key can be set")
        except Exception as e:
            logger.info(f"   Note: API key setting issue: {e}")
            
    except ImportError as e:
        logger.error(f"❌ stripe import failed: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error importing stripe: {e}")

def main():
    """Main function"""
    logger.info("🚀 Starting Render deployment debug...")
    logger.info("=" * 60)
    
    check_environment()
    check_requirements_file()
    check_pip_install()
    check_stripe_import()
    
    logger.info("=" * 60)
    logger.info("🏁 Debug complete")

if __name__ == "__main__":
    main()