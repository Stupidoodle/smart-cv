from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.models.assistant import Assistant as AssistantModel
from app.schemas.assistant import AssistantCreate, AssistantResponse
from app.services.openai_assistant_service import OpenAIAssistantService

router = APIRouter()
ai_service = OpenAIAssistantService()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=AssistantResponse)
def create_assistant(assistant: AssistantCreate, db: Session = Depends(get_db)):
    try:
        # Create Assistant via OpenAI
        assistant_data = ai_service.create_assistant(
            name=assistant.name,
            instructions=assistant.instructions,
            model=assistant.model,
            tools=[tool.model_dump() for tool in assistant.tools],
            response_format=assistant.response_format,
        )

        # Save Assistant in DB
        db_assistant = AssistantModel(
            id=assistant_data.id,
            name=assistant_data.name,
            instructions=assistant_data.instructions,
            model=assistant_data.model,
        )
        db.add(db_assistant)
        db.commit()
        db.refresh(db_assistant)

        return db_assistant
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[AssistantResponse])
def list_assistants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assistants = ai_service.list_assistants()
    if assistants:
        for assistant in assistants:
            assistant_entry = db.query(AssistantModel).filter(
                AssistantModel.id == assistant.id,
                AssistantModel.name == assistant.name,
            )
            if not assistant_entry.first():
                db_assistant = AssistantModel(
                    id=assistant.id,
                    name=assistant.name,
                    instructions=assistant.instructions,
                    model=assistant.model,
                )
                db.add(db_assistant)
                db.commit()
    assistants = db.query(AssistantModel).offset(skip).limit(limit).all()
    return assistants


@router.get("/{assistant_id}", response_model=AssistantResponse)
def get_assistant(assistant_id: str, db: Session = Depends(get_db)):
    assistant = (
        db.query(AssistantModel).filter(AssistantModel.id == assistant_id).first()
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant
