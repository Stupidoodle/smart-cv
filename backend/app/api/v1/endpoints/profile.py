from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=ProfileResponse, status_code=200)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(Profile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile


@router.post("/", response_model=ProfileResponse, status_code=201)
def create_profile(profile_request: ProfileCreate, db: Session = Depends(get_db)):
    profile_data = profile_request.model_dump()

    db_profile = Profile(**profile_data)

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    return db_profile


@router.put("/", response_model=ProfileResponse, status_code=200)
def update_profile(profile_request: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(Profile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    profile_data = profile_request.model_dump(exclude_unset=True)
    for key, value in profile_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/", status_code=204)
def delete_profile(db: Session = Depends(get_db)):
    profile = db.query(Profile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    db.delete(profile)
    db.commit()
    return
