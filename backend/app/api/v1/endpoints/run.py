# backend/app/api/v1/endpoints/run.py
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import SessionLocal
from app.models.conversation import Conversation as ConversationModel
from app.models.run import Run as RunModel
from app.schemas.run import RunResponse
from app.services.openai_assistant_service import OpenAIAssistantService
from app.services.analysis_service import handle_run

router = APIRouter()
ai_service = OpenAIAssistantService()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{conversation_id}/run", response_model=RunResponse)
def run_assistant(
    conversation_id: str,
    instructions: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        # Fetch the conversation
        conversation = (
            db.query(ConversationModel)
            .filter(ConversationModel.id == conversation_id)
            .first()
        )
        if not conversation and not isinstance(conversation, ConversationModel):
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Run Assistant on Thread
        run = ai_service.run_assistant_on_thread(
            thread_id=conversation_id,
            assistant_id=str(conversation.assistant_id),
            instructions=instructions,
        )

        # Save Run in DB
        db_run = RunModel(
            id=run.id,
            conversation_id=conversation_id,
            status=run.status,
            created_at=datetime.fromtimestamp(run.created_at),
            updated_at=datetime.now(),
        )
        db.add(db_run)
        db.commit()
        db.refresh(db_run)

        # Handle the run (function calls if any)
        handle_run(run, ai_service, db, conversation)

        return db_run
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/run/{run_id}", response_model=RunResponse)
def get_run(conversation_id: str, run_id: str, db: Session = Depends(get_db)):
    run = (
        db.query(RunModel)
        .filter(RunModel.id == run_id, RunModel.conversation_id == conversation_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
