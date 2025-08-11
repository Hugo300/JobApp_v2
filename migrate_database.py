#!/usr/bin/env python3
"""
Database migration script to add new columns to existing tables
"""

import sqlite3
import os
import sys

def migrate_database():
    """Add new columns to the job_application table"""
    db_path = 'instance/job_app.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found. Please run the application first to create the database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting database migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(job_application)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'office_location' not in columns:
            migrations_needed.append("ALTER TABLE job_application ADD COLUMN office_location VARCHAR(200)")
        
        if 'country' not in columns:
            migrations_needed.append("ALTER TABLE job_application ADD COLUMN country VARCHAR(100)")
        
        if 'job_mode' not in columns:
            migrations_needed.append("ALTER TABLE job_application ADD COLUMN job_mode VARCHAR(50) DEFAULT 'On-site'")
        
        if not migrations_needed:
            print("✅ Database is already up to date!")
            return True
        
        # Execute migrations
        for migration in migrations_needed:
            print(f"🔄 Executing: {migration}")
            cursor.execute(migration)
        
        conn.commit()
        print(f"✅ Successfully applied {len(migrations_needed)} migration(s)!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(job_application)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📊 Current columns: {', '.join(columns)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def rollback_migration():
    """Rollback the migration (remove new columns)"""
    print("⚠️  Rollback not supported for SQLite ALTER TABLE ADD COLUMN.")
    print("To rollback, you would need to:")
    print("1. Export your data")
    print("2. Drop and recreate the table")
    print("3. Import the data back")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
    else:
        success = migrate_database()
        if success:
            print("\n🎉 Migration completed successfully!")
            print("You can now restart the application to use the new features.")
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
            sys.exit(1)
