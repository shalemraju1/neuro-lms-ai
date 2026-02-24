#!/usr/bin/env python3
"""
Test script for the Note model
"""

from app import app, db, Note, User, Course

with app.app_context():
    # Test creating a note
    print('Testing Note Model')
    print('=' * 50)
    
    # Get trainer
    trainer = User.query.filter_by(role='trainer').first()
    
    # Get or create a test course
    course = Course.query.first()
    if not course:
        print('Creating test course...')
        course = Course(
            title='Machine Learning Basics',
            description='Introduction to machine learning concepts',
            created_by=1
        )
        db.session.add(course)
        db.session.commit()
    
    if trainer and course:
        # Create a test note
        print(f'\nCreating note...')
        note = Note(
            course_id=course.id,
            trainer_id=trainer.id,
            content='This is a test note for the course. Students should focus on understanding the core concepts.'
        )
        
        db.session.add(note)
        db.session.commit()
        
        print(f'✅ Note created successfully')
        print(f'   Note ID: {note.id}')
        print(f'   Course: {course.title} (ID: {course.id})')
        print(f'   Trainer: {trainer.name} (ID: {trainer.id})')
        print(f'   Content: {note.content}')
        print(f'   Created: {note.created_at}')
        
        # Test querying notes
        notes = Note.query.filter_by(course_id=course.id).all()
        print(f'\n✅ Notes for course "{course.title}": {len(notes)}')
        
        trainer_notes = Note.query.filter_by(trainer_id=trainer.id).all()
        print(f'✅ Notes by trainer "{trainer.name}": {len(trainer_notes)}')
        
        # Test relationships
        print(f'\n✅ Testing relationships:')
        print(f'   note.course: {note.course.title}')
        print(f'   note.trainer: {note.trainer.name}')
        
        # Show course notes via backref
        print(f'\n✅ Testing backreferences:')
        print(f'   course.notes: {len(course.notes)} note(s)')
        print(f'   trainer.notes: {len(trainer.notes)} note(s)')
        
        # Create another note to test multiple notes
        print(f'\nCreating second note...')
        note2 = Note(
            course_id=course.id,
            trainer_id=trainer.id,
            content='This is a second note. Remember to review the assignments.'
        )
        db.session.add(note2)
        db.session.commit()
        
        print(f'✅ Second note created')
        print(f'   Total notes for course: {len(course.notes)}')
        print(f'   Total notes by trainer: {len(trainer.notes)}')
        
        print(f'\n📋 All notes:')
        for n in course.notes:
            print(f'   [{n.id}] {n.content[:50]}...')
        
        # Clean up test notes
        db.session.delete(note)
        db.session.delete(note2)
        db.session.commit()
        print(f'\n✅ Test notes deleted')
        
        print(f'\n' + '=' * 50)
        print(f'✨ Note Model Test Passed!')
    else:
        print('❌ No trainer found to test with')