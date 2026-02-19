from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.photo import Photo
from ..models.vault import VaultFile
from ..models.receipt import Receipt
from ..models.person import Person
from ..models.face import Face
from ..auth_utils import get_current_user

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)

@router.get("/")
def get_dashboard_stats(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    user_id = current_user.id
    
    total_photos = db.query(Photo).filter(Photo.user_id == user_id).count()
    total_vault_items = db.query(VaultFile).filter(VaultFile.user_id == user_id).count()
    total_receipts = db.query(Receipt).join(Photo).filter(Photo.user_id == user_id).count()
    total_people = db.query(Person).filter(Person.user_id == user_id).count()
    
    # Mock storage usage since we aren't tracking file sizes in DB yet (or sum if we add size column)
    # Assuming avg 2MB per photo
    storage_used_mb = (total_photos * 2) + (total_vault_items * 1.5)
    
    return {
        "total_photos": total_photos,
        "total_vault": total_vault_items,
        "total_receipts": total_receipts,
        "total_people": total_people,
        "storage_used_gb": round(storage_used_mb / 1024, 2),
        "storage_limit_gb": 10 # Free tier limit
    }
