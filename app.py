from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from ai_engine import ai_engine, enhance_script, summarize_pdf
from risk_model import risk_model, calculate_risk
import os
from werkzeug.security import generate_password_hash, check_password_hash
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_change_in_production')

import os
# ... existing imports ...

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), "instance", "database.db")}'
db = SQLAlchemy(app)

# =====================
# DATABASE MODELS
# =====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(50))
    trainer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationship to trainer (for users with role "user")
    trainer = db.relationship('User', remote_side=[id], backref='students')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    created_by = db.Column(db.Integer)

class Script(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer)
    original_script = db.Column(db.Text)
    ai_script = db.Column(db.Text)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='notes')
    trainer = db.relationship('User', backref='notes', foreign_keys=[trainer_id])

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='quizzes')
    trainer = db.relationship('User', backref='quizzes', foreign_keys=[trainer_id])

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    score = db.Column(db.Float)
    attempts = db.Column(db.Integer)
    time_taken = db.Column(db.Float)
    risk_score = db.Column(db.Float)
    
    # Relationship to Course
    course = db.relationship('Course', backref='user_progress')

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

# =====================
# ROUTES
# =====================

@app.route("/")
def home():
    return render_template("login.html", session=session)

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session["user_id"] = user.id
        session["role"] = user.role
        return redirect("/dashboard")

    return "Invalid credentials"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        
        if User.query.filter_by(email=email).first():
            return "Email already exists"
        
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="user"
        )
        
        db.session.add(user)
        db.session.commit()
        
        return redirect("/")
    
    return render_template("register.html", session=session)
@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/")

    role = session.get("role")
    current_user = User.query.get(session["user_id"])
    courses = []
    course_notes = {}
    trainees = []
    stats = {}
    risk_scores = []
    admin_email = "admin@neurolms.com"

    if role == "admin":
        # Admin sees all courses
        courses = Course.query.all()
        course_notes = {}
        
        # Admin stats
        stats = {
            'total_courses': len(courses),
            'total_trainers': User.query.filter_by(role="trainer").count(),
            'total_users': User.query.filter_by(role="user").count()
        }

    elif role == "trainer":
        # Trainer sees courses created by admin
        admin_user = User.query.filter_by(role="admin").first()
        admin_id = admin_user.id if admin_user else None
        
        if admin_id:
            courses = Course.query.filter_by(created_by=admin_id).all()
        
        # Get trainees assigned to this trainer
        trainees = current_user.students if current_user else []
        course_notes = {}
        
        # Trainer stats
        stats = {
            'total_trainees': len(trainees),
            'available_courses': len(courses),
            'total_quizzes': Quiz.query.filter_by(trainer_id=session["user_id"]).count(),
            'total_notes': Note.query.filter_by(trainer_id=session["user_id"]).count()
        }

    elif role == "user":
        # User sees all available courses
        all_courses = Course.query.all()
        
        # Get user's enrollments
        enrollments = Enrollment.query.filter_by(user_id=session["user_id"]).all()
        enrolled_course_ids = {enrollment.course_id for enrollment in enrollments}
        enrolled_courses = [enrollment.course for enrollment in enrollments]
        
        # Prepare course data with enrollment status
        courses_with_status = []
        for course in all_courses:
            is_enrolled = course.id in enrolled_course_ids
            courses_with_status.append({
                'course': course,
                'is_enrolled': is_enrolled
            })
        courses = courses_with_status
        
        # Get user's trainer
        trainer_id = current_user.trainer_id if current_user else None
        
        # Get notes from trainer for enrolled courses
        course_notes = {}
        if trainer_id:
            for enrolled_course in enrolled_courses:
                course_notes[enrolled_course.id] = Note.query.filter_by(
                    course_id=enrolled_course.id,
                    trainer_id=trainer_id
                ).all()
        
        # User stats
        total_quizzes = sum(len(Quiz.query.filter_by(course_id=course['course'].id).all()) for course in courses)
        user_progress = UserProgress.query.filter_by(user_id=session["user_id"]).all()
        
        # Get user's risk scores (previous quiz attempts)
        risk_scores = UserProgress.query.filter_by(user_id=session["user_id"]).order_by(UserProgress.id.desc()).all()
        
        # Get admin contact info
        admin_user = User.query.filter_by(role="admin").first()
        admin_email = admin_user.email if admin_user else "admin@neurolms.com"
        
        stats = {
            'enrolled_courses': len(enrolled_courses),
            'total_quizzes': total_quizzes,
            'quizzes_taken': len(user_progress),
            'trainer_name': User.query.get(trainer_id).name if trainer_id else 'Not assigned'
        }

    return render_template(
        "dashboard.html",
        role=role,
        courses=courses,
        course_notes=course_notes,
        trainees=trainees,
        stats=stats,
        risk_scores=risk_scores,
        admin_email=admin_email,
        session=session
    )

# =====================
# ADMIN ROUTES
# =====================

@app.route("/create_course", methods=["GET", "POST"])
def create_course():

    if session.get("role") != "admin":
        return "Unauthorized Access"

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        course = Course(
            title=title,
            description=description,
            created_by=session["user_id"]
        )

        db.session.add(course)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("create_course.html", session=session)

@app.route("/create_trainer", methods=["GET", "POST"])
def create_trainer():

    if session.get("role") != "admin":
        return "Unauthorized Access"

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # Validation
        if not name or not email or not password:
            return "All fields are required"

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already registered"

        # Create trainer
        trainer = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="trainer"
        )

        db.session.add(trainer)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("create_trainer.html", session=session)

@app.route("/assign_trainer/<int:user_id>/<int:trainer_id>", methods=["POST"])
def assign_trainer(user_id, trainer_id):

    if session.get("role") != "admin":
        return "Unauthorized Access"

    # Verify user exists and is a trainee (role="user")
    user = User.query.get(user_id)
    if not user or user.role != "user":
        return "Invalid user"

    # Verify trainer exists and is a trainer (role="trainer")
    trainer = User.query.get(trainer_id)
    if not trainer or trainer.role != "trainer":
        return "Invalid trainer"

    # Assign trainer to user
    user.trainer_id = trainer_id
    db.session.commit()

    return redirect("/manage_users")

@app.route("/manage_users")
def manage_users():
    if session.get("role") != "admin":
        return "Unauthorized Access"

    # Get all trainers
    trainers = User.query.filter_by(role="trainer").all()

    # For each trainer, get their assigned students
    trainer_data = []
    for trainer in trainers:
        students = User.query.filter_by(trainer_id=trainer.id, role="user").all()
        trainer_data.append({
            'trainer': trainer,
            'students': students
        })

    # Also get unassigned users (users with no trainer)
    unassigned_users = User.query.filter_by(trainer_id=None, role="user").all()

    return render_template(
        "manage_users.html",
        trainer_data=trainer_data,
        unassigned_users=unassigned_users,
        session=session
    )

@app.route("/risk_dashboard")
def risk_dashboard():

    if session.get("role") != "admin":
        return "Unauthorized Access"

    # Get all trainers
    trainers = User.query.filter_by(role="trainer").all()

    # Build trainer data with their students and progress
    trainer_data = []

    for trainer in trainers:
        trainer_info = {
            "trainer": trainer,
            "students": []
        }

        # Get all students assigned to this trainer
        students = trainer.students

        for student in students:
            # Get all UserProgress records for this student
            progress_records = UserProgress.query.filter_by(user_id=student.id).all()

            for progress in progress_records:
                course = Course.query.get(progress.course_id)

                # Calculate risk level
                if progress.risk_score < 40:
                    risk_level = "LOW"
                elif progress.risk_score < 70:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"

                trainer_info["students"].append({
                    "student_name": student.name,
                    "course_name": course.title if course else "Unknown Course",
                    "score": progress.score,
                    "risk_score": progress.risk_score,
                    "risk_level": risk_level
                })

        if trainer_info["students"]:  # Only add trainer if they have students with progress
            trainer_data.append(trainer_info)

    return render_template(
        "risk_dashboard.html",
        trainer_data=trainer_data,
        session=session
    )

# =====================
# TRAINER ROUTES
# =====================

@app.route("/my_trainees")
def my_trainees():

    if session.get("role") != "trainer":
        return "Unauthorized Access"

    # Get the current trainer
    trainer = User.query.get(session["user_id"])
    if not trainer or trainer.role != "trainer":
        return "Unauthorized Access"

    # Get all students assigned to this trainer
    trainees = trainer.students

    return render_template(
        "my_trainees.html",
        trainer=trainer,
        trainees=trainees,
        session=session
    )

@app.route("/upload_script/<int:course_id>", methods=["GET", "POST"])
def upload_script(course_id):

    if session.get("role") != "trainer":
        return "Unauthorized Access"

    if request.method == "POST":
        script_text = request.form["script"]

        ai_version = enhance_script(script_text)

        new_script = Script(
            course_id=course_id,
            original_script=script_text,
            ai_script=ai_version
        )

        db.session.add(new_script)
        db.session.commit()

        return f"<pre>{ai_version}</pre>"

    return """
        <h2>Upload Script</h2>
        <form method="POST">
            <textarea name="script" rows="10" cols="50"></textarea><br><br>
            <button type="submit">Generate AI Script</button>
        </form>
    """

@app.route("/upload_pdf/<int:course_id>", methods=["GET", "POST"])
def upload_pdf(course_id):

    if session.get("role") != "trainer":
        return "Unauthorized Access"

    if request.method == "POST":
        file = request.files["pdf"]

        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")

            path = os.path.join("uploads", file.filename)
            file.save(path)

            ai_output = summarize_pdf(path)

            return f"<pre>{ai_output}</pre>"

    return """
        <h2>Upload PDF</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="pdf"><br><br>
            <button type="submit">Analyze</button>
        </form>
    """

@app.route("/upload_note/<int:course_id>", methods=["GET", "POST"])
def upload_note(course_id):

    if session.get("role") != "trainer":
        return "Unauthorized Access"

    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return "Course not found"

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        if not content:
            return "Note content cannot be empty"

        # Create note
        note = Note(
            course_id=course_id,
            trainer_id=session["user_id"],
            content=content
        )

        db.session.add(note)
        db.session.commit()

        return render_template(
            "upload_note_success.html",
            course=course,
            note=note,
            session=session
        )

    # Get existing notes for this course by this trainer
    existing_notes = Note.query.filter_by(
        course_id=course_id,
        trainer_id=session["user_id"]
    ).all()

    return render_template(
        "upload_note.html",
        course=course,
        existing_notes=existing_notes,
        session=session
    )

# =====================
# USER ROUTES
# =====================

@app.route("/take_quiz/<int:course_id>", methods=["GET", "POST"])
def take_quiz(course_id):

    if session.get("role") != "user":
        return "Unauthorized Access"

    # Verify user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=session["user_id"],
        course_id=course_id
    ).first()

    if not enrollment:
        return "You are not enrolled in this course"

    course = Course.query.get(course_id)
    if not course:
        return "Course not found"

    if request.method == "POST":
        # Get quizzes for the course
        quizzes = Quiz.query.filter_by(course_id=course_id).all()

        if not quizzes:
            return "No quizzes available for this course"

        # Calculate score by comparing answers
        correct_count = 0
        total_count = len(quizzes)

        for quiz in quizzes:
            # Get user's answer for this quiz
            user_answer = request.form.get(f"answer_{quiz.id}", "").strip()

            # Compare with correct answer (case-insensitive)
            if user_answer.lower() == quiz.correct_answer.lower():
                correct_count += 1

        # Calculate score as percentage
        score = (correct_count / total_count * 100) if total_count > 0 else 0

        # Get attempt count and time taken from form
        attempts = int(request.form.get("attempts", 1))
        time_taken = float(request.form.get("time_taken", 0))

        # Calculate risk
        risk = calculate_risk(score, attempts, time_taken)

        # Store in UserProgress
        progress = UserProgress(
            user_id=session["user_id"],
            course_id=course_id,
            score=score,
            attempts=attempts,
            time_taken=time_taken,
            risk_score=risk
        )

        db.session.add(progress)
        db.session.commit()

        return render_template(
            "quiz_result.html",
            course=course,
            score=score,
            correct_count=correct_count,
            total_count=total_count,
            risk=risk,
            session=session
        )

    # GET: Show quiz form
    quizzes = Quiz.query.filter_by(course_id=course_id).all()

    if not quizzes:
        return "No quizzes available for this course"

    return render_template(
        "take_quiz.html",
        course=course,
        quizzes=quizzes,
        session=session
    )

# =====================
# ADMIN ROUTES
# =====================

@app.route("/admin/trainers_trainees")
def admin_trainers_trainees():
    """Admin view showing all trainers and their assigned trainees"""
    
    if session.get("role") != "admin":
        return "Unauthorized Access"
    
    # Get all trainers
    trainers = User.query.filter_by(role="trainer").all()
    
    # Build trainer data with their trainees
    trainer_data = []
    for trainer in trainers:
        trainer_info = {
            'trainer': trainer,
            'trainees': trainer.students,
            'trainee_count': len(trainer.students)
        }
        trainer_data.append(trainer_info)
    
    return render_template(
        "admin_trainers_trainees.html",
        trainer_data=trainer_data,
        total_trainers=len(trainers),
        session=session
    )

# =====================
# ENROLLMENT ROUTE
# =====================

@app.route("/enroll/<int:course_id>")
def enroll(course_id):
    if not session.get("user_id") or session.get("role") != "user":
        return "Unauthorized Access"

    user_id = session["user_id"]

    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return "Course not found."

    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if existing_enrollment:
        return "You are already enrolled in this course."

    # Create new enrollment
    new_enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.session.add(new_enrollment)
    db.session.commit()

    return redirect("/dashboard")

# =====================
# AUTO USER CREATION
# =====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        users = [
            ("Admin", "admin@test.com", "1234", "admin"),
            ("Trainer", "trainer@test.com", "1234", "trainer"),
            ("Learner", "user@test.com", "1234", "user"),
        ]

        for name, email, password, role in users:
            if not User.query.filter_by(email=email).first():
                db.session.add(User(
                    name=name,
                    email=email,
                    password = generate_password_hash(password),
                    role=role
                ))

        db.session.commit()

    app.run(debug=True)

    # Add secure password hashing system