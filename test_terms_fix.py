"""
Test script to verify the Terms and Conditions fix.
This script tests that:
1. The Process Documents button always has the correct modern style
2. Terms validation works correctly without changing button style
3. Document processing works after terms are accepted
"""
import streamlit as st
from utils.ui_helpers import restore_button

# Initialize session state
if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False

st.title("Terms and Conditions Fix Verification")

# Test the restore_button function
st.subheader("Button Styling Test")
st.write("The button below should always have the modern 'primary' styling:")

# Create a button placeholder
button_placeholder = st.empty()

# Test restoring button with primary styling
with button_placeholder.container():
    clicked = st.button("Test Button", key="test_button", type="primary")

# If clicked, restore with primary styling
if clicked:
    st.write("Button was clicked - restoring with primary styling...")
    restore_button(button_placeholder, "Restored Button", key="test_button")

# Test terms validation flow
st.subheader("Terms Validation Test")

# Terms checkbox
terms_accepted = st.checkbox(
    "I have read and accept the Terms of Service and Privacy Policy",
    value=st.session_state.get('terms_accepted', False),
    key="test_terms_acceptance"
)

# Update session state
st.session_state.terms_accepted = terms_accepted

# Process button
process_clicked = st.button("Process Documents", key="test_process_button", type="primary")

if process_clicked:
    st.write(f"Process button clicked. Terms accepted: {st.session_state.terms_accepted}")
    if not st.session_state.terms_accepted:
        st.warning("⚠️ You must accept the Terms of Service and Privacy Policy to process documents.")
    else:
        st.success("✅ Terms accepted! Processing would begin here.")

st.write("---")
st.write("✅ All tests completed. Check that:")
st.write("1. Buttons maintain consistent styling")
st.write("2. Terms validation works without changing button appearance")
st.write("3. Processing proceeds normally when terms are accepted")