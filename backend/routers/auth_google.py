from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..auth_utils import create_access_token, get_password_hash
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import os
import secrets

router = APIRouter(
    prefix="/auth/google",
    tags=["auth"],
)

class GoogleLogin(BaseModel):
    token: str

@router.post("/")
def google_login(login_data: GoogleLogin, db: Session = Depends(get_db)):
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    if not GOOGLE_CLIENT_ID:
         raise HTTPException(status_code=500, detail="Google Client ID not configured")

    try:
        print(f"DEBUG: Verifying Google Token: {login_data.token[:20]}...")
        # Verify token
        id_info = id_token.verify_oauth2_token(
            login_data.token, requests.Request(), GOOGLE_CLIENT_ID
        )
        print(f"DEBUG: Token verified. Email: {id_info.get('email')}")

        email = id_info['email']
        name = id_info.get('name', '')
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            # Set a random password since they use Google
            random_password = secrets.token_urlsafe(16)
            hashed_password = get_password_hash(random_password)
            
            user = User(
                email=email,
                password_hash=hashed_password,
                full_name=name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

    except ValueError as e:
        print(f"DEBUG: ValueError in Google Login: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"DEBUG: Critical Error in Google Login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
