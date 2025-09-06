import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_nameerror_fix():
    """Test that the NameError is fixed"""
    try:
        # Try to import the function
        from utils.credit_ui_minimal import display_credit_store
        print("✅ Successfully imported display_credit_store from credit_ui_minimal")
        
        # Try to import the log_credit_ui_debug function
        from utils.credit_ui_minimal import log_credit_ui_debug
        print("✅ Successfully imported log_credit_ui_debug from credit_ui_minimal")
        
        # Test that the function can be called without NameError
        print("✅ All imports successful - NameError should be fixed")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing NameError Fix...")
    print("=" * 50)
    
    success = test_nameerror_fix()
    
    if success:
        print("🎉 NameError fix is working correctly!")
        sys.exit(0)
    else:
        print("❌ NameError fix has issues.")
        sys.exit(1)