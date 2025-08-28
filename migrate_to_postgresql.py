#!/usr/bin/env python3
"""
NOI Analyzer - Database Migration Script
Safely migrate from SQLite to PostgreSQL with data preservation
"""

import os
import sys
import json
import sqlite3
import psycopg2
from datetime import datetime
from typing import Dict, List, Any

def backup_sqlite_data(sqlite_path: str) -> Dict[str, List[Dict]]:
    """Backup all data from SQLite database"""
    print(f"📥 Backing up data from {sqlite_path}")
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    
    backup_data = {}
    
    # Get all table names
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        print(f"  📋 Backing up table: {table}")
        cursor = conn.execute(f"SELECT * FROM {table}")
        rows = [dict(row) for row in cursor.fetchall()]
        backup_data[table] = rows
        print(f"     ✅ {len(rows)} records backed up")
    
    conn.close()
    
    # Save backup to file
    backup_file = f"noi_analyzer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)
    
    print(f"💾 Backup saved to: {backup_file}")
    return backup_data

def create_postgresql_schema(pg_conn):
    """Create PostgreSQL schema matching SQLite structure"""
    print("🏗️  Creating PostgreSQL schema")
    
    cursor = pg_conn.cursor()
    
    # Drop existing tables if they exist
    tables_to_drop = ['credit_transactions', 'credit_packages', 'ip_trial_usage', 'users']
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            user_id VARCHAR(32) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            credits INTEGER DEFAULT 0,
            total_credits_purchased INTEGER DEFAULT 0,
            total_credits_used INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            free_trial_used BOOLEAN DEFAULT FALSE,
            ip_address VARCHAR(45),
            user_agent TEXT,
            device_fingerprint VARCHAR(32)
        )
    ''')
    
    # IP tracking table
    cursor.execute('''
        CREATE TABLE ip_trial_usage (
            ip_address VARCHAR(45) PRIMARY KEY,
            trial_count INTEGER DEFAULT 0,
            first_trial_date TIMESTAMP,
            last_trial_date TIMESTAMP,
            blocked BOOLEAN DEFAULT FALSE,
            blocked_reason TEXT
        )
    ''')
    
    # Credit transactions table
    cursor.execute('''
        CREATE TABLE credit_transactions (
            transaction_id VARCHAR(32) PRIMARY KEY,
            user_id VARCHAR(32) NOT NULL,
            type VARCHAR(20) NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT NOT NULL,
            stripe_session_id VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Credit packages table
    cursor.execute('''
        CREATE TABLE credit_packages (
            package_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            credits INTEGER NOT NULL,
            price_cents INTEGER NOT NULL,
            stripe_price_id VARCHAR(100) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX idx_transactions_user_id ON credit_transactions(user_id)')
    cursor.execute('CREATE INDEX idx_transactions_created_at ON credit_transactions(created_at)')
    cursor.execute('CREATE INDEX idx_transactions_stripe_session ON credit_transactions(stripe_session_id)')
    
    # Add new reliability tables
    cursor.execute('''
        CREATE TABLE webhook_log (
            id SERIAL PRIMARY KEY,
            stripe_session_id VARCHAR(200) UNIQUE NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'processed',
            retry_count INTEGER DEFAULT 0,
            last_error TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE credit_audit (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(32) NOT NULL,
            action VARCHAR(50) NOT NULL,
            details JSONB,
            admin_user VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    pg_conn.commit()
    print("✅ PostgreSQL schema created successfully")

def migrate_data(backup_data: Dict[str, List[Dict]], pg_conn):
    """Migrate data from backup to PostgreSQL"""
    print("📤 Migrating data to PostgreSQL")
    
    cursor = pg_conn.cursor()
    
    # Migration order (respecting foreign keys)
    migration_order = ['users', 'ip_trial_usage', 'credit_packages', 'credit_transactions']
    
    for table in migration_order:
        if table in backup_data:
            rows = backup_data[table]
            print(f"  📋 Migrating {len(rows)} records to {table}")
            
            if rows:
                # Get column names from first row
                columns = list(rows[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                insert_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                
                # Convert data for PostgreSQL
                for row in rows:
                    values = []
                    for col in columns:
                        value = row[col]
                        # Convert boolean values
                        if isinstance(value, int) and col in ['free_trial_used', 'blocked', 'is_active']:
                            value = bool(value)
                        values.append(value)
                    
                    cursor.execute(insert_query, values)
                
                print(f"     ✅ {len(rows)} records migrated")
    
    pg_conn.commit()
    print("✅ Data migration completed successfully")

def verify_migration(backup_data: Dict[str, List[Dict]], pg_conn):
    """Verify migration integrity"""
    print("🔍 Verifying migration integrity")
    
    cursor = pg_conn.cursor()
    
    for table in backup_data.keys():
        # Count records in PostgreSQL
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = cursor.fetchone()[0]
        
        # Compare with backup
        sqlite_count = len(backup_data[table])
        
        if pg_count == sqlite_count:
            print(f"  ✅ {table}: {pg_count} records (matches backup)")
        else:
            print(f"  ❌ {table}: {pg_count} records (expected {sqlite_count})")
            return False
    
    # Verify critical data integrity
    cursor.execute("""
        SELECT 
            COUNT(*) as total_users,
            SUM(credits) as total_credits,
            SUM(total_credits_purchased) as total_purchased
        FROM users
    """)
    
    stats = cursor.fetchone()
    print(f"📊 Migration Summary:")
    print(f"   Total Users: {stats[0]}")
    print(f"   Total Credits: {stats[1]}")
    print(f"   Total Purchased: {stats[2]}")
    
    return True

def main():
    """Main migration function"""
    print("🚀 NOI Analyzer Database Migration")
    print("   SQLite → PostgreSQL")
    print("=" * 40)
    
    # Configuration
    SQLITE_PATH = os.getenv("DATABASE_PATH", "noi_analyzer.db")
    PG_HOST = os.getenv("PG_HOST", "localhost")
    PG_PORT = os.getenv("PG_PORT", "5432")
    PG_DB = os.getenv("PG_DATABASE", "noianalyzer")
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "")
    
    # Check if SQLite file exists
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ SQLite database not found: {SQLITE_PATH}")
        return False
    
    try:
        # 1. Backup SQLite data
        backup_data = backup_sqlite_data(SQLITE_PATH)
        
        # 2. Connect to PostgreSQL
        print(f"🔌 Connecting to PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DB}")
        pg_conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        
        # 3. Create schema
        create_postgresql_schema(pg_conn)
        
        # 4. Migrate data
        migrate_data(backup_data, pg_conn)
        
        # 5. Verify migration
        if verify_migration(backup_data, pg_conn):
            print("🎉 Migration completed successfully!")
            print("\n📝 Next steps:")
            print("   1. Update DATABASE_URL environment variable")
            print("   2. Update database.py to use PostgreSQL")
            print("   3. Test the application")
            print("   4. Keep SQLite backup for safety")
            return True
        else:
            print("❌ Migration verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)