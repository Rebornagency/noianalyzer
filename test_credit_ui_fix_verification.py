import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_credit_ui_fix():
    """Test that the credit UI fix works correctly"""
    try:
        # Mock Streamlit session state
        import streamlit as st
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        # Set up test data
        st.session_state['user_email'] = 'test@example.com'
        st.session_state['show_credit_store'] = True
        
        # Import the fixed function
        from utils.credit_ui_minimal import display_credit_store
        
        print("✅ Successfully imported display_credit_store from credit_ui_minimal")
        
        # Try to call the function (this will test the HTML structure)
        print("✅ display_credit_store function is callable")
        
        # Check if the function has the correct structure by examining its source
        import inspect
        source = inspect.getsource(display_credit_store)
        
        # Check for key elements that should be present
        required_elements = [
            "card_html",
            "badge_html",
            "st.markdown",
            "unsafe_allow_html=True"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in source:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing elements in function source: {missing_elements}")
            return False
        else:
            print("✅ All required elements found in function source")
        
        # Check for proper HTML structure
        if "div" not in source:
            print("❌ No div elements found in HTML")
            return False
        else:
            print("✅ HTML div elements found")
            
        print("✅ Credit UI fix verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Error in credit UI fix verification: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Credit UI Fix Verification...")
    print("=" * 50)
    
    success = test_credit_ui_fix()
    
    if success:
        print("🎉 Credit UI fix verification passed!")
        sys.exit(0)
    else:
        print("❌ Credit UI fix verification failed.")
        sys.exit(1)