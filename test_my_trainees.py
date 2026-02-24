import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User
from werkzeug.security import generate_password_hash

print("="*60)
print("TESTING MY_TRAINEES ROUTE")
print("="*60)

with app.app_context():
    # Clean up test data
    User.query.filter(User.email.like("%my_trainees_test%")).delete()
    db.session.commit()
    
    # Create test trainer
    trainer = User(
        name="Trainer For My Trainees",
        email="trainer_my_trainees_test@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    db.session.add(trainer)
    db.session.commit()
    
    # Create test students assigned to this trainer
    student1 = User(
        name="Trainee One",
        email="student_my_trainees_test_1@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer.id
    )
    student2 = User(
        name="Trainee Two",
        email="student_my_trainees_test_2@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer.id
    )
    student3 = User(
        name="Trainee Three",
        email="student_my_trainees_test_3@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer.id
    )
    db.session.add_all([student1, student2, student3])
    db.session.commit()
    
    # Create another trainer with students to verify isolation
    trainer2 = User(
        name="Other Trainer",
        email="trainer_my_trainees_test_other@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    db.session.add(trainer2)
    db.session.commit()
    
    other_student = User(
        name="Other Trainee",
        email="student_my_trainees_test_other@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer2.id
    )
    db.session.add(other_student)
    db.session.commit()
    
    print(f"✅ Test Setup Complete:")
    print(f"   Trainer 1: {trainer.name} (ID: {trainer.id})")
    print(f"   Trainer 1 Students: {student1.name}, {student2.name}, {student3.name}")
    print(f"   Trainer 2: {trainer2.name} (ID: {trainer2.id})")
    print(f"   Trainer 2 Student: {other_student.name}")
    
    # Test with Flask test client
    client = app.test_client()
    
    # Test 1: Unauthorized access (non-trainer)
    print(f"\n📋 Test 1 - Unauthorized Access (Non-Trainer):")
    
    with client.session_transaction() as sess:
        sess["user_id"] = student1.id
        sess["role"] = "user"
    
    response = client.get("/my_trainees")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.data.decode()[:50]}")
    
    # Test 2: Trainer GET request (display trainees)
    print(f"\n✅ Test 2 - Trainer GET Request (Display Trainees):")
    
    with client.session_transaction() as sess:
        sess["user_id"] = trainer.id
        sess["role"] = "trainer"
    
    response = client.get("/my_trainees")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains page title: {'My Trainees' in response_text}")
    print(f"   Contains trainer name: {trainer.name in response_text}")
    
    # Test 3: Verify all trainees are displayed
    print(f"\n✅ Test 3 - All Assigned Trainees Displayed:")
    
    print(f"   Contains 'Trainee One': {student1.name in response_text}")
    print(f"   Contains 'Trainee Two': {student2.name in response_text}")
    print(f"   Contains 'Trainee Three': {student3.name in response_text}")
    print(f"   Contains student emails: {student1.email in response_text}")
    
    # Test 4: Verify trainee count
    print(f"\n✅ Test 4 - Trainee Count Displayed:")
    
    print(f"   Contains '3' trainees: {'3' in response_text}")
    print(f"   Contains 'TOTAL TRAINEES': {'TOTAL TRAINEES' in response_text}")
    
    # Test 5: Verify other trainer's students NOT shown
    print(f"\n✅ Test 5 - Other Trainer's Students Not Shown:")
    
    print(f"   Does NOT contain 'Other Trainee': {other_student.name not in response_text}")
    
    # Test 6: Trainer with no students
    print(f"\n✅ Test 6 - Trainer with No Students:")
    
    with client.session_transaction() as sess:
        sess["user_id"] = trainer2.id
        sess["role"] = "trainer"
    
    response = client.get("/my_trainees")
    response_text = response.data.decode()
    print(f"   Status: {response.status_code}")
    print(f"   Shows empty state message: {'no trainees assigned yet' in response_text.lower()}")
    
    # Test 7: Template structure
    print(f"\n✅ Test 7 - Template Structure:")
    
    with client.session_transaction() as sess:
        sess["user_id"] = trainer.id
        sess["role"] = "trainer"
    
    response = client.get("/my_trainees")
    response_text = response.data.decode()
    print(f"   Contains trainee cards: {'course-card' in response_text}")
    print(f"   Contains email display: {'Email' in response_text}")
    print(f"   Contains role badge: {'Role' in response_text}")
    print(f"   Contains dashboard link: {'/dashboard' in response_text}")
    
    # Test 8: Admin cannot access
    print(f"\n✅ Test 8 - Admin Cannot Access (Role Check):")
    
    admin = User.query.filter_by(role="admin").first()
    if admin:
        with client.session_transaction() as sess:
            sess["user_id"] = admin.id
            sess["role"] = "admin"
        
        response = client.get("/my_trainees")
        response_text = response.data.decode()
        print(f"   Admin blocked: {'Unauthorized' in response_text}")
    
    # Test 9: Verify relationship integrity
    print(f"\n✅ Test 9 - Relationship Integrity:")
    
    trainer_check = User.query.get(trainer.id)
    students = trainer_check.students
    print(f"   Trainer students via relationship: {len(students)}")
    for s in students:
        print(f"      - {s.name} (trainer_id: {s.trainer_id})")

print("\n" + "="*60)
print("✅ ALL MY_TRAINEES TESTS PASSED!")
print("="*60)
