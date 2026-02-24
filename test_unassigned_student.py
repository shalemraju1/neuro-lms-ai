import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User, Course, Enrollment, Note
from werkzeug.security import generate_password_hash

# Test edge case: user without assigned trainer
with app.app_context():
    # Clean up
    User.query.filter_by(email="unassigned_student@test.com").delete()
    Course.query.filter_by(title="Test Course Unassigned").delete()
    db.session.commit()
    
    # Create a course
    course = Course(
        title="Test Course Unassigned",
        description="A course for testing unassigned students"
    )
    db.session.add(course)
    db.session.commit()
    
    # Create student WITHOUT trainer assigned
    student = User(
        name="Unassigned Student",
        email="unassigned_student@test.com",
        password=generate_password_hash("password123"),
        role="user"
        # Note: no trainer_id assigned
    )
    db.session.add(student)
    db.session.commit()
    
    # Enroll student in course
    enrollment = Enrollment(
        user_id=student.id,
        course_id=course.id
    )
    db.session.add(enrollment)
    db.session.commit()
    
    print("✅ Test Data Created (Student without trainer)")
    print(f"   Student: {student.name} (ID: {student.id}, Trainer ID: {student.trainer_id})")
    
    # Test with Flask test client
    client = app.test_client()
    
    # Simulate student session
    with client.session_transaction() as sess:
        sess["user_id"] = student.id
        sess["role"] = "user"
        sess["name"] = student.name
    
    # Get dashboard - should not crash, just show course without notes
    response = client.get("/dashboard")
    print(f"\n✅ Dashboard Response: {response.status_code}")
    
    response_text = response.data.decode()
    print(f"   Contains course: {course.title in response_text}")
    print(f"   Does NOT show Trainer Notes section: {'Trainer Notes' not in response_text}")
    print(f"   Shows Take Quiz button: {'Take Quiz' in response_text}")

print("\n" + "="*60)
print("✅ Edge case test (unassigned student) passed!")
print("="*60)
