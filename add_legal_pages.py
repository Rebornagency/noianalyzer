#!/usr/bin/env python3
"""
Add Legal Pages to Streamlit App
This script adds Terms of Service and Privacy Policy pages to your app
"""

import streamlit as st
import os
from datetime import datetime

def display_terms_of_service():
    """Display Terms of Service page"""
    st.set_page_config(page_title="Terms of Service - NOI Analyzer", layout="wide")
    
    st.title("📄 Terms of Service")
    st.markdown("*Effective Date: " + datetime.now().strftime("%B %d, %Y") + "*")
    st.markdown("*Last Updated: " + datetime.now().strftime("%B %d, %Y") + "*")
    
    # Privacy guarantee callout
    st.success("🔒 **PRIVACY GUARANTEE**: We do NOT store your documents. All files are processed immediately and permanently deleted after analysis.")
    
    with st.expander("📋 Quick Summary", expanded=True):
        st.markdown("""
        - 🔒 **Your documents are NEVER stored** - complete privacy guaranteed
        - 💳 **Fair credit system** with free trial for new users
        - 📊 **Professional analysis** for real estate investment decisions
        - 🛡️ **Secure payments** through industry-standard processors
        - 📞 **Support available** for any questions or concerns
        """)
    
    # Full terms content
    if os.path.exists("TERMS_OF_SERVICE.md"):
        with open("TERMS_OF_SERVICE.md", "r", encoding="utf-8") as f:
            terms_content = f.read()
            # Remove the first line (title) since we already have it
            terms_content = "\n".join(terms_content.split("\n")[1:])
            st.markdown(terms_content)
    else:
        st.error("Terms of Service file not found. Please create TERMS_OF_SERVICE.md")
    
    # Back to app button
    if st.button("🏠 Back to NOI Analyzer", type="primary"):
        st.switch_page("app.py")

def display_privacy_policy():
    """Display Privacy Policy page"""
    st.set_page_config(page_title="Privacy Policy - NOI Analyzer", layout="wide")
    
    st.title("🔒 Privacy Policy")
    st.markdown("*Effective Date: " + datetime.now().strftime("%B %d, %Y") + "*")
    st.markdown("*Last Updated: " + datetime.now().strftime("%B %d, %Y") + "*")
    
    # Privacy guarantee callout
    st.success("🔒 **ZERO DOCUMENT STORAGE**: Your uploaded documents are NEVER stored on our servers. Processing happens in memory only and files are immediately deleted after analysis.")
    
    with st.expander("🛡️ Privacy Summary", expanded=True):
        st.markdown("""
        **🔒 Complete Document Privacy:**
        - Your uploaded documents are NEVER stored
        - Processing happens in memory only
        - Automatic deletion after analysis
        - No backups or copies made

        **📧 Minimal Data Collection:**
        - Only email address for account management
        - Credit balance and transaction history
        - No personal or financial details stored

        **🛡️ Maximum Security:**
        - HTTPS encryption for all communications
        - Secure payment processing through Stripe
        - Regular security audits and updates
        """)
    
    # Full privacy policy content
    if os.path.exists("PRIVACY_POLICY.md"):
        with open("PRIVACY_POLICY.md", "r", encoding="utf-8") as f:
            privacy_content = f.read()
            # Remove the first line (title) since we already have it
            privacy_content = "\n".join(privacy_content.split("\n")[1:])
            st.markdown(privacy_content)
    else:
        st.error("Privacy Policy file not found. Please create PRIVACY_POLICY.md")
    
    # Back to app button
    if st.button("🏠 Back to NOI Analyzer", type="primary"):
        st.switch_page("app.py")

def add_legal_links_to_footer():
    """Add legal links to the main app footer"""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📄 Terms of Service"):
            st.switch_page("pages/terms.py")
    
    with col2:
        if st.button("🔒 Privacy Policy"):
            st.switch_page("pages/privacy.py")
    
    with col3:
        st.markdown("*Your documents are never stored - complete privacy guaranteed*")

def create_legal_pages():
    """Create the legal page files for Streamlit"""
    
    # Create pages directory if it doesn't exist
    os.makedirs("pages", exist_ok=True)
    
    # Create terms page
    terms_page_content = '''
import streamlit as st
from add_legal_pages import display_terms_of_service

if __name__ == "__main__":
    display_terms_of_service()
'''
    
    with open("pages/terms.py", "w", encoding="utf-8") as f:
        f.write(terms_page_content.strip())
    
    # Create privacy page
    privacy_page_content = '''
import streamlit as st
from add_legal_pages import display_privacy_policy

if __name__ == "__main__":
    display_privacy_policy()
'''
    
    with open("pages/privacy.py", "w", encoding="utf-8") as f:
        f.write(privacy_page_content.strip())
    
    print("✅ Legal pages created successfully!")
    print("📁 Created: pages/terms.py")
    print("📁 Created: pages/privacy.py")
    print("\n📋 Next steps:")
    print("1. Add legal links to your main app.py footer")
    print("2. Update contact information in legal documents")
    print("3. Review and customize legal content as needed")

if __name__ == "__main__":
    create_legal_pages() 