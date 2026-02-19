import pymysql

try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Venu3421@',
        database='personalens',
        cursorclass=pymysql.cursors.DictCursor
    )

    with conn.cursor() as cursor:
        print("--- RECEIPTS ---")
        cursor.execute("SELECT id, merchant, amount, date, photo_id, category FROM receipts")
        for r in cursor.fetchall():
            print(r)
            # Check photo created_at
            if r['photo_id']:
                cursor.execute(f"SELECT created_at FROM photos WHERE id={r['photo_id']}")
                p = cursor.fetchone()
                print(f"  -> Photo Created: {p['created_at']}")

        print("\n--- FACES ---")
        cursor.execute("SELECT * FROM faces")
        faces = cursor.fetchall()
        for r in faces:
            print(r)
        
        if not faces:
            print("No faces found in DB.")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
