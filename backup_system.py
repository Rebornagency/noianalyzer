#!/usr/bin/env python3
"""
Simple Database Backup System for NOI Analyzer
Protects your credit system data from loss
"""

import os
import shutil
import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def backup_database(db_path="noi_analyzer.db", backup_dir="backups"):
    """Create a backup of the credit system database"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"noi_analyzer_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Also create JSON export for extra safety
        json_backup_path = backup_path.replace('.db', '.json')
        export_to_json(db_path, json_backup_path)
        
        # Keep only last 10 backups to save space
        cleanup_old_backups(backup_dir, keep_count=10)
        
        print(f"✅ Backup created: {backup_filename}")
        print(f"📄 JSON export: {os.path.basename(json_backup_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def export_to_json(db_path, json_path):
    """Export database to JSON format for human-readable backup"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    backup_data = {
        "backup_timestamp": datetime.now().isoformat(),
        "database_file": db_path,
        "tables": {}
    }
    
    # Get all table names
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor = conn.execute(f"SELECT * FROM {table}")
        rows = [dict(row) for row in cursor.fetchall()]
        backup_data["tables"][table] = {
            "row_count": len(rows),
            "data": rows
        }
    
    conn.close()
    
    # Save JSON with pretty formatting
    with open(json_path, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)

def cleanup_old_backups(backup_dir, keep_count=10):
    """Keep only the most recent backups"""
    backup_files = []
    
    for filename in os.listdir(backup_dir):
        if filename.startswith("noi_analyzer_backup_") and filename.endswith(".db"):
            filepath = os.path.join(backup_dir, filename)
            mtime = os.path.getmtime(filepath)
            backup_files.append((mtime, filepath, filename))
    
    # Sort by modification time (newest first)
    backup_files.sort(reverse=True)
    
    # Remove old backups
    for i, (mtime, filepath, filename) in enumerate(backup_files):
        if i >= keep_count:
            os.remove(filepath)
            # Also remove corresponding JSON file
            json_file = filepath.replace('.db', '.json')
            if os.path.exists(json_file):
                os.remove(json_file)
            print(f"🗑️ Removed old backup: {filename}")

def verify_database_integrity(db_path="noi_analyzer.db"):
    """Check database for corruption or issues"""
    print("🔍 Checking database integrity...")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Run integrity check
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        if result == "ok":
            print("✅ Database integrity: OK")
            
            # Check table counts
            tables = ["users", "credit_transactions", "credit_packages", "ip_trial_usage"]
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"📊 {table}: {count} records")
                except Exception as e:
                    print(f"⚠️ Error checking {table}: {e}")
            
            conn.close()
            return True
        else:
            print(f"❌ Database integrity check failed: {result}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def restore_from_backup(backup_path, target_path="noi_analyzer.db"):
    """Restore database from backup"""
    print(f"🔄 Restoring database from {backup_path}")
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        return False
    
    try:
        # Create a backup of current database first
        if os.path.exists(target_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = f"pre_restore_backup_{timestamp}.db"
            shutil.copy2(target_path, safety_backup)
            print(f"💾 Created safety backup: {safety_backup}")
        
        # Restore from backup
        shutil.copy2(backup_path, target_path)
        
        # Verify restored database
        if verify_database_integrity(target_path):
            print("✅ Database restored successfully")
            return True
        else:
            print("❌ Restored database failed integrity check")
            return False
            
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

def auto_backup_if_needed(db_path="noi_analyzer.db", backup_dir="backups", hours_threshold=24):
    """Automatically backup if last backup is too old"""
    
    if not os.path.exists(db_path):
        return False
    
    # Check if backup is needed
    backup_needed = True
    
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) 
                       if f.startswith("noi_analyzer_backup_") and f.endswith(".db")]
        
        if backup_files:
            # Get the newest backup
            newest_backup = max(backup_files, 
                              key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
            newest_backup_time = os.path.getmtime(os.path.join(backup_dir, newest_backup))
            
            # Check if backup is recent enough
            hours_since_backup = (datetime.now().timestamp() - newest_backup_time) / 3600
            
            if hours_since_backup < hours_threshold:
                backup_needed = False
                print(f"ℹ️ Recent backup exists ({hours_since_backup:.1f} hours old)")
    
    if backup_needed:
        print(f"⏰ Creating automatic backup (threshold: {hours_threshold} hours)")
        return backup_database(db_path, backup_dir)
    
    return True

def main():
    """CLI interface for backup system"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 NOI Analyzer Database Backup Tool")
        print("Usage:")
        print("  python backup_system.py backup       - Create backup")
        print("  python backup_system.py verify       - Check database integrity")
        print("  python backup_system.py auto         - Auto backup if needed")
        print("  python backup_system.py restore <file> - Restore from backup")
        return
    
    command = sys.argv[1].lower()
    
    if command == "backup":
        backup_database()
        
    elif command == "verify":
        verify_database_integrity()
        
    elif command == "auto":
        auto_backup_if_needed()
        
    elif command == "restore" and len(sys.argv) > 2:
        backup_file = sys.argv[2]
        restore_from_backup(backup_file)
        
    else:
        print("❌ Unknown command or missing backup file")

if __name__ == "__main__":
    main()