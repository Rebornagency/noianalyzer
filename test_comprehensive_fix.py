import streamlit as st
from utils.ui_helpers import create_loading_button, show_button_loading, restore_button

# Initialize session state
if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False

if 'show_tos_error' not in st.session_state:
    st.session_state.show_tos_error = False

st.title("Comprehensive Terms of Service Fix Test")

# Terms of Service acceptance checkbox
st.markdown(
    '<div class="tos-checkbox-label">🔒 By processing documents, you agree to our <a href="/terms-of-service" target="_blank" class="tos-link">Terms of Service</a> and <a href="/privacy-policy" target="_blank" class="tos-link">Privacy Policy</a></div>',
    unsafe_allow_html=True
)
terms_accepted = st.checkbox(
    "I have read and accept the Terms of Service and Privacy Policy",
    value=st.session_state.get('terms_accepted', False),
    key="terms_acceptance"
)

# Update session state with terms acceptance
st.session_state.terms_accepted = terms_accepted

# Display error message if terms were not accepted on previous attempt
# This needs to be here to ensure the message is displayed after button click
if st.session_state.get('show_tos_error', False):
    st.markdown(
        '<div class="tos-error">⚠️ You must accept the Terms of Service and Privacy Policy to process documents.</div>',
        unsafe_allow_html=True
    )
    # Reset the error flag after displaying the message
    st.session_state.show_tos_error = False

# Enhanced Process Documents button with loading state
process_clicked, process_button_placeholder = create_loading_button(
    "Process Documents",
    key="main_process_button",
    help="Process the uploaded documents to generate NOI analysis",
    type="primary",
    use_container_width=True
)

# Display error message if terms were not accepted on previous attempt
# This needs to be here to ensure the message is displayed after button click
if st.session_state.get('show_tos_error', False):
    st.markdown(
        '<div class="tos-error">⚠️ You must accept the Terms of Service and Privacy Policy to process documents.</div>',
        unsafe_allow_html=True
    )
    # Reset the error flag after displaying the message
    st.session_state.show_tos_error = False

if process_clicked:
    st.write(f"Process button clicked. Terms accepted: {st.session_state.terms_accepted}")
    
    # Show loading state immediately
    show_button_loading(process_button_placeholder, "Processing Documents...")
    
    # Check if Terms of Service have been accepted
    if not st.session_state.get('terms_accepted', False):
        st.session_state.show_tos_error = True
        # Clear loading states before showing error
        restore_button(process_button_placeholder, "Process Documents", key="main_process_button", type="primary", use_container_width=True)
        # Don't call st.rerun() here to prevent infinite loop
        # The error message will be displayed on the next render cycle
    else:
        st.success("Processing documents...")
        # Restore button after processing
        restore_button(process_button_placeholder, "Process Documents", key="main_process_button", type="primary", use_container_width=True)