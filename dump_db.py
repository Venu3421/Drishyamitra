import sqlite3
import os

db_path = "sql_app.db"
if not os.path.exists(db_path):
    print(f"DB file {db_path} not found.")
    files = [f for f in os.listdir('.') if f.endswith('.db')]
    if files:
        print(f"Found DB files: {files}")
        db_path = files[0]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n--- RECEIPTS ---")
cursor.execute("SELECT id, merchant, amount, date, category FROM receipts")
rows = cursor.fetchall()
for r in rows:
    print(r)

print("\n--- FACES ---")
cursor.execute("SELECT id, photo_id, person_id FROM faces")
rows = cursor.fetchall()
for r in rows:
    print(r)

print("\n--- PHOTOS ---")
cursor.execute("SELECT id, filename, category FROM photos WHERE category='Person' LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(r)

conn.close()
