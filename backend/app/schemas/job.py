from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class JobBase(BaseModel):
    title: str
    description: str
    company: str
    location: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

class JobResponse(JobBase):
    id: int
    posted_at: datetime

    class Config:
        orm_mode = True
