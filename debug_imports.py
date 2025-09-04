import sys
import os
import traceback

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Credit UI Import Debug Test ===")

# Test robust implementation
print("\n1. Testing credit_ui_robust import:")
try:
    from utils.credit_ui_robust import display_credit_store
    print("   ✅ Successfully imported display_credit_store from credit_ui_robust")
    print(f"   Function location: {display_credit_store.__module__}")
except Exception as e:
    print(f"   ❌ Failed to import display_credit_store from credit_ui_robust: {e}")
    traceback.print_exc()

# Test fresh implementation
print("\n2. Testing credit_ui_fresh import:")
try:
    from utils.credit_ui_fresh import display_credit_store
    print("   ✅ Successfully imported display_credit_store from credit_ui_fresh")
    print(f"   Function location: {display_credit_store.__module__}")
except Exception as e:
    print(f"   ❌ Failed to import display_credit_store from credit_ui_fresh: {e}")
    traceback.print_exc()

# Test original implementation
print("\n3. Testing credit_ui import:")
try:
    from utils.credit_ui import display_credit_store
    print("   ✅ Successfully imported display_credit_store from credit_ui")
    print(f"   Function location: {display_credit_store.__module__}")
except Exception as e:
    print(f"   ❌ Failed to import display_credit_store from credit_ui: {e}")
    traceback.print_exc()

print("\n=== Import Test Complete ===")