from dataclasses import field

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.message import MessageResponse


class ConversationCreate(BaseModel):
    cv_id: int
    job_id: int
    assistant_id: str


class ConversationResponse(BaseModel):
    id: int
    cv_id: int
    job_id: int
    assistant_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: List[MessageResponse] = field(default_factory=List)

    class Config:
        orm_mode = True