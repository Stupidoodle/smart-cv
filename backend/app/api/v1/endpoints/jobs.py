import json

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.assistant import Assistant
from app.models.conversation import Conversation as ConversationModel
from app.models.job import Job
from app.models.message import Message
from app.models.run import Run as RunModel
from app.services.analysis_service import handle_run
from app.services.openai_assistant_service import OpenAIAssistantService
from app.schemas.job import JobCreate, JobUpdate, JobResponse

router = APIRouter()
ai_service = OpenAIAssistantService()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=JobResponse, status_code=201)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    if job.url is None:
        required_fields = ["title", "status", "description", "company"]
        for field in required_fields:
            if getattr(job, field) is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field} is required if url is not provided.",
                )
        db_job = Job(
            title=job.title,
            status=job.status,
            description=job.description,
            company=job.company,
            location=job.location,
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
    else:
        db_job = Job(
            url=job.url,
            status=job.status,
            description="temp",
            company="temp",
            location="temp",
            title="temp",
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)

        try:
            assistant = (
                db.query(Assistant).filter(Assistant.name == "Job Assistant").first()
            )
            if not assistant:
                raise HTTPException(status_code=404, detail="Assistant not found")

            thread = ai_service.create_thread()

            db_conversation = ConversationModel(
                id=thread.id,
                job_id=db_job.id,
                assistant_id=assistant.id,
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)

            openai_message = ai_service.add_message_to_thread(
                thread_id=thread.id, role="user", content="Follow your instructions."
            )

            db_message = Message(
                id=openai_message.id,
                conversation_id=db_conversation.id,
                role="user",
                content="Follow your instructions.",
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)

            run = ai_service.run_assistant_on_thread(
                thread_id=thread.id,
                assistant_id=str(assistant.id),
            )

            db_run = RunModel(
                id=run.id,
                conversation_id=db_conversation.id,
                status=run.status,
            )
            db.add(db_run)
            db.commit()
            db.refresh(db_run)

            run = handle_run(
                run=run,
                ai_service=ai_service,
                db=db,
                conversation_id=db_conversation.id,
            )

            if run.status == "completed":
                message_result = ai_service.list_messages_in_thread(
                    thread_id=thread.id
                )[0]
                job_output = json.loads(
                    ai_service.list_messages_in_thread(thread_id=thread.id)[0]
                    .content[0]
                    .text.value
                )

                db_message_result = Message(
                    id=message_result.id,
                    conversation_id=db_conversation.id,
                    role=message_result.role,
                    content=message_result.content[0].text.value,
                )
                db.add(db_message_result)
                db.commit()
                db.refresh(db_message_result)

                db_job.title = job_output["job_title"]
                db_job.description = job_output["job_description"]
                db_job.company = job_output["job_company"]
                db_job.location = job_output["job_location"]

                db.commit()
                db.refresh(db_job)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return db_job


@router.get("/", response_model=List[JobResponse])
def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def read_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    for key, value in job_update.model_dump(exclude_unset=True).items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    db.delete(job)
    db.commit()
    return
