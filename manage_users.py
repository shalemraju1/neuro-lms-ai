from app import app, db, User
from werkzeug.security import generate_password_hash
import sys

def create_user(name, email, password, role='user', trainer_id=None):
    with app.app_context():
        if User.query.filter_by(email=email).first():
            print(f"User with email {email} already exists!")
            return False

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            trainer_id=trainer_id
        )

        db.session.add(user)
        db.session.commit()
        print(f"User {name} ({email}) created successfully with role: {role}")
        if trainer_id:
            print(f"  Assigned to trainer ID: {trainer_id}")
        return True

def list_users():
    with app.app_context():
        users = User.query.all()
        print("Current users:")
        for user in users:
            trainer_info = ""
            if user.trainer_id:
                trainer = User.query.get(user.trainer_id)
                if trainer:
                    trainer_info = f" → Trainer: {trainer.name} (ID: {trainer.id})"
            
            student_info = ""
            if user.students:
                student_names = [s.name for s in user.students]
                student_info = f" | Students: {', '.join(student_names)}"
            
            print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}{trainer_info}{student_info}")

def reset_password(email, new_password):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found!")
            return False

        user.password = generate_password_hash(new_password)
        db.session.commit()
        print(f"Password reset for {email}")
        return True

def assign_trainer(user_email, trainer_email):
    """Assign a trainer to a user"""
    with app.app_context():
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"User with email {user_email} not found!")
            return False
        
        trainer = User.query.filter_by(email=trainer_email).first()
        if not trainer:
            print(f"Trainer with email {trainer_email} not found!")
            return False
        
        if trainer.role != 'trainer':
            print(f"User {trainer.name} is not a trainer (role: {trainer.role})")
            return False
        
        user.trainer_id = trainer.id
        db.session.commit()
        print(f"✅ Assigned trainer {trainer.name} to user {user.name}")
        return True

def unassign_trainer(user_email):
    """Remove trainer assignment from a user"""
    with app.app_context():
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"User with email {user_email} not found!")
            return False
        
        if not user.trainer_id:
            print(f"User {user.name} does not have a trainer assigned")
            return False
        
        trainer = User.query.get(user.trainer_id)
        trainer_name = trainer.name if trainer else "Unknown"
        
        user.trainer_id = None
        db.session.commit()
        print(f"✅ Removed trainer {trainer_name} from user {user.name}")
        return True

def get_trainer_students(trainer_email):
    """Get all students assigned to a trainer"""
    with app.app_context():
        trainer = User.query.filter_by(email=trainer_email).first()
        if not trainer:
            print(f"Trainer with email {trainer_email} not found!")
            return False
        
        if trainer.role != 'trainer':
            print(f"User {trainer.name} is not a trainer (role: {trainer.role})")
            return False
        
        students = User.query.filter_by(trainer_id=trainer.id).all()
        
        print(f"\n👨‍🏫 Trainer: {trainer.name} (ID: {trainer.id})")
        if students:
            print(f"📚 Students ({len(students)}):")
            for student in students:
                print(f"  - {student.name} ({student.email})")
        else:
            print("  No students assigned")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_users.py list")
        print("  python manage_users.py create <name> <email> <password> [role]")
        print("  python manage_users.py reset <email> <new_password>")
        print("  python manage_users.py assign_trainer <user_email> <trainer_email>")
        print("  python manage_users.py unassign_trainer <user_email>")
        print("  python manage_users.py get_students <trainer_email>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_users()
    elif command == "create":
        if len(sys.argv) < 5:
            print("Usage: python manage_users.py create <name> <email> <password> [role]")
            sys.exit(1)
        name = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        role = sys.argv[5] if len(sys.argv) > 5 else 'user'
        create_user(name, email, password, role)
    elif command == "reset":
        if len(sys.argv) < 4:
            print("Usage: python manage_users.py reset <email> <new_password>")
            sys.exit(1)
        email = sys.argv[2]
        new_password = sys.argv[3]
        reset_password(email, new_password)
    elif command == "assign_trainer":
        if len(sys.argv) < 4:
            print("Usage: python manage_users.py assign_trainer <user_email> <trainer_email>")
            sys.exit(1)
        user_email = sys.argv[2]
        trainer_email = sys.argv[3]
        assign_trainer(user_email, trainer_email)
    elif command == "unassign_trainer":
        if len(sys.argv) < 3:
            print("Usage: python manage_users.py unassign_trainer <user_email>")
            sys.exit(1)
        user_email = sys.argv[2]
        unassign_trainer(user_email)
    elif command == "get_students":
        if len(sys.argv) < 3:
            print("Usage: python manage_users.py get_students <trainer_email>")
            sys.exit(1)
        trainer_email = sys.argv[2]
        get_trainer_students(trainer_email)
    else:
        print("Unknown command. Use 'list', 'create', 'reset', 'assign_trainer', 'unassign_trainer', or 'get_students'")