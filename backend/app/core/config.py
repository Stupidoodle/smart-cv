import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql://ats_user:ats_password@db:5432/ats_applicant"
    OPEN_AI_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
