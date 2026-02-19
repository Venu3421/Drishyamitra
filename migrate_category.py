from sqlalchemy import create_engine, text
from backend.database import DATABASE_URL

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE photos ADD COLUMN category VARCHAR(50) DEFAULT 'General'"))
            print("Successfully added 'category' column to photos table.")
        except Exception as e:
            print(f"Migration failed (might already exist): {e}")

if __name__ == "__main__":
    migrate()
