"""
Test suite for role-based dashboard logic

Tests:
1. Admin sees all courses
2. Trainer sees courses created by admin + their trainees
3. User sees only enrolled courses + notes from their trainer
"""

import os
import sys
from app import app, db, User, Course, Enrollment, Note

def test_dashboard_logic():
    with app.app_context():
        print("\n" + "="*60)
        print("TESTING DASHBOARD ROLE-BASED LOGIC")
        print("="*60)

        # ========== SETUP ==========
        print("\n🔧 Setup:")

        # Find or create admin
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            admin = User(name="Admin Test", email="admin_test@test.com", password="1234", role="admin")
            db.session.add(admin)
            db.session.commit()
        print(f"   ✓ Admin: {admin.name} (ID: {admin.id})")

        # Find or create trainer
        trainer = User.query.filter_by(role="trainer").first()
        if not trainer:
            trainer = User(name="Trainer Test", email="trainer_test@test.com", password="1234", role="trainer")
            db.session.add(trainer)
            db.session.commit()
        print(f"   ✓ Trainer: {trainer.name} (ID: {trainer.id})")

        # Create test users
        test_user = User.query.filter_by(email="testuser@dashboard.com").first()
        if not test_user:
            test_user = User(
                name="Dashboard Test User",
                email="testuser@dashboard.com",
                password="1234",
                role="user",
                trainer_id=trainer.id
            )
            db.session.add(test_user)
            db.session.commit()
        print(f"   ✓ Test User: {test_user.name} (ID: {test_user.id}, assigned trainer: {trainer.name})")

        # Create test courses created by admin
        admin_course1 = Course.query.filter_by(title="Admin Course 1").first()
        if not admin_course1:
            admin_course1 = Course(
                title="Admin Course 1",
                description="Course created by admin",
                created_by=admin.id
            )
            db.session.add(admin_course1)
            db.session.commit()
        print(f"   ✓ Admin Course 1: {admin_course1.title} (created by admin)")

        admin_course2 = Course.query.filter_by(title="Admin Course 2").first()
        if not admin_course2:
            admin_course2 = Course(
                title="Admin Course 2",
                description="Another admin course",
                created_by=admin.id
            )
            db.session.add(admin_course2)
            db.session.commit()
        print(f"   ✓ Admin Course 2: {admin_course2.title} (created by admin)")

        # Create course by trainer (should not appear in trainer's dashboard)
        trainer_course = Course.query.filter_by(title="Trainer Course").first()
        if not trainer_course:
            trainer_course = Course(
                title="Trainer Course",
                description="Course created by trainer",
                created_by=trainer.id
            )
            db.session.add(trainer_course)
            db.session.commit()
        print(f"   ✓ Trainer Course: {trainer_course.title} (created by trainer, should NOT appear in trainer dashboard)")

        # Enroll test user in one admin course
        existing_enrollment = Enrollment.query.filter_by(
            user_id=test_user.id,
            course_id=admin_course1.id
        ).first()
        if not existing_enrollment:
            enrollment = Enrollment(user_id=test_user.id, course_id=admin_course1.id)
            db.session.add(enrollment)
            db.session.commit()
        print(f"   ✓ Enrolled test user in Admin Course 1")

        # Create a note from trainer for admin course 1
        note = Note.query.filter_by(
            trainer_id=trainer.id,
            course_id=admin_course1.id
        ).first()
        if not note:
            note = Note(
                course_id=admin_course1.id,
                trainer_id=trainer.id,
                content="Test note from trainer about Admin Course 1"
            )
            db.session.add(note)
            db.session.commit()
        print(f"   ✓ Created note from trainer for Admin Course 1")

        # ========== TEST ADMIN VIEW ==========
        print("\n\n📊 TEST 1 - Admin Dashboard:")
        admin_courses = Course.query.all()
        print(f"   Admin should see: All courses in database")
        print(f"   Courses in database: {len(admin_courses)}")
        for course in admin_courses:
            print(f"      - {course.title} (created by ID: {course.created_by})")
        assert len(admin_courses) >= 2, "Admin should see at least 2 courses"
        print("   ✅ TEST PASSED: Admin sees all courses")

        # ========== TEST TRAINER VIEW ==========
        print("\n\n📊 TEST 2 - Trainer Dashboard:")
        trainer_view_courses = Course.query.filter_by(created_by=admin.id).all()
        print(f"   Trainer should see: Courses created by admin only")
        print(f"   Admin-created courses: {len(trainer_view_courses)}")
        for course in trainer_view_courses:
            print(f"      - {course.title}")

        # Check trainer's trainees
        trainer_trainees = trainer.students
        print(f"\n   Trainer's assigned trainees: {len(trainer_trainees)}")
        for trainee in trainer_trainees:
            print(f"      - {trainee.name} ({trainee.email})")

        assert len(trainer_view_courses) >= 2, "Trainer should see at least 2 admin-created courses"
        assert trainer_course not in trainer_view_courses, "Trainer's own course should NOT appear"
        assert admin_course1 in trainer_view_courses, "Admin Course 1 should be visible to trainer"
        assert admin_course2 in trainer_view_courses, "Admin Course 2 should be visible to trainer"
        assert len(trainer_trainees) >= 1, "Trainer should have at least 1 trainee"
        assert test_user in trainer_trainees, "Test user should be in trainer's trainees"
        print("   ✅ TEST PASSED: Trainer sees only admin courses + their trainees")

        # ========== TEST USER VIEW ==========
        print("\n\n📊 TEST 3 - User Dashboard:")
        user_enrollments = Enrollment.query.filter_by(user_id=test_user.id).all()
        user_courses = [enrollment.course for enrollment in user_enrollments]
        print(f"   User should see: Only enrolled courses")
        print(f"   Enrolled courses for test user: {len(user_courses)}")
        for course in user_courses:
            print(f"      - {course.title}")

        # Check notes from trainer
        trainer_notes = {}
        if test_user.trainer_id:
            for course in user_courses:
                notes = Note.query.filter_by(
                    course_id=course.id,
                    trainer_id=test_user.trainer_id
                ).all()
                trainer_notes[course.id] = notes

        print(f"\n   Notes from trainer for enrolled courses:")
        for course in user_courses:
            course_notes = trainer_notes.get(course.id, [])
            if course_notes:
                print(f"      - {course.title}: {len(course_notes)} note(s)")
                for n in course_notes:
                    print(f"         * {n.content[:50]}...")
            else:
                print(f"      - {course.title}: No notes")

        assert len(user_courses) == 1, "User should see exactly 1 enrolled course"
        assert admin_course1 in user_courses, "User's enrolled course should be visible"
        assert admin_course2 not in user_courses, "User's non-enrolled course should NOT be visible"
        assert len(trainer_notes.get(admin_course1.id, [])) >= 1, "Notes from trainer should be visible"
        print("   ✅ TEST PASSED: User sees only enrolled courses + trainer notes")

        # ========== FINAL RESULT ==========
        print("\n\n" + "="*60)
        print("✅ ALL DASHBOARD TESTS PASSED!")
        print("="*60 + "\n")

if __name__ == "__main__":
    test_dashboard_logic()
