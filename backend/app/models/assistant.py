from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base


class Assistant(Base):
    __tablename__ = "assistants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    instructions = Column(String, nullable=False)
    model = Column(String, nullable=False)

    tools = relationship("Tool", back_populates="assistant")
    conversations = relationship("Conversation", back_populates="assistant")
