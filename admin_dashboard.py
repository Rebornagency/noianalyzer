#!/usr/bin/env python3
"""
Simple Admin Dashboard for Credit System Support
Helps you manually fix customer credit issues
"""

import streamlit as st
import sqlite3
from datetime import datetime
import os

# Set page config
st.set_page_config(page_title="NOI Analyzer Admin", page_icon="🛠️", layout="wide")

def get_db_connection():
    """Get database connection"""
    db_path = os.getenv("DATABASE_PATH", "credits.db")
    if not os.path.exists(db_path):
        st.error(f"Database not found: {db_path}")
        return None
    return sqlite3.connect(db_path)

def load_users():
    """Load all users from database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        query = """
        SELECT email, credits, created_at
        FROM users 
        ORDER BY created_at DESC
        """
        cursor = conn.cursor()
        cursor.execute(query)
        users = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries for easier handling
        users_list = []
        for user in users:
            users_list.append({
                'email': user[0],
                'credits': user[1],
                'created_at': user[2]
            })
        return users_list
    except Exception as e:
        st.error(f"Error loading users: {e}")
        conn.close()
        return []

def load_transactions(email=None):
    """Load transactions from database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        if email:
            query = """
            SELECT id, email, package_type, credits, amount, status, created_at
            FROM transactions 
            WHERE email = ?
            ORDER BY created_at DESC
            """
            cursor.execute(query, (email,))
        else:
            query = """
            SELECT id, email, package_type, credits, amount, status, created_at
            FROM transactions 
            ORDER BY created_at DESC
            LIMIT 100
            """
            cursor.execute(query)
        
        transactions = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        transactions_list = []
        for transaction in transactions:
            transactions_list.append({
                'id': transaction[0],
                'email': transaction[1],
                'package_type': transaction[2],
                'credits': transaction[3],
                'amount': transaction[4],
                'status': transaction[5],
                'created_at': transaction[6]
            })
        return transactions_list
    except Exception as e:
        st.error(f"Error loading transactions: {e}")
        conn.close()
        return []

def add_credits_manual(email, amount, reason):
    """Manually add credits to user account"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if user exists, create if not
        cursor.execute("SELECT credits FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        if result:
            current_credits = result[0]
            new_credits = current_credits + amount
            # Update existing user
            cursor.execute("""
                UPDATE users 
                SET credits = ?
                WHERE email = ?
            """, (new_credits, email))
        else:
            # Create new user
            new_credits = max(0, amount)
            cursor.execute("""
                INSERT INTO users (email, credits) 
                VALUES (?, ?)
            """, (email, new_credits))
        
        # Add transaction record
        import uuid
        transaction_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO transactions 
            (id, email, package_type, credits, amount, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (transaction_id, email, f"admin_adjustment", amount, amount * 100, "completed"))
        
        conn.commit()
        return True
        
    except Exception as e:
        st.error(f"Error adding credits: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

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
        
        # Manual credit adjustment
        st.subheader("🔧 Manual Credit Adjustment")
        st.warning("⚠️ Use this carefully! Only for customer support issues.")
        
        # Allow manual email entry for new users
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Select Existing User:**")
            users_list = load_users()
            if users_list:
                user_emails = ["Select user..."] + [user['email'] for user in users_list]
                selected_existing = st.selectbox("Choose from existing users:", user_emails, key="existing_user")
            else:
                selected_existing = "Select user..."
                st.info("No existing users found")
        
        with col2:
            st.markdown("**Or Enter New User Email:**")
            manual_email = st.text_input("Email address:", key="manual_email")
        
        # Determine which email to use
        target_email = None
        if selected_existing != "Select user..." and selected_existing:
            target_email = selected_existing
        elif manual_email:
            target_email = manual_email
        
        if target_email:
            # Show current credits if user exists
            user_found = next((user for user in users_list if user['email'] == target_email), None)
            if user_found:
                current_credits = user_found['credits']
                st.info(f"**Current Credits for {target_email}:** {current_credits}")
            else:
                st.info(f"**New User:** {target_email} (will be created with credits)")
            
            # Credit adjustment form
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Credits to add/remove:", value=0, step=1, min_value=-1000, max_value=1000)
            with col2:
                reason = st.text_input("Reason for adjustment:", placeholder="e.g., Customer support refund")
            
            if st.button("💳 Apply Credit Adjustment", type="primary"):
                if reason.strip():
                    if add_credits_manual(target_email, amount, reason):
                        st.success(f"✅ Successfully {'added' if amount > 0 else 'removed'} {abs(amount)} credits {'to' if amount > 0 else 'from'} {target_email}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to adjust credits")
                else:
                    st.error("Please provide a reason for the adjustment")
        else:
            st.info("👆 Select a user or enter an email address to manage credits")
        
        # System health check
        st.subheader("🏥 System Health")
        if st.button("Run Health Check"):
            conn = get_db_connection()
            if conn:
                st.success("✅ Database connection working")
                
                # Check database tables
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM transactions")
                    transaction_count = cursor.fetchone()[0]
                    
                    st.info(f"📊 Database contains {user_count} users and {transaction_count} transactions")
                    
                    # Check for users with negative credits (shouldn't happen)
                    cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
                    negative_credits = cursor.fetchone()[0]
                    
                    if negative_credits > 0:
                        st.warning(f"⚠️ {negative_credits} users have negative credits")
                    else:
                        st.success("✅ No users with negative credits")
                        
                except Exception as e:
                    st.error(f"❌ Database query failed: {e}")
                
                conn.close()
            else:
                st.error("❌ Database connection failed")

if __name__ == "__main__":
    main()