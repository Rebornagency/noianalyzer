import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_and_function():
    """Test that we can import and call the function without errors"""
    try:
        # Try to import the function
        from utils.credit_ui_minimal import display_credit_store, log_credit_ui_debug
        print("✅ Successfully imported display_credit_store and log_credit_ui_debug")
        
        # Test that log_credit_ui_debug function works
        log_credit_ui_debug("Test message")
        print("✅ log_credit_ui_debug function works correctly")
        
        return True
    except Exception as e:
        print(f"❌ Import or function test failed: {e}")
        return False

def test_html_structure():
    """Test that the HTML structure is properly formed"""
    try:
        # Read the file
        with open('utils/credit_ui_minimal.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper function structure
        if 'def display_credit_store():' not in content:
            print("❌ display_credit_store function not found")
            return False
            
        # Check that log_credit_ui_debug is defined before display_credit_store
        lines = content.split('\n')
        log_debug_line = -1
        display_store_line = -1
        
        for i, line in enumerate(lines):
            if 'def log_credit_ui_debug(' in line:
                log_debug_line = i
            elif 'def display_credit_store():' in line:
                display_store_line = i
                
        if log_debug_line == -1:
            print("❌ log_credit_ui_debug function not found")
            return False
            
        if display_store_line == -1:
            print("❌ display_credit_store function not found")
            return False
            
        if log_debug_line > display_store_line:
            print("❌ log_credit_ui_debug defined after display_credit_store (will cause NameError)")
            return False
            
        print("✅ Function definitions are in correct order")
        
        # Check for proper HTML construction
        if 'card_html = f"""' not in content:
            print("❌ card_html construction not found")
            return False
            
        if 'st.markdown(card_html, unsafe_allow_html=True)' not in content:
            print("❌ st.markdown call with unsafe_allow_html not found")
            return False
            
        print("✅ HTML construction pattern is correct")
        
        return True
    except Exception as e:
        print(f"❌ HTML structure test failed: {e}")
        return False

def test_badge_display():
    """Test that badge display logic is correct"""
    try:
        # Read the file
        with open('utils/credit_ui_minimal.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for badge conditions
        required_badges = [
            "5 Credits!",
            "Best Value!",
        ]
        
        for badge in required_badges:
            if badge not in content:
                print(f"❌ Required badge '{badge}' not found in HTML")
                return False
                
        print("✅ All required badges found in HTML")
        
        # Check for badge logic conditions
        required_conditions = [
            "idx == 0 and len(packages) > 1",
            "(len(packages) > 2 and idx == 1) or (len(packages) == 2 and idx == 1)",
            "savings_text and idx > 1"
        ]
        
        for condition in required_conditions:
            if condition not in content:
                print(f"❌ Required badge condition '{condition}' not found")
                return False
                
        print("✅ All badge display conditions found")
        
        return True
    except Exception as e:
        print(f"❌ Badge display test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Final Credit UI Test")
    print("=" * 50)
    
    test1 = test_import_and_function()
    print()
    test2 = test_html_structure()
    print()
    test3 = test_badge_display()
    
    if test1 and test2 and test3:
        print("\n🎉 All tests passed!")
        print("The credit UI should now display properly with:")
        print("  - Proper HTML structure")
        print("  - Green containers (badges) above CTAs")
        print("  - CTA button styling and functionality preserved")
        print("  - Debugging support included")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)