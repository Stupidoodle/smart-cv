from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.cv import CV, CVVersion
from app.schemas.cv import CVCreating, CVResponse, CVListItem
from app.utils.file_management import save_cv_file, generate_unique_filename, UPLOAD_DIR
import shutil
import os
from app.services.cv_service import process_cv

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", response_model=CVResponse)
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "text/x-tex" and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a LaTeX (.tex) or PDF (.pdf) file.",
        )

    try:
        # Save the uploaded file
        unique_filename = generate_unique_filename(file.filename)
        upload_dir = UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        file_location = os.path.join(upload_dir, unique_filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create CV entry in DB
        cv_entry = CV(filename=unique_filename, filepath=file_location)
        db.add(cv_entry)
        db.commit()
        db.refresh(cv_entry)

        # Create initial CVVersion
        cv_version = CVVersion(
            cv_id=cv_entry.id, version_number=1, filepath=file_location
        )
        db.add(cv_version)
        db.commit()
        db.refresh(cv_version)

        # Process the CV (e.g., compile LaTeX, analyze)
        try:
            process_cv(cv_entry.id)  # Note: Replace job_id with appropriate logic
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return CVResponse(
            id=cv_entry.id, filename=cv_entry.filename, uploaded_at=cv_entry.uploaded_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[CVListItem])
def list_cvs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cvs = db.query(CV).order_by(CV.uploaded_at.desc()).offset(skip).limit(limit).all()
    return cvs
