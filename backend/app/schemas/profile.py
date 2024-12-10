from pydantic import BaseModel
from typing import Optional, List


class ProfileBase(BaseModel):
    name: str

    # Psychological Profiling
    feedback_preference: str
    confidence_level: str
    criticism_reaction: str
    rejection_reaction: str
    motivation: str

    # Focus and Improvement Profiling
    primary_goal: str
    analysis_goal: str
    feedback_type: str
    improvement_type: str
    explanation_type: str

    # Decision-Making and Problem-Solving Profiling
    challenge_approach: str
    priority_focus: str
    improvement_confidence: str

    # Personal Profiling
    role_reason: str
    role_type: List[str]
    application_status: str
    top_challenges: List[str]

    # CV and Skill Profiling
    cv_confidence: str
    cv_prep: str
    cv_struggles: List[str]

    # Tracking and Organization Profiling
    tracking_method: str
    search_improvements: List[str]

    # Misc
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "feedback_preference": "Balanced with a mix of positives and negatives.",
                "confidence_level": "Somewhat confident—I know it could use improvement.",
                "criticism_reaction": "I find it challenging but try to adapt.",
                "rejection_reaction": "It’s discouraging, but I keep going.",
                "motivation": "Personal growth and development.",
                "primary_goal": "Receive suggestions to improve my chances of success.",
                "analysis_goal": "Highlight specific areas where I can improve.",
                "feedback_type": "High-level overview with key insights.",
                "improvement_type": "By gaining hands-on experience through projects.",
                "explanation_type": "Very important—I want to understand every detail.",
                "challenge_approach": "Adapt and stay flexible.",
                "priority_focus": "I evaluate the impact of each task.",
                "improvement_confidence": "Neutral—I’m unsure where to start.",
                "role_reason": "Dissatisfied with current role.",
                "role_type": ["Full-time.", "Internship."],
                "application_status": "Actively applying.",
                "top_challenges": [
                    "Identifying skill gaps.",
                    "Difficulty tailoring my CV to job descriptions.",
                ],
                "cv_confidence": "Neutral.",
                "cv_prep": "Sometimes.",
                "cv_struggles": [
                    "Matching skills with job requirements.",
                    "Highlighting key achievements.",
                ],
                "tracking_method": "Spreadsheet.",
                "search_improvements": ["CV quality.", "Confidence in applying."],
                "github_url": "https://github.com/janedoe",
                "linkedin_url": "https://linkedin.com/in/janedoe",
            }
        }


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: Optional[str]

    # Psychological Profiling
    feedback_preference: Optional[str]
    confidence_level: Optional[str]
    criticism_reaction: Optional[str]
    rejection_reaction: Optional[str]
    motivation: Optional[str]

    # Focus and Improvement Profiling
    primary_goal: Optional[str]
    analysis_goal: Optional[str]
    feedback_type: Optional[str]
    improvement_type: Optional[str]
    explanation_type: Optional[str]

    # Decision-Making and Problem-Solving Profiling
    challenge_approach: Optional[str]
    priority_focus: Optional[str]
    improvement_confidence: Optional[str]

    # Personal Profiling
    role_reason: Optional[str]
    role_type: Optional[List[str]]
    application_status: Optional[str]
    top_challenges: Optional[List[str]]

    # CV and Skill Profiling
    cv_confidence: Optional[str]
    cv_prep: Optional[str]
    cv_struggles: Optional[List[str]]

    # Tracking and Organization Profiling
    tracking_method: Optional[str]
    search_improvements: Optional[List[str]]

    # Misc
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: int

    class Config:
        orm_mode = True
