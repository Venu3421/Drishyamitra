import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models.user import User
from backend.auth_utils import get_password_hash
import secrets

def test_google_user_creation():
    print("Testing Google User Creation Logic...")
    db = SessionLocal()
    try:
        email = "test_google_script@example.com"
        name = "Test Google User"
        
        # Cleanup if exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("Deleting existing test user...")
            db.delete(existing)
            db.commit()
            
        print("Generating password...")
        random_password = secrets.token_urlsafe(16)
        print(f"Password: {random_password}")
        
        print("Hashing password...")
        hashed_password = get_password_hash(random_password)
        print(f"Hash: {hashed_password[:20]}...")
        
        print("Creating User object...")
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=name,
            is_active=True
        )
        
        print("Adding to DB...")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User created successfully with ID: {user.id}")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_google_user_creation()
