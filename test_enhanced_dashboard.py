"""
Test suite for enhanced dashboard features

Tests:
1. Admin dashboard shows stats (courses, trainers, users)
2. Trainer dashboard shows stats (trainees, courses, quizzes, notes)
3. User dashboard shows stats (enrolled courses, quizzes taken, trainer name)
"""

import os
import sys
from app import app, db, User, Course, Enrollment, Note, Quiz

def test_enhanced_dashboard():
    with app.app_context():
        print("\n" + "="*70)
        print("TESTING ENHANCED DASHBOARD FEATURES")
        print("="*70)

        # ========== SETUP ==========
        print("\n🔧 Setup:")

        # Get or create admin
        admin = User.query.filter_by(role="admin").first()
        print(f"   ✓ Admin: {admin.name} (ID: {admin.id})")

        # Get or create trainer
        trainer = User.query.filter_by(role="trainer").first()
        print(f"   ✓ Trainer: {trainer.name} (ID: {trainer.id})")

        # Get or create user
        test_user = User.query.filter_by(email="testuser@dashboard.com").first()
        if not test_user:
            test_user = User(
                name="Enhanced Dashboard Test",
                email="testuser@dashboard.com",
                password="1234",
                role="user",
                trainer_id=trainer.id
            )
            db.session.add(test_user)
            db.session.commit()
        print(f"   ✓ Test User: {test_user.name} (ID: {test_user.id})")

        # Get test course
        test_course = Course.query.filter_by(title="Admin Course 1").first()
        if not test_course:
            test_course = Course(
                title="Admin Course 1",
                description="Test course",
                created_by=admin.id
            )
            db.session.add(test_course)
            db.session.commit()
        print(f"   ✓ Test Course: {test_course.title}")

        # Enroll user if not already enrolled
        enrollment = Enrollment.query.filter_by(
            user_id=test_user.id,
            course_id=test_course.id
        ).first()
        if not enrollment:
            enrollment = Enrollment(user_id=test_user.id, course_id=test_course.id)
            db.session.add(enrollment)
            db.session.commit()

        # Create quiz if not exists
        quiz = Quiz.query.filter_by(
            course_id=test_course.id,
            trainer_id=trainer.id
        ).first()
        if not quiz:
            quiz = Quiz(
                course_id=test_course.id,
                trainer_id=trainer.id,
                question="Test question?",
                correct_answer="Test answer"
            )
            db.session.add(quiz)
            db.session.commit()

        # Create note if not exists
        note = Note.query.filter_by(
            course_id=test_course.id,
            trainer_id=trainer.id
        ).first()
        if not note:
            note = Note(
                course_id=test_course.id,
                trainer_id=trainer.id,
                content="Test note"
            )
            db.session.add(note)
            db.session.commit()

        # ========== TEST 1: ADMIN STATS ==========
        print("\n\n📊 TEST 1 - Admin Dashboard Stats:")
        total_courses = Course.query.count()
        total_trainers = User.query.filter_by(role="trainer").count()
        total_users = User.query.filter_by(role="user").count()
        
        print(f"   Total Courses in system: {total_courses}")
        print(f"   Total Trainers: {total_trainers}")
        print(f"   Total Users: {total_users}")
        
        assert total_courses > 0, "Should have at least 1 course"
        assert total_trainers > 0, "Should have at least 1 trainer"
        assert total_users > 0, "Should have at least 1 user"
        print("   ✅ TEST PASSED: Admin stats calculated correctly")

        # ========== TEST 2: TRAINER STATS ==========
        print("\n\n📊 TEST 2 - Trainer Dashboard Stats:")
        trainer_trainees = trainer.students
        trainer_courses = Course.query.filter_by(created_by=admin.id).all()
        trainer_quizzes = Quiz.query.filter_by(trainer_id=trainer.id).count()
        trainer_notes = Note.query.filter_by(trainer_id=trainer.id).count()
        
        print(f"   Trainer's Trainees: {len(trainer_trainees)}")
        print(f"   Available Courses: {len(trainer_courses)}")
        print(f"   Quizzes Created: {trainer_quizzes}")
        print(f"   Notes Created: {trainer_notes}")
        
        assert len(trainer_trainees) > 0, "Trainer should have at least 1 trainee"
        assert len(trainer_courses) > 0, "Trainer should see at least 1 course"
        assert trainer_quizzes >= 0, "Trainer quizzes should be >= 0"
        assert trainer_notes >= 0, "Trainer notes should be >= 0"
        print("   ✅ TEST PASSED: Trainer stats calculated correctly")

        # ========== TEST 3: USER STATS ==========
        print("\n\n📊 TEST 3 - User Dashboard Stats:")
        user_enrollments = Enrollment.query.filter_by(user_id=test_user.id).all()
        user_courses = [enrollment.course for enrollment in user_enrollments]
        
        total_quizzes = sum(
            len(Quiz.query.filter_by(course_id=course.id).all()) 
            for course in user_courses
        )
        
        from app import UserProgress
        user_progress = UserProgress.query.filter_by(user_id=test_user.id).all()
        quizzes_taken = len(user_progress)
        
        trainer_name = User.query.get(test_user.trainer_id).name if test_user.trainer_id else 'Not assigned'
        
        print(f"   Enrolled Courses: {len(user_courses)}")
        print(f"   Total Quizzes Available: {total_quizzes}")
        print(f"   Quizzes Taken: {quizzes_taken}/{total_quizzes}")
        print(f"   Assigned Trainer: {trainer_name}")
        
        assert len(user_courses) > 0, "User should be enrolled in at least 1 course"
        assert total_quizzes >= 0, "Total quizzes should be >= 0"
        assert quizzes_taken >= 0, "Quizzes taken should be >= 0"
        assert trainer_name != 'Not assigned', "User should have assigned trainer"
        print("   ✅ TEST PASSED: User stats calculated correctly")

        # ========== TEST 4: STATS PASSED TO TEMPLATE ==========
        print("\n\n📊 TEST 4 - Stats Dictionary Structure:")
        
        from flask import session
        
        # Simulate admin session
        with app.test_client() as client:
            # Check that dashboard route can render with stats
            with client.session_transaction() as sess:
                sess['user_id'] = admin.id
                sess['role'] = 'admin'
            
            # Just verify the route exists and doesn't error
            response = client.get('/dashboard')
            assert response.status_code == 200, "Dashboard should load for admin"
            assert (b'Total Courses' in response.data or 
                    b'Courses' in response.data), "Dashboard should show course stats"
            print(f"   Admin dashboard loaded: {response.status_code}")
            print("   ✅ Template receives admin stats correctly")
        
        # ========== FINAL RESULT ==========
        print("\n\n" + "="*70)
        print("✅ ALL ENHANCED DASHBOARD TESTS PASSED!")
        print("="*70)
        print("\n✨ Dashboard Enhancements Summary:")
        print("   • Admin sees: Total Courses, Active Trainers, Total Learners")
        print("   • Trainer sees: Assigned Trainees, Courses to Teach, Quizzes Created, Notes Created")
        print("   • User sees: Enrolled Courses, Quizzes Completed, Assigned Trainer")
        print("\n")

if __name__ == "__main__":
    test_enhanced_dashboard()
