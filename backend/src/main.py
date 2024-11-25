from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import json
from datetime import datetime
from pathlib import Path
import aiofiles
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .core.job_analyzers.pipeline import CVAnalysisPipeline
from .core.cv_manager import CVManager
from .db.cache import ResultCache
from .utils.file_handler import FileHandler


class AnalysisRequest(BaseModel):
    cv_id: Optional[str] = None
    job_description: str
    template_id: Optional[str] = None


class AnalysisResponse(BaseModel):
    task_id: str
    status: str


class ResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


app = FastAPI(title="Smart CV Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pipeline = CVAnalysisPipeline()
cv_manager = CVManager()
cache = ResultCache()
file_handler = FileHandler()


# Background task to run analysis
async def run_analysis(task_id: str, cv_text: str, job_text: str):
    try:
        # Run analysis
        result = pipeline.analyze(cv_text, job_text)

        # Cache result
        await cache.store_result(
            task_id,
            {
                "status": "completed",
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        await cache.store_result(
            task_id,
            {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.post("/api/cv/upload", response_model=Dict[str, str])
async def upload_cv(
    file: UploadFile = File(...), template_id: Optional[str] = Form(None)
):
    """Upload and store a CV file."""
    try:
        cv_id = str(uuid.uuid4())
        file_path = await file_handler.save_cv(file, cv_id)

        # Store CV metadata
        metadata = {
            "original_filename": file.filename,
            "template_id": template_id,
            "upload_time": datetime.utcnow().isoformat(),
            "file_path": str(file_path),
        }
        await cv_manager.store_cv_metadata(cv_id, metadata)

        return {"cv_id": cv_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_cv(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start CV analysis process."""
    try:
        task_id = str(uuid.uuid4())

        # Get CV text
        if request.cv_id:
            cv_text = await cv_manager.get_cv_text(request.cv_id)
        else:
            raise HTTPException(status_code=400, detail="CV ID is required")

        # Initialize task in cache
        await cache.store_result(
            task_id,
            {"status": "processing", "timestamp": datetime.utcnow().isoformat()},
        )

        # Start background analysis
        background_tasks.add_task(
            run_analysis, task_id, cv_text, request.job_description
        )

        return {"task_id": task_id, "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/result/{task_id}", response_model=ResultResponse)
async def get_result(task_id: str):
    """Get analysis result for a given task ID."""
    try:
        cached_result = await cache.get_result(task_id)
        if not cached_result:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": task_id,
            "status": cached_result["status"],
            "result": cached_result.get("result"),
            "error": cached_result.get("error"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/improve")
async def improve_cv(
    cv_id: str, analysis_result: Dict[str, Any], template_id: Optional[str] = None
):
    """Generate improved CV based on analysis results."""
    try:
        improved_cv = await cv_manager.improve_cv(cv_id, analysis_result, template_id)
        return improved_cv
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/templates")
async def get_templates():
    """Get available CV templates."""
    try:
        templates = await cv_manager.get_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
