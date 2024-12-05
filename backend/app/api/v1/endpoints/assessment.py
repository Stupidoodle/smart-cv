from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/submit", status_code=201)
def submit_assessment(
    assessment_request: AssessmentCreate, db: Session = Depends(get_db)
):
    try:
        # Fetch all existing assessments for the given analysis_id
        existing_assessments = (
            db.query(Assessment)
            .filter(Assessment.analysis_id == assessment_request.analysis_id)
            .all()
        )
        # Map existing questions to their objects for quick lookup
        existing_map = {
            assessment.question: assessment for assessment in existing_assessments
        }

        # Iterate through the incoming results
        for question, score in assessment_request.results.items():
            if question in existing_map:
                # Update the score if the question exists
                # noinspection PyTypeChecker
                existing_map[question].score = score
            else:
                # Add a new entry if the question doesn't exist
                new_assessment = Assessment(
                    analysis_id=assessment_request.analysis_id,
                    question=question,
                    score=score,
                )
                db.add(new_assessment)

        # Commit all changes in one transaction
        db.commit()
        return {"message": "Assessment submitted successfully."}

    except Exception as e:
        # Handle exceptions globally
        raise HTTPException(
            status_code=500, detail=f"Error submitting assessment: {str(e)}"
        )
