"""
Migration: Add missing columns to photos table
- category VARCHAR(50) DEFAULT 'General'
- is_sensitive BOOLEAN DEFAULT FALSE
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text

def column_exists(conn, table, column):
    result = conn.execute(text(
        f"SELECT COUNT(*) FROM information_schema.columns "
        f"WHERE table_schema = DATABASE() AND table_name = :table AND column_name = :column"
    ), {"table": table, "column": column})
    return result.scalar() > 0

def run_migration():
    with engine.connect() as conn:
        # Add 'category' column if missing
        if not column_exists(conn, "photos", "category"):
            print("Adding 'category' column to photos table...")
            conn.execute(text(
                "ALTER TABLE photos ADD COLUMN category VARCHAR(50) DEFAULT 'General'"
            ))
            conn.commit()
            print("  ✓ 'category' column added.")
        else:
            print("  ✓ 'category' column already exists, skipping.")

        # Add 'is_sensitive' column if missing
        if not column_exists(conn, "photos", "is_sensitive"):
            print("Adding 'is_sensitive' column to photos table...")
            conn.execute(text(
                "ALTER TABLE photos ADD COLUMN is_sensitive BOOLEAN DEFAULT FALSE"
            ))
            conn.commit()
            print("  ✓ 'is_sensitive' column added.")
        else:
            print("  ✓ 'is_sensitive' column already exists, skipping.")

        # Add 'vector_embedding' column if missing (JSON type)
        if not column_exists(conn, "photos", "vector_embedding"):
            print("Adding 'vector_embedding' column to photos table...")
            conn.execute(text(
                "ALTER TABLE photos ADD COLUMN vector_embedding JSON NULL"
            ))
            conn.commit()
            print("  ✓ 'vector_embedding' column added.")
        else:
            print("  ✓ 'vector_embedding' column already exists, skipping.")

    print("\nMigration complete!")

if __name__ == "__main__":
    run_migration()
