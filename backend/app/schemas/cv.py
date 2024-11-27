from pydantic import BaseModel
from datetime import datetime

class CVCreating(BaseModel):
    filename: str

class CVResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    class Config:
        orm_mode = True

class CVListItem(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    class Config:
        orm_mode = True