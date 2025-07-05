#!/usr/bin/env python3
"""
Stripe Price Update Script for NOI Analyzer
This script updates the database with real Stripe price IDs
"""

import os
import sys
from pay_per_use.database import db_service

def update_stripe_prices():
    """Update Stripe price IDs in the database"""
    
    print("🎯 NOI Analyzer - Stripe Price Update Script")
    print("=" * 50)
    
    # Check if environment variables are set
    env_vars = {
        "STRIPE_SECRET_KEY": os.getenv("STRIPE_SECRET_KEY"),
        "STRIPE_STARTER_PRICE_ID": os.getenv("STRIPE_STARTER_PRICE_ID"),
        "STRIPE_PROFESSIONAL_PRICE_ID": os.getenv("STRIPE_PROFESSIONAL_PRICE_ID"),
        "STRIPE_BUSINESS_PRICE_ID": os.getenv("STRIPE_BUSINESS_PRICE_ID")
    }
    
    print("\n📋 Environment Variable Check:")
    missing_vars = []
    for var_name, var_value in env_vars.items():
        if var_value and not var_value.startswith("PLACEHOLDER"):
            print(f"✅ {var_name}: {var_value[:20]}...")
        else:
            print(f"❌ {var_name}: NOT SET OR PLACEHOLDER")
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("\n📝 To fix this:")
        print("1. Create a .env file in your project root")
        print("2. Add the missing variables with real Stripe values")
        print("3. Run this script again")
        print("\nExample .env content:")
        print("STRIPE_SECRET_KEY=sk_test_...")
        print("STRIPE_STARTER_PRICE_ID=price_...")
        print("STRIPE_PROFESSIONAL_PRICE_ID=price_...")
        print("STRIPE_BUSINESS_PRICE_ID=price_...")
        return False
    
    # Map package IDs to Stripe price IDs
    price_mapping = {
        "starter-5": env_vars["STRIPE_STARTER_PRICE_ID"],
        "professional-15": env_vars["STRIPE_PROFESSIONAL_PRICE_ID"], 
        "business-50": env_vars["STRIPE_BUSINESS_PRICE_ID"]
    }
    
    print(f"\n🔄 Updating database with Stripe price IDs...")
    
    try:
        # Update the database
        db_service.update_stripe_price_ids(price_mapping)
        
        print("✅ Database updated successfully!")
        
        # Verify the update
        print("\n📊 Current packages:")
        packages = db_service.get_active_packages()
        for pkg in packages:
            status = "✅" if not pkg.stripe_price_id.startswith("PLACEHOLDER") else "❌"
            print(f"{status} {pkg.name}: {pkg.stripe_price_id}")
        
        print(f"\n🎉 Success! Updated {len(price_mapping)} packages with real Stripe price IDs.")
        print("\n📱 Next steps:")
        print("1. Restart your application")
        print("2. Test credit purchases - you should now see real Stripe checkout")
        print("3. Use Stripe test cards to complete test payments")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False

def interactive_setup():
    """Interactive setup for Stripe price IDs"""
    print("\n🛠️  Interactive Stripe Setup")
    print("Enter your Stripe price IDs (or press Enter to skip):")
    
    price_ids = {}
    packages = [
        ("starter-5", "Starter Pack (5 credits, $25)"),
        ("professional-15", "Professional Pack (15 credits, $60)"),
        ("business-50", "Business Pack (50 credits, $150)")
    ]
    
    for package_id, description in packages:
        price_id = input(f"\n{description}\nPrice ID (price_...): ").strip()
        if price_id and price_id.startswith("price_"):
            price_ids[package_id] = price_id
        else:
            print("Skipping (invalid or empty price ID)")
    
    if price_ids:
        print(f"\n🔄 Updating {len(price_ids)} packages...")
        try:
            db_service.update_stripe_price_ids(price_ids)
            print("✅ Updated successfully!")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    else:
        print("❌ No valid price IDs provided")
        return False

def check_current_status():
    """Check current package status"""
    print("\n📊 Current Package Status:")
    print("-" * 50)
    
    try:
        packages = db_service.get_active_packages()
        if not packages:
            print("❌ No packages found. Run database initialization first.")
            return
        
        for pkg in packages:
            status = "✅ READY" if not pkg.stripe_price_id.startswith("PLACEHOLDER") else "❌ PLACEHOLDER"
            print(f"{status} | {pkg.name}")
            print(f"        Credits: {pkg.credits} | Price: ${pkg.price_cents/100:.2f}")
            print(f"        Stripe ID: {pkg.stripe_price_id}")
            print()
        
        ready_count = sum(1 for pkg in packages if not pkg.stripe_price_id.startswith("PLACEHOLDER"))
        print(f"📈 Summary: {ready_count}/{len(packages)} packages ready for Stripe")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_setup()
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        check_current_status()
    else:
        if not update_stripe_prices():
            print("\n💡 Alternative options:")
            print("   python update_stripe_prices.py --interactive  # Manual entry")
            print("   python update_stripe_prices.py --status       # Check current status") 