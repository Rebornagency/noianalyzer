#!/usr/bin/env python3
"""
Simple Admin Dashboard for Credit System Support
Helps you manually fix customer credit issues
"""

import streamlit as st
import requests
from datetime import datetime
import os
import json

# Set page config
st.set_page_config(page_title="NOI Analyzer Admin", page_icon="🛠️", layout="wide")

# Credit API URL
CREDIT_API_URL = os.getenv("CREDIT_API_URL", "https://noianalyzer-1.onrender.com")

def api_request(endpoint, method="GET", data=None):
    """Make API request to credit service"""
    try:
        url = f"{CREDIT_API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return None
            
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def load_users():
    """Load all users from credit API"""
    # For now, we'll show a message that this feature needs API enhancement
    st.info("📈 **User management via API coming soon!**\n\n"
           "Currently, you can check individual user credits using the Support Tools tab.\n\n"
           "To see all users, contact the system administrator.")
    return []

def get_user_credits(email):
    """Get credits for a specific user"""
    if not email:
        return None
        
    result = api_request(f"/credits?email={email}")
    if result:
        return result.get('credits', 0)
    return None

def load_transactions(email=None):
    """Load transactions - placeholder for now"""
    st.info("📄 **Transaction history via API coming soon!**\n\n"
           "Currently, transaction details are stored on the credit service.\n\n"
           "For transaction inquiries, contact the system administrator.")
    return []

def add_credits_manual(email, amount, reason):
    """Manually add credits - placeholder for now"""
    st.warning("🔧 **Manual credit adjustment is currently disabled**\n\n"
              "This feature requires additional API endpoints for security.\n\n"
              "For urgent credit adjustments, contact the system administrator directly.")
    return False

def main():
    """Main admin dashboard"""
    st.title("🛠️ NOI Analyzer Admin Dashboard")
    st.markdown("**Customer Support Tool for Credit System**")
    
    # Admin password protection
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.warning("🔐 Admin Access Required")
        password = st.text_input("Enter admin password:", type="password")
        if st.button("Login"):
            # Simple password check (in production, use proper authentication)
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            if password == admin_password:
                st.session_state.admin_authenticated = True
                st.success("✅ Access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid password")
        
        st.info("**Default password:** admin123 (change ADMIN_PASSWORD environment variable)")
        return
    
    # Main dashboard
    tab1, tab2, tab3 = st.tabs(["👥 Users", "💳 Transactions", "🛠️ Support Tools"])
    
    with tab1:
        st.header("User Management")
        
        # Load and display users
        users_list = load_users()
        if not users_list:
            st.warning("No users found in database")
            st.info("Users will appear here after they use the credit system for the first time.")
        else:
            # Create a simple table display
            st.write("**Users Overview:**")
            for user in users_list:
                with st.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"📧 {user['email']}")
                    with col2:
                        st.write(f"💳 {user['credits']} credits")
                    with col3:
                        st.write(f"📅 {user['created_at']}")
                    st.divider()
            
            # User stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", len(users_list))
            with col2:
                total_credits = sum(user['credits'] for user in users_list)
                st.metric("Total Credits Outstanding", total_credits)
            with col3:
                total_transactions = len(load_transactions())
                st.metric("Total Transactions", total_transactions)
    
    with tab2:
        st.header("Transaction History")
        
        # Filter by user
        users_list = load_users()
        if users_list:
            user_emails = ["All Users"] + [user['email'] for user in users_list]
            selected_user = st.selectbox("Filter by user:", user_emails)
            
            if selected_user == "All Users":
                transactions_list = load_transactions()
            else:
                transactions_list = load_transactions(selected_user)
            
            if not transactions_list:
                st.warning("No transactions found")
            else:
                # Display transactions in a simple format
                st.write("**Transaction History:**")
                for transaction in transactions_list:
                    with st.container():
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.write(f"📧 {transaction['email']}")
                        with col2:
                            st.write(f"💳 {transaction['credits']} credits")
                        with col3:
                            amount_display = f"${transaction['amount']/100:.2f}" if transaction['amount'] > 100 else f"${transaction['amount']:.2f}"
                            st.write(f"💰 {amount_display}")
                        with col4:
                            st.write(f"📅 {transaction['created_at']}")
                        st.divider()
        else:
            st.info("No users found. Transactions will appear after users start using the system.")
    
    with tab3:
        st.header("Support Tools")
        
        # Credit lookup tool
        st.subheader("🔍 Credit Lookup")
        st.info("📱 **Check individual user credits using the credit API**")
        
        lookup_email = st.text_input("Enter user email to check credits:", key="lookup_email")
        
        if st.button("🔍 Check Credits", type="primary"):
            if lookup_email:
                with st.spinner("Checking credits..."):
                    credits = get_user_credits(lookup_email)
                    if credits is not None:
                        st.success(f"✅ **{lookup_email}** has **{credits} credits**")
                    else:
                        st.warning(f"⚠️ Could not find credits for **{lookup_email}** or API error")
            else:
                st.error("Please enter an email address")
        
        st.divider()
        
        # Manual credit adjustment (disabled for security)
        st.subheader("🔧 Manual Credit Adjustment")
        st.warning("⚠️ **Currently disabled for security reasons**\n\n"
                  "Manual credit adjustments require secure API endpoints.\n\n"
                  "For urgent credit issues, contact the system administrator.")
        
        st.divider()
        
        # System health check
        st.subheader("🏥 System Health")
        if st.button("Test Credit API Connection"):
            with st.spinner("Testing API connection..."):
                # Test the health endpoint
                health_result = api_request("/health")
                if health_result:
                    st.success(f"✅ **Credit API is working!**\n\n"
                             f"**Status:** {health_result.get('status', 'Unknown')}\n\n"
                             f"**Message:** {health_result.get('message', 'No message')}")
                    
                    # Test packages endpoint
                    packages_result = api_request("/packages")
                    if packages_result:
                        st.info(f"📆 **Available credit packages:** {len(packages_result)}")
                    else:
                        st.warning("⚠️ Packages endpoint not responding")
                else:
                    st.error("❌ **Credit API connection failed**\n\n"
                           "Check if the credit service is running properly.")

if __name__ == "__main__":
    main()