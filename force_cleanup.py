import sys
import os
import pymysql

# Load env vars manually since we are running standalone
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "personalens")

def force_delete_users():
    print(f"Connecting to {DB_NAME} as {DB_USER}...")
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection:
            with connection.cursor() as cursor:
                # Disable foreign key checks to allow deleting users even if they have related data
                # (Ideally we cascade delete, but for now we just want to clear users)
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                print("Deleting all users...")
                rows = cursor.execute("DELETE FROM users")
                print(f"Deleted {rows} users.")
                
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            connection.commit()
            print("Cleanup complete.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_delete_users()
