#!/usr/bin/env python3
"""
Note Model Usage Guide

The Note model is used to store trainer notes for courses in NeuroLMS.
"""

from app import app, db, Note, User, Course
from datetime import datetime

# Example 1: Create a note
def create_note_example():
    with app.app_context():
        # Get a trainer and course
        trainer = User.query.filter_by(role='trainer').first()
        course = Course.query.first()
        
        if trainer and course:
            note = Note(
                course_id=course.id,
                trainer_id=trainer.id,
                content="This is an important note about the course content."
            )
            
            db.session.add(note)
            db.session.commit()
            
            print(f"Created note: {note.id}")
            return note

# Example 2: Query notes by course
def get_course_notes_example():
    with app.app_context():
        course = Course.query.first()
        if course:
            notes = course.notes  # Using backref
            print(f"Notes for {course.title}: {len(notes)}")
            for note in notes:
                print(f"  - {note.content}")

# Example 3: Query notes by trainer
def get_trainer_notes_example():
    with app.app_context():
        trainer = User.query.filter_by(role='trainer').first()
        if trainer:
            notes = trainer.notes  # Using backref
            print(f"Notes by {trainer.name}: {len(notes)}")
            for note in notes:
                print(f"  - {note.content[:50]}...")

# Example 4: Update a note
def update_note_example(note_id):
    with app.app_context():
        note = Note.query.get(note_id)
        if note:
            note.content = "Updated note content"
            note.updated_at = datetime.utcnow()
            db.session.commit()
            print(f"Updated note: {note.id}")

# Example 5: Delete a note
def delete_note_example(note_id):
    with app.app_context():
        note = Note.query.get(note_id)
        if note:
            db.session.delete(note)
            db.session.commit()
            print(f"Deleted note: {note_id}")

# Example 6: Query notes by course and trainer
def get_notes_by_course_and_trainer_example():
    with app.app_context():
        course = Course.query.first()
        trainer = User.query.filter_by(role='trainer').first()
        
        if course and trainer:
            notes = Note.query.filter_by(
                course_id=course.id,
                trainer_id=trainer.id
            ).all()
            
            print(f"Notes by {trainer.name} for {course.title}: {len(notes)}")
            for note in notes:
                print(f"  - {note.content}")
                print(f"    Created: {note.created_at}")
                print(f"    Updated: {note.updated_at}")

if __name__ == "__main__":
    print("Note Model Examples")
    print("=" * 60)
    
    # Run examples
    print("\nExample 1: Create a note")
    create_note_example()
    
    print("\nExample 2: Get notes by course")
    get_course_notes_example()
    
    print("\nExample 3: Get notes by trainer")
    get_trainer_notes_example()
    
    print("\nExample 6: Get notes by course and trainer")
    get_notes_by_course_and_trainer_example()