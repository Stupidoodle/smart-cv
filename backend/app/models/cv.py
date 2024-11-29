from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    versions = relationship("CVVersion", back_populates="cv")
    analysis_results = relationship("AnalysisResult", back_populates="cv")
    conversations = relationship("Conversation", back_populates="cv")


class CVVersion(Base):
    __tablename__ = "cv_versions"

    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    filepath = Column(String, unique=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
    cv = relationship("CV", back_populates="versions")
