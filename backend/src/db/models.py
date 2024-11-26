from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Table,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime
import uuid

Base = declarative_base()

# Association tables
cv_skills = Table(
    "cv_skills",
    Base.metadata,
    Column("cv_id", String, ForeignKey("cvs.id")),
    Column("skill_id", Integer, ForeignKey("skills.id")),
)

job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", String, ForeignKey("job_postings.id")),
    Column("skill_id", Integer, ForeignKey("skills.id")),
)


# Enums
class SkillLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ContentType(enum.Enum):
    TEXT = "text"
    DOCUMENT = "document"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class AnalysisStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CVVersion(Base):
    __tablename__ = "cv_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cv_id = Column(String, ForeignKey("cvs.id"))
    version_number = Column(Integer)
    content = Column(String)  # LaTeX content
    created_at = Column(DateTime, default=func.now())
    changes = Column(JSON)  # Description of changes from previous version

    cv = relationship("CV", back_populates="versions")


class CV(Base):
    __tablename__ = "cvs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    current_version = Column(Integer, default=1)
    template_id = Column(String, ForeignKey("templates.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    metadata = Column(JSON)

    # Relationships
    versions = relationship(
        "CVVersion", back_populates="cv", order_by="CVVersion.version_number"
    )
    skills = relationship("Skill", secondary=cv_skills, back_populates="cvs")
    analyses = relationship("Analysis", back_populates="cv")
    template = relationship("Template")
    conversations = relationship("Conversation", back_populates="cv")


class Template(Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    content = Column(String)  # LaTeX template
    metadata = Column(JSON)  # Template description, tags, etc.
    created_at = Column(DateTime, default=func.now())


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(String)
    parsed_requirements = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    skills = relationship("Skill", secondary=job_skills, back_populates="jobs")
    analyses = relationship("Analysis", back_populates="job")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    category = Column(String)
    description = Column(String)
    metadata = Column(JSON)  # Additional skill information

    # Relationships
    cvs = relationship("CV", secondary=cv_skills, back_populates="skills")
    jobs = relationship("JobPosting", secondary=job_skills, back_populates="skills")
    assessments = relationship("SkillAssessment", back_populates="skill")


class SkillAssessment(Base):
    __tablename__ = "skill_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cv_id = Column(String, ForeignKey("cvs.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    level = Column(SQLEnum(SkillLevel))
    confidence_score = Column(Float)
    evidence = Column(JSON)  # Projects, experience, etc.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    skill = relationship("Skill", back_populates="assessments")
    validations = relationship("SkillValidation", back_populates="assessment")


class SkillValidation(Base):
    __tablename__ = "skill_validations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String, ForeignKey("skill_assessments.id"))
    questions = Column(JSON)  # Validation questions
    answers = Column(JSON)  # User's answers
    score = Column(Float)
    feedback = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    assessment = relationship("SkillAssessment", back_populates="validations")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cv_id = Column(String, ForeignKey("cvs.id"))
    job_id = Column(String, ForeignKey("job_postings.id"))
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    match_score = Column(Float)
    detailed_scores = Column(JSON)
    missing_skills = Column(JSON)
    suggestions = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

    # Relationships
    cv = relationship("CV", back_populates="analyses")
    job = relationship("JobPosting", back_populates="analyses")
    improvements = relationship("CVImprovement", back_populates="analysis")


class CVImprovement(Base):
    __tablename__ = "cv_improvements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cv_id = Column(String, ForeignKey("cvs.id"))
    analysis_id = Column(String, ForeignKey("analyses.id"))
    changes = Column(JSON)
    improvement_type = Column(String)  # Format, Content, Skills, etc.
    status = Column(String)  # Pending, Applied, Rejected
    created_at = Column(DateTime, default=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="improvements")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cv_id = Column(String, ForeignKey("cvs.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    metadata = Column(JSON)

    # Relationships
    cv = relationship("CV", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", order_by="Message.timestamp"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # user, assistant, system
    timestamp = Column(DateTime, default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    contents = relationship(
        "MessageContent", back_populates="message", order_by="MessageContent.order"
    )


class MessageContent(Base):
    __tablename__ = "message_contents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"))
    content_type = Column(SQLEnum(ContentType))
    content = Column(JSON)
    order = Column(Integer)  # Maintain content order within a message

    # Relationships
    message = relationship("Message", back_populates="contents")
