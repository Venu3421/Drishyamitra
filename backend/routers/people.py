from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.person import Person
from ..models.face import Face
from ..models.photo import Photo
from ..auth_utils import get_current_user
from ..ai_services.face_recognition import FaceRecognitionService
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter(prefix="/people", tags=["people"])

API_URL = "http://localhost:8000"

class PersonResponse(BaseModel):
    id: int
    name: str
    photo_count: int
    cover_photo: Optional[str] = None   # URL of one face photo

    class Config:
        from_attributes = True


@router.get("/", response_model=List[PersonResponse])
def get_people(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    people = db.query(Person).filter(Person.user_id == current_user.id).all()
    result = []
    for p in people:
        # Get cover photo from first linked face
        cover = None
        if p.faces:
            first_face = p.faces[0]
            photo = db.query(Photo).filter(Photo.id == first_face.photo_id).first()
            if photo:
                clean = photo.path.replace("\\", "/")
                if not clean.startswith("photos/") and not clean.startswith("receipts/"):
                    clean = clean.replace("uploads/", "")
                cover = f"/static/uploads/{clean}"
        result.append(PersonResponse(id=p.id, name=p.name, photo_count=len(p.faces), cover_photo=cover))
    return result


@router.post("/")
def create_person(name: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    new_person = Person(name=name, user_id=current_user.id)
    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    return {"id": new_person.id, "name": new_person.name, "photo_count": 0}


@router.get("/photos-with-faces")
def get_photos_with_faces(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Return all photos categorized as 'Person' for the current user,
    along with any person_id already tagged to each photo's face.
    """
    photos = db.query(Photo).filter(
        Photo.user_id == current_user.id,
        Photo.category == "Person"
    ).order_by(Photo.created_at.desc()).all()

    result = []
    for photo in photos:
        clean = photo.path.replace("\\", "/")
        if not clean.startswith("photos/") and not clean.startswith("receipts/"):
            clean = clean.replace("uploads/", "")

        # Check if any face in this photo is tagged
        face = db.query(Face).filter(Face.photo_id == photo.id).first()
        tagged_person_id = face.person_id if face else None
        tagged_person_name = None
        if tagged_person_id:
            person = db.query(Person).filter(Person.id == tagged_person_id).first()
            tagged_person_name = person.name if person else None

        result.append({
            "photo_id": photo.id,
            "filename": photo.filename,
            "path": clean,
            "tagged_person_id": tagged_person_id,
            "tagged_person_name": tagged_person_name,
        })
    return result


@router.post("/tag-photo")
def tag_person_in_photo(
    photo_id: int,
    person_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Assign a person to all faces detected in a photo.
    If no Face records exist for the photo, create one as a placeholder.
    """
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    person = db.query(Person).filter(Person.id == person_id, Person.user_id == current_user.id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    faces = db.query(Face).filter(Face.photo_id == photo_id).all()
    if not faces:
        # No face record yet — create a placeholder so we can tag it
        face = Face(photo_id=photo_id, person_id=person_id, encoding=[])
        db.add(face)
    else:
        for face in faces:
            face.person_id = person_id

    db.commit()
    return {"message": f"Photo #{photo_id} tagged as '{person.name}'"}


@router.delete("/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    person = db.query(Person).filter(Person.id == person_id, Person.user_id == current_user.id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(person)
    db.commit()
    return {"message": "Person deleted"}
