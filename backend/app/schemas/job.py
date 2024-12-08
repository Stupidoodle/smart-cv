from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional


class JobBase(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None

    @model_validator(mode="after")
    def validate_fields(self):
        url = self.url
        # If `url` is None, enforce that other required fields are not None
        if url is None:
            required_fields = ["title", "status", "description", "company"]
            for field in required_fields:
                if getattr(self, field) is None:
                    raise ValueError(f"{field} is required if url is not provided.")
        return self


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None


class JobResponse(JobBase):
    id: int
    posted_at: datetime

    class Config:
        orm_mode = True
