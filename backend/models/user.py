from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.sql import func
from ..database import Base

from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    dob = Column(Date, nullable=True)  # For Vault security
    smtp_email = Column(String(255), nullable=True) # User's personal email for sending
    smtp_password = Column(String(255), nullable=True) # App Password
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    people = relationship("Person", back_populates="owner")
