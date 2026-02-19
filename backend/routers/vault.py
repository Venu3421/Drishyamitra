from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.vault import VaultFile
from ..auth_utils import verify_password # Use hash check or similar
import shutil
import os
import uuid
from pydantic import BaseModel
from ..auth_utils import get_current_user

router = APIRouter(
    prefix="/vault",
    tags=["vault"],
)

class PinRequest(BaseModel):
    pin: str

@router.post("/verify-pin")
def verify_pin(
    request: PinRequest,
    current_user = Depends(get_current_user)
):
    # Verify if PIN matches Year of Birth
    if not current_user.dob:
        raise HTTPException(status_code=400, detail="User date of birth not set")
        
    user_birth_year = str(current_user.dob.year)
    
    if request.pin == user_birth_year:
        return {"success": True, "message": "Vault Unlocked"}
    else:
        raise HTTPException(status_code=403, detail="Invalid PIN")


VAULT_DIR = "uploads/vault"
os.makedirs(VAULT_DIR, exist_ok=True)

@router.post("/upload")
async def upload_to_vault(
    file: UploadFile = File(...),
    pin: str = Form(...), # User's DOB-based PIN
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    # 1. Verify PIN (hash check against user's stored hash?)
    # For prototype, we assume PIN is correct key for encryption
    
    # 2. Encrypt file
    # Mock encryption: rename to .enc
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}.enc"
    file_path = os.path.join(VAULT_DIR, filename)
    
    # Real app: use cryptography.fernet or AES with Key derived from PIN
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    new_vault_file = VaultFile(
        user_id=user_id,
        original_filename=file.filename,
        encrypted_path=file_path,
        encryption_iv="mock_iv"
    )
    db.add(new_vault_file)
    db.commit()
    
    return {"message": "File encrypted and vaulted"}


@router.get("/")
def get_vault_files(
    user_id: int = 1, # TODO: actual auth
    db: Session = Depends(get_db)
):
    files = db.query(VaultFile).filter(VaultFile.user_id == user_id).order_by(VaultFile.created_at.desc()).all()
    return [
        {
            "id": f.id,
            "filename": f.original_filename,
            "created_at": f.created_at,
            "size": os.path.getsize(f.encrypted_path) if os.path.exists(f.encrypted_path) else 0
        }
        for f in files
    ]


from fastapi.responses import FileResponse, StreamingResponse
import mimetypes

@router.get("/{file_id}/content")
def get_vault_content(
    file_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    vf = db.query(VaultFile).filter(VaultFile.id == file_id, VaultFile.user_id == user_id).first()
    if not vf or not os.path.exists(vf.encrypted_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # In real app: decrypt here. 
    # For now, just serve the file but set correct content-type
    mime_type, _ = mimetypes.guess_type(vf.original_filename)
    return FileResponse(
        vf.encrypted_path,
        media_type=mime_type or "application/octet-stream",
        filename=vf.original_filename
    )
