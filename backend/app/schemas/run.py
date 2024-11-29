from pydantic import BaseModel
from datetime import datetime


class RunResponse(BaseModel):
    id: str
    conversation_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
