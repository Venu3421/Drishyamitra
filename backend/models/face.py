from sqlalchemy import Column, Integer, String, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from ..database import Base

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True)
    encoding = Column(JSON) # Store list of floats
    photo_id = Column(Integer, ForeignKey("photos.id"))
    person_id = Column(Integer, ForeignKey("people.id"), nullable=True) # Identifying the person
    
    photo = relationship("Photo", back_populates="faces")
    person = relationship("Person", back_populates="faces")
