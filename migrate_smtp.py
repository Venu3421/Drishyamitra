import sys
import os

# Add the current directory to sys.path to allow imports from backend
sys.path.append(os.getcwd())

from backend.database import SQLALCHEMY_DATABASE_URL as DATABASE_URL
from sqlalchemy import create_engine, text

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN smtp_email VARCHAR(255)"))
            print("Successfully added 'smtp_email' column.")
        except Exception as e:
            print(f"Migration 'smtp_email' failed (might exist): {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN smtp_password VARCHAR(255)"))
            print("Successfully added 'smtp_password' column.")
        except Exception as e:
            print(f"Migration 'smtp_password' failed (might exist): {e}")

if __name__ == "__main__":
    migrate()
