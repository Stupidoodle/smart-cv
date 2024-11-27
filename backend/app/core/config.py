import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./ats_applicant.db"

    class Config:
        env_file = ".env"

settings = Settings()
