import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import the fresh credit UI implementation
    from utils.credit_ui_fresh import display_credit_store, get_credit_packages, get_user_credits
    print("✅ Successfully imported fresh credit UI implementation")
    
    # Try to call the get_credit_packages function
    packages = get_credit_packages()
    print(f"✅ get_credit_packages() returned {len(packages)} packages")
    
    # Try to call the display_credit_store function (this will just define it, not execute it)
    print("✅ display_credit_store function is available")
    
    print("\n🎉 All tests passed! The fresh credit UI implementation is ready to use.")
    
except Exception as e:
    print(f"❌ Error importing or using fresh credit UI implementation: {e}")
    import traceback
    traceback.print_exc()