"""
Enhanced Database Service with PostgreSQL Support and Reliability Improvements
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
import sqlite3

# PostgreSQL support (fallback to SQLite if not available)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

from .models import User, CreditTransaction, CreditPackage, TransactionType, UserStatus

logger = logging.getLogger(__name__)

class EnhancedDatabaseService:
    """Enhanced database service with PostgreSQL support and reliability features"""
    
    def __init__(self):
        self.db_type = self._determine_db_type()
        self.conn_string = self._get_connection_string()
        self.init_database()
        logger.info(f"Database initialized: {self.db_type}")
    
    def _determine_db_type(self) -> str:
        """Determine which database to use"""
        if os.getenv("DATABASE_URL") and POSTGRESQL_AVAILABLE:
            return "postgresql"
        else:
            return "sqlite"
    
    def _get_connection_string(self) -> str:
        """Get appropriate connection string"""
        if self.db_type == "postgresql":
            return os.getenv("DATABASE_URL")
        else:
            return os.getenv("DATABASE_PATH", "noi_analyzer.db")
    
    def get_connection(self):
        """Get database connection"""
        if self.db_type == "postgresql":
            return psycopg2.connect(self.conn_string, cursor_factory=RealDictCursor)
        else:
            conn = sqlite3.connect(self.conn_string)
            conn.row_factory = sqlite3.Row
            return conn
    
    def init_database(self):
        """Initialize database with enhanced schema"""
        conn = self.get_connection()
        try:
            if self.db_type == "postgresql":
                self._init_postgresql_schema(conn)
            else:
                self._init_sqlite_schema(conn)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_postgresql_schema(self, conn):
        """Initialize PostgreSQL schema"""
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
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
            CREATE TABLE IF NOT EXISTS ip_trial_usage (
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
            CREATE TABLE IF NOT EXISTS credit_transactions (
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
            CREATE TABLE IF NOT EXISTS credit_packages (
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
        
        # Webhook processing log (NEW - for reliability)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_log (
                id SERIAL PRIMARY KEY,
                stripe_session_id VARCHAR(200) UNIQUE NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'processed',
                retry_count INTEGER DEFAULT 0,
                last_error TEXT
            )
        ''')
        
        # Credit audit log (NEW - for admin tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_audit (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(32) NOT NULL,
                action VARCHAR(50) NOT NULL,
                details JSONB,
                admin_user VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        self._create_postgresql_indexes(cursor)
    
    def _init_sqlite_schema(self, conn):
        """Initialize SQLite schema (fallback)"""
        cursor = conn.cursor()
        
        # Original SQLite schema (unchanged for compatibility)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                credits INTEGER DEFAULT 0,
                total_credits_purchased INTEGER DEFAULT 0,
                total_credits_used INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                free_trial_used BOOLEAN DEFAULT FALSE,
                ip_address TEXT,
                user_agent TEXT,
                device_fingerprint TEXT
            )
        ''')
        
        # Add other tables...
        # (Include all original SQLite table definitions)
    
    def _create_postgresql_indexes(self, cursor):
        """Create PostgreSQL indexes"""
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
            'CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON credit_transactions(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON credit_transactions(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_transactions_stripe_session ON credit_transactions(stripe_session_id)',
            'CREATE INDEX IF NOT EXISTS idx_webhook_log_session ON webhook_log(stripe_session_id)',
            'CREATE INDEX IF NOT EXISTS idx_audit_user_id ON credit_audit(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_audit_created_at ON credit_audit(created_at)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    # WEBHOOK RELIABILITY METHODS (NEW)
    
    def is_webhook_processed(self, stripe_session_id: str) -> bool:
        """Check if webhook has already been processed"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM webhook_log WHERE stripe_session_id = %s',
                (stripe_session_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Error checking webhook status: {e}")
            return False
        finally:
            conn.close()
    
    def mark_webhook_processed(self, stripe_session_id: str, status: str = 'processed'):
        """Mark webhook as processed"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO webhook_log (stripe_session_id, status)
                VALUES (%s, %s)
                ON CONFLICT (stripe_session_id) 
                DO UPDATE SET processed_at = CURRENT_TIMESTAMP, status = %s
            ''', (stripe_session_id, status, status))
            conn.commit()
            logger.info(f"Webhook marked as {status}: {stripe_session_id}")
        except Exception as e:
            logger.error(f"Error marking webhook processed: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def log_webhook_error(self, stripe_session_id: str, error: str, retry_count: int = 0):
        """Log webhook processing error"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO webhook_log (stripe_session_id, status, retry_count, last_error)
                VALUES (%s, 'failed', %s, %s)
                ON CONFLICT (stripe_session_id)
                DO UPDATE SET 
                    retry_count = %s,
                    last_error = %s,
                    status = 'failed'
            ''', (stripe_session_id, retry_count, error, retry_count, error))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging webhook error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ADMIN AUDIT METHODS (NEW)
    
    def log_admin_action(self, user_id: str, action: str, details: Dict[str, Any], admin_user: str = None):
        """Log administrative actions for audit"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO credit_audit (user_id, action, details, admin_user)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, action, json.dumps(details), admin_user))
            conn.commit()
            logger.info(f"Admin action logged: {action} for user {user_id}")
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_admin_audit_log(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get admin audit log"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT * FROM credit_audit 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM credit_audit 
                    ORDER BY created_at DESC 
                    LIMIT %s
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting audit log: {e}")
            return []
        finally:
            conn.close()
    
    # ENHANCED USER METHODS
    
    def manual_add_credits(self, user_id: str, amount: int, reason: str, admin_user: str = None) -> bool:
        """Manually add credits (admin function with audit)"""
        try:
            # Use existing update_user_credits method
            success = self.update_user_credits(
                user_id, amount, TransactionType.bonus, f"Manual addition: {reason}"
            )
            
            if success:
                # Log admin action
                self.log_admin_action(
                    user_id=user_id,
                    action="manual_credit_addition",
                    details={
                        "amount": amount,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    },
                    admin_user=admin_user
                )
                logger.info(f"Manual credits added: {amount} to user {user_id} by {admin_user}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error manually adding credits: {e}")
            return False
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get overall user statistics"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_users,
                    SUM(credits) as total_credits_available,
                    SUM(total_credits_purchased) as total_credits_purchased,
                    SUM(total_credits_used) as total_credits_used,
                    COUNT(CASE WHEN free_trial_used = true THEN 1 END) as trial_users,
                    COUNT(CASE WHEN total_credits_purchased > 0 THEN 1 END) as paying_users
                FROM users
            ''')
            
            stats = dict(cursor.fetchone())
            
            # Recent activity
            cursor.execute('''
                SELECT COUNT(*) as recent_transactions
                FROM credit_transactions 
                WHERE created_at > %s
            ''', (datetime.now() - timedelta(days=7),))
            
            stats['recent_weekly_transactions'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
        finally:
            conn.close()
    
    # Include all original methods from the original database service
    # (Copy them over with minimal changes)
    
    # ... (rest of the original methods)

# Create enhanced service instance
enhanced_db_service = EnhancedDatabaseService()