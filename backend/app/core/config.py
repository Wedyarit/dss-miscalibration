from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    BACKEND_PORT: int = 8000
    API_KEY: str = "dev-key"
    CONF_THRESHOLD: float = 0.7
    ALLOWED_ORIGINS: str = "*"
    DATABASE_URL: str = "sqlite:///./data/database.db"
    DATA_DIR: str = "./data"
    MODELS_DIR: str = "./data/models"
    LOG_FILE: str = "./data/app.log"

    class Config:
        env_file = ".env"

settings = Settings()
