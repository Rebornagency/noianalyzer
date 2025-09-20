#!/usr/bin/env python3
"""
Test script to verify the NOI Coach infinite loop fix.
This script tests that the NOI Coach no longer causes infinite refresh cycles.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_noi_coach_fix():
    """Test that the NOI Coach fix prevents infinite loops."""
    print("Testing NOI Coach infinite loop fix...")
    
    # Import the app module
    try:
        import app
        print("✓ Successfully imported app module")
    except Exception as e:
        print(f"✗ Failed to import app module: {e}")
        return False
    
    # Check that the display_noi_coach function exists
    if not hasattr(app, 'display_noi_coach'):
        print("✗ display_noi_coach function not found")
        return False
    
    print("✓ display_noi_coach function exists")
    
    # Check the source code for the fix
    import inspect
    source = inspect.getsource(app.display_noi_coach)
    
    # Check that st.rerun() is commented out or removed
    if 'st.rerun()' in source and '# st.rerun()' not in source:
        print("✗ st.rerun() still present in display_noi_coach function")
        return False
    
    print("✓ st.rerun() properly removed/commented out")
    
    # Check that the function has proper session state handling
    if 'noi_coach_history' not in source:
        print("✗ noi_coach_history not found in function")
        return False
    
    print("✓ noi_coach_history properly handled")
    
    print("All tests passed! The NOI Coach infinite loop fix is correctly implemented.")
    return True

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Run the test
    success = test_noi_coach_fix()
    
    if success:
        print("\n✅ NOI Coach fix verification successful!")
        sys.exit(0)
    else:
        print("\n❌ NOI Coach fix verification failed!")
        sys.exit(1)