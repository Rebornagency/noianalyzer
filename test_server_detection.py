#!/usr/bin/env python3
"""
Test script to check server detection logic
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, '.')

# Import the functions from start_credit_api.py
from start_credit_api import is_stripe_configured, is_stripe_library_available

def test_server_detection():
    """Test server detection logic"""
    print("Server Detection Test")
    print("=" * 30)
    
    # Check if Stripe library is available
    print("Checking Stripe library availability...")
    library_available = is_stripe_library_available()
    print(f"Stripe library available: {library_available}")
    
    # Check if Stripe is configured
    print("\nChecking Stripe configuration...")
    configured = is_stripe_configured()
    print(f"Stripe configured: {configured}")
    
    # Show environment variables
    print("\nRelevant environment variables:")
    stripe_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_BUSINESS_PRICE_ID"
    ]
    for var in stripe_vars:
        value = os.getenv(var, "NOT SET")
        if var == "STRIPE_SECRET_KEY" and value != "NOT SET":
            # Mask the secret key for security
            masked_value = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
            print(f"  {var}: {masked_value}")
        else:
            print(f"  {var}: {value}")
    
    # Determine which server should be started
    print("\nServer selection logic:")
    if configured and library_available:
        print("  🟢 Should start: Minimal FastAPI server (Stripe configured and library available)")
    elif configured and not library_available:
        print("  🟡 Should start: Ultra minimal server (Stripe configured but library not available)")
    else:
        print("  🔵 Should start: Ultra minimal server (Stripe not configured)")

if __name__ == "__main__":
    test_server_detection()