from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "ORBIT AI Industrial Copilot"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://orbit:orbit@localhost:5432/orbit_ai"
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ML
    ml_model_dir: str = "ml/models"
    ml_retrain_on_startup: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
