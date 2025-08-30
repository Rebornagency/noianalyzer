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
    db_path = os.getenv("DATABASE_PATH", "credits.db")
    if not os.path.exists(db_path):
        st.error(f"Database not found: {db_path}")
        return None
    return sqlite3.connect(db_path)

def load_users():
    """Load all users from database"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT email, credits, created_at
        FROM users 
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading users: {e}")
        conn.close()
        return pd.DataFrame()

def load_transactions(email=None):
    """Load transactions from database"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        if email:
            query = """
            SELECT id, email, package_type, credits, amount, status, created_at
            FROM transactions 
            WHERE email = ?
            ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(email,))
        else:
            query = """
            SELECT id, email, package_type, credits, amount, status, created_at
            FROM transactions 
            ORDER BY created_at DESC
            LIMIT 100
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading transactions: {e}")
        conn.close()
        return pd.DataFrame()

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
        users_df = load_users()
        if users_df.empty:
            st.warning("No users found in database")
            st.info("Users will appear here after they use the credit system for the first time.")
        else:
            st.dataframe(users_df, use_container_width=True)
            
            # User stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", len(users_df))
            with col2:
                st.metric("Total Credits Outstanding", users_df['credits'].sum())
            with col3:
                total_transactions = len(load_transactions())
                st.metric("Total Transactions", total_transactions)
    
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
                transactions_df = load_transactions(selected_user)
            
            if transactions_df.empty:
                st.warning("No transactions found")
            else:
                # Format the dataframe for better display
                if not transactions_df.empty:
                    # Convert amount from cents to dollars if it's a large number
                    if 'amount' in transactions_df.columns:
                        transactions_df['amount_display'] = transactions_df['amount'].apply(
                            lambda x: f"${x/100:.2f}" if x > 100 else f"${x:.2f}"
                        )
                st.dataframe(transactions_df, use_container_width=True)
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
            users_df = load_users()
            if not users_df.empty:
                user_emails = ["Select user..."] + list(users_df['email'].values)
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
            if not users_df.empty and target_email in users_df['email'].values:
                current_credits = users_df[users_df['email'] == target_email]['credits'].iloc[0]
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