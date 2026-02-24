import sys
import os
sys.path.insert(0, os.getcwd())

from app import app, db, User, Course, Note

# Test the upload_note route
with app.app_context():
    # Create test data
    test_user = User.query.filter_by(email="trainer@test.com").first()
    if not test_user:
        test_user = User(
            name="Test Trainer",
            email="trainer@test.com",
            password="hashed_password_here",
            role="trainer"
        )
        db.session.add(test_user)
        db.session.commit()
        print("✅ Created test trainer user")
    
    test_course = Course.query.filter_by(title="Test Course").first()
    if not test_course:
        test_course = Course(
            title="Test Course",
            description="A test course for note upload"
        )
        db.session.add(test_course)
        db.session.commit()
        print("✅ Created test course")
    
    # Test the route with Flask test client
    client = app.test_client()
    
    # Test 1: Unauthorized access (no session)
    response = client.get(f"/upload_note/{test_course.id}")
    print(f"\n📋 Test 1 - Unauthorized Access: {response.status_code}")
    print(f"   Response: {response.data.decode()[:100]}")
    
    # Test 2: Access as trainer (simulate session)
    with client.session_transaction() as sess:
        sess["user_id"] = test_user.id
        sess["role"] = "trainer"
        sess["name"] = "Test Trainer"
    
    response = client.get(f"/upload_note/{test_course.id}")
    print(f"\n✅ Test 2 - Trainer GET Access: {response.status_code}")
    print(f"   Content-Type: {response.content_type}")
    print(f"   Contains form: {'textarea' in response.data.decode()}")
    
    # Test 3: Submit a note
    data = {
        "content": "This is a test note for the course.\n\nIt contains important information."
    }
    response = client.post(f"/upload_note/{test_course.id}", data=data)
    print(f"\n✅ Test 3 - POST Note: {response.status_code}")
    print(f"   Contains success message: {'Successfully' in response.data.decode() or 'Note' in response.data.decode()}")
    
    # Test 4: Verify note was created
    note = Note.query.filter_by(course_id=test_course.id, trainer_id=test_user.id).first()
    if note:
        print(f"\n✅ Test 4 - Note Created in Database")
        print(f"   Note ID: {note.id}")
        print(f"   Content: {note.content[:50]}...")
        print(f"   Created: {note.created_at}")
    else:
        print(f"\n❌ Test 4 - Note not found in database")
    
    # Test 5: Get notes (should show existing notes)
    response = client.get(f"/upload_note/{test_course.id}")
    print(f"\n✅ Test 5 - GET with existing notes: {response.status_code}")
    print(f"   Contains existing notes: {'existing_notes' in response.data.decode() or 'Your Notes' in response.data.decode()}")
    
    # Test 6: Invalid course
    response = client.get(f"/upload_note/99999")
    print(f"\n📋 Test 6 - Invalid Course: {response.status_code}")
    print(f"   Response: {response.data.decode()[:50]}")

print("\n" + "="*60)
print("✅ All tests completed!")
print("="*60)
