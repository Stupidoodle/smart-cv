from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    messages = relationship("Message", back_populates="conversation")
    cv = relationship("CV", back_populates="conversations")
    job = relationship("Job", back_populates="conversations")
    assistant = relationship("Assistant", back_populates="conversations")
