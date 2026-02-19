from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models.user import User
from sqlalchemy import text

def delete_all_users():
    db: Session = SessionLocal()
    try:
        print("Deleting all users...")
        # Delete all users
        num_deleted = db.query(User).delete()
        db.commit()
        print(f"Successfully deleted {num_deleted} users.")
        
        # Optional: Reset auto-increment
        # db.execute(text("ALTER TABLE users AUTO_INCREMENT = 1"))
        # db.commit()
        
    except Exception as e:
        print(f"Error deleting users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_users()
