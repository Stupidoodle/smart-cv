from pydantic import BaseModel
from datetime import datetime


class MessageCreate(BaseModel):
    conversation_id: int
    role: str  # 'user' or 'assistant'
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True
