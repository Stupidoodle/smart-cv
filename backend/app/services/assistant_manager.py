from app.services.openai_assistant_service import OpenAIAssistantService
from sqlalchemy.orm import Session
from app.models.assistant import Assistant as AssistantModel


def load_assistants(db: Session, ai_service: OpenAIAssistantService):
    assistants = db.query(AssistantModel).all()
    for assistant in assistants:
        pass
