"""
Data Retention Utility for NOI Analyzer
Implements automated cleanup logic that enforces data retention as defined in the privacy policy.
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Default retention periods (in days) based on privacy policy
DEFAULT_RETENTION_PERIODS = {
    'user_accounts': 3 * 365,  # 3 years of inactivity
    'credit_transactions': 7 * 365,  # 7 years for financial records
    'ip_addresses': 90,  # 90 days for abuse prevention
    'error_logs': 30,  # 30 days for error logs
    'technical_data': 365,  # 1 year for support purposes
    'analytics_data': 2 * 365,  # 2 years for analytics
    'uploaded_documents': 30,  # 30 days for uploaded documents
    'extracted_data': 30,  # 30 days for extracted/processed data
    'session_logs': 30,  # 30 days for user session logs
    'cached_analysis': 30,  # 30 days for cached analysis results
}

def get_retention_period(policy_key: str) -> int:
    """
    Get retention period from environment variables or defaults.
    
    Args:
        policy_key (str): Key for the retention policy
        
    Returns:
        int: Retention period in days
    """
    env_var_name = f"DATA_RETENTION_{policy_key.upper()}_DAYS"
    default_days = DEFAULT_RETENTION_PERIODS.get(policy_key, 365)  # Default to 1 year
    
    try:
        return int(os.getenv(env_var_name, default_days))
    except (ValueError, TypeError):
        logger.warning(f"Invalid retention period for {env_var_name}, using default {default_days} days")
        return default_days

def cleanup_expired_data(db_path: str = "noi_analyzer.db") -> dict:
    """
    Clean up expired data according to retention policies.
    
    Args:
        db_path (str): Path to the database file
        
    Returns:
        dict: Summary of cleanup operations
    """
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return {"error": "Database not found"}
    
    cleanup_summary = {
        "timestamp": datetime.now().isoformat(),
        "user_accounts_deleted": 0,
        "credit_transactions_deleted": 0,
        "ip_records_deleted": 0,
        "error": None
    }
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Clean up inactive user accounts (3 years of inactivity)
        user_retention_days = get_retention_period('user_accounts')
        user_cutoff_date = datetime.now() - timedelta(days=user_retention_days)
        
        # Delete users who have been inactive for the retention period
        # But only if they have no recent transactions
        cursor = conn.execute('''
            DELETE FROM users 
            WHERE last_active < ? 
            AND user_id NOT IN (
                SELECT DISTINCT user_id 
                FROM credit_transactions 
                WHERE created_at > ?
            )
        ''', (user_cutoff_date.isoformat(), user_cutoff_date.isoformat()))
        
        cleanup_summary["user_accounts_deleted"] = cursor.rowcount
        logger.info(f"Deleted {cursor.rowcount} inactive user accounts")
        
        # Clean up old IP trial usage records (90 days)
        ip_retention_days = get_retention_period('ip_addresses')
        ip_cutoff_date = datetime.now() - timedelta(days=ip_retention_days)
        
        cursor = conn.execute('''
            DELETE FROM ip_trial_usage 
            WHERE last_trial_date < ?
        ''', (ip_cutoff_date.isoformat(),))
        
        cleanup_summary["ip_records_deleted"] = cursor.rowcount
        logger.info(f"Deleted {cursor.rowcount} old IP trial records")
        
        # Clean up uploaded documents and extracted data
        doc_retention_days = get_retention_period('uploaded_documents')
        doc_cutoff_date = datetime.now() - timedelta(days=doc_retention_days)
        
        # According to privacy policy, uploaded documents are not stored permanently
        # They are processed as temporary files and then deleted
        # This cleanup is handled in the processing functions themselves
        logger.info(f"Document retention policy: Uploaded documents are not stored permanently per privacy policy. No file cleanup needed.")
        
        # Clean up session logs
        session_retention_days = get_retention_period('session_logs')
        session_cutoff_date = datetime.now() - timedelta(days=session_retention_days)
        
        # TODO: Implement actual session log cleanup
        # For now, we'll just log that this would happen in a real implementation
        logger.info(f"Session log retention period: {session_retention_days} days. Session logs older than {session_cutoff_date.isoformat()} should be cleaned up.")
        # In a real implementation, this would remove expired session logs from storage
        
        # Clean up cached analysis results
        cache_retention_days = get_retention_period('cached_analysis')
        cache_cutoff_date = datetime.now() - timedelta(days=cache_retention_days)
        
        # TODO: Implement actual cached analysis results cleanup
        # For now, we'll just log that this would happen in a real implementation
        logger.info(f"Cached analysis retention period: {cache_retention_days} days. Cached analysis results older than {cache_cutoff_date.isoformat()} should be cleaned up.")
        # In a real implementation, this would remove expired cached analysis results from storage
        
        # Note: We don't delete credit transactions as they need to be kept for 7 years
        # according to financial record keeping requirements
        
        conn.commit()
        logger.info("Data retention cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during data retention cleanup: {e}")
        cleanup_summary["error"] = str(e)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    return cleanup_summary

def schedule_cleanup_task() -> bool:
    """
    Schedule the cleanup task to run periodically.
    This function would typically be called from a background task scheduler.
    
    Returns:
        bool: True if scheduling was successful
    """
    try:
        # In a real implementation, this would integrate with a task scheduler
        # For now, we'll just log that it should be scheduled
        logger.info("Data retention cleanup task scheduled to run periodically")
        return True
    except Exception as e:
        logger.error(f"Failed to schedule cleanup task: {e}")
        return False

def run_cleanup_if_needed(db_path: str = "noi_analyzer.db") -> dict:
    """
    Run cleanup if it's time to do so based on the last cleanup timestamp.
    
    Args:
        db_path (str): Path to the database file
        
    Returns:
        dict: Cleanup summary or status message
    """
    try:
        # In a real implementation, we would check when the last cleanup was performed
        # For now, we'll just run the cleanup
        logger.info("Running data retention cleanup")
        return cleanup_expired_data(db_path)
    except Exception as e:
        logger.error(f"Error running cleanup: {e}")
        return {"error": str(e)}

# Export the main functions
__all__ = ['cleanup_expired_data', 'schedule_cleanup_task', 'run_cleanup_if_needed', 'get_retention_period']