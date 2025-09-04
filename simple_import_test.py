print("Testing credit_ui_robust import...")
try:
    from utils.credit_ui_robust import display_credit_store
    print("✅ SUCCESS: credit_ui_robust imported successfully")
    print(f"   Function: {display_credit_store}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\nTesting credit_ui_fresh import...")
try:
    from utils.credit_ui_fresh import display_credit_store
    print("✅ SUCCESS: credit_ui_fresh imported successfully")
    print(f"   Function: {display_credit_store}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\nTesting credit_ui import...")
try:
    from utils.credit_ui import display_credit_store
    print("✅ SUCCESS: credit_ui imported successfully")
    print(f"   Function: {display_credit_store}")
except Exception as e:
    print(f"❌ FAILED: {e}")