#!/usr/bin/env python3
"""
Script to add Excel export import to app.py
"""

import os

# Read the app.py file
app_file_path = 'app.py'
with open(app_file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the import is already there
if 'from excel_export import generate_comparison_excel' in content:
    print("Excel export import already exists in app.py")
    exit(0)

# Find the location to insert the import
import_location = 'from utils.ui_helpers import ('
insert_text = '''from utils.ui_helpers import (
    show_processing_status, display_loading_spinner, display_progress_bar,
    display_inline_loading, LoadingContext, get_loading_message_for_action,
    create_loading_button, show_button_loading, restore_button
)

# Try to import Excel export function
try:
    from excel_export import generate_comparison_excel
except ImportError:
    def generate_comparison_excel():
        st.error("Excel export functionality not available")
        return None

# Constants for testing mode'''

# Replace the old import section with the new one
old_import = '''from utils.ui_helpers import (
    show_processing_status, display_loading_spinner, display_progress_bar,
    display_inline_loading, LoadingContext, get_loading_message_for_action,
    create_loading_button, show_button_loading, restore_button
)

# Constants for testing mode'''

if old_import in content:
    content = content.replace(old_import, insert_text)
    # Write the modified content back to the file
    with open(app_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully added Excel export import to app.py")
else:
    print("Could not find the import section to modify")
    exit(1)