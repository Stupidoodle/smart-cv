from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.models.base import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    keyword_match_score = Column(Float, default=0.0)
    bert_similarity_score = Column(Float, default=0.0)
    cosine_similarity_score = Column(Float, default=0.0)
    jaccard_similarity_score = Column(Float, default=0.0)
    ner_similarity_score = Column(Float, default=0.0)
    lsa_analysis_score = Column(Float, default=0.0)
    aggregated_score = Column(Float, default=0.0)

    cv = relationship("CV")
    job = relationship("Job", back_populates="analysis_results")
