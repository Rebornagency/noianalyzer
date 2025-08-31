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

# Optional plotly import for visualizations
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Set page config
st.set_page_config(page_title="NOI Analyzer Admin", page_icon="🛠️", layout="wide")

# Credit API URL
CREDIT_API_URL = os.getenv("CREDIT_API_URL", "https://noianalyzer-1.onrender.com")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "test_admin_key_change_me")

def api_request(endpoint, method="GET", data=None, params=None):
    """Make API request to credit service"""
    try:
        url = f"{CREDIT_API_URL}{endpoint}"
        
        # Add admin key to params for GET requests
        if method == "GET" and "admin" in endpoint:
            if params is None:
                params = {}
            params["admin_key"] = ADMIN_API_KEY
        
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            # Add admin key to form data for POST requests
            if "admin" in endpoint and data:
                data["admin_key"] = ADMIN_API_KEY
            response = requests.post(url, data=data, timeout=10)
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
    result = api_request("/pay-per-use/admin/users")
    if result and 'users' in result:
        return result['users']
    return []

def get_user_credits(email):
    """Get credits for a specific user"""
    if not email:
        return None
        
    result = api_request(f"/credits?email={email}")
    if result:
        return result.get('credits', 0)
    return None

def get_user_details(email):
    """Get detailed user information"""
    if not email:
        return None
        
    result = api_request(f"/pay-per-use/admin/user/{email}")
    return result

def load_transactions(email=None):
    """Load transactions from credit API"""
    if email:
        # Get transactions for specific user
        user_details = get_user_details(email)
        if user_details and 'transactions' in user_details:
            # Format for display
            transactions = []
            for tx in user_details['transactions']:
                transactions.append({
                    'email': email,
                    'credits': tx['amount'],
                    'amount': 0,  # We don't store dollar amounts in transactions
                    'created_at': tx['created_at'],
                    'type': tx['type'],
                    'description': tx['description']
                })
            return transactions
        return []
    else:
        # Get all transactions
        result = api_request("/pay-per-use/admin/transactions")
        if result and 'transactions' in result:
            # Format for display
            transactions = []
            for tx in result['transactions']:
                transactions.append({
                    'email': tx['email'],
                    'credits': tx['amount'],
                    'amount': 0,  # We don't store dollar amounts in transactions
                    'created_at': tx['created_at'],
                    'type': tx['type'],
                    'description': tx['description']
                })
            return transactions
        return []

def add_credits_manual(email, amount, reason):
    """Manually add credits to user account"""
    if not email or not reason.strip():
        return False, "Email and reason are required"
    
    if amount == 0:
        return False, "Credit change cannot be zero"
    
    data = {
        'email': email,
        'credit_change': amount,
        'reason': reason
    }
    
    result = api_request("/pay-per-use/admin/adjust-credits", method="POST", data=data)
    
    if result and result.get('success'):
        return True, result.get('message', 'Credits adjusted successfully')
    else:
        return False, "Failed to adjust credits"

def get_system_stats():
    """Get system statistics"""
    result = api_request("/pay-per-use/admin/stats")
    if result and 'stats' in result:
        return result['stats']
    return {}

def update_user_status(email, status):
    """Update user status"""
    data = {
        'email': email,
        'status': status
    }
    
    result = api_request("/pay-per-use/admin/user-status", method="POST", data=data)
    
    if result and result.get('success'):
        return True, result.get('message', 'Status updated successfully')
    else:
        return False, "Failed to update status"

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
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "💳 Transactions", "🛠️ Support Tools", "📊 System Stats"])
    
    with tab1:
        st.header("User Management")
        
        # System stats overview
        stats = get_system_stats()
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", stats.get('total_users', 0))
            with col2:
                st.metric("Outstanding Credits", stats.get('total_outstanding_credits', 0))
            with col3:
                st.metric("Credits Purchased", stats.get('total_credits_purchased', 0))
            with col4:
                st.metric("Credits Used", stats.get('total_credits_used', 0))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("New Users (7 days)", stats.get('new_users_last_7_days', 0))
            with col2:
                st.metric("Purchases (30 days)", stats.get('purchases_last_30_days', 0))
            
            st.divider()
        
        # Load and display users
        users_list = load_users()
        if not users_list:
            st.warning("No users found in database")
            st.info("Users will appear here after they use the credit system for the first time.")
        else:
            # Search and filter
            st.subheader("👥 All Users")
            
            # Search functionality
            search_term = st.text_input("🔍 Search users by email:", placeholder="Enter email to search...")
            
            # Filter users based on search
            if search_term:
                filtered_users = [user for user in users_list if search_term.lower() in user['email'].lower()]
            else:
                filtered_users = users_list
            
            st.write(f"**Showing {len(filtered_users)} of {len(users_list)} users**")
            
            # Display users in a table format
            for user in filtered_users:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 2])
                    
                    with col1:
                        st.write(f"📧 **{user['email']}**")
                        st.caption(f"ID: {user['user_id'][:8]}...")
                    
                    with col2:
                        st.metric("Credits", user['credits'])
                    
                    with col3:
                        st.write(f"📈 {user['total_credits_purchased']}")
                        st.caption("Purchased")
                    
                    with col4:
                        st.write(f"📉 {user['total_credits_used']}")
                        st.caption("Used")
                    
                    with col5:
                        status = user['status']
                        if status == 'active':
                            st.success(f"✅ {status.title()}")
                        elif status == 'suspended':
                            st.warning(f"⚠️ {status.title()}")
                        else:
                            st.error(f"🚫 {status.title()}")
                        
                        st.caption(f"Created: {user['created_at'][:10]}")
                    
                    # Quick actions
                    with st.expander(f"Quick Actions for {user['email']}"):
                        action_col1, action_col2 = st.columns(2)
                        
                        with action_col1:
                            # Quick credit adjustment
                            quick_credits = st.number_input(f"Credits to add/remove:", value=0, step=1, key=f"quick_{user['user_id']}")
                            quick_reason = st.text_input(f"Reason:", placeholder="e.g., Customer support issue", key=f"reason_{user['user_id']}")
                            
                            if st.button(f"Adjust Credits", key=f"adjust_{user['user_id']}"):
                                if quick_credits != 0 and quick_reason.strip():
                                    success, message = add_credits_manual(user['email'], quick_credits, quick_reason)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                                else:
                                    st.error("Please enter both credit amount and reason")
                        
                        with action_col2:
                            # Status management
                            new_status = st.selectbox(
                                f"Change Status:",
                                ["active", "suspended", "banned"],
                                index=["active", "suspended", "banned"].index(user['status']),
                                key=f"status_{user['user_id']}"
                            )
                            
                            if st.button(f"Update Status", key=f"update_status_{user['user_id']}"):
                                if new_status != user['status']:
                                    success, message = update_user_status(user['email'], new_status)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                                else:
                                    st.info("Status unchanged")
                    
                    st.divider()
    
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
                st.write(f"**Showing {len(transactions_list)} transactions**")
                
                # Display transactions in a detailed format
                for transaction in transactions_list:
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 2])
                        
                        with col1:
                            st.write(f"📧 **{transaction['email']}**")
                        
                        with col2:
                            amount = transaction['credits']
                            if amount > 0:
                                st.success(f"+{amount}")
                            else:
                                st.error(f"{amount}")
                            st.caption("Credits")
                        
                        with col3:
                            tx_type = transaction.get('type', 'unknown')
                            type_emoji = {
                                'purchase': '📋',
                                'usage': '📉',
                                'bonus': '🎁',
                                'refund': '🔄'
                            }.get(tx_type, '🔍')
                            st.write(f"{type_emoji} {tx_type.title()}")
                        
                        with col4:
                            st.write(f"📅 {transaction['created_at'][:16]}")
                        
                        with col5:
                            description = transaction.get('description', 'No description')
                            st.caption(description)
                        
                        st.divider()
        else:
            st.info("No users found. Transactions will appear after users start using the system.")
    
    with tab3:
        st.header("Support Tools")
        
        # Enhanced user lookup
        st.subheader("🔍 Enhanced User Lookup")
        st.info("📱 **Get detailed user information and transaction history**")
        
        lookup_email = st.text_input("Enter user email to get detailed info:", key="lookup_email")
        
        if st.button("🔍 Get User Details", type="primary"):
            if lookup_email:
                with st.spinner("Fetching user details..."):
                    user_details = get_user_details(lookup_email)
                    if user_details:
                        user = user_details['user']
                        transactions = user_details['transactions']
                        
                        # Display user info
                        st.success(f"✅ **User Found: {user['email']}**")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Current Credits", user['credits'])
                        with col2:
                            st.metric("Total Purchased", user['total_credits_purchased'])
                        with col3:
                            st.metric("Total Used", user['total_credits_used'])
                        with col4:
                            status = user['status']
                            if status == 'active':
                                st.success(f"✅ {status.title()}")
                            elif status == 'suspended':
                                st.warning(f"⚠️ {status.title()}")
                            else:
                                st.error(f"🚫 {status.title()}")
                        
                        # User metadata
                        st.write(f"**User ID:** {user['user_id']}")
                        st.write(f"**Created:** {user['created_at']}")
                        st.write(f"**Last Active:** {user['last_active'] or 'Never'}")
                        st.write(f"**Free Trial Used:** {'Yes' if user['free_trial_used'] else 'No'}")
                        
                        # Transaction history
                        if transactions:
                            st.subheader(f"📄 Recent Transactions ({len(transactions)})")
                            for tx in transactions[:10]:  # Show last 10
                                col1, col2, col3 = st.columns([2, 1, 2])
                                with col1:
                                    tx_type = tx['type']
                                    type_emoji = {
                                        'purchase': '📋',
                                        'usage': '📉',
                                        'bonus': '🎁',
                                        'refund': '🔄'
                                    }.get(tx_type, '🔍')
                                    st.write(f"{type_emoji} {tx_type.title()}")
                                
                                with col2:
                                    amount = tx['amount']
                                    if amount > 0:
                                        st.success(f"+{amount}")
                                    else:
                                        st.error(f"{amount}")
                                
                                with col3:
                                    st.caption(tx['description'])
                                    st.caption(tx['created_at'][:16])
                        else:
                            st.info("No transactions found for this user")
                    else:
                        st.warning(f"⚠️ Could not find user: **{lookup_email}**")
            else:
                st.error("Please enter an email address")
        
        st.divider()
        
        # Manual credit adjustment - NOW ENABLED!
        st.subheader("🔧 Manual Credit Adjustment")
        st.success("✅ **Manual credit adjustments are now ENABLED with secure API endpoints!**")
        
        adjustment_col1, adjustment_col2 = st.columns(2)
        
        with adjustment_col1:
            adjust_email = st.text_input("User email for credit adjustment:", key="adjust_email")
            credit_amount = st.number_input("Credits to add/remove:", value=0, step=1, help="Use positive numbers to add credits, negative to remove")
        
        with adjustment_col2:
            adjustment_reason = st.text_area("Reason for adjustment:", placeholder="e.g., Customer support compensation, Refund for service issue, Account correction", key="adjust_reason")
        
        if st.button("🔧 Apply Credit Adjustment", type="primary"):
            if adjust_email and adjustment_reason.strip() and credit_amount != 0:
                with st.spinner("Applying credit adjustment..."):
                    success, message = add_credits_manual(adjust_email, credit_amount, adjustment_reason)
                    if success:
                        st.success(f"✅ {message}")
                        # Show updated balance
                        updated_credits = get_user_credits(adjust_email)
                        if updated_credits is not None:
                            st.info(f"💳 **{adjust_email}** now has **{updated_credits} credits**")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.error("Please fill in all fields with valid values")
        
        st.divider()
        
        # System health check
        st.subheader("🏥 System Health Check")
        
        health_col1, health_col2 = st.columns(2)
        
        with health_col1:
            if st.button("🔍 Test Credit API Connection"):
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
        
        with health_col2:
            if st.button("📊 Test Admin Endpoints"):
                with st.spinner("Testing admin endpoints..."):
                    # Test admin endpoints
                    stats_result = get_system_stats()
                    if stats_result:
                        st.success("✅ **Admin endpoints working!**")
                        st.json(stats_result)
                    else:
                        st.error("❌ **Admin endpoints failed**\n\n"
                               "Check your ADMIN_API_KEY configuration.")
    
    with tab4:
        st.header("System Statistics & Monitoring")
        
        # Auto-refresh option
        auto_refresh = st.checkbox("Auto-refresh stats (every 30 seconds)", value=False)
        
        if auto_refresh:
            import time
            time.sleep(30)
            st.rerun()
        
        # Manual refresh
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Refresh Stats"):
                st.rerun()
        
        with col2:
            st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Get system stats
        stats = get_system_stats()
        
        if stats:
            # Main metrics
            st.subheader("📈 Key Metrics")
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric(
                    "👥 Total Users",
                    stats.get('total_users', 0),
                    help="Total number of registered users"
                )
            
            with metric_col2:
                st.metric(
                    "💳 Outstanding Credits",
                    stats.get('total_outstanding_credits', 0),
                    help="Credits currently in user accounts"
                )
            
            with metric_col3:
                st.metric(
                    "📋 Total Purchased",
                    stats.get('total_credits_purchased', 0),
                    help="All credits ever purchased"
                )
            
            with metric_col4:
                st.metric(
                    "📉 Total Used",
                    stats.get('total_credits_used', 0),
                    help="All credits ever consumed"
                )
            
            # Activity metrics
            st.subheader("📆 Recent Activity")
            
            activity_col1, activity_col2, activity_col3 = st.columns(3)
            
            with activity_col1:
                st.metric(
                    "🆕 New Users (7 days)",
                    stats.get('new_users_last_7_days', 0),
                    help="New user registrations in the last 7 days"
                )
            
            with activity_col2:
                st.metric(
                    "📋 Purchases (30 days)",
                    stats.get('purchases_last_30_days', 0),
                    help="Credit purchases in the last 30 days"
                )
            
            with activity_col3:
                st.metric(
                    "📄 Total Transactions",
                    stats.get('total_transactions', 0),
                    help="All transaction records"
                )
            
            # Credit efficiency analysis
            st.subheader("📀 Credit Analysis")
            
            purchased = stats.get('total_credits_purchased', 0)
            used = stats.get('total_credits_used', 0)
            outstanding = stats.get('total_outstanding_credits', 0)
            
            if purchased > 0:
                usage_rate = (used / purchased) * 100
                st.metric(
                    "📊 Usage Rate",
                    f"{usage_rate:.1f}%",
                    help="Percentage of purchased credits that have been used"
                )
                
                # Credit flow analysis
                analysis_col1, analysis_col2 = st.columns(2)
                
                with analysis_col1:
                    st.write("**Credit Flow:**")
                    st.write(f"➡️ Credits Purchased: {purchased:,}")
                    st.write(f"⬅️ Credits Used: {used:,}")
                    st.write(f"📦 Credits Outstanding: {outstanding:,}")
                    
                    # Validation check
                    calculated_outstanding = purchased - used
                    if abs(calculated_outstanding - outstanding) > 1:
                        st.warning(f"⚠️ Data inconsistency detected: {calculated_outstanding} vs {outstanding}")
                    else:
                        st.success("✅ Credit accounting is consistent")
                
                with analysis_col2:
                    # Visual representation
                    if PLOTLY_AVAILABLE:
                        fig = go.Figure(data=[
                            go.Bar(name='Used', x=['Credits'], y=[used]),
                            go.Bar(name='Outstanding', x=['Credits'], y=[outstanding])
                        ])
                        
                        fig.update_layout(
                            title='Credit Distribution',
                            barmode='stack',
                            height=300
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.write("**Credit Distribution:**")
                        st.progress(used / (used + outstanding) if (used + outstanding) > 0 else 0)
                        st.caption(f"Used: {used:,} credits")
                        st.progress(outstanding / (used + outstanding) if (used + outstanding) > 0 else 0)
                        st.caption(f"Outstanding: {outstanding:,} credits")
            
            # System health indicators
            st.subheader("🟢 System Health")
            
            health_col1, health_col2 = st.columns(2)
            
            with health_col1:
                # Database connectivity
                if stats:
                    st.success("🟢 Database: Connected")
                else:
                    st.error("🔴 Database: Connection Failed")
                
                # Credit system status
                total_users = stats.get('total_users', 0)
                if total_users > 0:
                    st.success(f"🟢 Credit System: Active ({total_users} users)")
                else:
                    st.warning("🟡 Credit System: No users yet")
            
            with health_col2:
                # Recent activity check
                recent_users = stats.get('new_users_last_7_days', 0)
                recent_purchases = stats.get('purchases_last_30_days', 0)
                
                if recent_users > 0:
                    st.success(f"🟢 User Growth: {recent_users} new users")
                else:
                    st.warning("🟡 User Growth: No new users recently")
                
                if recent_purchases > 0:
                    st.success(f"🟢 Revenue: {recent_purchases} recent purchases")
                else:
                    st.info("🟠 Revenue: No recent purchases")
            
            # Raw data for debugging
            with st.expander("🛠️ Raw System Data (Debug)"):
                st.json(stats)
        
        else:
            st.error("❌ Unable to fetch system statistics")
            st.info("This could indicate:")
            st.write("- API connection issues")
            st.write("- Invalid admin API key")
            st.write("- Database connectivity problems")
            
            if st.button("Test Connection"):
                test_result = api_request("/health")
                if test_result:
                    st.success("Basic API connection works")
                else:
                    st.error("Basic API connection failed")

if __name__ == "__main__":
    main()