from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    posted_at = Column(DateTime, default=datetime.utcnow)
    analysis_results = relationship("AnalysisResult", back_populates="job")
