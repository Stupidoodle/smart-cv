from fastapi import (
    FastAPI,
    BackgroundTasks,
    HTTPException,
    UploadFile,
    File,
    Form,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
from pathlib import Path

from .core.job_analyzers.pipeline import IntegratedAnalysisPipeline
from .db.service import DatabaseService
from .utils.file_handler import FileHandler
from .db.models import CV, JobPosting, Analysis, TaskStatus

# Initialize FastAPI app
app = FastAPI(title="Smart CV Analyzer")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_service = DatabaseService()
file_handler = FileHandler()
pipeline = IntegratedAnalysisPipeline(db_service)


# Dependency for database session
async def get_db():
    async with db_service.get_db() as session:
        yield session


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    await db_service.init_db()


@app.post("/api/cv/upload")
async def upload_cv(
    file: UploadFile = File(...),
    template_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a CV file."""
    try:
        # Validate file type
        if not file.filename.endswith(".tex"):
            raise HTTPException(
                status_code=400, detail="Only LaTeX (.tex) files are supported"
            )

        # Generate CV ID
        cv_id = str(uuid.uuid4())

        # Save file using FileHandler
        file_path = await file_handler.save_cv(file, cv_id)

        # Get content from saved file
        cv_content = await file_handler.get_cv_content(file_path)

        # Store in database
        cv = await db_service.create_cv(cv_content, template_id)

        return {
            "cv_id": cv.id,
            "version": cv.version,
            "created_at": cv.created_at,
            "template_id": template_id,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze")
async def analyze_cv(
    cv_id: str,
    job_description: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start CV analysis process."""
    try:
        # Create job posting
        job = await db_service.create_job_posting(
            content=job_description,
            parsed_requirements={},  # Basic implementation for now
        )

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Store initial task status
        await db_service.store_task_status(
            task_id=task_id, status="processing", cv_id=cv_id, job_id=job.id
        )

        # Start analysis in background
        background_tasks.add_task(
            analyze_in_background, task_id, cv_id, job.id, db_service, pipeline
        )

        return {"task_id": task_id, "status": "processing"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/result/{task_id}")
async def get_result(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get analysis result for a task."""
    try:
        task_status = await db_service.get_task_status(task_id)

        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")

        if task_status.status == "failed":
            return {"task_id": task_id, "status": "failed", "error": task_status.error}

        if task_status.status == "completed":
            analysis_result = await db_service.get_analysis_result(task_id)
            return {
                "task_id": task_id,
                "status": "completed",
                "result": analysis_result,
            }

        return {"task_id": task_id, "status": "processing"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cv/{cv_id}/history")
async def get_cv_history(cv_id: str, db: AsyncSession = Depends(get_db)):
    """Get CV analysis history."""
    try:
        # Get analyses
        analyses = await db_service.get_cv_analyses(cv_id)

        # Get skill assessments
        skill_assessments = await db_service.get_skill_assessments(cv_id)

        # Get CV details
        cv = await db_service.get_latest_cv_version(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found")

        return {
            "cv_id": cv_id,
            "current_version": cv.version,
            "analyses": analyses,
            "skill_assessments": skill_assessments,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/templates")
async def get_templates(db: AsyncSession = Depends(get_db)):
    """Get available CV templates."""
    try:
        # Get template files
        template_files = await file_handler.list_templates()

        templates = []
        for template_name in template_files:
            content = await file_handler.get_template_content(template_name)
            if content:
                templates.append(
                    {"id": template_name, "name": template_name, "content": content}
                )

        return templates

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Background task helper
async def analyze_in_background(
    task_id: str,
    cv_id: str,
    job_id: str,
    db_service: DatabaseService,
    pipeline: IntegratedAnalysisPipeline,
):
    """Run analysis in background and store results."""
    try:
        # Run analysis
        results = await pipeline.analyze(cv_id, job_id)

        # Update task status with results
        await db_service.update_task_status(
            task_id=task_id, status="completed", result=results
        )

    except Exception as e:
        # Update task status with error
        await db_service.update_task_status(
            task_id=task_id, status="failed", error=str(e)
        )
