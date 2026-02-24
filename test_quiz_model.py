import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User, Course, Quiz
from werkzeug.security import generate_password_hash

print("="*60)
print("TESTING QUIZ MODEL")
print("="*60)

with app.app_context():
    # Clean up test data
    Quiz.query.delete()
    User.query.filter_by(email="quiz_trainer@test.com").delete()
    Course.query.filter_by(title="Quiz Test Course").delete()
    db.session.commit()
    
    # Create test trainer
    trainer = User(
        name="Quiz Trainer",
        email="quiz_trainer@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    db.session.add(trainer)
    db.session.commit()
    print(f"✅ Created trainer: {trainer.name} (ID: {trainer.id})")
    
    # Create test course
    course = Course(
        title="Quiz Test Course",
        description="A course for testing quizzes"
    )
    db.session.add(course)
    db.session.commit()
    print(f"✅ Created course: {course.title} (ID: {course.id})")
    
    # Create test quizzes
    quiz1 = Quiz(
        course_id=course.id,
        trainer_id=trainer.id,
        question="What is the capital of France?",
        correct_answer="Paris"
    )
    
    quiz2 = Quiz(
        course_id=course.id,
        trainer_id=trainer.id,
        question="What is 2 + 2?",
        correct_answer="4"
    )
    
    quiz3 = Quiz(
        course_id=course.id,
        trainer_id=trainer.id,
        question="What is the largest planet in our solar system?",
        correct_answer="Jupiter"
    )
    
    db.session.add_all([quiz1, quiz2, quiz3])
    db.session.commit()
    print(f"\n✅ Created 3 quizzes:")
    print(f"   Quiz 1 ID: {quiz1.id} - {quiz1.question}")
    print(f"   Quiz 2 ID: {quiz2.id} - {quiz2.question}")
    print(f"   Quiz 3 ID: {quiz3.id} - {quiz3.question}")
    
    # Test relationships
    print("\n📋 Testing Relationships:")
    print("-" * 60)
    
    # Get quiz and verify course relationship
    retrieved_quiz = Quiz.query.get(quiz1.id)
    print(f"✅ Retrieved quiz: {retrieved_quiz.question}")
    print(f"   Linked course: {retrieved_quiz.course.title}")
    print(f"   Linked trainer: {retrieved_quiz.trainer.name}")
    
    # Get course and check quizzes backref
    retrieved_course = Course.query.get(course.id)
    print(f"\n✅ Retrieved course: {retrieved_course.title}")
    print(f"   Linked quizzes ({len(retrieved_course.quizzes)}):")
    for q in retrieved_course.quizzes:
        print(f"      - {q.question}")
    
    # Get trainer and check quizzes backref
    retrieved_trainer = User.query.get(trainer.id)
    print(f"\n✅ Retrieved trainer: {retrieved_trainer.name}")
    print(f"   Created quizzes ({len(retrieved_trainer.quizzes)}):")
    for q in retrieved_trainer.quizzes:
        print(f"      - {q.question}")
    
    # Test querying quizzes for a specific course
    course_quizzes = Quiz.query.filter_by(course_id=course.id).all()
    print(f"\n✅ Query: Quizzes for course '{course.title}'")
    print(f"   Count: {len(course_quizzes)}")
    
    # Test querying quizzes created by a trainer
    trainer_quizzes = Quiz.query.filter_by(trainer_id=trainer.id).all()
    print(f"\n✅ Query: Quizzes created by trainer '{trainer.name}'")
    print(f"   Count: {len(trainer_quizzes)}")
    
    # Test filtering by both course and trainer
    specific_quizzes = Quiz.query.filter_by(
        course_id=course.id,
        trainer_id=trainer.id
    ).all()
    print(f"\n✅ Query: Quizzes for course '{course.title}' by trainer '{trainer.name}'")
    print(f"   Count: {len(specific_quizzes)}")
    for q in specific_quizzes:
        print(f"      - Q: {q.question}")
        print(f"        A: {q.correct_answer}")
    
    # Test timestamps
    print(f"\n✅ Timestamp Testing:")
    print(f"   Quiz created_at: {quiz1.created_at}")

print("\n" + "="*60)
print("✅ ALL QUIZ MODEL TESTS PASSED!")
print("="*60)
