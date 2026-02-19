from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.photo import Photo
from ..models.receipt import Receipt
from ..models.vault import VaultFile
from ..ai_services.groq_client import GroqClient
from ..ai_services.face_recognition import FaceRecognitionService
from ..ai_services.receipt_analyzer import ReceiptAnalyzer
import shutil
import os
import uuid
from typing import List
from datetime import date as py_date


router = APIRouter(
    prefix="/photos",
    tags=["photos"],
)

UPLOAD_DIR = "uploads/photos"
VAULT_DIR = "uploads/vault"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VAULT_DIR, exist_ok=True)


def auto_classify_image(file_path: str, filename: str) -> dict:
    result = GroqClient.analyze_image(file_path)
    if result:
        return result
    fname = filename.lower()
    if any(kw in fname for kw in ["receipt", "bill", "invoice"]):
        return {"category": "Receipt", "is_sensitive": False, "doc_type": "receipt"}
    if any(kw in fname for kw in ["note", "memo"]):
        return {"category": "Note", "is_sensitive": False, "doc_type": "note"}
    if any(kw in fname for kw in ["aadhaar", "aadhar", "pan", "passport", "license", "bank"]):
        return {"category": "Document", "is_sensitive": True, "doc_type": "id_document"}
    return {"category": "General", "is_sensitive": False, "doc_type": "general"}


def vault_file(original_path: str, original_filename: str, user_id: int, db: Session):
    vault_filename = f"{uuid.uuid4()}_{original_filename}.enc"
    vault_path = os.path.join(VAULT_DIR, vault_filename)
    shutil.copy2(original_path, vault_path)
    vault_entry = VaultFile(
        user_id=user_id,
        original_filename=original_filename,
        encrypted_path=vault_path,
        encryption_iv="auto_vault"
    )
    db.add(vault_entry)
    db.commit()
    print(f"[AUTO-VAULT] Sensitive document '{original_filename}' vaulted automatically.")


@router.post("/upload")
async def upload_photo(
    files: List[UploadFile] = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    results = []
    for file in files:
        file_ext = file.filename.split(".")[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        relative_path = f"photos/{unique_filename}"
        absolute_path = os.path.join("uploads", relative_path)

        with open(absolute_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            classification = auto_classify_image(absolute_path, file.filename)
        except Exception as e:
            print(f"[Classification error] {e}")
            classification = {"category": "General", "is_sensitive": False, "doc_type": "general"}

        category = classification.get("category", "General")
        is_sensitive = classification.get("is_sensitive", False)

        embeddings = []
        if category == "Person":
            try:
                embeddings = FaceRecognitionService.generate_embedding(absolute_path)
            except Exception as e:
                print(f"[Embedding error] {e}")

        new_photo = Photo(
            user_id=user_id,
            path=relative_path,
            filename=file.filename,
            vector_embedding=embeddings if embeddings else None,
            category=category,
            is_sensitive=is_sensitive
        )
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)
        results.append({
            "id": new_photo.id,
            "filename": file.filename,
            "category": category,
            "is_sensitive": is_sensitive
        })

        # --- Auto-analyze receipt if classified as Receipt ---
        if category == "Receipt":
            try:
                print(f"[Auto-Receipt] Analyzing receipt: {absolute_path}")
                receipt_data = ReceiptAnalyzer.analyze_receipt(absolute_path)
                if receipt_data:
                    # Parse amounts
                    def to_float(v):
                        try:
                            return float(str(v).replace("$", "").replace("₹", "").replace(",", "").strip())
                        except Exception:
                            return 0.0

                    merchant    = receipt_data.get("Merchant Name") or "Unknown"
                    raw_amount  = receipt_data.get("Total Amount") or receipt_data.get("amount") or 0
                    raw_tax     = receipt_data.get("Tax Amount") or receipt_data.get("tax") or 0
                    cat         = receipt_data.get("Category") or "General"
                    raw_date    = receipt_data.get("Date")
                    amount      = to_float(raw_amount)
                    tax_val     = to_float(raw_tax)

                    r_date = None
                    if raw_date:
                        try:
                            r_date = py_date.fromisoformat(str(raw_date))
                        except Exception:
                            r_date = None

                    new_receipt = Receipt(
                        photo_id=new_photo.id,
                        merchant=merchant,
                        amount=amount,
                        tax=tax_val,
                        date=r_date,
                        category=cat
                    )
                    db.add(new_receipt)
                    db.commit()
                    # Update result with extracted data
                    results[-1]["receipt"] = {
                        "merchant": merchant, "amount": amount, "tax": tax_val,
                        "date": str(r_date) if r_date else None, "category": cat
                    }
                    print(f"[Auto-Receipt] Saved: {merchant} ₹{amount}")
            except Exception as e:
                print(f"[Auto-Receipt] Error: {e}")

        # --- Auto-vault sensitive documents ---
        if is_sensitive:
            try:
                vault_file(absolute_path, file.filename, user_id, db)
            except Exception as e:
                print(f"[Auto-vault error] {e}")

    return {"message": f"{len(results)} photo(s) uploaded successfully", "results": results}


@router.patch("/{photo_id}/category")
def update_photo_category(photo_id: int, user_id: int, category: str, db: Session = Depends(get_db)):
    valid_categories = ["Person", "Receipt", "Document", "Note", "General"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category. Use one of: {', '.join(valid_categories)}")
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found for user {user_id}")
    old_category = photo.category
    photo.category = category
    db.commit()
    return {"message": f"Photo moved from '{old_category}' to '{category}'", "photo_id": photo_id}


@router.delete("/{photo_id}")
def delete_photo(photo_id: int, user_id: int, db: Session = Depends(get_db)):
    """Delete a photo — removes DB record and file from disk."""
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")
    # Delete file from disk
    file_path = os.path.join("uploads", photo.path.replace("\\", "/"))
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(photo)
    db.commit()
    return {"message": f"Photo #{photo_id} ('{photo.filename}') deleted successfully"}


@router.get("/")
def get_photos(user_id: int, category: str = None, db: Session = Depends(get_db)):
    query = db.query(Photo).filter(Photo.user_id == user_id)
    if category:
        query = query.filter(Photo.category == category)
    photos = query.order_by(Photo.created_at.desc()).all()

    def normalize_path(raw_path: str) -> str:
        p = raw_path.replace("\\", "/")
        if p.startswith("uploads/"):
            p = p[len("uploads/"):]
        return p

    return [
        {
            "id": p.id,
            "filename": p.filename,
            "path": normalize_path(p.path),
            "category": p.category,
            "is_sensitive": p.is_sensitive,
            "created_at": str(p.created_at)
        }
        for p in photos
    ]
