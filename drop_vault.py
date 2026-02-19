from backend.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS vault"))
    conn.commit()
    print("Dropped vault table")
