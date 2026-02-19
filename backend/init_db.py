import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Venu3421%40@localhost:3306/personalens")
# Parse user/pass/host from URL or use env vars
# Simple parsing for prototype
try:
    # Assuming format: mysql+pymysql://user:pass@host/dbname
    from sqlalchemy.engine.url import make_url
    url = make_url(DB_URL)
    
    print(f"Connecting to MySQL at {url.host} to create database '{url.database}' if needed...")
    
    connection = pymysql.connect(
        host=url.host,
        user=url.username,
        password=url.password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {url.database}")
            print(f"Database '{url.database}' created or already exists.")
    finally:
        connection.close()

except Exception as e:
    print(f"Error initializing database: {e}")
