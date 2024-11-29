from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True, index=True)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=False)
    type = Column(String, nullable=False)  # e.g., 'function', 'code_interpreter'
    function_definition = Column(JSON, nullable=True)  # For function type tools

    assistant = relationship("Assistant", back_populates="tools")
