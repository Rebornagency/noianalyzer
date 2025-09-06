import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_credit_ui_render():
    """Test that the credit UI function can be called without errors"""
    try:
        # Mock Streamlit
        import streamlit as st
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        # Set up test data
        st.session_state['user_email'] = 'test@example.com'
        
        # Mock the display_loading_spinner function
        import utils.credit_ui_minimal as credit_ui
        original_display_loading_spinner = None
        
        # Try to import and mock the function if it exists
        try:
            from utils.ui_helpers import display_loading_spinner
        except ImportError:
            # Create a mock function
            def display_loading_spinner(message="", subtitle=""):
                pass
            credit_ui.display_loading_spinner = display_loading_spinner
        
        # Mock the get_credit_packages function to return test data
        def mock_get_credit_packages():
            return [
                {
                    "package_id": "starter",
                    "name": "Starter Pack",
                    "credits": 5,
                    "price_dollars": 5.00,
                    "per_credit_cost": 1.00,
                    "description": "Perfect for trying out the service"
                },
                {
                    "package_id": "professional",
                    "name": "Professional Pack",
                    "credits": 20,
                    "price_dollars": 15.00,
                    "per_credit_cost": 0.75,
                    "description": "Best value for regular users"
                },
                {
                    "package_id": "enterprise",
                    "name": "Enterprise Pack",
                    "credits": 50,
                    "price_dollars": 30.00,
                    "per_credit_cost": 0.60,
                    "description": "Maximum value for heavy users"
                }
            ]
        
        # Replace the function
        credit_ui.get_credit_packages = mock_get_credit_packages
        
        # Try to call the function
        credit_ui.display_credit_store()
        
        print("✅ display_credit_store function executed without errors")
        return True
        
    except Exception as e:
        print(f"❌ Error calling display_credit_store function: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing Credit UI Render...")
    print("=" * 50)
    
    success = test_credit_ui_render()
    
    if success:
        print("\n🎉 Credit UI render test passed!")
        print("The function can be called without syntax errors.")
        sys.exit(0)
    else:
        print("\n❌ Credit UI render test failed.")
        sys.exit(1)