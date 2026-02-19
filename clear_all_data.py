"""
Clears all user data from the DB and deletes all uploaded files.
Safe to run - only deletes app data, not schema.
"""
import sys, shutil, os
sys.path.insert(0, '.')

from backend.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Disable FK checks temporarily (MySQL)
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

    tables = ["faces", "receipts", "vault", "people", "photos", "users"]
    for table in tables:
        result = conn.execute(text(f"DELETE FROM {table}"))
        print(f"  Cleared {table}: {result.rowcount} row(s)")
        # Reset AUTO_INCREMENT so IDs start from 1 again after clearing
        conn.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1"))
        print(f"  Reset AUTO_INCREMENT for {table}")

    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    conn.commit()

print("\nDB cleared.")

# Delete uploaded files
for folder in ["uploads/photos", "uploads/vault", "uploads/receipts"]:
    if os.path.exists(folder):
        count = len(os.listdir(folder))
        shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
        print(f"  Cleared {folder}: {count} file(s) deleted")

print("\nAll done! You can now register a fresh account.")
