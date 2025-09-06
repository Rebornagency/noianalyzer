import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set a test email for demonstration
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

# Import the credit UI functions
try:
    from utils.credit_ui_minimal import display_credit_store
    st.success("✅ Successfully imported display_credit_store from credit_ui_minimal")
except ImportError as e:
    st.error(f"❌ Failed to import display_credit_store from credit_ui_minimal: {e}")
    st.stop()

# Set up the page
st.set_page_config(
    page_title="Credit Store Debug",
    page_icon="💳",
    layout="wide"
)

st.title("💳 Credit Store Debug")

# Add some debugging info
st.sidebar.markdown("### Debug Info")
st.sidebar.write(f"User email: {st.session_state.get('user_email', 'Not set')}")

# Add a debug flag
DEBUG_CREDITS = st.sidebar.checkbox("Enable Debug Logging", value=False)

if DEBUG_CREDITS:
    st.sidebar.markdown("### Debug Output")
    st.sidebar.info("Debug logging enabled")

# Display the credit store
try:
    display_credit_store()
    st.success("✅ display_credit_store executed without errors")
except Exception as e:
    st.error(f"❌ Error in display_credit_store: {e}")
    st.exception(e)

# Add a back button
if st.button("← Back to Main App"):
    st.session_state.show_credit_store = False
    st.experimental_rerun()