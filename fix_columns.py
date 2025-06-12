#!/usr/bin/env python3
"""
Script to fix the unused column creation in app.py
"""

def fix_app_file():
    # Read the current file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the problematic lines
    old_text = """            # Create a row for the options
            options_col1, options_col2 = st.columns(2)

            # Show Zero Values toggle (now full width since theme toggle moved to header)"""
    
    new_text = """            # Show Zero Values toggle (now full width since theme toggle moved to header)"""
    
    # Perform the replacement
    new_content = content.replace(old_text, new_text)
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fixed unused column creation in app.py")

if __name__ == "__main__":
    fix_app_file() 