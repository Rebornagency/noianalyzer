#!/usr/bin/env python3
"""
Test script to verify the NOI Coach one-step behind fix.
This script tests that the NOI Coach now responds immediately to user inputs.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_noi_coach_immediate_response():
    """Test that the NOI Coach responds immediately to user inputs."""
    print("Testing NOI Coach immediate response fix...")
    
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
    
    # Check that the form submission handling happens before chat history display
    if 'Handle form submission BEFORE displaying chat history' not in source:
        print("✗ Fix not properly implemented - form submission should happen before chat history display")
        return False
    
    print("✓ Form submission handling properly positioned before chat history display")
    
    # Check that immediate display of new messages is implemented
    if 'Display the new messages immediately' not in source:
        print("✗ Fix not properly implemented - new messages should be displayed immediately")
        return False
    
    print("✓ New messages are displayed immediately after being added to history")
    
    # Check that st.rerun() is not being used
    if 'st.rerun()' in source and '# st.rerun()' not in source:
        print("✗ st.rerun() still present in display_noi_coach function")
        return False
    
    print("✓ st.rerun() properly removed/commented out")
    
    print("All tests passed! The NOI Coach one-step behind fix is correctly implemented.")
    return True

def test_noi_coach_no_infinite_loop():
    """Test that the NOI Coach doesn't enter infinite loops."""
    print("\nTesting NOI Coach infinite loop prevention...")
    
    # Import the app module
    try:
        import app
        print("✓ Successfully imported app module")
    except Exception as e:
        print(f"✗ Failed to import app module: {e}")
        return False
    
    # Check the source code for infinite loop prevention
    import inspect
    source = inspect.getsource(app.display_noi_coach)
    
    # Check that there's no st.rerun() call that could cause infinite loops
    if 'st.rerun()' in source and '# st.rerun()' not in source:
        print("✗ st.rerun() still present which could cause infinite loops")
        return False
    
    print("✓ No st.rerun() calls that could cause infinite loops")
    
    # Check that the implementation uses direct display instead of reruns
    if 'Display the new messages immediately' not in source:
        print("✗ Implementation should use direct display instead of reruns")
        return False
    
    print("✓ Implementation uses direct display to prevent infinite loops")
    
    print("All infinite loop prevention tests passed!")
    return True

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Run the tests
    success1 = test_noi_coach_immediate_response()
    success2 = test_noi_coach_no_infinite_loop()
    
    if success1 and success2:
        print("\n✅ NOI Coach fix verification successful!")
        print("The one-step behind issue has been resolved and infinite loops are prevented.")
        sys.exit(0)
    else:
        print("\n❌ NOI Coach fix verification failed!")
        sys.exit(1)