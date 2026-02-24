#!/usr/bin/env python3
"""
Database migration script to add trainer_id column to User table
"""

import sqlite3
import os
from datetime import datetime

def backup_database():
    """Backup the existing database"""
    db_path = 'instance/database.db'
    backup_path = f'instance/database.db.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    if os.path.exists(db_path):
        with open(db_path, 'rb') as src:
            with open(backup_path, 'wb') as dst:
                dst.write(src.read())
        print(f"✅ Database backed up to: {backup_path}")
        return True
    return False

def migrate_database():
    """Add trainer_id column to user table"""
    db_path = 'instance/database.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if trainer_id column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'trainer_id' in columns:
            print("⚠️  trainer_id column already exists in user table")
            conn.close()
            return True
        
        # Add trainer_id column to user table
        print("Adding trainer_id column to user table...")
        cursor.execute("""
            ALTER TABLE user ADD COLUMN trainer_id INTEGER DEFAULT NULL
        """)
        
        # Add foreign key constraint (SQLite has limited ALTER TABLE support, 
        # but the column is the important part)
        conn.commit()
        conn.close()
        
        print("✅ Successfully added trainer_id column to user table")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Migration failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_migration():
    """Verify the migration was successful"""
    db_path = 'instance/database.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(user)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        if 'trainer_id' in columns:
            print("✅ Verification successful - trainer_id column exists")
            print(f"   Column type: {columns['trainer_id']}")
            
            # Show sample data
            cursor.execute("SELECT id, name, role, trainer_id FROM user LIMIT 5")
            users = cursor.fetchall()
            if users:
                print("\n   Sample user data:")
                for user in users:
                    print(f"   - ID: {user[0]}, Name: {user[1]}, Role: {user[2]}, Trainer ID: {user[3]}")
        else:
            print("❌ Verification failed - trainer_id column does not exist")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Database Migration: Add trainer_id to User model")
    print("=" * 60)
    
    # Backup database
    if backup_database():
        print()
        
        # Run migration
        if migrate_database():
            print()
            
            # Verify migration
            verify_migration()
            
            print("\n" + "=" * 60)
            print("🎉 Migration complete!")
            print("\nNext steps:")
            print("1. Run: python app.py")
            print("2. Use manage_users.py to assign trainers to users")
            print("3. Create routes to view/manage trainer-student relationships")
        else:
            print("\n❌ Migration failed. Using backup if needed.")
    else:
        print("⚠️  No database found. Creating fresh database on app start.")