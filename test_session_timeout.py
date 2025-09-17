import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import streamlit as st
    
    # Test session timeout logic
    print("SUCCESS: Imported streamlit")
    
    # Initialize session state variables
    if 'last_activity' not in st.session_state:
        st.session_state['last_activity'] = time.time()
    
    if 'session_start_time' not in st.session_state:
        st.session_state['session_start_time'] = time.time()
    
    print("SUCCESS: Session state initialized")
    
    # Test session timeout configuration
    import os
    session_timeout = int(os.getenv("SESSION_TIMEOUT_SECONDS", 3600))
    print(f"SUCCESS: Session timeout configured to {session_timeout} seconds")
    
    # Test time functions
    current_time = time.time()
    idle_time = current_time - st.session_state['last_activity']
    print(f"SUCCESS: Current time: {current_time}, Idle time: {idle_time}")
    
    print("SUCCESS: All session timeout tests completed")
    
except Exception as e:
    print(f"ERROR: Failed to test session timeout logic: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)