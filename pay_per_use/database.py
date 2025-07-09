import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
import logging

from .models import User, CreditTransaction, CreditPackage, TransactionType, UserStatus

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "noi_analyzer.db")

class DatabaseService:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        try:
            # Users table
            conn.execute('''
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
            
            # IP tracking table for free trial abuse prevention
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ip_trial_usage (
                    ip_address TEXT PRIMARY KEY,
                    trial_count INTEGER DEFAULT 0,
                    first_trial_date TIMESTAMP,
                    last_trial_date TIMESTAMP,
                    blocked BOOLEAN DEFAULT FALSE,
                    blocked_reason TEXT
                )
            ''')
            
            # Credit transactions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS credit_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    stripe_session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Credit packages table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS credit_packages (
                    package_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    credits INTEGER NOT NULL,
                    price_cents INTEGER NOT NULL,
                    stripe_price_id TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON credit_transactions(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON credit_transactions(created_at)')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # USER MANAGEMENT
    def get_or_create_user(self, email: str, ip_address: str = None, user_agent: str = None) -> User:
        """Get existing user or create new one"""
        conn = self.get_connection()
        try:
            # Try to get existing user
            cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            
            if row:
                # Update last_active
                conn.execute('UPDATE users SET last_active = ? WHERE email = ?', 
                           (datetime.now(), email))
                conn.commit()
                
                return User(
                    user_id=row['user_id'],
                    email=row['email'],
                    credits=row['credits'],
                    total_credits_purchased=row['total_credits_purchased'],
                    total_credits_used=row['total_credits_used'],
                    status=UserStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_active=datetime.now(),
                    free_trial_used=bool(row['free_trial_used'])
                )
            else:
                # Check for IP abuse before creating new user
                free_trial_credits = 0
                free_trial_allowed = True
                
                if ip_address:
                    free_trial_allowed, reason = self._check_ip_trial_eligibility(ip_address)
                    if not free_trial_allowed:
                        logger.warning(f"Free trial denied for IP {ip_address}: {reason}")
                
                if free_trial_allowed:
                    free_trial_credits = int(os.getenv("FREE_TRIAL_CREDITS", "3"))
                    if ip_address:
                        self._record_ip_trial_usage(ip_address)
                
                # Create new user
                user_id = uuid4().hex
                device_fingerprint = self._generate_device_fingerprint(ip_address, user_agent)
                
                conn.execute('''
                    INSERT INTO users (user_id, email, credits, free_trial_used, created_at, last_active, ip_address, user_agent, device_fingerprint)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, email, free_trial_credits, free_trial_credits > 0, datetime.now(), datetime.now(), ip_address, user_agent, device_fingerprint))
                
                # Record free trial transaction if credits given
                if free_trial_credits > 0:
                    self._add_transaction_internal(conn, user_id, TransactionType.bonus, 
                                                 free_trial_credits, "Free trial credits")
                    logger.info(f"Created new user {email} with {free_trial_credits} free credits")
                else:
                    logger.info(f"Created new user {email} with no free credits (IP restriction)")
                
                conn.commit()
                
                return User(
                    user_id=user_id,
                    email=email,
                    credits=free_trial_credits,
                    total_credits_purchased=0,
                    total_credits_used=0,
                    status=UserStatus.active,
                    created_at=datetime.now(),
                    last_active=datetime.now(),
                    free_trial_used=free_trial_credits > 0
                )
                
        except Exception as e:
            logger.error(f"Error getting/creating user {email}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def update_user_credits(self, user_id: str, credits_change: int, transaction_type: TransactionType, description: str, stripe_session_id: Optional[str] = None) -> bool:
        """Update user credits and record transaction"""
        conn = self.get_connection()
        try:
            # Get current user
            cursor = conn.execute('SELECT credits, total_credits_purchased, total_credits_used FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"User {user_id} not found")
                return False
            
            new_credits = row['credits'] + credits_change
            if new_credits < 0:
                logger.error(f"Insufficient credits for user {user_id}")
                return False
            
            # Update user credits and totals
            total_purchased = row['total_credits_purchased']
            total_used = row['total_credits_used']
            
            if transaction_type in [TransactionType.purchase, TransactionType.bonus]:
                total_purchased += max(0, credits_change)
            elif transaction_type == TransactionType.usage:
                total_used += abs(credits_change)
            
            conn.execute('''
                UPDATE users 
                SET credits = ?, total_credits_purchased = ?, total_credits_used = ?, last_active = ?
                WHERE user_id = ?
            ''', (new_credits, total_purchased, total_used, datetime.now(), user_id))
            
            # Record transaction
            self._add_transaction_internal(conn, user_id, transaction_type, credits_change, description, stripe_session_id)
            
            conn.commit()
            logger.info(f"Updated credits for user {user_id}: {credits_change} ({transaction_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating credits for user {user_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def _add_transaction_internal(self, conn, user_id: str, transaction_type: TransactionType, amount: int, description: str, stripe_session_id: Optional[str] = None):
        """Internal method to add transaction (uses existing connection)"""
        transaction_id = uuid4().hex
        conn.execute('''
            INSERT INTO credit_transactions (transaction_id, user_id, type, amount, description, stripe_session_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (transaction_id, user_id, transaction_type.value, amount, description, stripe_session_id, datetime.now()))
    
    def get_user_transactions(self, user_id: str, limit: int = 50) -> List[CreditTransaction]:
        """Get user's transaction history"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM credit_transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append(CreditTransaction(
                    transaction_id=row['transaction_id'],
                    user_id=row['user_id'],
                    type=TransactionType(row['type']),
                    amount=row['amount'],
                    description=row['description'],
                    stripe_session_id=row['stripe_session_id'],
                    created_at=datetime.fromisoformat(row['created_at'])
                ))
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transactions for user {user_id}: {e}")
            return []
        finally:
            conn.close()
    
    # CREDIT PACKAGES
    def create_default_packages(self):
        """Create default credit packages with placeholder Stripe IDs"""
        # IMPORTANT: You need to replace these placeholder price IDs with real ones from Stripe!
        default_packages = [
            {
                "package_id": "starter-3",
                "name": "Starter Pack",
                "credits": 3,
                "price_cents": 1500,  # $15.00
                "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "PLACEHOLDER_STARTER_PRICE_ID"),
                "description": "Perfect for trying out our service"
            },
            {
                "package_id": "professional-10",
                "name": "Professional Pack",
                "credits": 10,
                "price_cents": 3000,  # $30.00
                "stripe_price_id": os.getenv("STRIPE_PROFESSIONAL_PRICE_ID", "PLACEHOLDER_PROFESSIONAL_PRICE_ID"),
                "description": "Great for regular users"
            },
            {
                "package_id": "business-40",
                "name": "Business Pack",
                "credits": 40,
                "price_cents": 7500,  # $75.00
                "stripe_price_id": os.getenv("STRIPE_BUSINESS_PRICE_ID", "PLACEHOLDER_BUSINESS_PRICE_ID"),
                "description": "Best value for power users"
            }
        ]
        
        conn = self.get_connection()
        try:
            for package in default_packages:
                # Check if package already exists
                cursor = conn.execute('SELECT package_id FROM credit_packages WHERE package_id = ?', (package['package_id'],))
                if not cursor.fetchone():
                    conn.execute('''
                        INSERT INTO credit_packages (package_id, name, credits, price_cents, stripe_price_id, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        package['package_id'],
                        package['name'],
                        package['credits'],
                        package['price_cents'],
                        package['stripe_price_id'],
                        package['description']
                    ))
                else:
                    # Update existing package with new Stripe price ID
                    conn.execute('''
                        UPDATE credit_packages 
                        SET stripe_price_id = ?
                        WHERE package_id = ?
                    ''', (package['stripe_price_id'], package['package_id']))
            
            conn.commit()
            logger.info("Default credit packages created/updated")
            
            # Check for placeholder IDs and warn
            cursor = conn.execute('SELECT name, stripe_price_id FROM credit_packages WHERE stripe_price_id LIKE "PLACEHOLDER%"')
            placeholders = cursor.fetchall()
            if placeholders:
                logger.warning("⚠️  IMPORTANT: Some packages still have placeholder Stripe price IDs:")
                for row in placeholders:
                    logger.warning(f"   - {row['name']}: {row['stripe_price_id']}")
                logger.warning("   Update your .env file with real Stripe price IDs!")
            
        except Exception as e:
            logger.error(f"Error creating default packages: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def update_stripe_price_ids(self, price_id_mapping: dict):
        """Update Stripe price IDs for existing packages"""
        conn = self.get_connection()
        try:
            for package_id, stripe_price_id in price_id_mapping.items():
                conn.execute('''
                    UPDATE credit_packages 
                    SET stripe_price_id = ?
                    WHERE package_id = ?
                ''', (stripe_price_id, package_id))
            
            conn.commit()
            logger.info(f"Updated Stripe price IDs for {len(price_id_mapping)} packages")
            
        except Exception as e:
            logger.error(f"Error updating Stripe price IDs: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_active_packages(self) -> List[CreditPackage]:
        """Get all active credit packages"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM credit_packages WHERE is_active = TRUE ORDER BY credits ASC')
            packages = []
            
            for row in cursor.fetchall():
                packages.append(CreditPackage(
                    package_id=row['package_id'],
                    name=row['name'],
                    credits=row['credits'],
                    price_cents=row['price_cents'],
                    stripe_price_id=row['stripe_price_id'],
                    description=row['description'],
                    is_active=bool(row['is_active'])
                ))
            
            return packages
            
        except Exception as e:
            logger.error(f"Error getting active packages: {e}")
            return []
        finally:
            conn.close()
    
    def get_package_by_id(self, package_id: str) -> Optional[CreditPackage]:
        """Get specific package by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM credit_packages WHERE package_id = ?', (package_id,))
            row = cursor.fetchone()
            
            if row:
                return CreditPackage(
                    package_id=row['package_id'],
                    name=row['name'],
                    credits=row['credits'],
                    price_cents=row['price_cents'],
                    stripe_price_id=row['stripe_price_id'],
                    description=row['description'],
                    is_active=bool(row['is_active'])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting package {package_id}: {e}")
            return None
        finally:
            conn.close()
    
    # ABUSE PREVENTION METHODS
    def _check_ip_trial_eligibility(self, ip_address: str) -> tuple[bool, str]:
        """Check if IP address is eligible for free trial"""
        max_trials_per_ip = int(os.getenv("MAX_TRIALS_PER_IP", "2"))  # Allow 2 trials per IP
        trial_cooldown_days = int(os.getenv("TRIAL_COOLDOWN_DAYS", "7"))  # 7 day cooldown
        
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM ip_trial_usage WHERE ip_address = ?', (ip_address,))
            row = cursor.fetchone()
            
            if not row:
                return True, "First trial from this IP"
            
            if row['blocked']:
                return False, f"IP blocked: {row['blocked_reason']}"
            
            if row['trial_count'] >= max_trials_per_ip:
                # Check if enough time has passed
                last_trial = datetime.fromisoformat(row['last_trial_date'])
                days_since_last = (datetime.now() - last_trial).days
                
                if days_since_last < trial_cooldown_days:
                    return False, f"Maximum {max_trials_per_ip} trials reached. Try again in {trial_cooldown_days - days_since_last} days"
                else:
                    # Reset counter after cooldown
                    conn.execute('''
                        UPDATE ip_trial_usage 
                        SET trial_count = 0, first_trial_date = ?
                        WHERE ip_address = ?
                    ''', (datetime.now(), ip_address))
                    conn.commit()
                    return True, "Cooldown period elapsed, trials reset"
            
            return True, f"Trial {row['trial_count'] + 1} of {max_trials_per_ip}"
            
        except Exception as e:
            logger.error(f"Error checking IP trial eligibility: {e}")
            return True, "Error checking eligibility - allowing trial"
        finally:
            conn.close()
    
    def _record_ip_trial_usage(self, ip_address: str):
        """Record that an IP address used a free trial"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT trial_count FROM ip_trial_usage WHERE ip_address = ?', (ip_address,))
            row = cursor.fetchone()
            
            if row:
                # Update existing record
                conn.execute('''
                    UPDATE ip_trial_usage 
                    SET trial_count = trial_count + 1, last_trial_date = ?
                    WHERE ip_address = ?
                ''', (datetime.now(), ip_address))
            else:
                # Create new record
                conn.execute('''
                    INSERT INTO ip_trial_usage (ip_address, trial_count, first_trial_date, last_trial_date)
                    VALUES (?, 1, ?, ?)
                ''', (ip_address, datetime.now(), datetime.now()))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error recording IP trial usage: {e}")
        finally:
            conn.close()
    
    def _generate_device_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """Generate a simple device fingerprint"""
        import hashlib
        
        # Combine IP and user agent to create a basic fingerprint
        fingerprint_data = f"{ip_address}:{user_agent or 'unknown'}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def block_ip_address(self, ip_address: str, reason: str):
        """Admin function to block an IP address"""
        conn = self.get_connection()
        try:
            conn.execute('''
                INSERT OR REPLACE INTO ip_trial_usage 
                (ip_address, trial_count, first_trial_date, last_trial_date, blocked, blocked_reason)
                VALUES (?, 999, ?, ?, TRUE, ?)
            ''', (ip_address, datetime.now(), datetime.now(), reason))
            
            conn.commit()
            logger.info(f"Blocked IP address {ip_address}: {reason}")
            
        except Exception as e:
            logger.error(f"Error blocking IP address: {e}")
        finally:
            conn.close()
    
    def get_suspicious_ips(self, min_trials: int = 3) -> list:
        """Get IP addresses with suspicious activity"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT ip_address, trial_count, first_trial_date, last_trial_date
                FROM ip_trial_usage 
                WHERE trial_count >= ? AND blocked = FALSE
                ORDER BY trial_count DESC
            ''', (min_trials,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting suspicious IPs: {e}")
            return []
        finally:
            conn.close()

# Global database service instance
db_service = DatabaseService() 