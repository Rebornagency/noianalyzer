import streamlit as st
from utils.credit_ui import display_credit_store

st.set_page_config(page_title="Credit Store Test", layout="wide")

st.title("Credit Store UI Test")

# Initialize session state
if 'show_credit_store' not in st.session_state:
    st.session_state.show_credit_store = True

# Display the credit store
display_credit_store()