#!/usr/bin/env python3
"""
Test script to verify terms acceptance functionality
"""

import streamlit as st

def test_terms_acceptance():
    """Test the terms acceptance functionality"""
    st.title("Terms Acceptance Test")
    
    # Display the terms acceptance checkbox
    st.markdown(
        '<div class="tos-checkbox-label">🔒 By processing documents, you agree to our <a href="/terms-of-service" target="_blank" class="tos-link">Terms of Service</a> and <a href="/privacy-policy" target="_blank" class="tos-link">Privacy Policy</a></div>',
        unsafe_allow_html=True
    )
    terms_accepted = st.checkbox(
        "I have read and accept the Terms of Service and Privacy Policy",
        value=st.session_state.get('terms_accepted', False),
        key="terms_acceptance_test"
    )
    
    # Update session state with terms acceptance
    st.session_state.terms_accepted = terms_accepted
    
    # Display current status
    st.write(f"Terms accepted: {st.session_state.terms_accepted}")
    
    # Test the error message display
    if st.button("Test Error Message"):
        st.session_state.show_tos_error = True
        st.experimental_rerun()
    
    # Display error message if terms were not accepted on previous attempt
    if st.session_state.get('show_tos_error', False):
        st.markdown(
            '<div class="tos-error">⚠️ You must accept the Terms of Service and Privacy Policy to process documents.</div>',
            unsafe_allow_html=True
        )
        # Reset the error flag
        st.session_state.show_tos_error = False

if __name__ == "__main__":
    test_terms_acceptance()