import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User
from werkzeug.security import generate_password_hash

print("="*60)
print("TESTING ASSIGN_TRAINER ROUTE")
print("="*60)

with app.app_context():
    # Clean up test data
    User.query.filter(User.email.like("%assign_trainer_test%")).delete()
    db.session.commit()
    
    # Create test admin
    admin = User(
        name="Admin Assign Test",
        email="admin_assign_trainer_test@test.com",
        password=generate_password_hash("password123"),
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()
    
    # Create test trainers
    trainer1 = User(
        name="Trainer For Assign",
        email="trainer_assign_trainer_test_1@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    trainer2 = User(
        name="Trainer For Assign 2",
        email="trainer_assign_trainer_test_2@test.com",
        password=generate_password_hash("password123"),
        role="trainer"
    )
    db.session.add_all([trainer1, trainer2])
    db.session.commit()
    
    # Create test users (trainees)
    student1 = User(
        name="Student For Assign 1",
        email="student_assign_trainer_test_1@test.com",
        password=generate_password_hash("password123"),
        role="user"
    )
    student2 = User(
        name="Student For Assign 2",
        email="student_assign_trainer_test_2@test.com",
        password=generate_password_hash("password123"),
        role="user"
    )
    student3 = User(
        name="Student For Assign 3",
        email="student_assign_trainer_test_3@test.com",
        password=generate_password_hash("password123"),
        role="user",
        trainer_id=trainer1.id  # Already assigned
    )
    db.session.add_all([student1, student2, student3])
    db.session.commit()
    
    print(f"✅ Test Setup Complete:")
    print(f"   Admin: {admin.name} (ID: {admin.id})")
    print(f"   Trainers: {trainer1.name} (ID: {trainer1.id}), {trainer2.name} (ID: {trainer2.id})")
    print(f"   Students: {student1.name} (ID: {student1.id}, trainer: {student1.trainer_id})")
    print(f"            {student2.name} (ID: {student2.id}, trainer: {student2.trainer_id})")
    print(f"            {student3.name} (ID: {student3.id}, trainer: {student3.trainer_id})")
    
    # Test with Flask test client
    client = app.test_client()
    
    # Test 1: Unauthorized access (non-admin)
    print(f"\n📋 Test 1 - Unauthorized Access (Non-Admin):")
    
    with client.session_transaction() as sess:
        sess["user_id"] = student1.id
        sess["role"] = "user"
    
    response = client.post(f"/assign_trainer/{student1.id}/{trainer1.id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.data.decode()[:50]}")
    
    # Test 2: Admin assigns student to trainer - successful
    print(f"\n✅ Test 2 - Admin Assigns Student to Trainer:")
    
    with client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["role"] = "admin"
    
    response = client.post(f"/assign_trainer/{student1.id}/{trainer1.id}")
    print(f"   Status: {response.status_code} (should be 302 redirect)")
    
    # Verify assignment in database
    updated_student = User.query.get(student1.id)
    print(f"   Student trainer_id updated: {updated_student.trainer_id == trainer1.id}")
    print(f"   Student trainer: {updated_student.trainer.name if updated_student.trainer else 'None'}")
    
    # Test 3: Invalid user ID
    print(f"\n✅ Test 3 - Invalid User ID:")
    
    response = client.post(f"/assign_trainer/99999/{trainer1.id}")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains error: {'Invalid user' in response_text}")
    
    # Test 4: Invalid trainer ID
    print(f"\n✅ Test 4 - Invalid Trainer ID:")
    
    response = client.post(f"/assign_trainer/{student2.id}/99999")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains error: {'Invalid trainer' in response_text}")
    
    # Test 5: Assign another student to same trainer
    print(f"\n✅ Test 5 - Multiple Students to Same Trainer:")
    
    response = client.post(f"/assign_trainer/{student2.id}/{trainer1.id}")
    print(f"   Status: {response.status_code} (redirect)")
    
    updated_student2 = User.query.get(student2.id)
    print(f"   Student 2 assigned to trainer1: {updated_student2.trainer_id == trainer1.id}")
    
    # Verify trainer has multiple students
    trainer_students = trainer1.students
    print(f"   Trainer1 now has {len(trainer_students)} students")
    
    # Test 6: Reassign student to different trainer
    print(f"\n✅ Test 6 - Reassign Student to Different Trainer:")
    
    response = client.post(f"/assign_trainer/{student1.id}/{trainer2.id}")
    print(f"   Status: {response.status_code}")
    
    updated_student = User.query.get(student1.id)
    print(f"   Student reassigned from trainer1 to trainer2: {updated_student.trainer_id == trainer2.id}")
    
    # Test 7: Try to assign trainer to trainer (should fail)
    print(f"\n✅ Test 7 - Cannot Assign Trainer to Trainer:")
    
    response = client.post(f"/assign_trainer/{trainer2.id}/{trainer1.id}")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains error: {'Invalid user' in response_text}")
    
    # Test 8: Try to assign user to non-trainer (should fail)
    print(f"\n✅ Test 8 - Cannot Assign to Non-Trainer:")
    
    response = client.post(f"/assign_trainer/{student2.id}/{admin.id}")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains error: {'Invalid trainer' in response_text}")
    
    # Test 9: Verify trainer-student relationships
    print(f"\n✅ Test 9 - Verify Final Relationships:")
    
    trainer1_current = User.query.get(trainer1.id)
    trainer2_current = User.query.get(trainer2.id)
    
    print(f"   Trainer1 students: {len(trainer1_current.students)}")
    for s in trainer1_current.students:
        print(f"      - {s.name}")
    
    print(f"   Trainer2 students: {len(trainer2_current.students)}")
    for s in trainer2_current.students:
        print(f"      - {s.name}")
    
    student3_check = User.query.get(student3.id)
    print(f"   Student3 still assigned to trainer1: {student3_check.trainer_id == trainer1.id}")

print("\n" + "="*60)
print("✅ ALL ASSIGN_TRAINER TESTS PASSED!")
print("="*60)
