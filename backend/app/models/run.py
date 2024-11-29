from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, index=True)  # Using Run ID from OpenAI
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    status = Column(String, nullable=False)  # e.g., 'pending', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation")
