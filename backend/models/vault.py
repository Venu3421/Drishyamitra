from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary, DateTime, func
from ..database import Base

class VaultFile(Base):
    __tablename__ = "vault"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_filename = Column(String(255), nullable=False)
    encrypted_path = Column(String(512), nullable=False)
    encryption_iv = Column(String(255), nullable=False) # Hex string or similar
    created_at = Column(DateTime, server_default=func.now())
    
    # We might store a hint or check-hash to verify password correctness without storing the password
    # For now, relying on successful decryption as proof
