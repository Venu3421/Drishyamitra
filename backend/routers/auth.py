from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..auth_utils import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from pydantic import BaseModel, EmailStr
from fastapi import Body
from datetime import timedelta, date
from typing import Optional

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    dob: Optional[date] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        password_hash=hashed_password,
        full_name=user_in.full_name,
        dob=user_in.dob
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": new_user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    print(f"DEBUG: Login attempt for {login_data.email}")
    try:
        user = db.query(User).filter(User.email == login_data.email).first()
        print(f"DEBUG: User found: {user is not None}")
        
        if not user:
            print("DEBUG: User not found")
        elif not verify_password(login_data.password, user.password_hash):
            print("DEBUG: Password mismatch")

        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
        )
        print("DEBUG: Access token generated")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"CRITICAL LOGIN ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise e
@router.put("/smtp-settings")
def update_smtp_settings(
    settings: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.smtp_email = settings.get("smtp_email")
    current_user.smtp_password = settings.get("smtp_password")
    db.commit()
    return {"message": "SMTP settings updated successfully"}
