import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="HTML Construction Test",
    page_icon="💳",
    layout="wide"
)

st.title("HTML Construction Test")

# Set a test email
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

# Mock package data
packages = [
    {
        "package_id": "starter",
        "name": "Starter",
        "credits": 5,
        "price_dollars": 5.00,
        "per_credit_cost": 1.00,
        "description": "Perfect for trying out our service"
    },
    {
        "package_id": "professional",
        "name": "Professional",
        "credits": 20,
        "price_dollars": 15.00,
        "per_credit_cost": 0.75,
        "description": "Best value for regular users"
    }
]

# Test HTML construction for the first package (Starter)
package = packages[0]
idx = 0

# Build the complete card HTML in one piece
card_html = f"""
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
        {package["name"]}
    </h3>
    
    <div style="
        color: #FFFFFF;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1rem 0;
        width: 100%;
        text-align: center;
    ">
        {package["credits"]} Credits
    </div>
    
    <div style="
        color: #FFFFFF;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 1rem 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        width: 100%;
        text-align: center;
    ">
        ${package["price_dollars"]:.2f}
    </div>
    
    <div style="
        color: #A0A0A0;
        font-size: 1rem;
        font-style: italic;
        margin: 0.5rem 0 1.5rem 0;
        width: 100%;
        text-align: center;
    ">
        ${package["per_credit_cost"]:.2f} per credit
    </div>
"""

# Add savings badge for Starter pack
if idx == 0 and len(packages) > 1:
    card_html += """
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
"""

# Add time savings and description
hours_saved = int(round(package['credits'] * 1.75))
description_text = package.get('description', f"Top up {package['credits']} credits")

card_html += f"""
    <div style="
        color: #FACC15;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 1rem 0;
        width: 100%;
        text-align: center;
    ">
        ⏱ Save ~{hours_saved} hours of work!
    </div>
    
    <div style="
        color: #D0D0D0;
        font-size: 1rem;
        line-height: 1.6;
        margin: 1.5rem 0;
        flex-grow: 1;
        width: 100%;
        text-align: center;
    ">
        {description_text}
    </div>
"""

# Close the card div
card_html += "</div>"

# Display the constructed HTML
st.markdown("## Constructed HTML:")
st.code(card_html, language="html")

st.markdown("## Rendered HTML:")
st.markdown(card_html, unsafe_allow_html=True)