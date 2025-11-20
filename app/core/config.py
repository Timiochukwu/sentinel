"""Application configuration management"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Sentinel Fraud Detection"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"

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

    # Fraud Detection - Global Defaults
    RISK_THRESHOLD_HIGH: int = 70
    RISK_THRESHOLD_MEDIUM: int = 40
    MAX_PROCESSING_TIME_MS: int = 100

    # Multi-Vertical Support (NEW)
    # Per-vertical risk thresholds - can be overridden per client
    VERTICAL_RISK_THRESHOLDS: dict = {
        "lending": {"high": 70, "medium": 40},      # Traditional lending fraud
        "fintech": {"high": 65, "medium": 35},      # Fintech payments
        "payments": {"high": 65, "medium": 35},     # Payment processing
        "crypto": {"high": 60, "medium": 30},       # Crypto is higher risk
        "ecommerce": {"high": 75, "medium": 45},    # E-commerce more permissive
        "betting": {"high": 55, "medium": 25},      # Betting/gaming strict
        "gaming": {"high": 55, "medium": 25},
        "marketplace": {"high": 70, "medium": 40}   # Marketplace fraud
    }

    # Per-vertical rule weights for ML models
    # Example: crypto industry doubles the weight of suspicious_wallet rule
    VERTICAL_RULE_WEIGHTS: dict = {
        "crypto": {
            "new_wallet_high_value": 1.3,       # Emphasize wallet-based fraud
            "suspicious_wallet": 1.5,            # Critical for crypto
            "p2p_velocity": 1.2                  # P2P trading fraud
        },
        "betting": {
            "bonus_abuse": 1.4,                  # Strong penalty for bonus abuse
            "withdrawal_without_wagering": 1.5,  # Money laundering focus
            "device_sharing": 1.3                # Multi-accounting
        },
        "ecommerce": {
            "card_bin_fraud": 1.2,               # Focus on card fraud
            "shipping_mismatch": 1.1             # Shipping scams
        }
    }

    # Consortium Intelligence
    ENABLE_CONSORTIUM: bool = True
    CONSORTIUM_MIN_CLIENTS: int = 2
    # Per-vertical consortium behavior
    CONSORTIUM_VERTICAL_SENSITIVITY: dict = {
        "lending": 2,       # High sensitivity for loan stacking
        "crypto": 1,        # Lower sensitivity (lots of legitimate multiple wallets)
        "fintech": 2,       # High sensitivity
        "betting": 1,       # Lower (many legitimate multi-platform players)
    }

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
