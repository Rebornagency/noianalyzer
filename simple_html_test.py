import streamlit as st

st.set_page_config(
    page_title="Simple HTML Test",
    page_icon="💳",
    layout="wide"
)

st.title("Simple HTML Test")

# Test 1: Simple div with text
st.markdown("## Test 1: Simple div with text")
st.markdown("<div style='background: red; padding: 10px;'>This should be a red box with text</div>", unsafe_allow_html=True)

# Test 2: Div with nested elements
st.markdown("## Test 2: Div with nested elements")
st.markdown("""
<div style='background: blue; padding: 10px; color: white;'>
    <h3>Header inside div</h3>
    <p>Paragraph inside div</p>
    <div style='background: green; padding: 5px; margin: 5px; color: white;'>
        Nested green div with text
    </div>
</div>
""", unsafe_allow_html=True)

# Test 3: Same structure as credit store
st.markdown("## Test 3: Same structure as credit store")
st.markdown("""
<div style="
    background: linear-gradient(145deg, #1a2436, #0f1722);
    border: 1px solid #2a3a50;
    border-radius: 16px;
    padding: 2rem;
    margin: 1.5rem 0;
    text-align: center;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    width: 100%;
    box-sizing: border-box;
    color: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
">
    <h3 style="
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 0 1.5rem 0;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        width: 100%;
        text-align: center;
    ">
        Starter Package
    </h3>
    
    <div style="
        color: #FFFFFF;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1rem 0;
        width: 100%;
        text-align: center;
    ">
        5 Credits
    </div>
    
    <div style="
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.8rem 1.5rem;
        border-radius: 50px;
        margin: 1rem auto;
        width: fit-content;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        text-align: center;
    ">
        5 Credits!
    </div>
</div>
""", unsafe_allow_html=True)