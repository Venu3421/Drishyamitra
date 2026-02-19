from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from ..database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), unique=True)
    merchant = Column(String(255), nullable=True)
    date = Column(Date, nullable=True)
    amount = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    category = Column(String(100), nullable=True)
    
    photo = relationship("Photo", back_populates="receipt")
