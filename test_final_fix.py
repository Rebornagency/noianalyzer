import streamlit as st

# Initialize session state for terms acceptance
if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False

# Initialize session state for error display
if 'show_tos_error' not in st.session_state:
    st.session_state.show_tos_error = False

# Initialize session state for user email
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

st.title("Final Terms of Service Fix Test")

# Email input
user_email = st.text_input("Email", value=st.session_state.get('user_email', ''), key="user_email_input")
st.session_state.user_email = user_email

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
    st.write(f"User email: {st.session_state.user_email}")
    
    # Check if email is provided
    if not st.session_state.user_email.strip():
        st.error("📧 Email address is required. Please enter your email address before processing documents.")
    elif not st.session_state.terms_accepted:
        st.session_state.show_tos_error = True
        st.markdown(
            '<div class="tos-error">⚠️ You must accept the Terms of Service and Privacy Policy to process documents.</div>',
            unsafe_allow_html=True
        )
        st.session_state.show_tos_error = False  # Reset immediately for this test
    else:
        st.success("Processing documents...")
        # Simulate document processing
        st.write("Document processing would happen here...")