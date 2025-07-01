#!/usr/bin/env python3
"""
Helper script to update Stripe price IDs in your credit system

After creating products in Stripe, run this script to update your database
with the real price IDs that Stripe generated.

Usage:
    python update_stripe_prices.py

The script will prompt you for the real price IDs from Stripe.
"""

from pay_per_use.database import db_service

def main():
    print("🔧 Stripe Price ID Updater")
    print("=" * 40)
    print()
    print("After creating products in Stripe, you'll get price IDs like:")
    print("  price_1ABC123DEF456789")
    print("  price_1XYZ789GHI012345")
    print("  price_1QRS456TUV890123")
    print()
    print("Enter the real price IDs below:")
    print()
    
    # Get price IDs from user
    starter_price = input("📦 Starter Pack ($25, 5 credits) price ID: ").strip()
    professional_price = input("📦 Professional Pack ($60, 15 credits) price ID: ").strip()
    business_price = input("📦 Business Pack ($150, 50 credits) price ID: ").strip()
    
    # Validate that they look like real Stripe price IDs
    valid_prices = []
    
    if starter_price.startswith('price_') and len(starter_price) > 10:
        valid_prices.append(('starter-5', starter_price))
    else:
        print(f"⚠️  Warning: '{starter_price}' doesn't look like a valid Stripe price ID")
    
    if professional_price.startswith('price_') and len(professional_price) > 10:
        valid_prices.append(('professional-15', professional_price))
    else:
        print(f"⚠️  Warning: '{professional_price}' doesn't look like a valid Stripe price ID")
    
    if business_price.startswith('price_') and len(business_price) > 10:
        valid_prices.append(('business-50', business_price))
    else:
        print(f"⚠️  Warning: '{business_price}' doesn't look like a valid Stripe price ID")
    
    if not valid_prices:
        print("❌ No valid price IDs entered. Exiting.")
        return
    
    # Confirm with user
    print()
    print("📋 Summary of updates:")
    for package_id, price_id in valid_prices:
        package_name = {
            'starter-5': 'Starter Pack',
            'professional-15': 'Professional Pack', 
            'business-50': 'Business Pack'
        }.get(package_id, package_id)
        print(f"  {package_name}: {price_id}")
    
    print()
    confirm = input("✅ Update database with these price IDs? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        try:
            # Update the database
            price_mapping = dict(valid_prices)
            db_service.update_stripe_price_ids(price_mapping)
            
            print()
            print("🎉 SUCCESS! Stripe price IDs updated in database")
            print()
            print("Next steps:")
            print("1. Add these to your .env file:")
            
            for package_id, price_id in valid_prices:
                env_var = {
                    'starter-5': 'STRIPE_STARTER_PRICE_ID',
                    'professional-15': 'STRIPE_PROFESSIONAL_PRICE_ID',
                    'business-50': 'STRIPE_BUSINESS_PRICE_ID'
                }.get(package_id)
                print(f"   {env_var}={price_id}")
            
            print()
            print("2. Restart your API server")
            print("3. Test credit purchases!")
            
        except Exception as e:
            print(f"❌ ERROR updating database: {e}")
    else:
        print("❌ Cancelled. No changes made.")

if __name__ == "__main__":
    main() 