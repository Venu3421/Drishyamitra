from backend.database import SessionLocal
from backend.models.receipt import Receipt
from backend.models.photo import Photo

db = SessionLocal()
receipts = db.query(Receipt).all()

print(f"Total receipts: {len(receipts)}")
for r in receipts:
    print(f"ID: {r.id}, Merchant: {r.merchant}, Amount: {r.amount}, Date: {r.date}, Category: {r.category}")
    if r.photo_id:
        p = db.query(Photo).filter(Photo.id == r.photo_id).first()
        if p:
            print(f"  - Photo Created At: {p.created_at}")

db.close()
