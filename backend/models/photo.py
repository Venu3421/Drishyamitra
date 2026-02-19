from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    path = Column(String(512), nullable=False)
    filename = Column(String(255), nullable=False)
    vector_embedding = Column(JSON, nullable=True) # For face recognition/semantic search
    category = Column(String(50), default="General") # e.g. Receipt, Person, Nature, Note
    is_sensitive = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    receipt = relationship("Receipt", back_populates="photo", uselist=False)

    faces = relationship("Face", back_populates="photo")
