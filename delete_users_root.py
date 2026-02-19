import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models.user import User
from sqlalchemy import text

def delete_all_users():
    db = SessionLocal()
    try:
        print("Deleting all users...")
        # Check count before
        count = db.query(User).count()
        print(f"User count before: {count}")

        # Delete all users
        db.query(User).delete()
        db.commit()
        
        # Check count after
        count_after = db.query(User).count()
        print(f"User count after: {count_after}")
        print("Successfully deleted users.")
        
    except Exception as e:
        print(f"Error deleting users: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_users()
