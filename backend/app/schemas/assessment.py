from pydantic import BaseModel


class AssessmentCreate(BaseModel):
    analysis_id: int
    results: dict[str, int]


class AssessmentResponse(BaseModel):
    pass
