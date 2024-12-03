from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.models.conversation import Conversation as ConversationModel
from app.models.cv import CV
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.message import MessageCreate, MessageResponse
from app.services.openai_assistant_service import OpenAIAssistantService
from app.models.assistant import Assistant
from app.models.message import Message

router = APIRouter()
ai_service = OpenAIAssistantService()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ConversationResponse)
def create_conversation(
    conversation: ConversationCreate, db: Session = Depends(get_db)
):
    try:
        # Fetch the assistant
        assistant = (
            db.query(Assistant)
            .filter(Assistant.id == conversation.assistant_id)
            .first()
        )
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")

        # Create Thread via OpenAI
        thread = ai_service.create_thread()

        # Save Conversation in DB
        db_conversation = ConversationModel(
            id=thread.id,
            cv_id=conversation.cv_id,
            job_id=conversation.job_id,
            assistant_id=conversation.assistant_id,  # FIXME
            analysis_id=conversation.analysis_id,
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)

        return db_conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def add_message(
    conversation_id: str, message: MessageCreate, db: Session = Depends(get_db)
):
    try:
        # Verify Conversation exists
        conversation = (
            db.query(ConversationModel)
            .filter(ConversationModel.id == conversation_id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Add Message via OpenAI
        openai_message = ai_service.add_message_to_thread(
            thread_id=str(conversation_id),
            role=message.role,
            content=message.content,
        )

        # Save Message in DB
        db_message = Message(
            id=openai_message.id,
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        return db_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def list_messages(conversation_id: str, db: Session = Depends(get_db)):
    messages = ai_service.list_messages_in_thread(conversation_id)
    if messages:
        for message in messages:
            message_entry = (
                db.query(Message)
                .filter(
                    Message.id == message.id,
                    Message.conversation_id == conversation_id,
                    Message.role == message.role,
                )
                .first()
            )
            if not message_entry:
                db_message = Message(
                    id=message.id,
                    conversation_id=conversation_id,
                    role=message.role,
                    content=message.content[0].text.value,
                    timestamp=datetime.fromtimestamp(message.created_at),
                )
                db.add(db_message)
                db.commit()
                db.refresh(db_message)
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp)
        .all()
    )
    if not messages:
        raise HTTPException(
            status_code=404, detail="No messages found for this conversation"
        )
    return messages
