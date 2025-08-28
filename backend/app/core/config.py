"""Application configuration module."""
from typing import List, Optional, Union
from pydantic import BaseSettings, AnyHttpUrl, validator
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "BioNewsBot"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TIMEOUT: int = 60

    # Redis
    REDIS_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Analysis Settings
    ANALYSIS_BATCH_SIZE: int = 10
    ANALYSIS_RETRY_ATTEMPTS: int = 3
    ANALYSIS_RETRY_DELAY: int = 60
    ANALYSIS_SCHEDULE_HOUR: int = 2  # 2 AM daily

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600

    # Insights Priority Thresholds
    HIGH_PRIORITY_KEYWORDS: List[str] = [
        "FDA approval", "EMA approval", "regulatory approval",
        "Phase 3", "Phase III", "clinical trial results",
        "acquisition", "merger", "M&A", "acquired",
        "Series A", "Series B", "Series C", "funding round",
        "partnership", "collaboration", "strategic alliance"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
