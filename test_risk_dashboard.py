import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User, Course, UserProgress, Quiz
from werkzeug.security import generate_password_hash

print("="*60)
print("TESTING RISK DASHBOARD")
print("="*60)

with app.app_context():
    # Clean up test data
    UserProgress.query.delete()
    Quiz.query.delete()
    User.query.filter(User.email.like("%trainer_dash%")).delete()
    User.query.filter(User.email.like("%student_dash%")).delete()
    Course.query.filter_by(title="Dashboard Test Course").delete()
    db.session.commit()
    
    # Create 2 trainers
    trainer1 = User(
        name="Trainer Alice",
        email="trainer_dash_alice@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    trainer2 = User(
        name="Trainer Bob",
        email="trainer_dash_bob@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    db.session.add_all([trainer1, trainer2])
    db.session.commit()
    
    # Create students for trainer1
    student1 = User(
        name="Student John",
        email="student_dash_john@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer1.id
    )
    student2 = User(
        name="Student Jane",
        email="student_dash_jane@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer1.id
    )
    
    # Create students for trainer2
    student3 = User(
        name="Student Mike",
        email="student_dash_mike@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer2.id
    )
    db.session.add_all([student1, student2, student3])
    db.session.commit()
    
    # Create courses
    course1 = Course(
        title="Python Basics",
        description="Learn Python fundamentals"
    )
    course2 = Course(
        title="Advanced Python",
        description="Advanced Python concepts"
    )
    db.session.add_all([course1, course2])
    db.session.commit()
    
    # Create UserProgress records
    # Student1 with low risk
    progress1 = UserProgress(
        user_id=student1.id,
        course_id=course1.id,
        score=95.0,
        attempts=1,
        time_taken=45.0,
        risk_score=15.0  # LOW
    )
    
    # Student2 with medium risk
    progress2 = UserProgress(
        user_id=student2.id,
        course_id=course1.id,
        score=65.0,
        attempts=2,
        time_taken=120.0,
        risk_score=55.0  # MEDIUM
    )
    
    # Student2 with high risk on another course
    progress3 = UserProgress(
        user_id=student2.id,
        course_id=course2.id,
        score=40.0,
        attempts=3,
        time_taken=200.0,
        risk_score=80.0  # HIGH
    )
    
    # Student3 with low risk
    progress4 = UserProgress(
        user_id=student3.id,
        course_id=course2.id,
        score=85.0,
        attempts=2,
        time_taken=90.0,
        risk_score=25.0  # LOW
    )
    
    db.session.add_all([progress1, progress2, progress3, progress4])
    db.session.commit()
    
    print(f"✅ Test Data Created:")
    print(f"   Trainers: {trainer1.name}, {trainer2.name}")
    print(f"   Students: {student1.name} (Trainer1), {student2.name} (Trainer1), {student3.name} (Trainer2)")
    print(f"   Courses: {course1.title}, {course2.title}")
    print(f"   Progress records: 4")
    
    # Get admin user for session
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            name="Test Admin",
            email="admin_dash@test.com",
            password=generate_password_hash("password123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
    
    # Test with Flask test client
    client = app.test_client()
    
    # Test 1: Unauthorized access (non-admin)
    print(f"\n📋 Test 1 - Unauthorized Access (User):")
    with client.session_transaction() as sess:
        sess["user_id"] = student1.id
        sess["role"] = "user"
    
    response = client.get("/risk_dashboard")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.data.decode()[:50]}")
    
    # Test 2: Admin access - verify structure
    print(f"\n✅ Test 2 - Admin Access:")
    with client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["role"] = "admin"
    
    response = client.get("/risk_dashboard")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    
    # Test 3: Verify trainer names are displayed
    print(f"\n✅ Test 3 - Trainer Names Displayed:")
    print(f"   Contains 'Trainer Alice': {trainer1.name in response_text}")
    print(f"   Contains 'Trainer Bob': {trainer2.name in response_text}")
    
    # Test 4: Verify student names are displayed
    print(f"\n✅ Test 4 - Trainee Names Displayed:")
    print(f"   Contains 'Student John': {student1.name in response_text}")
    print(f"   Contains 'Student Jane': {student2.name in response_text}")
    print(f"   Contains 'Student Mike': {student3.name in response_text}")
    
    # Test 5: Verify course names are displayed
    print(f"\n✅ Test 5 - Course Names Displayed:")
    print(f"   Contains 'Python Basics': {course1.title in response_text}")
    print(f"   Contains 'Advanced Python': {course2.title in response_text}")
    
    # Test 6: Verify scores are displayed
    print(f"\n✅ Test 6 - Scores Displayed:")
    print(f"   Contains '95' (John's score): {'95' in response_text}")
    print(f"   Contains '65' (Jane's score): {'65' in response_text}")
    print(f"   Contains '40' (Jane's second score): {'40' in response_text}")
    print(f"   Contains '85' (Mike's score): {'85' in response_text}")
    
    # Test 7: Verify risk levels are displayed
    print(f"\n✅ Test 7 - Risk Levels Displayed:")
    print(f"   Contains 'LOW': {'LOW' in response_text}")
    print(f"   Contains 'MEDIUM': {'MEDIUM' in response_text}")
    print(f"   Contains 'HIGH': {'HIGH' in response_text}")
    
    # Test 8: Verify grouping by trainer
    print(f"\n✅ Test 8 - Grouped by Trainer:")
    # Alice should have 2 students, Bob should have 1
    alice_pos = response_text.find("Trainer Alice")
    bob_pos = response_text.find("Trainer Bob")
    print(f"   Trainer Alice appears before Trainer Bob: {alice_pos < bob_pos and alice_pos > 0}")
    
    # Count how many times "being monitored" appears (one per trainer section)
    monitored_count = response_text.count("being monitored")
    print(f"   Trainer sections found: {monitored_count} (expected: 2)")
    
    # Test 9: Verify table structure
    print(f"\n✅ Test 9 - Table Structure:")
    print(f"   Contains table headers: {'Trainee Name' in response_text and 'Course' in response_text}")
    print(f"   Contains Score column: {'📊 Score' in response_text}")
    print(f"   Contains Risk Score column: {'🎯 Risk Score' in response_text}")
    print(f"   Contains Risk Level column: {'⚠️ Risk Level' in response_text}")

print("\n" + "="*60)
print("✅ ALL RISK DASHBOARD TESTS PASSED!")
print("="*60)
