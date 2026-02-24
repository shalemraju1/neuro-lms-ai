#!/usr/bin/env python3
"""
Database migration script to add Note table
Linked to Course and Trainer (User with role "trainer")
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
    """Add Note table to database"""
    db_path = 'instance/database.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if note table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='note'")
        if cursor.fetchone():
            print("⚠️  note table already exists")
            conn.close()
            return True
        
        # Create note table
        print("Creating note table...")
        cursor.execute("""
            CREATE TABLE note (
                id INTEGER PRIMARY KEY,
                course_id INTEGER NOT NULL,
                trainer_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES course (id),
                FOREIGN KEY (trainer_id) REFERENCES user (id)
            )
        """)
        
        # Create index on course_id and trainer_id for faster queries
        cursor.execute("""
            CREATE INDEX idx_note_course_id ON note(course_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_note_trainer_id ON note(trainer_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_note_course_trainer ON note(course_id, trainer_id)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully created note table with indexes")
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
        cursor.execute("PRAGMA table_info(note)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        if not columns:
            print("❌ Verification failed - note table does not exist")
            return False
        
        print("✅ Verification successful - note table exists with columns:")
        expected_columns = ['id', 'course_id', 'trainer_id', 'content', 'created_at', 'updated_at']
        for col in expected_columns:
            if col in columns:
                print(f"   ✓ {col} ({columns[col]})")
            else:
                print(f"   ✗ {col} (MISSING)")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='note'")
        indexes = cursor.fetchall()
        print(f"\n   Indexes created: {len(indexes)}")
        for idx in indexes:
            print(f"   - {idx[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def show_migration_info():
    """Show information about the Note model"""
    print("\n📋 Note Model Schema")
    print("=" * 60)
    print("\nTable: note")
    print("\nColumns:")
    print("  • id (INTEGER PRIMARY KEY)")
    print("  • course_id (INTEGER FK → course.id) - NOT NULL")
    print("  • trainer_id (INTEGER FK → user.id) - NOT NULL")
    print("  • content (TEXT) - NOT NULL")
    print("  • created_at (TIMESTAMP) - Auto-generated")
    print("  • updated_at (TIMESTAMP) - Auto-updated")
    print("\nUsage:")
    print("  Each note links a trainer to a course with textual content")
    print("  Trainers can create notes for their courses")
    print("  Multiple notes per course and trainer are supported")
    print("\nIndexes:")
    print("  • idx_note_course_id - Fast lookup by course")
    print("  • idx_note_trainer_id - Fast lookup by trainer")
    print("  • idx_note_course_trainer - Fast lookup by course+trainer")

if __name__ == "__main__":
    print("🔄 Database Migration: Add Note table")
    print("=" * 60)
    
    # Backup database
    if backup_database():
        print()
        
        # Run migration
        if migrate_database():
            print()
            
            # Verify migration
            if verify_migration():
                print()
                show_migration_info()
                
                print("\n" + "=" * 60)
                print("🎉 Migration complete!")
                print("\nNext steps:")
                print("1. Run: python app.py")
                print("2. Trainers can now create notes for their courses")
                print("3. Use the Note model in your application")
            else:
                print("\n❌ Verification failed")
        else:
            print("\n❌ Migration failed. Using backup if needed.")
    else:
        print("⚠️  No database found. Creating fresh database on app start.")