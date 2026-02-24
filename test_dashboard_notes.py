import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User, Course, Enrollment, Note
from werkzeug.security import generate_password_hash

# Test the dashboard notes feature for users
with app.app_context():
    # Clean up test data
    User.query.filter_by(email="trainer_test@test.com").delete()
    User.query.filter_by(email="student_test@test.com").delete()
    Course.query.filter_by(title="Test Course for Notes").delete()
    db.session.commit()
    
    # Create a trainer
    trainer = User(
        name="Test Trainer",
        email="trainer_test@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    db.session.add(trainer)
    db.session.commit()
    
    # Create a student with trainer assigned
    student = User(
        name="Test Student",
        email="student_test@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer.id
    )
    db.session.add(student)
    db.session.commit()
    
    # Create a course
    course = Course(
        title="Test Course for Notes",
        description="A test course"
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
    
    # Create notes from trainer
    note1 = Note(
        course_id=course.id,
        trainer_id=trainer.id,
        content="This is the first note with important information about the course."
    )
    note2 = Note(
        course_id=course.id,
        trainer_id=trainer.id,
        content="This is the second note with additional guidance for students."
    )
    db.session.add_all([note1, note2])
    db.session.commit()
    
    print("✅ Test Data Created")
    print(f"   Trainer: {trainer.name} (ID: {trainer.id})")
    print(f"   Student: {student.name} (ID: {student.id}, Trainer ID: {student.trainer_id})")
    print(f"   Course: {course.title} (ID: {course.id})")
    print(f"   Notes: {len([note1, note2])}")
    
    # Test with Flask test client
    client = app.test_client()
    
    # Simulate student session
    with client.session_transaction() as sess:
        sess["user_id"] = student.id
        sess["role"] = "user"
        sess["name"] = student.name
    
    # Get dashboard
    response = client.get("/dashboard")
    print(f"\n✅ Dashboard Response: {response.status_code}")
    
    # Check if response contains the course
    response_text = response.data.decode()
    print(f"   Contains course title: {course.title in response_text}")
    print(f"   Contains 'Trainer Notes': {'Trainer Notes' in response_text}")
    print(f"   Contains note content: {'first note' in response_text}")
    print(f"   Contains second note: {'second note' in response_text}")
    
    # Test admin dashboard (should not show notes section)
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            name="Test Admin",
            email="admin_test@test.com",
            password=generate_password_hash("password123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
    
    with client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["role"] = "admin"
        sess["name"] = admin.name
    
    response = client.get("/dashboard")
    response_text = response.data.decode()
    print(f"\n✅ Admin Dashboard (should not show Trainer Notes): {response.status_code}")
    print(f"   Does NOT contain 'Trainer Notes': {'Trainer Notes' not in response_text}")
    
    # Test trainer dashboard (should show upload note button)
    with client.session_transaction() as sess:
        sess["user_id"] = trainer.id
        sess["role"] = "trainer"
        sess["name"] = trainer.name
    
    response = client.get("/dashboard")
    response_text = response.data.decode()
    print(f"\n✅ Trainer Dashboard: {response.status_code}")
    print(f"   Contains 'Add Note' button: {'Add Note' in response_text}")
    print(f"   Contains upload_note link: {'upload_note' in response_text}")

print("\n" + "="*60)
print("✅ All dashboard notes tests completed!")
print("="*60)
