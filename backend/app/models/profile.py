from sqlalchemy import Column, Integer, String, ARRAY
from app.models.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    # Psychological Profiling
    feedback_preference = Column(String(100), nullable=False)
    confidence_level = Column(String(100), nullable=False)
    criticism_reaction = Column(String(100), nullable=False)
    rejection_reaction = Column(String(100), nullable=False)
    motivation = Column(String(100), nullable=False)

    # Focus and Improvement Profiling
    primary_goal = Column(String(100), nullable=False)
    analysis_goal = Column(String(100), nullable=False)
    feedback_type = Column(String(100), nullable=False)
    improvement_type = Column(String(100), nullable=False)
    explanation_type = Column(String(100), nullable=False)

    # Decision-Making and Problem-Solving Profiling
    challenge_approach = Column(String(100), nullable=False)
    priority_focus = Column(String(100), nullable=False)
    improvement_confidence = Column(String(100), nullable=False)

    # Personal Profiling
    role_reason = Column(String(100), nullable=False)
    role_type = Column(ARRAY(String(100)), nullable=False)
    application_status = Column(String(100), nullable=False)
    top_challenges = Column(ARRAY(String(100)), nullable=False)

    # CV and Skill Profiling
    cv_confidence = Column(String(100), nullable=False)
    cv_prep = Column(String(100), nullable=False)
    cv_struggles = Column(ARRAY(String(100)), nullable=False)

    # Tracking and Organization Profiling
    tracking_method = Column(String(100), nullable=False)
    search_improvements = Column(ARRAY(String(100)), nullable=False)

    # Misc
    github_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
