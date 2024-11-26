from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, select
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import TaskStatus
import json

from .models import (
    Base,
    CV,
    JobPosting,
    Skill,
    Analysis,
    SkillAssessment,
    CVImprovement,
    InterviewPrep,
)


class DatabaseService:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=True)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_db(self) -> AsyncSession:
        """Get database session."""
        async with self.SessionLocal() as session:
            return session

    # CV Operations
    async def create_cv(self, content: str, template_id: Optional[str] = None) -> CV:
        """Create new CV entry."""
        async with self.get_db() as db:
            cv = CV(content=content, template_id=template_id)
            db.add(cv)
            await db.commit()
            await db.refresh(cv)
            return cv

    async def update_cv(self, cv_id: str, content: str) -> CV:
        """Update CV content and increment version."""
        async with self.get_db() as db:
            cv = await db.query(CV).filter(CV.id == cv_id).first()
            if cv:
                cv.content = content
                cv.version += 1
                cv.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(cv)
            return cv

    # Job Posting Operations
    async def create_job_posting(
        self, content: str, parsed_requirements: Dict[str, Any]
    ) -> JobPosting:
        """Create new job posting entry."""
        async with self.get_db() as db:
            job = JobPosting(content=content, parsed_requirements=parsed_requirements)
            db.add(job)
            await db.commit()
            await db.refresh(job)
            return job

    # Skill Operations
    async def get_or_create_skill(self, name: str, category: str) -> Skill:
        """Get existing skill or create new one."""
        async with self.get_db() as db:
            skill = await db.query(Skill).filter(Skill.name == name).first()
            if not skill:
                skill = Skill(name=name, category=category)
                db.add(skill)
                await db.commit()
                await db.refresh(skill)
            return skill

    # Analysis Operations
    async def create_analysis(
        self, cv_id: str, job_id: str, results: Dict[str, Any]
    ) -> Analysis:
        """Create new analysis entry."""
        async with self.get_db() as db:
            analysis = Analysis(
                cv_id=cv_id,
                job_id=job_id,
                match_score=results["match_percentage"],
                detailed_scores=results["detailed_analysis"],
                missing_skills=results["overall_analysis"]["missing_items"],
                suggestions=results["overall_analysis"]["suggestions"],
            )
            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)
            return analysis

    # Skill Assessment Operations
    async def create_skill_assessment(
        self,
        cv_id: str,
        skill_id: int,
        confidence_score: float,
        evidence: Dict[str, Any],
    ) -> SkillAssessment:
        """Create new skill assessment entry."""
        async with self.get_db() as db:
            assessment = SkillAssessment(
                cv_id=cv_id,
                skill_id=skill_id,
                confidence_score=confidence_score,
                evidence=evidence,
                verification_status="pending",
            )
            db.add(assessment)
            await db.commit()
            await db.refresh(assessment)
            return assessment

    # CV Improvement Operations
    async def create_cv_improvement(
        self, cv_id: str, changes: List[Dict[str, Any]], improvement_type: str
    ) -> CVImprovement:
        """Create new CV improvement entry."""
        async with self.get_db() as db:
            improvement = CVImprovement(
                cv_id=cv_id,
                changes=changes,
                improvement_type=improvement_type,
                status="pending",
            )
            db.add(improvement)
            await db.commit()
            await db.refresh(improvement)
            return improvement

    # Interview Prep Operations
    async def create_interview_prep(
        self, job_id: str, questions: List[Dict[str, Any]]
    ) -> InterviewPrep:
        """Create new interview prep entry."""
        async with self.get_db() as db:
            prep = InterviewPrep(
                job_id=job_id,
                questions=questions,
                answers={},
                feedback={},
                confidence_scores={},
            )
            db.add(prep)
            await db.commit()
            await db.refresh(prep)
            return prep

    async def update_interview_prep(
        self,
        prep_id: str,
        answers: Dict[str, str],
        feedback: Optional[Dict[str, Any]] = None,
        confidence_scores: Optional[Dict[str, float]] = None,
    ) -> InterviewPrep:
        """Update interview prep with answers and feedback."""
        async with self.get_db() as db:
            prep = (
                await db.query(InterviewPrep)
                .filter(InterviewPrep.id == prep_id)
                .first()
            )
            if prep:
                prep.answers = answers
                if feedback:
                    prep.feedback = feedback
                if confidence_scores:
                    prep.confidence_scores = confidence_scores
                await db.commit()
                await db.refresh(prep)
            return prep

    # Query Operations
    async def get_cv_history(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get CV improvement history."""
        async with self.get_db() as db:
            improvements = (
                await db.query(CVImprovement)
                .filter(CVImprovement.cv_id == cv_id)
                .order_by(CVImprovement.created_at.desc())
                .all()
            )

            return [
                {
                    "id": imp.id,
                    "created_at": imp.created_at,
                    "changes": imp.changes,
                    "type": imp.improvement_type,
                    "status": imp.status,
                }
                for imp in improvements
            ]

    async def get_skill_assessments(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get all skill assessments for a CV."""
        async with self.get_db() as db:
            assessments = (
                await db.query(SkillAssessment)
                .filter(SkillAssessment.cv_id == cv_id)
                .join(Skill)
                .all()
            )

            return [
                {
                    "skill_name": assessment.skill.name,
                    "confidence_score": assessment.confidence_score,
                    "evidence": assessment.evidence,
                    "status": assessment.verification_status,
                }
                for assessment in assessments
            ]

    async def store_task_status(
        self, task_id: str, status: str, cv_id: str, job_id: str
    ) -> TaskStatus:
        """Store initial task status."""
        async with self.get_db() as db:
            task_status = TaskStatus(
                task_id=task_id, cv_id=cv_id, job_id=job_id, status=status
            )
            db.add(task_status)
            await db.commit()
            await db.refresh(task_status)
            return task_status

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current task status."""
        async with self.get_db() as db:
            result = await db.execute(
                select(TaskStatus).where(TaskStatus.task_id == task_id)
            )
            return result.scalar_one_or_none()

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> TaskStatus:
        """Update task status with results or error."""
        async with self.get_db() as db:
            task_status = await db.get(TaskStatus, task_id)
            if task_status:
                task_status.status = status
                task_status.result = result
                task_status.error = error
                task_status.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(task_status)
            return task_status

    async def get_analysis_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result for a task."""
        task_status = await self.get_task_status(task_id)
        if task_status and task_status.status == "completed":
            return task_status.result
        return None

    async def get_cv_analyses(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get all analyses for a CV."""
        async with self.get_db() as db:
            result = await db.execute(
                select(Analysis)
                .where(Analysis.cv_id == cv_id)
                .order_by(Analysis.created_at.desc())
            )
            analyses = result.scalars().all()

            return [
                {
                    "id": analysis.id,
                    "match_score": analysis.match_score,
                    "detailed_scores": analysis.detailed_scores,
                    "missing_skills": analysis.missing_skills,
                    "suggestions": analysis.suggestions,
                    "created_at": analysis.created_at,
                }
                for analysis in analyses
            ]

    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Get specific analysis by ID."""
        async with self.get_db() as db:
            return await db.get(Analysis, analysis_id)

    async def update_cv_content(self, cv_id: str, improvements: CVImprovement) -> CV:
        """Update CV content based on improvements."""
        async with self.get_db() as db:
            cv = await db.get(CV, cv_id)
            if not cv:
                raise ValueError(f"CV with id {cv_id} not found")

            # Increment version
            cv.version += 1
            cv.updated_at = datetime.utcnow()

            # Store improvement record
            improvement = CVImprovement(
                cv_id=cv_id,
                changes=improvements.changes,
                improvement_type=improvements.improvement_type,
                status="applied",
            )
            db.add(improvement)

            await db.commit()
            await db.refresh(cv)
            return cv

    async def get_latest_cv_version(self, cv_id: str) -> Optional[CV]:
        """Get the latest version of a CV."""
        async with self.get_db() as db:
            result = await db.execute(
                select(CV).where(CV.id == cv_id).order_by(CV.version.desc()).limit(1)
            )
            return result.scalar_one_or_none()
