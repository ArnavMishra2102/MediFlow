
from getpass import getpass

from pwdlib import PasswordHash

from backend.app.database import SessionLocal
from backend.app.models import User


def create_admin():

    db = SessionLocal()

    try:
        print("\n===== MediFlow Admin Setup =====\n")

        full_name = input("Admin full name: ").strip()
        email = input("Admin email: ").strip().lower()

        if not full_name or not email:
            print("Name and email are required.")
            return

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("An account with this email already exists.")
            return

        password = getpass("Enter admin password: ")
        confirm_password = getpass("Confirm admin password: ")

        if len(password) < 8:
            print("Password must contain at least 8 characters.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        hashed_password = PasswordHash.recommended().hash(password)

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            role="admin",
        )

        db.add(admin)
        db.commit()

        print("\nAdmin account created successfully!")
        print(f"Email: {email}")
        print("Role: admin")

    except Exception as error:
        db.rollback()
        print(f"Error creating admin: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
