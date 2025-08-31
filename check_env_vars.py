#!/usr/bin/env python3
"""
Check environment variables related to Stripe
"""

import os

print("Checking Stripe-related environment variables...")

stripe_vars = [
    "STRIPE_SECRET_KEY",
    "STRIPE_STARTER_PRICE_ID", 
    "STRIPE_PROFESSIONAL_PRICE_ID",
    "STRIPE_BUSINESS_PRICE_ID"
]

for var in stripe_vars:
    value = os.getenv(var, "NOT SET")
    if value == "NOT SET":
        print(f"❌ {var}: {value}")
    else:
        # Mask sensitive values
        if 'KEY' in var.upper() or 'SECRET' in var.upper():
            masked_value = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"✅ {var}: SET (value: {value[:20]}{'...' if len(value) > 20 else ''})")

print("\nAll environment variables containing 'STRIPE':")
all_env = dict(os.environ)
stripe_env = {k: v for k, v in all_env.items() if 'STRIPE' in k.upper()}
if stripe_env:
    for k, v in stripe_env.items():
        # Mask sensitive values
        if 'KEY' in k.upper() or 'SECRET' in k.upper():
            masked_value = f"{v[:3]}...{v[-4:]}" if len(v) > 7 else "Too short"
            print(f"  {k}: {masked_value}")
        else:
            print(f"  {k}: {v[:20]}{'...' if len(v) > 20 else ''}")
else:
    print("  No STRIPE-related environment variables found")