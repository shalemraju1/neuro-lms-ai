import sqlite3
import os
from datetime import datetime
import time

# Database path
db_path = os.path.join(os.getcwd(), 'instance', 'database.db')

print("="*60)
print("MIGRATING DATABASE: Adding Quiz Table")
print("="*60)

# Wait a moment to ensure database is not locked
time.sleep(1)

# Connect to database with timeout
conn = sqlite3.connect(db_path, timeout=10)
cursor = conn.cursor()

try:
    # Check if quiz table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz'")
    if cursor.fetchone():
        print("\n⚠️  Quiz table already exists. Skipping creation.")
    else:
        # Create quiz table
        cursor.execute('''
            CREATE TABLE quiz (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                trainer_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES course(id),
                FOREIGN KEY (trainer_id) REFERENCES user(id)
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX idx_quiz_course_id ON quiz(course_id)')
        cursor.execute('CREATE INDEX idx_quiz_trainer_id ON quiz(trainer_id)')
        
        conn.commit()
        print("\n✅ Created quiz table successfully")
        print("✅ Created indexes: idx_quiz_course_id, idx_quiz_trainer_id")
    
    # Verify table structure
    cursor.execute("PRAGMA table_info(quiz)")
    columns = cursor.fetchall()
    print("\n📋 Quiz Table Schema:")
    print("-" * 60)
    for col_id, col_name, col_type, not_null, default, pk in columns:
        nullable = "NOT NULL" if not_null else "NULL"
        pk_str = "PRIMARY KEY" if pk else ""
        print(f"  {col_name}: {col_type} {nullable} {pk_str}")
    
    # Verify foreign keys
    cursor.execute("PRAGMA foreign_key_list(quiz)")
    fks = cursor.fetchall()
    print("\n🔗 Foreign Keys:")
    print("-" * 60)
    for fk_id, seq, table, from_col, to_col, on_delete, on_update, match in fks:
        print(f"  {from_col} -> {table}.{to_col}")
    
    # Count existing quizzes
    cursor.execute("SELECT COUNT(*) FROM quiz")
    count = cursor.fetchone()[0]
    print(f"\n📊 Total quizzes in database: {count}")
    
    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    print("="*60)

except sqlite3.Error as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()
    exit(1)

finally:
    conn.close()

