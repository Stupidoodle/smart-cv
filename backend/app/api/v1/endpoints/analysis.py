from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.analysis import AnalysisResult
from app.models.cv import CV
from app.models.job import Job
from app.schemas.analysis import AnalysisInitiate, AnalysisResponse
from app.services.analysis_service import analyze_cv

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/start", response_model=AnalysisResponse, status_code=201)
def start_analysis(analysis_request: AnalysisInitiate, db: Session = Depends(get_db)):
    # Verify CV exists
    cv_entry = db.query(CV).filter(CV.id == analysis_request.cv_id).first()
    if not cv_entry:
        raise HTTPException(status_code=404, detail="CV not found.")

    # Verify Job exists
    job_entry = db.query(Job).filter(Job.id == analysis_request.job_id).first()
    if not job_entry:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Check if analysis already exists
    existing_analysis = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.cv_id == analysis_request.cv_id,
            AnalysisResult.job_id == analysis_request.job_id,
        )
        .first()
    )
    if existing_analysis:
        return existing_analysis

    try:
        # Perform analysis
        analyze_cv(analysis_request.cv_id, analysis_request.job_id)  # No need to fix

        # Retrieve the newly created analysis
        analysis = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.cv_id == analysis_request.cv_id,
                AnalysisResult.job_id == analysis_request.job_id,
            )
            .first()
        )

        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/list/{cv_id}/{job_id}", response_model=List[int])
def get_analysis_results(cv_id: int, job_id: int, db: Session = Depends(get_db)):
    analysis_ids = [
        result[0]
        for result in (
            db.query(AnalysisResult.id)
            .filter(AnalysisResult.cv_id == cv_id, AnalysisResult.job_id == job_id)
            .all()
        )
    ]

    if not analysis_ids:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis_ids


@router.get("/results/{cv_id}/{job_id}/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    cv_id: int, job_id: int, analysis_id: int, db: Session = Depends(get_db)
):
    analysis = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.cv_id == cv_id,
            AnalysisResult.job_id == job_id,
            AnalysisResult.id == analysis_id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis
