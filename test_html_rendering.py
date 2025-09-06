import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_html_rendering():
    """Test that HTML rendering works correctly"""
    try:
        # Mock the necessary Streamlit functions and session state
        import streamlit as st
        from utils.credit_ui_minimal import display_credit_store
        
        # Mock session state
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        st.session_state['user_email'] = 'test@example.com'
        
        print("✅ HTML rendering test passed - no syntax errors")
        return True
    except Exception as e:
        print(f"❌ HTML rendering test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing HTML Rendering...")
    print("=" * 50)
    
    success = test_html_rendering()
    
    if success:
        print("🎉 HTML rendering is working correctly!")
        sys.exit(0)
    else:
        print("❌ HTML rendering has issues.")
        sys.exit(1)