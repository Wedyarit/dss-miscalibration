from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_DIR / ".env"),
        extra="ignore",
    )

    BACKEND_PORT: int = 8000
    API_KEY: str = "dev-key"
    CONF_THRESHOLD: float = 0.7
    ALLOWED_ORIGINS: str = "*"

    DATA_DIR: Path = BACKEND_DIR / "data"
    MODELS_DIR: Path = BACKEND_DIR / "data" / "models"
    LOG_FILE: Path = BACKEND_DIR / "data" / "app.log"
    DATABASE_URL: str = f"sqlite:///{str(BACKEND_DIR / 'data' / 'database.db')}"

settings = Settings()
