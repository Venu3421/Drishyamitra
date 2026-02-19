from sqlalchemy import create_engine, inspect
from backend.database import engine
from backend.models import user, photo, receipt, vault

def check_tables():
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("Tables in database:", tables)
        
        # Explicitly check for expected tables
        expected = ["users", "photos", "receipts", "vault", "faces"]
        missing = [t for t in expected if t not in tables]
        
        if missing:
            print(f"MISSING TABLES: {missing}")
            print("Attempting to create them now...")
            from backend.database import Base
            Base.metadata.create_all(bind=engine)
            print("Creation command sent. Re-checking...")
            tables_after = inspect(engine).get_table_names()
            print("Tables in database now:", tables_after)
        else:
            print("All expected tables exist.")
            
    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    check_tables()
