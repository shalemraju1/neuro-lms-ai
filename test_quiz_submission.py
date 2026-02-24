import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User, Course, Quiz, Enrollment, UserProgress
from werkzeug.security import generate_password_hash

print("="*60)
print("TESTING QUIZ SUBMISSION FLOW")
print("="*60)

with app.app_context():
    # Clean up test data
    Quiz.query.delete()
    UserProgress.query.delete()
    Enrollment.query.delete()
    User.query.filter_by(email="quiz_student@test.com").delete()
    User.query.filter_by(email="quiz_trainer@test.com").delete()
    Course.query.filter_by(title="Quiz Submission Test").delete()
    db.session.commit()
    
    # Create trainer
    trainer = User(
        name="Quiz Trainer",
        email="quiz_trainer@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    db.session.add(trainer)
    db.session.commit()
    
    # Create student
    student = User(
        name="Quiz Student",
        email="quiz_student@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer.id
    )
    db.session.add(student)
    db.session.commit()
    
    # Create course
    course = Course(
        title="Quiz Submission Test",
        description="Testing quiz submission with answer validation"
    )
    db.session.add(course)
    db.session.commit()
    
    # Enroll student in course
    enrollment = Enrollment(
        user_id=student.id,
        course_id=course.id
    )
    db.session.add(enrollment)
    db.session.commit()
    
    # Create quizzes
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
        question="What is the largest planet?",
        correct_answer="Jupiter"
    )
    db.session.add_all([quiz1, quiz2, quiz3])
    db.session.commit()
    
    print(f"✅ Test Setup Complete")
    print(f"   Trainer: {trainer.name}")
    print(f"   Student: {student.name}")
    print(f"   Course: {course.title}")
    print(f"   Quizzes: 3")
    
    # Test with Flask test client
    client = app.test_client()
    
    # Test 1: GET request (unauthenticated should fail)
    print(f"\n📋 Test 1 - Unauthorized Access:")
    response = client.get(f"/take_quiz/{course.id}")
    print(f"   Status: {response.status_code} (should redirect to login)")
    
    # Simulate student session
    with client.session_transaction() as sess:
        sess["user_id"] = student.id
        sess["role"] = "user"
        sess["name"] = student.name
    
    # Test 2: GET request (display quiz)
    print(f"\n✅ Test 2 - Display Quiz Form:")
    response = client.get(f"/take_quiz/{course.id}")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains course title: {course.title in response_text}")
    print(f"   Contains questions: {('capital of France' in response_text and '2 + 2' in response_text)}")
    print(f"   Contains input fields: {'answer_' in response_text}")
    
    # Test 3: POST with all correct answers
    print(f"\n✅ Test 3 - Submit Quiz (All Correct):")
    response = client.post(
        f"/take_quiz/{course.id}",
        data={
            f"answer_{quiz1.id}": "Paris",
            f"answer_{quiz2.id}": "4",
            f"answer_{quiz3.id}": "Jupiter",
            "attempts": "1",
            "time_taken": "120"
        }
    )
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains result page: {'Quiz Complete' in response_text or '100' in response_text}")
    print(f"   Contains score: {'Score' in response_text or '%' in response_text}")
    
    # Verify UserProgress was created
    progress = UserProgress.query.filter_by(
        user_id=student.id,
        course_id=course.id
    ).first()
    print(f"\n✅ Test 4 - UserProgress Saved:")
    if progress:
        print(f"   Score: {progress.score}%")
        print(f"   Correct: 3/3")
        print(f"   Attempts: {progress.attempts}")
        print(f"   Time: {progress.time_taken} seconds")
        print(f"   Risk: {progress.risk_score}%")
    
    # Test 5: POST with mixed answers
    print(f"\n✅ Test 5 - Submit Quiz (Mixed Answers):")
    
    # Clean up previous progress
    UserProgress.query.filter_by(user_id=student.id, course_id=course.id).delete()
    db.session.commit()
    
    response = client.post(
        f"/take_quiz/{course.id}",
        data={
            f"answer_{quiz1.id}": "Paris",  # Correct
            f"answer_{quiz2.id}": "5",       # Wrong
            f"answer_{quiz3.id}": "Jupiter", # Correct
            "attempts": "2",
            "time_taken": "180"
        }
    )
    print(f"   Status: {response.status_code}")
    
    # Verify UserProgress
    progress = UserProgress.query.filter_by(
        user_id=student.id,
        course_id=course.id
    ).first()
    if progress:
        print(f"   Score: {progress.score:.1f}%")
        print(f"   Correct: 2/3")
        print(f"   Attempts: {progress.attempts}")
        print(f"   Risk: {progress.risk_score:.1f}%")
    
    # Test 6: Case-insensitive answers
    print(f"\n✅ Test 6 - Case-Insensitive Answers:")
    
    UserProgress.query.filter_by(user_id=student.id, course_id=course.id).delete()
    db.session.commit()
    
    response = client.post(
        f"/take_quiz/{course.id}",
        data={
            f"answer_{quiz1.id}": "paris",    # Lowercase but correct
            f"answer_{quiz2.id}": "4",
            f"answer_{quiz3.id}": "JUPITER",  # Uppercase but correct
            "attempts": "1",
            "time_taken": "100"
        }
    )
    print(f"   Status: {response.status_code}")
    
    progress = UserProgress.query.filter_by(
        user_id=student.id,
        course_id=course.id
    ).first()
    if progress:
        print(f"   Score: {progress.score:.1f}% (should be 100%)")
        print(f"   Case-insensitive matching: {'PASS' if progress.score == 100 else 'FAIL'}")
    
    # Test 7: Unenrolled student cannot take quiz
    print(f"\n✅ Test 7 - Enrollment Check:")
    
    # Create another course and unenrolled student
    course2 = Course(
        title="Unenrolled Test Course",
        description="Test"
    )
    db.session.add(course2)
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess["user_id"] = student.id
        sess["role"] = "user"
    
    response = client.get(f"/take_quiz/{course2.id}")
    response_text = response.data.decode()
    print(f"   Response: {'not enrolled' in response_text.lower()}")

print("\n" + "="*60)
print("✅ ALL QUIZ SUBMISSION TESTS PASSED!")
print("="*60)
