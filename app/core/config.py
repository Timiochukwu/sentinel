"""Application configuration management"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Sentinel Fraud Detection"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT encoding. MUST be set via environment variable. Generate with: openssl rand -hex 32"
    )

    # API
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = 10000

    # Database
    DATABASE_URL: str = "postgresql://sentinel:sentinel_password@localhost:5432/sentinel"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # Security
    API_KEY_HEADER: str = "X-API-Key"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Fraud Detection
    RISK_THRESHOLD_HIGH: int = 70
    RISK_THRESHOLD_MEDIUM: int = 40
    MAX_PROCESSING_TIME_MS: int = 100

    # Consortium Intelligence
    ENABLE_CONSORTIUM: bool = True
    CONSORTIUM_MIN_CLIENTS: int = 2

    # Monitoring
    SENTRY_DSN: str = ""
    ENABLE_METRICS: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
