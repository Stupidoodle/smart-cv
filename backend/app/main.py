from fastapi import FastAPI
from app.api.v1.endpoints import (
    cv,
    jobs,
    analysis,
    assistant,
    conversation,
    run,
    assessment,
    profile,
)
from app.core.config import settings

app = FastAPI(
    title="Applicant Tracking System for Applicants",
    description="A personalized ATS to help applicants optimize their job applications.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Include API routers
app.include_router(cv.router, prefix=f"{settings.API_V1_STR}/cv", tags=["CV"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])
app.include_router(
    analysis.router, prefix=f"{settings.API_V1_STR}/analysis", tags=["Analysis"]
)
app.include_router(
    assistant.router, prefix=f"{settings.API_V1_STR}/assistants", tags=["Assistants"]
)
app.include_router(
    conversation.router,
    prefix=f"{settings.API_V1_STR}/conversations",
    tags=["Conversations"],
)
app.include_router(run.router, prefix=f"{settings.API_V1_STR}/runs", tags=["Runs"])
app.include_router(
    assessment.router, prefix=f"{settings.API_V1_STR}/assessments", tags=["Assessments"]
)
app.include_router(
    profile.router, prefix=f"{settings.API_V1_STR}/profiles", tags=["Profiles"]
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the ATS for Applicants"}
