#!/usr/bin/env python3
"""
Simple Admin Dashboard for Credit System Support
Helps you manually fix customer credit issues
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# Set page config
st.set_page_config(page_title="NOI Analyzer Admin", page_icon="🛠️", layout="wide")

def get_db_connection():
    """Get database connection"""
    db_path = os.getenv("DATABASE_PATH", "noi_analyzer.db")
    if not os.path.exists(db_path):
        st.error(f"Database not found: {db_path}")
        return None
    return sqlite3.connect(db_path)

def load_users():
    """Load all users from database"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
    SELECT user_id, email, credits, total_credits_purchased, total_credits_used, 
           free_trial_used, created_at, last_active
    FROM users 
    ORDER BY last_active DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def load_transactions(user_id=None):
    """Load transactions from database"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    if user_id:
        query = """
        SELECT transaction_id, user_id, type, amount, description, 
               stripe_session_id, created_at
        FROM credit_transactions 
        WHERE user_id = ?
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
    else:
        query = """
        SELECT transaction_id, user_id, type, amount, description, 
               stripe_session_id, created_at
        FROM credit_transactions 
        ORDER BY created_at DESC
        LIMIT 100
        """
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df

def add_credits_manual(user_id, amount, reason):
    """Manually add credits to user account"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get current user credits
        cursor.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if not result:
            return False
        
        new_credits = result[0] + amount
        
        # Update user credits
        cursor.execute("""
            UPDATE users 
            SET credits = ?, total_credits_purchased = total_credits_purchased + ?
            WHERE user_id = ?
        """, (new_credits, max(0, amount), user_id))
        
        # Add transaction record
        from uuid import uuid4
        transaction_id = uuid4().hex
        cursor.execute("""
            INSERT INTO credit_transactions 
            (transaction_id, user_id, type, amount, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (transaction_id, user_id, "bonus" if amount > 0 else "refund", 
              amount, f"Manual adjustment: {reason}", datetime.now()))
        
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
        users_df = load_users()
        if users_df.empty:
            st.warning("No users found in database")
        else:
            st.dataframe(users_df, use_container_width=True)
            
            # User stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", len(users_df))
            with col2:
                st.metric("Total Credits Outstanding", users_df['credits'].sum())
            with col3:
                st.metric("Total Credits Purchased", users_df['total_credits_purchased'].sum())
            with col4:
                st.metric("Total Credits Used", users_df['total_credits_used'].sum())
    
    with tab2:
        st.header("Transaction History")
        
        # Filter by user
        users_df = load_users()
        if not users_df.empty:
            user_options = ["All Users"] + list(users_df['email'].values)
            selected_user = st.selectbox("Filter by user:", user_options)
            
            if selected_user == "All Users":
                transactions_df = load_transactions()
            else:
                user_id = users_df[users_df['email'] == selected_user]['user_id'].iloc[0]
                transactions_df = load_transactions(user_id)
            
            if transactions_df.empty:
                st.warning("No transactions found")
            else:
                st.dataframe(transactions_df, use_container_width=True)
    
    with tab3:
        st.header("Support Tools")
        
        # Manual credit adjustment
        st.subheader("🔧 Manual Credit Adjustment")
        st.warning("⚠️ Use this carefully! Only for customer support issues.")
        
        users_df = load_users()
        if not users_df.empty:
            # User selection
            user_emails = list(users_df['email'].values)
            selected_email = st.selectbox("Select user:", user_emails, key="support_user")
            
            if selected_email:
                user_row = users_df[users_df['email'] == selected_email].iloc[0]
                st.info(f"**Current Credits:** {user_row['credits']}")
                
                # Credit adjustment form
                col1, col2 = st.columns(2)
                with col1:
                    amount = st.number_input("Credits to add/remove:", value=0, step=1)
                with col2:
                    reason = st.text_input("Reason for adjustment:", placeholder="e.g., Webhook failed, refund request")
                
                if st.button("Apply Credit Adjustment", type="primary"):
                    if reason.strip():
                        success = add_credits_manual(user_row['user_id'], amount, reason)
                        if success:
                            st.success(f"✅ Added {amount} credits to {selected_email}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to add credits")
                    else:
                        st.error("Please provide a reason for the adjustment")
        
        # System health check
        st.subheader("🏥 System Health")
        if st.button("Run Health Check"):
            conn = get_db_connection()
            if conn:
                st.success("✅ Database connection working")
                
                # Check for recent webhook failures (would need webhook log table)
                st.info("ℹ️ Webhook monitoring not implemented yet")
                
                # Check for users with suspicious activity
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE total_credits_purchased = 0 AND total_credits_used > 0
                """)
                suspicious_users = cursor.fetchone()[0]
                
                if suspicious_users > 0:
                    st.warning(f"⚠️ {suspicious_users} users have used credits without purchasing")
                else:
                    st.success("✅ No suspicious user activity detected")
                
                conn.close()
            else:
                st.error("❌ Database connection failed")

if __name__ == "__main__":
    main()