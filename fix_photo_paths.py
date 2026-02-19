import sys
sys.path.insert(0, '.')
from backend.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Fix paths that start with 'uploads/' or 'uploads\'
    result = conn.execute(text("""
        UPDATE photos
        SET path = CASE
            WHEN path LIKE 'uploads/%' THEN SUBSTRING(path, 9)
            WHEN path LIKE 'uploads\\\\%' THEN SUBSTRING(path, 9)
            ELSE path
        END
        WHERE path LIKE 'uploads/%' OR path LIKE 'uploads\\\\%'
    """))
    conn.commit()
    print(f"Fixed {result.rowcount} photo path(s) in DB")
    
    # Verify
    rows = conn.execute(text("SELECT id, path FROM photos LIMIT 10")).fetchall()
    for r in rows:
        print(f"  id={r[0]}  path={r[1]}")
