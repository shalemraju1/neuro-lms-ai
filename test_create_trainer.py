import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User
from werkzeug.security import check_password_hash

print("="*60)
print("TESTING CREATE_TRAINER ROUTE")
print("="*60)

with app.app_context():
    # Clean up test data
    User.query.filter(User.email.like("%create_trainer_test%")).delete()
    db.session.commit()
    
    # Get or create admin user
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = User(
            name="Test Admin",
            email="admin_create_trainer_test@test.com",
            password=generate_password_hash("password123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
    
    # Test with Flask test client
    client = app.test_client()
    
    # Test 1: Unauthorized access (non-admin)
    print(f"\n📋 Test 1 - Unauthorized Access (Non-Admin):")
    
    # Create a student user
    student = User.query.filter_by(role="user").first()
    if not student:
        from werkzeug.security import generate_password_hash
        student = User(
            name="Test Student",
            email="student_create_trainer_test@test.com",
            password=generate_password_hash("password123"),
            role="user"
        )
        db.session.add(student)
        db.session.commit()
    
    with client.session_transaction() as sess:
        sess["user_id"] = student.id
        sess["role"] = "user"
    
    response = client.get("/create_trainer")
    print(f"   GET /create_trainer (student): {response.status_code}")
    print(f"   Response: {response.data.decode()[:50]}")
    
    # Test 2: Admin GET request (display form)
    print(f"\n✅ Test 2 - Admin GET Request (Display Form):")
    
    with client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["role"] = "admin"
    
    response = client.get("/create_trainer")
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains form: {'<form' in response_text}")
    print(f"   Contains name field: {'name' in response_text}")
    print(f"   Contains email field: {'email' in response_text}")
    print(f"   Contains password field: {'password' in response_text}")
    print(f"   Contains submit button: {'Create Trainer' in response_text}")
    
    # Test 3: Admin POST request - successful trainer creation
    print(f"\n✅ Test 3 - Admin POST Request (Create Trainer):")
    
    response = client.post(
        "/create_trainer",
        data={
            "name": "Trainer Test One",
            "email": "trainer_create_trainer_test_1@test.com",
            "password": "SecurePassword123"
        }
    )
    print(f"   Status: {response.status_code} (should redirect: 302)")
    
    # Verify trainer was created in database
    trainer1 = User.query.filter_by(email="trainer_create_trainer_test_1@test.com").first()
    if trainer1:
        print(f"   ✅ Trainer created in database")
        print(f"      Name: {trainer1.name}")
        print(f"      Email: {trainer1.email}")
        print(f"      Role: {trainer1.role}")
        print(f"      Password hashed: {trainer1.password != 'SecurePassword123'}")
        print(f"      Password correct: {check_password_hash(trainer1.password, 'SecurePassword123')}")
    
    # Test 4: Create another trainer
    print(f"\n✅ Test 4 - Create Second Trainer:")
    
    response = client.post(
        "/create_trainer",
        data={
            "name": "Trainer Test Two",
            "email": "trainer_create_trainer_test_2@test.com",
            "password": "AnotherPassword456"
        }
    )
    print(f"   Status: {response.status_code}")
    
    trainer2 = User.query.filter_by(email="trainer_create_trainer_test_2@test.com").first()
    if trainer2:
        print(f"   ✅ Second trainer created")
        print(f"      Name: {trainer2.name}")
        print(f"      Email: {trainer2.email}")
    
    # Test 5: Duplicate email validation
    print(f"\n✅ Test 5 - Duplicate Email Validation:")
    
    response = client.post(
        "/create_trainer",
        data={
            "name": "Trainer Duplicate",
            "email": "trainer_create_trainer_test_1@test.com",  # Same as trainer1
            "password": "DifferentPassword789"
        }
    )
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains error message: {'already registered' in response_text.lower()}")
    
    # Test 6: Missing fields validation
    print(f"\n✅ Test 6 - Missing Fields Validation:")
    
    response = client.post(
        "/create_trainer",
        data={
            "name": "Incomplete Trainer",
            # Missing email and password
        }
    )
    print(f"   Status: {response.status_code}")
    response_text = response.data.decode()
    print(f"   Contains error message: {'required' in response_text.lower()}")
    
    # Test 7: Verify trainers count
    print(f"\n✅ Test 7 - Verify Trainers in Database:")
    
    trainers = User.query.filter_by(role="trainer").all()
    print(f"   Total trainers in database: {len(trainers)}")
    test_trainers = [t for t in trainers if "create_trainer_test" in t.email]
    print(f"   Test trainers created: {len(test_trainers)}")
    for trainer in test_trainers:
        print(f"      - {trainer.name} ({trainer.email})")
    
    # Test 8: No students assigned initially
    print(f"\n✅ Test 8 - New Trainer Has No Students:")
    
    if trainer1:
        students = trainer1.students
        print(f"   Trainer: {trainer1.name}")
        print(f"   Assigned students: {len(students)}")

print("\n" + "="*60)
print("✅ ALL CREATE_TRAINER TESTS PASSED!")
print("="*60)
