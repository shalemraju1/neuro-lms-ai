from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from ai_engine import enhance_script, summarize_pdf
from risk_model import calculate_risk
import os

app = Flask(__name__)
app.secret_key = "secretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
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

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    course_id = db.Column(db.Integer)
    score = db.Column(db.Float)
    attempts = db.Column(db.Integer)
    time_taken = db.Column(db.Float)
    risk_score = db.Column(db.Float)

# =====================
# ROUTES
# =====================

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(email=email, password=password).first()

    if user:
        session["user_id"] = user.id
        session["role"] = user.role
        return redirect("/dashboard")

    return "Invalid credentials"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/")

    courses = Course.query.all()

    return render_template(
        "dashboard.html",
        role=session.get("role"),
        courses=courses
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

    return render_template("create_course.html")

@app.route("/risk_dashboard")
def risk_dashboard():

    if session.get("role") != "admin":
        return "Unauthorized Access"

    records = UserProgress.query.all()

    output = "<h2>AI Risk Dashboard</h2><hr>"

    for r in records:
        if r.risk_score < 40:
            level = "LOW"
        elif r.risk_score < 70:
            level = "MEDIUM"
        else:
            level = "HIGH"

        output += f"""
        User ID: {r.user_id}<br>
        Course ID: {r.course_id}<br>
        Score: {r.score}<br>
        Risk Score: {r.risk_score}%<br>
        Risk Level: <b>{level}</b>
        <hr>
        """

    return output

# =====================
# TRAINER ROUTES
# =====================

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

# =====================
# USER ROUTES
# =====================

@app.route("/take_quiz/<int:course_id>", methods=["GET", "POST"])
def take_quiz(course_id):

    if session.get("role") != "user":
        return "Unauthorized Access"

    if request.method == "POST":
        score = float(request.form["score"])
        attempts = int(request.form["attempts"])
        time_taken = float(request.form["time_taken"])

        risk = calculate_risk(score, attempts, time_taken)

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

        return f"<h3>Your Risk Score: {risk}%</h3>"

    return """
        <h2>Take Quiz</h2>
        <form method="POST">
            Score: <input type="number" name="score"><br><br>
            Attempts: <input type="number" name="attempts"><br><br>
            Time Taken (sec): <input type="number" name="time_taken"><br><br>
            <button type="submit">Submit</button>
        </form>
    """

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
                    password=password,
                    role=role
                ))

        db.session.commit()

    app.run(debug=True)