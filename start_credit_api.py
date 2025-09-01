#!/usr/bin/env python3
"""
Simple script to start the credit API server
This will try different server options and start the first one that works
"""

import sys
import os
import logging

# Add helper to detect Stripe config
STRIPE_ENV_VARS = [
    "STRIPE_SECRET_KEY",
    "STRIPE_STARTER_PRICE_ID",
    "STRIPE_PROFESSIONAL_PRICE_ID",
    "STRIPE_BUSINESS_PRICE_ID",
]

# Import centralized logging configuration
try:
    from logging_config import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def is_stripe_configured() -> bool:
    """Return True if a Stripe secret key and at least one price ID are configured (non-placeholder)."""
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        return False
    # At least one non-placeholder price ID
    for var in STRIPE_ENV_VARS[1:]:
        val = os.getenv(var, "").strip()
        if val and not val.startswith("PLACEHOLDER"):
            return True
    return False

def is_stripe_library_available() -> bool:
    """Check if the Stripe library is available for import."""
    try:
        import stripe
        logger.info("✅ Stripe library imported successfully")
        logger.info(f"   Stripe version info: {getattr(stripe, 'VERSION', 'Unknown')}")
        return True
    except ImportError as e:
        logger.warning(f"❌ Stripe library import failed: {e}")
        # Try to provide more specific debugging info
        try:
            import pkg_resources
            installed_packages = [d.project_name for d in pkg_resources.working_set]
            stripe_packages = [pkg for pkg in installed_packages if 'stripe' in pkg.lower()]
            if stripe_packages:
                logger.info(f"   Stripe-related packages found: {stripe_packages}")
            else:
                logger.info("   No Stripe-related packages found in installed packages")
        except Exception as pkg_error:
            logger.info(f"   Could not check installed packages: {pkg_error}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during Stripe import: {e}")
        return False

def start_ultra_minimal():
    """Start the ultra minimal API server (most reliable)"""
    logger.info("🚀 Starting Ultra Minimal Credit API Server...")
    logger.info("   - Port: 10000")
    logger.info("   - No external dependencies")
    logger.info("   - Press Ctrl+C to stop")
    logger.info("=" * 50)
    
    try:
        # Import and run the ultra minimal server
        from ultra_minimal_api import run_server
        run_server()
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start ultra minimal server: {e}")
        return False
    
    return True

def start_minimal():
    """Start the minimal FastAPI server"""
    logger.info("🚀 Starting Minimal FastAPI Credit Server...")
    logger.info("   - Port: 8000")
    logger.info("   - Requires FastAPI and uvicorn")
    logger.info("   - Press Ctrl+C to stop")
    logger.info("=" * 50)
    
    try:
        import uvicorn
        from api_server_minimal import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError as e:
        logger.error(f"❌ Missing dependencies for FastAPI server: {e}")
        logger.info("💡 Try the ultra minimal server instead")
        return False
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start minimal server: {e}")
        return False
    
    return True

def start_simple_server():
    """Start the simple server with Stripe integration"""
    logger.info("🚀 Starting Simple Credit Server with Stripe Integration...")
    logger.info("   - Port: 10000")
    logger.info("   - Requires Stripe library")
    logger.info("   - Press Ctrl+C to stop")
    logger.info("=" * 50)
    
    try:
        # Import and run the simple server
        from simple_server import run_server
        run_server()
    except ImportError as e:
        logger.error(f"❌ Missing dependencies for simple server: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start simple server: {e}")
        return False
    
    return True

def main():
    """Main function to start the credit API"""
    logger.info("NOI Analyzer Credit API Starter")
    logger.info("=" * 50)
    
    # Debug: Show current working directory and Python path
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Debug: Check if requirements-api.txt exists
    if os.path.exists('requirements-api.txt'):
        logger.info("✅ requirements-api.txt found")
        # Show first few lines of requirements-api.txt
        try:
            with open('requirements-api.txt', 'r') as f:
                lines = f.readlines()
                logger.info(f"   First 5 lines of requirements-api.txt:")
                for i, line in enumerate(lines[:5]):
                    logger.info(f"     {i+1}: {line.strip()}")
        except Exception as e:
            logger.error(f"   Error reading requirements-api.txt: {e}")
    else:
        logger.warning("❌ requirements-api.txt not found")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        server_type = sys.argv[1].lower()
        if server_type == "ultra":
            start_ultra_minimal()
            return
        elif server_type == "minimal":
            start_minimal()
            return
        elif server_type == "simple":
            start_simple_server()
            return
        else:
            logger.error(f"❌ Unknown server type: {server_type}")
            logger.info("Valid options: ultra, minimal, simple")
            return
    
    # Try to start servers in order of reliability
    logger.info("🔍 Auto-selecting best server option...")

    # NEW: Prefer the minimal FastAPI server when Stripe is configured AND library is available
    if is_stripe_configured() and is_stripe_library_available():
        logger.info("\n1️⃣ Detected Stripe configuration and library – trying minimal FastAPI server first...")
        if start_minimal():
            return
        logger.info("\n2️⃣ Falling back to simple server...")
        if start_simple_server():
            return
        logger.info("\n3️⃣ Falling back to ultra minimal server...")
        start_ultra_minimal()
        return
    elif is_stripe_configured() and not is_stripe_library_available():
        # Stripe is configured but library is not available - show warning and use fallback
        logger.warning("⚠️  Stripe is configured but stripe library is not available")
        logger.warning("   This may be due to missing dependencies during deployment")
        logger.info("   🔍 Debugging steps:")
        logger.info("      1. Check Render build logs for 'pip install' errors")
        logger.info("      2. Verify requirements-api.txt contains 'stripe==10.10.0'")
        logger.info("      3. Check if there are any version conflicts")
        logger.info("\n1️⃣ Trying ultra minimal server (most reliable)...")
        if start_ultra_minimal():
            return
        logger.info("\n2️⃣ Trying minimal FastAPI server...")
        if start_minimal():
            return
        logger.info("\n3️⃣ Trying simple server (will show Stripe warning)...")
        if start_simple_server():
            return
    # Original order when Stripe is NOT configured
    logger.info("\n1️⃣ Trying ultra minimal server...")
    if start_ultra_minimal():
        return
    
    logger.info("\n2️⃣ Trying minimal FastAPI server...")
    if start_minimal():
        return
    
    logger.info("\n3️⃣ Trying simple server...")
    if start_simple_server():
        return
    
    # If all fail, show instructions
    logger.error("\n❌ Could not start any server.")
    logger.info("\n💡 Manual options:")
    logger.info("   python start_credit_api.py ultra    # Start ultra minimal server")
    logger.info("   python start_credit_api.py minimal  # Start FastAPI server")
    logger.info("   python start_credit_api.py simple   # Start simple server")
    logger.info("\n🔧 If you're still having issues:")
    logger.info("   1. Check that you have Python installed")
    logger.info("   2. Check that the required files exist")
    logger.info("   3. For FastAPI server, install: pip install fastapi uvicorn")
    logger.info("   4. For Stripe integration, install: pip install stripe")

if __name__ == "__main__":
    main()