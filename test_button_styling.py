"""
Test script to verify button styling consistency.
This script tests that the Process Documents button maintains consistent styling
with the "Buy More Credits" button.
"""
import streamlit as st
from utils.ui_helpers import create_loading_button, show_button_loading, restore_button

st.title("Button Styling Test")

# Test the Process Documents button styling
st.subheader("Process Documents Button")
st.write("This button should maintain consistent styling:")

# Create a button placeholder
process_button_placeholder = st.empty()

# Create the button with primary type (like Process Documents)
with process_button_placeholder.container():
    process_clicked = st.button("Process Documents", key="test_process", type="primary")

# If clicked, show loading state and then restore
if process_clicked:
    st.write("Button clicked - showing loading state...")
    show_button_loading(process_button_placeholder, "Processing...")
    
    # Simulate some processing time
    import time
    time.sleep(2)
    
    # Restore the button
    st.write("Restoring button...")
    restore_button(process_button_placeholder, "Process Documents", key="test_process_restored", type="primary")

st.markdown("---")

# Test the Buy More Credits button styling
st.subheader("Buy More Credits Button")
st.write("This button should have the same styling:")

# Create using create_loading_button (like Buy More Credits)
buy_clicked, buy_button_placeholder = create_loading_button("🛒 Buy More Credits", key="test_buy")

if buy_clicked:
    st.write("Buy button clicked - showing loading state...")
    show_button_loading(buy_button_placeholder, "Loading Store...")
    
    # Simulate some processing time
    import time
    time.sleep(2)
    
    # Restore the button
    st.write("Restoring button...")
    restore_button(buy_button_placeholder, "🛒 Buy More Credits", key="test_buy_restored")

st.markdown("---")
st.write("✅ Both buttons should have consistent styling throughout their lifecycle.")