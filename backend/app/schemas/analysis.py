from pydantic import BaseModel
from datetime import datetime


class AnalysisInitiate(BaseModel):
    cv_id: int
    job_id: int


class AnalysisResponse(BaseModel):
    id: int
    cv_id: int
    job_id: int
    keyword_match_score: float
    bert_similarity_score: float
    cosine_similarity_score: float
    jaccard_similarity_score: float
    ner_similarity_score: float
    lsa_analysis_score: float
    aggregated_score: float

    class Config:
        orm_mode = True
        from_attributes = True
