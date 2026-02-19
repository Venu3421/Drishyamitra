import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time


# ─── Email ────────────────────────────────────────────────────────────────────
def send_email(to_email: str, subject: str, message: str, smtp_user: str = None, smtp_pass: str = None):
    """Sends an email using Gmail SMTP."""
    email_user = smtp_user or os.getenv("EMAIL_USER")
    email_pass = smtp_pass or os.getenv("EMAIL_PASS")
    if not email_user or not email_pass:
        return {"status": "error", "message": "Email credentials not configured. Please add them in Settings → Email tab."}
    try:
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, to_email, msg.as_string())
        server.quit()
        return {"status": "success", "message": f"Email sent to {to_email}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── WhatsApp ─────────────────────────────────────────────────────────────────
def send_whatsapp(phone_number: str, message: str, image_path: str = None):
    """
    Sends a WhatsApp message or image via WhatsApp Web automation.
    phone_number must include country code, e.g. '+919876543210'
    image_path: optional path to image file (relative to project root, e.g. 'uploads/photos/uuid.jpg')
    """
    try:
        import pywhatkit
        import pyautogui

        phone_number = phone_number.strip().replace(" ", "").replace("-", "")
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number

        # Resolve image path relative to project root
        abs_image = None
        if image_path:
            # Try 1: Exact path given
            if os.path.exists(image_path):
                abs_image = os.path.abspath(image_path)
            # Try 2: Prepend 'uploads/' if missing
            elif os.path.exists(os.path.join("uploads", image_path)):
                abs_image = os.path.abspath(os.path.join("uploads", image_path))
            else:
                return {"status": "error", "message": f"Image file not found: {image_path}"}

        if abs_image:
            # Normalize path for pywhatkit (it can be picky on Windows)
            abs_image = abs_image.replace("\\", "/")
            print(f"[WhatsApp] Sending image {abs_image} to {phone_number}")
            pywhatkit.sendwhats_image(
                receiver=phone_number,
                img_path=abs_image,
                caption=message or "",
                wait_time=45,
                tab_close=False
            )
        else:
            print(f"[WhatsApp] Sending text to {phone_number}: {message}")
            pywhatkit.sendwhatmsg_instantly(
                phone_no=phone_number,
                message=message,
                wait_time=30,
                tab_close=False,
                close_time=3
            )

        time.sleep(5)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'w')
        return {"status": "success", "message": f"WhatsApp {'image' if abs_image else 'message'} sent to {phone_number}"}

    except ImportError as e:
        return {"status": "error", "message": f"Import failed: {str(e)}. Try installing pywhatkit and pyautogui."}
    except Exception as e:
        return {"status": "error", "message": f"WhatsApp send failed: {str(e)}"}


# ─── Photo Management ─────────────────────────────────────────────────────────
def _get_db():
    import sys
    sys.path.insert(0, os.path.abspath('.'))
    from backend.database import SessionLocal
    return SessionLocal()


def list_photos(user_id: int, category: str = None):
    """List all photos for a user, optionally filtered by category."""
    try:
        db = _get_db()
        try:
            from backend.models.photo import Photo
            q = db.query(Photo).filter(Photo.user_id == user_id)
            if category:
                q = q.filter(Photo.category == category)
            photos = q.order_by(Photo.id.desc()).all()
            return {
                "status": "success",
                "count": len(photos),
                "photos": [
                    {"id": p.id, "filename": p.filename, "category": p.category,
                     "path": p.path, "is_sensitive": p.is_sensitive, "created_at": str(p.created_at)}
                    for p in photos
                ]
            }
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_photo(photo_id: int, user_id: int):
    """Delete a photo by ID — removes from DB and disk."""
    try:
        db = _get_db()
        try:
            from backend.models.photo import Photo
            photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
            if not photo:
                return {"status": "error", "message": f"Photo {photo_id} not found for this user."}
            filename = photo.filename
            file_path = os.path.join("uploads", photo.path.replace("\\", "/"))
            if os.path.exists(file_path):
                os.remove(file_path)
            db.delete(photo)
            db.commit()
            return {"status": "success", "message": f"Photo #{photo_id} ('{filename}') deleted."}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def move_photo(photo_id: int, category: str, user_id: int):
    """Move a photo to a different category: Person / Receipt / Document / Note / General"""
    valid = ["Person", "Receipt", "Document", "Note", "General"]
    if category not in valid:
        return {"status": "error", "message": f"Invalid category. Use: {', '.join(valid)}"}
    try:
        db = _get_db()
        try:
            from backend.models.photo import Photo
            photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
            if not photo:
                return {"status": "error", "message": f"Photo {photo_id} not found."}
            old = photo.category
            photo.category = category
            db.commit()
            return {"status": "success", "message": f"Photo #{photo_id} moved from '{old}' to '{category}'"}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── People ───────────────────────────────────────────────────────────────────
def list_people(user_id: int):
    """List all named people in the user's library."""
    try:
        db = _get_db()
        try:
            from backend.models.person import Person
            people = db.query(Person).filter(Person.user_id == user_id).all()
            return {
                "status": "success",
                "count": len(people),
                "people": [{"id": p.id, "name": p.name, "tagged_photos": len(p.faces)} for p in people]
            }
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_person(name: str, user_id: int):
    """Create a new named person profile."""
    try:
        db = _get_db()
        try:
            from backend.models.person import Person
            p = Person(name=name, user_id=user_id)
            db.add(p); db.commit(); db.refresh(p)
            return {"status": "success", "message": f"Person '{name}' created with ID {p.id}", "person_id": p.id}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tag_person_in_photo(photo_id: int, person_id: int, user_id: int):
    """Tag a person in a photo by linking their IDs."""
    try:
        db = _get_db()
        try:
            from backend.models.photo import Photo
            from backend.models.person import Person
            from backend.models.face import Face
            photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
            person = db.query(Person).filter(Person.id == person_id, Person.user_id == user_id).first()
            if not photo:
                return {"status": "error", "message": f"Photo {photo_id} not found."}
            if not person:
                return {"status": "error", "message": f"Person {person_id} not found."}
            faces = db.query(Face).filter(Face.photo_id == photo_id).all()
            if not faces:
                db.add(Face(photo_id=photo_id, person_id=person_id, encoding=[]))
            else:
                for f in faces: f.person_id = person_id
            db.commit()
            return {"status": "success", "message": f"Photo #{photo_id} tagged as '{person.name}'"}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── Receipts ─────────────────────────────────────────────────────────────────
def get_receipt_summary(user_id: int):
    """Get expense summary: total spending and breakdown by category."""
    try:
        db = _get_db()
        try:
            from backend.models.receipt import Receipt
            from backend.models.photo import Photo
            receipts = db.query(Receipt, Photo).join(Photo).filter(Photo.user_id == user_id).all()
            total = sum(r.amount or 0 for r, _ in receipts)
            by_cat = {}
            for r, _ in receipts:
                cat = r.category or "General"
                by_cat[cat] = round(by_cat.get(cat, 0) + (r.amount or 0), 2)
            return {
                "status": "success",
                "total": round(total, 2),
                "count": len(receipts),
                "by_category": by_cat,
                "receipts": [
                    {"id": r.id, "merchant": r.merchant, "amount": r.amount,
                     "date": str(r.date), "category": r.category}
                    for r, _ in receipts
                ]
            }
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_receipt(receipt_id: int, user_id: int):
    """Delete a receipt record."""
    try:
        db = _get_db()
        try:
            from backend.models.receipt import Receipt
            from backend.models.photo import Photo
            r = db.query(Receipt).join(Photo).filter(Receipt.id == receipt_id, Photo.user_id == user_id).first()
            if not r:
                return {"status": "error", "message": f"Receipt {receipt_id} not found."}
            db.delete(r); db.commit()
            return {"status": "success", "message": f"Receipt #{receipt_id} deleted."}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── Vault ────────────────────────────────────────────────────────────────────
def list_vault(user_id: int):
    """List all files in the secure vault."""
    try:
        db = _get_db()
        try:
            from backend.models.vault import VaultFile
            files = db.query(VaultFile).filter(VaultFile.user_id == user_id).all()
            return {
                "status": "success",
                "count": len(files),
                "files": [{"id": f.id, "filename": f.original_filename, "added": str(f.created_at)} for f in files]
            }
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── Tool Registry ────────────────────────────────────────────────────────────
TOOL_REGISTRY = {
    # Messaging
    "send_email":          send_email,
    "send_whatsapp":       send_whatsapp,
    # Photo management
    "list_photos":         list_photos,
    "delete_photo":        delete_photo,
    "move_photo":          move_photo,
    # People
    "list_people":         list_people,
    "create_person":       create_person,
    "tag_person_in_photo": tag_person_in_photo,
    # Receipts & expenses
    "get_receipt_summary": get_receipt_summary,
    "delete_receipt":      delete_receipt,
    # Vault
    "list_vault":          list_vault,
}
