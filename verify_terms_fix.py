"""
Test script to verify the Terms of Service validation fix
"""
import streamlit as st

# Initialize session state
if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False

if 'show_tos_error' not in st.session_state:
    st.session_state.show_tos_error = False

st.title("Terms of Service Validation Fix Verification")

st.markdown("""
This test verifies that the Terms of Service validation works correctly:
1. If terms are not accepted, show error message and prevent processing
2. If terms are accepted, allow processing to proceed
""")

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

# Process button
if st.button("Process Documents", key="main_process_button"):
    st.write(f"Process button clicked. Terms accepted: {st.session_state.terms_accepted}")
    
    if not st.session_state.terms_accepted:
        st.session_state.show_tos_error = True
        st.markdown(
            '<div class="tos-error">⚠️ You must accept the Terms of Service and Privacy Policy to process documents.</div>',
            unsafe_allow_html=True
        )
        st.session_state.show_tos_error = False  # Reset immediately for this test
    else:
        st.success("✅ Terms accepted! Processing would proceed normally.")
        st.write("In the actual application, document processing would happen here...")

st.markdown("---")
st.markdown("✅ **Test Results:**")
st.markdown("- If you click 'Process Documents' without accepting terms, you should see an error message")
st.markdown("- If you accept terms and then click 'Process Documents', you should see a success message")
st.markdown("- No DuplicateWidgetID errors should occur")