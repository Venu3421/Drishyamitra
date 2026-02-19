from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.receipt import Receipt
from ..models.photo import Photo
from ..auth_utils import get_current_user
from ..ai_services.receipt_analyzer import ReceiptAnalyzer
import shutil, os, uuid, json
from datetime import date

router = APIRouter(prefix="/receipts", tags=["receipts"])
UPLOAD_DIR = "uploads/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze")
async def analyze_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    file_ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4()}.{file_ext}"
    relative_path = f"receipts/{filename}"
    file_path = os.path.join("uploads", relative_path)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # AI analysis
    data = ReceiptAnalyzer.analyze_receipt(file_path)

    # Save Photo entry
    new_photo = Photo(
        user_id=current_user.id,
        path=relative_path,
        filename=file.filename,
        category="Receipt",
        is_sensitive=False
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)

    # Parse & save Receipt
    merchant = None
    amount = None
    tax = None
    receipt_date = None
    category = "General"

    if data:
        merchant = data.get("Merchant Name") or data.get("merchant") or "Unknown"
        raw_amount = data.get("Total Amount") or data.get("amount") or data.get("total") or 0
        raw_tax   = data.get("Tax Amount")   or data.get("tax")    or 0
        category  = data.get("Category")     or data.get("category") or "General"
        raw_date  = data.get("Date")         or data.get("date")

        def to_float(v):
            try:
                return float(str(v).replace("$", "").replace("₹", "").replace(",", "").strip())
            except:
                return 0.0

        amount = to_float(raw_amount)
        tax    = to_float(raw_tax)

        if raw_date:
            try:
                receipt_date = date.fromisoformat(str(raw_date))
            except:
                receipt_date = None

    new_receipt = Receipt(
        photo_id=new_photo.id,
        merchant=merchant or "Unknown",
        amount=amount or 0.0,
        tax=tax or 0.0,
        date=receipt_date,
        category=category
    )
    db.add(new_receipt)
    db.commit()

    return {
        "message": "Receipt analyzed and saved",
        "receipt": {
            "id": new_receipt.id,
            "merchant": new_receipt.merchant,
            "amount": new_receipt.amount,
            "tax": new_receipt.tax,
            "date": str(new_receipt.date) if new_receipt.date else None,
            "category": new_receipt.category,
            "photo_path": relative_path
        }
    }


@router.get("/")
def get_receipts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Return all receipts for the current user with their photo paths."""
    receipts = (
        db.query(Receipt, Photo)
        .join(Photo, Receipt.photo_id == Photo.id)
        .filter(Photo.user_id == current_user.id)
        .order_by(Receipt.id.desc())
        .all()
    )
    total = sum(r.amount or 0 for r, _ in receipts)
    today = date.today()
    this_month_start = today.replace(day=1)
    
    # Use upload date (photo.created_at) for "This Month" spending to match user expectation of "Recent Activity"
    # regardless of the actual date on the receipt (which might be old or parsed incorrectly)
    month_total = sum(
        r.amount or 0 for r, p in receipts
        if p.created_at.date() >= this_month_start
    )

    def normalize(path: str) -> str:
        p = path.replace("\\", "/")
        if p.startswith("uploads/"):
            p = p[len("uploads/"):]
        return p

    return {
        "receipts": [
            {
                "id": r.id,
                "merchant": r.merchant or "Unknown",
                "amount": r.amount or 0,
                "tax": r.tax or 0,
                "date": str(r.date) if r.date else None,
                "category": r.category or "General",
                "photo_path": normalize(p.path)
            }
            for r, p in receipts
        ],
        "total_all_time": round(total, 2),
        "total_this_month": round(month_total, 2),
        "count": len(receipts)
    }


@router.delete("/{receipt_id}")
def delete_receipt(receipt_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    receipt = db.query(Receipt).join(Photo).filter(
        Receipt.id == receipt_id, Photo.user_id == current_user.id
    ).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    db.delete(receipt)
    db.commit()
    return {"message": "Deleted"}
