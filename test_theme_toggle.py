#!/usr/bin/env python3
"""
Test script to verify theme toggle implementation
"""

def test_theme_toggle_location():
    """Test that theme toggle has been moved to header"""
    
    # Read the app.py file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if theme toggle is in display_logo function
    if 'theme-toggle' in content and 'display_logo' in content:
        print("✅ Theme toggle found in display_logo function")
    else:
        print("❌ Theme toggle not found in display_logo function")
    
    # Check if old theme toggle location is removed
    if 'with options_col2:' not in content:
        print("✅ Old theme toggle location removed")
    else:
        print("❌ Old theme toggle location still exists")
    
    # Check for unused column creation
    if 'options_col1, options_col2 = st.columns(2)' in content:
        print("⚠️  Unused column creation still exists")
    else:
        print("✅ Unused column creation removed")

if __name__ == "__main__":
    test_theme_toggle_location() 