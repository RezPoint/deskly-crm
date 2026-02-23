import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DesklyCRM"
    APP_VERSION: str = "0.3.2"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./desklycrm.db")
    AUTO_CREATE_DB: bool = os.getenv("AUTO_CREATE_DB", "1") == "1"
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
