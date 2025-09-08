import streamlit as st

def test_terms_flow():
    """Test the terms of service flow to ensure no duplicate widget ID errors"""
    
    st.title("Terms of Service Flow Test")
    
    # Initialize session state
    if 'terms_accepted' not in st.session_state:
        st.session_state.terms_accepted = False
    
    # Terms of Service acceptance checkbox
    st.session_state.terms_accepted = st.checkbox(
        "I have read and accept the Terms of Service and Privacy Policy",
        value=st.session_state.terms_accepted,
        key="terms_checkbox"
    )
    
    # Process button
    process_clicked = st.button("Process Documents", key="test_process_button")
    
    if process_clicked:
        # Check if Terms of Service have been accepted BEFORE any processing
        if not st.session_state.terms_accepted:
            st.error("⚠️ You must accept the Terms of Service and Privacy Policy to process documents.")
            return  # Exit the function to prevent further processing
        
        # If terms are accepted, continue with processing
        st.success("Terms accepted! Continuing with document processing...")
        # Add your document processing logic here

if __name__ == "__main__":
    test_terms_flow()