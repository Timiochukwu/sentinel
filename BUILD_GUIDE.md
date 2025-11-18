# Sentinel Fraud Detection System - Complete Build Guide

This comprehensive guide provides step-by-step instructions to recreate the entire Sentinel fraud detection platform from scratch. Follow these steps in order to build a production-ready fraud detection system.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Initialization](#2-project-initialization)
3. [Backend Core Infrastructure](#3-backend-core-infrastructure)
4. [Database Layer](#4-database-layer)
5. [Security & Configuration](#5-security--configuration)
6. [Fraud Detection Engine](#6-fraud-detection-engine)
7. [Services Layer](#7-services-layer)
8. [API Layer](#8-api-layer)
9. [Middleware](#9-middleware)
10. [Database Initialization](#10-database-initialization)
11. [ML Model Training](#11-ml-model-training)
12. [Frontend Development](#12-frontend-development)
13. [Testing](#13-testing)
14. [Containerization](#14-containerization)
15. [Deployment](#15-deployment)
16. [Documentation](#16-documentation)
17. [Verification & Testing](#17-verification--testing)

---

## 1. Prerequisites

### Required Software

Install the following software on your development machine:

```bash
# System Requirements
- Python 3.11+
- Node.js 18+ and npm 9+
- PostgreSQL 15+
- Redis 7+
- Git
- Docker & Docker Compose (for containerization)
```

### Installation Commands

**macOS:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11
brew install node
brew install postgresql@15
brew install redis
brew install git
brew install docker
```

**Linux (Ubuntu/Debian):**
```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install PostgreSQL
sudo apt install postgresql-15 postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install Git
sudo apt install git

# Install Docker
sudo apt install docker.io docker-compose
```

**Windows:**
```powershell
# Use Chocolatey package manager
choco install python --version=3.11
choco install nodejs
choco install postgresql15
choco install redis
choco install git
choco install docker-desktop
```

### Start Required Services

```bash
# Start PostgreSQL
# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Start Redis
# macOS
brew services start redis

# Linux
sudo systemctl start redis
sudo systemctl enable redis
```

---

## 2. Project Initialization

### Step 2.1: Create Project Directory

```bash
# Create main project directory
mkdir sentinel
cd sentinel

# Initialize git repository
git init
git branch -M main
```

### Step 2.2: Create Directory Structure

```bash
# Backend structure
mkdir -p app/{api/v1/endpoints,core,db,middleware,models,services}
mkdir -p scripts/{ml,data}
mkdir -p tests
mkdir -p models  # For ML models

# Frontend structure
mkdir -p frontend/{src/{components,pages,lib,utils,types},public}
```

### Step 2.3: Create .gitignore

Create `/sentinel/.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
ENV/
env/
.venv

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3
*.sql

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# macOS
.DS_Store

# Frontend
frontend/node_modules/
frontend/dist/
frontend/build/
frontend/.vite/

# Logs
*.log
logs/

# Models (tracked separately)
models/*.pkl
models/*.joblib
!models/.gitkeep

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# Docker
*.env.docker
docker-compose.override.yml
```

### Step 2.4: Create Initial README

Create `/sentinel/README.md`:

```markdown
# Sentinel - Nigerian Fraud Detection Platform

AI-powered fraud detection system for Nigerian financial services.

## Quick Start

See BUILD_GUIDE.md for complete setup instructions.

## Features

- Real-time fraud detection (<100ms)
- 29+ specialized fraud rules
- ML-powered risk scoring
- Device fingerprinting
- Consortium intelligence
- Beautiful 3D dashboard

## Tech Stack

- Backend: Python 3.11 + FastAPI
- Database: PostgreSQL 15
- Cache: Redis 7
- ML: XGBoost
- Frontend: React 18 + TypeScript + Three.js
```

---

## 3. Backend Core Infrastructure

### Step 3.1: Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3.2: Create requirements.txt

Create `/sentinel/requirements.txt`:

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Cache & Session
redis==5.0.1
hiredis==2.2.3

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==41.0.7
python-dotenv==1.0.0

# HTTP Client
httpx==0.25.2
requests==2.31.0

# Data Science & ML
scikit-learn==1.3.2
xgboost==2.0.2
numpy==1.26.2
pandas==2.1.3
joblib==1.3.2

# Utilities
python-dateutil==2.8.2
pytz==2023.3
phonenumbers==8.13.26

# Monitoring & Logging
sentry-sdk[fastapi]==1.38.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
structlog==23.2.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# Development
black==23.11.0
flake8==6.1.0
mypy==1.7.1
isort==5.12.0
```

### Step 3.3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3.4: Create Core Configuration

Create `/sentinel/app/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings and configuration"""

    # Application
    APP_NAME: str = "Sentinel Fraud Detection"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str

    # API
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = 10000

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Fraud Detection
    RISK_THRESHOLD_HIGH: int = 70
    RISK_THRESHOLD_MEDIUM: int = 40
    ENABLE_CONSORTIUM: bool = True
    CACHE_TTL: int = 300  # 5 minutes

    # External APIs
    NIBSS_API_URL: str = ""
    NIBSS_API_KEY: str = ""

    # Monitoring
    SENTRY_DSN: str = ""
    ENABLE_TRACING: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### Step 3.5: Create Environment Template

Create `/sentinel/.env.example`:

```bash
# Application
APP_NAME=Sentinel Fraud Detection
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-change-this-in-production-use-openssl-rand-hex-32

# Database
DATABASE_URL=postgresql://sentinel:sentinel_password@localhost:5432/sentinel
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# API
API_V1_PREFIX=/api/v1
API_RATE_LIMIT=10000

# Security
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Fraud Detection
RISK_THRESHOLD_HIGH=70
RISK_THRESHOLD_MEDIUM=40
ENABLE_CONSORTIUM=true
CACHE_TTL=300

# External APIs (Optional)
NIBSS_API_URL=
NIBSS_API_KEY=

# Monitoring (Optional)
SENTRY_DSN=
ENABLE_TRACING=false
```

**Important:** Copy and customize:
```bash
cp .env.example .env
# Edit .env and change SECRET_KEY and database credentials
```

### Step 3.6: Create Logging Configuration

Create `/sentinel/app/core/logging_config.py`:

```python
import logging
import structlog
from structlog.stdlib import LoggerFactory


def setup_logging():
    """Configure structured logging with structlog"""

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )


logger = structlog.get_logger()
```

### Step 3.7: Create Security Utilities

Create `/sentinel/app/core/security.py`:

```python
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_pii(data: str) -> str:
    """Hash PII data using SHA-256 for consortium sharing"""
    if not data:
        return ""
    return hashlib.sha256(data.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"sk_{secrets.token_urlsafe(32)}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        return None
```

### Step 3.8: Create Monitoring Setup

Create `/sentinel/app/core/monitoring.py`:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .config import settings


def setup_monitoring(app):
    """Setup OpenTelemetry tracing"""

    if settings.ENABLE_TRACING:
        # Set up tracing
        trace.set_tracer_provider(TracerProvider())

        # Add span processor
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

    return app
```

---

## 4. Database Layer

### Step 4.1: Create Database Session Manager

Create `/sentinel/app/db/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/db/session.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 4.2: Create Database Models

Create `/sentinel/app/models/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/models/database.py`:

```python
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    JSON, ForeignKey, Index, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class TransactionType(str, enum.Enum):
    LOAN_APPLICATION = "loan_application"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PURCHASE = "purchase"
    CARD_TRANSACTION = "card_transaction"
    BET_PLACEMENT = "bet_placement"
    BET_WITHDRAWAL = "bet_withdrawal"
    CRYPTO_DEPOSIT = "crypto_deposit"
    CRYPTO_WITHDRAWAL = "crypto_withdrawal"
    MARKETPLACE_LISTING = "marketplace_listing"
    MARKETPLACE_PURCHASE = "marketplace_purchase"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Industry(str, enum.Enum):
    FINTECH = "fintech"
    ECOMMERCE = "e-commerce"
    BETTING = "betting"
    CRYPTO = "crypto"
    MARKETPLACE = "marketplace"


class SubscriptionPlan(str, enum.Enum):
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Transaction(Base):
    """Transaction table - stores all fraud check requests and results"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # Transaction details
    user_id = Column(String(255), index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="NGN")
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    industry = Column(SQLEnum(Industry), default=Industry.FINTECH)

    # User information (hashed for privacy)
    bvn_hash = Column(String(64), index=True)
    phone_hash = Column(String(64), index=True)
    email_hash = Column(String(64), index=True)

    # Device information
    device_id = Column(String(255), index=True)
    device_fingerprint = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Location
    location_data = Column(JSON)

    # Fraud detection results
    risk_score = Column(Integer, nullable=False)  # 0-100
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    flags = Column(JSON)  # List of triggered fraud flags
    recommendation = Column(String(50))  # APPROVE, REVIEW, REJECT

    # Context data
    velocity_data = Column(JSON)
    device_history = Column(JSON)
    consortium_signals = Column(JSON)

    # Metadata
    processing_time_ms = Column(Float)
    cached = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Feedback
    actual_fraud = Column(Boolean, nullable=True)
    feedback_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client = relationship("Client", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index('idx_client_risk', 'client_id', 'risk_level'),
        Index('idx_client_created', 'client_id', 'created_at'),
        Index('idx_device_fingerprint', 'device_fingerprint', postgresql_using='gin'),
    )


class Client(Base):
    """Client table - API customers"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)

    # Authentication
    api_key = Column(String(255), unique=True, index=True, nullable=False)
    api_key_hash = Column(String(255), nullable=False)

    # Subscription
    subscription_plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.STARTER)
    rate_limit = Column(Integer, default=100)  # Requests per minute

    # Configuration
    industry = Column(SQLEnum(Industry), default=Industry.FINTECH)
    enabled_rules = Column(JSON)  # List of rule IDs to enable
    webhook_url = Column(String(500))
    webhook_secret = Column(String(255))

    # ML Settings
    use_ml_model = Column(Boolean, default=True)
    ml_threshold = Column(Float, default=0.7)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="client")


class ConsortiumIntelligence(Base):
    """Consortium intelligence - privacy-preserving fraud pattern sharing"""
    __tablename__ = "consortium_intelligence"

    id = Column(Integer, primary_key=True, index=True)

    # Hashed identifiers (for privacy)
    device_hash = Column(String(64), index=True)
    bvn_hash = Column(String(64), index=True)
    phone_hash = Column(String(64), index=True)
    email_hash = Column(String(64), index=True)

    # Aggregated signals
    fraud_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    client_count = Column(Integer, default=0)  # How many different clients saw this

    # Risk metrics
    fraud_rate = Column(Float)  # fraud_count / total_count
    risk_level = Column(SQLEnum(RiskLevel))

    # Metadata
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_device_hash', 'device_hash'),
        Index('idx_bvn_hash', 'bvn_hash'),
        Index('idx_phone_hash', 'phone_hash'),
        Index('idx_email_hash', 'email_hash'),
    )


class RuleAccuracy(Base):
    """Rule accuracy tracking for continuous learning"""
    __tablename__ = "rule_accuracy"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, unique=True, index=True, nullable=False)
    rule_name = Column(String(255), nullable=False)

    # Metrics
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    true_negatives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)

    # Calculated metrics
    precision = Column(Float)
    recall = Column(Float)
    accuracy = Column(Float)
    weight = Column(Float, default=1.0)  # Dynamic weight based on performance

    # Metadata
    total_evaluations = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VelocityCheck(Base):
    """Velocity tracking for fraud detection"""
    __tablename__ = "velocity_checks"

    id = Column(Integer, primary_key=True, index=True)

    # Identifier (hashed)
    identifier_hash = Column(String(64), index=True, nullable=False)
    identifier_type = Column(String(50))  # device, phone, email, bvn, ip

    # Time windows
    count_1min = Column(Integer, default=0)
    count_10min = Column(Integer, default=0)
    count_1hour = Column(Integer, default=0)
    count_24hour = Column(Integer, default=0)

    # Amounts (for loan stacking detection)
    amount_1hour = Column(Float, default=0)
    amount_24hour = Column(Float, default=0)

    # Metadata
    last_transaction = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_identifier_type', 'identifier_hash', 'identifier_type'),
    )
```

### Step 4.3: Create Pydantic Schemas

Create `/sentinel/app/models/schemas.py`:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    LOAN_APPLICATION = "loan_application"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PURCHASE = "purchase"
    CARD_TRANSACTION = "card_transaction"
    BET_PLACEMENT = "bet_placement"
    BET_WITHDRAWAL = "bet_withdrawal"
    CRYPTO_DEPOSIT = "crypto_deposit"
    CRYPTO_WITHDRAWAL = "crypto_withdrawal"
    MARKETPLACE_LISTING = "marketplace_listing"
    MARKETPLACE_PURCHASE = "marketplace_purchase"


class Industry(str, Enum):
    FINTECH = "fintech"
    ECOMMERCE = "e-commerce"
    BETTING = "betting"
    CRYPTO = "crypto"
    MARKETPLACE = "marketplace"


class LocationData(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "NG"


class DeviceFingerprint(BaseModel):
    visitor_id: str
    confidence: float
    browser: Optional[str] = None
    os: Optional[str] = None
    device: Optional[str] = None
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class TransactionCheckRequest(BaseModel):
    """Request model for fraud check"""
    transaction_id: str = Field(..., min_length=1, max_length=255)
    user_id: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="NGN", max_length=3)
    transaction_type: TransactionType
    industry: Industry = Industry.FINTECH

    # User PII (will be hashed)
    bvn: Optional[str] = Field(None, max_length=11)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None

    # Device information
    device_id: Optional[str] = None
    device_fingerprint: Optional[DeviceFingerprint] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Location
    location: Optional[LocationData] = None

    # Additional context
    metadata: Optional[Dict[str, Any]] = None


class FraudFlag(BaseModel):
    """Individual fraud flag"""
    rule_id: int
    rule_name: str
    severity: str  # low, medium, high, critical
    message: str
    confidence: float = Field(ge=0, le=1)


class TransactionCheckResponse(BaseModel):
    """Response model for fraud check"""
    transaction_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: str  # low, medium, high, critical
    recommendation: str  # APPROVE, REVIEW, REJECT
    flags: List[FraudFlag]
    processing_time_ms: float
    cached: bool = False
    consortium_match: bool = False


class BatchCheckRequest(BaseModel):
    """Batch fraud check request"""
    transactions: List[TransactionCheckRequest] = Field(..., max_items=100)


class BatchCheckResponse(BaseModel):
    """Batch fraud check response"""
    results: List[TransactionCheckResponse]
    total_processed: int
    processing_time_ms: float


class FeedbackRequest(BaseModel):
    """Feedback for fraud detection accuracy"""
    transaction_id: str
    actual_fraud: bool
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response"""
    message: str
    transaction_id: str


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_transactions: int
    fraud_detected: int
    fraud_rate: float
    avg_risk_score: float
    high_risk_count: int
    processing_time_avg: float


class TransactionHistory(BaseModel):
    """Transaction history item"""
    id: int
    transaction_id: str
    amount: float
    risk_score: int
    risk_level: str
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClientInfo(BaseModel):
    """Client information"""
    name: str
    subscription_plan: str
    rate_limit: int
    industry: str
    api_calls_today: int
```

### Step 4.4: Setup Database

```bash
# Create PostgreSQL database
# macOS/Linux
psql postgres -c "CREATE DATABASE sentinel;"
psql postgres -c "CREATE USER sentinel WITH PASSWORD 'sentinel_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE sentinel TO sentinel;"

# Windows (using psql from Command Prompt)
psql -U postgres -c "CREATE DATABASE sentinel;"
psql -U postgres -c "CREATE USER sentinel WITH PASSWORD 'sentinel_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sentinel TO sentinel;"
```

---

## 5. Security & Configuration

### Step 5.1: Create API Dependencies

Create `/sentinel/app/api/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/api/deps.py`:

```python
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Client


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def get_current_client(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> Client:
    """
    Validate API key and return client
    """
    # Look up client by API key
    client = db.query(Client).filter(Client.api_key == api_key).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client account is inactive"
        )

    return client
```

---

## 6. Fraud Detection Engine

### Step 6.1: Create Main Fraud Detector

Create `/sentinel/app/core/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/core/fraud_detector.py`:

```python
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.schemas import TransactionCheckRequest, FraudFlag
from app.models.database import Transaction, ConsortiumIntelligence
from app.services.rules import RulesEngine
from app.services.ml_detector import MLDetector
from app.services.consortium import ConsortiumService
from app.services.redis_service import RedisService
from app.core.security import hash_pii
from app.core.logging_config import logger


class FraudDetector:
    """Main fraud detection orchestrator"""

    def __init__(self, db: Session, redis: RedisService):
        self.db = db
        self.redis = redis
        self.rules_engine = RulesEngine(db, redis)
        self.ml_detector = MLDetector()
        self.consortium = ConsortiumService(db)

    async def check_transaction(
        self,
        request: TransactionCheckRequest,
        client_id: int
    ) -> Tuple[int, str, str, List[FraudFlag], Dict]:
        """
        Main fraud detection method

        Returns:
            Tuple of (risk_score, risk_level, recommendation, flags, context)
        """
        start_time = datetime.now()

        # Build context
        context = await self._build_context(request, client_id)

        # Run rules engine
        rule_flags, rule_score = await self.rules_engine.evaluate(
            request,
            context
        )

        # Run ML model (if enabled)
        ml_score = 0
        if context.get("use_ml", True):
            ml_score = await self.ml_detector.predict(request, context)

        # Check consortium intelligence
        consortium_signals = await self.consortium.check_signals(
            hash_pii(request.bvn or ""),
            hash_pii(request.phone or ""),
            hash_pii(request.email or ""),
            hash_pii(request.device_id or "")
        )

        # Calculate final risk score (weighted combination)
        risk_score = self._calculate_risk_score(
            rule_score,
            ml_score,
            consortium_signals
        )

        # Determine risk level and recommendation
        risk_level = self._get_risk_level(risk_score)
        recommendation = self._get_recommendation(risk_score, rule_flags)

        # Add consortium signals to flags if present
        if consortium_signals["match_found"]:
            rule_flags.append(FraudFlag(
                rule_id=0,
                rule_name="Consortium Match",
                severity="high",
                message=f"Device/user seen in {consortium_signals['fraud_rate']*100:.1f}% fraud cases across consortium",
                confidence=consortium_signals["fraud_rate"]
            ))

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            "fraud_check_completed",
            transaction_id=request.transaction_id,
            risk_score=risk_score,
            risk_level=risk_level,
            flags_count=len(rule_flags),
            processing_time_ms=processing_time
        )

        return risk_score, risk_level, recommendation, rule_flags, context

    async def _build_context(
        self,
        request: TransactionCheckRequest,
        client_id: int
    ) -> Dict:
        """Build context for fraud detection"""
        context = {
            "client_id": client_id,
            "timestamp": datetime.now(),
        }

        # Get velocity data
        if request.device_id:
            context["device_velocity"] = await self.redis.get_velocity(
                f"device:{hash_pii(request.device_id)}"
            )

        if request.phone:
            context["phone_velocity"] = await self.redis.get_velocity(
                f"phone:{hash_pii(request.phone)}"
            )

        if request.email:
            context["email_velocity"] = await self.redis.get_velocity(
                f"email:{hash_pii(request.email)}"
            )

        # Get device history
        if request.device_id:
            context["device_history"] = self._get_device_history(request.device_id)

        return context

    def _get_device_history(self, device_id: str) -> Dict:
        """Get historical transactions for device"""
        device_hash = hash_pii(device_id)

        transactions = self.db.query(Transaction).filter(
            Transaction.device_id == device_id
        ).order_by(Transaction.created_at.desc()).limit(10).all()

        return {
            "total_transactions": len(transactions),
            "fraud_count": sum(1 for t in transactions if t.risk_level in ["high", "critical"]),
            "avg_amount": sum(t.amount for t in transactions) / len(transactions) if transactions else 0
        }

    def _calculate_risk_score(
        self,
        rule_score: int,
        ml_score: float,
        consortium_signals: Dict
    ) -> int:
        """Calculate weighted risk score"""
        # Weights
        rule_weight = 0.5
        ml_weight = 0.3
        consortium_weight = 0.2

        # Combine scores
        final_score = (
            rule_score * rule_weight +
            ml_score * 100 * ml_weight +
            consortium_signals.get("fraud_rate", 0) * 100 * consortium_weight
        )

        return min(100, int(final_score))

    def _get_risk_level(self, risk_score: int) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 70:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"

    def _get_recommendation(self, risk_score: int, flags: List[FraudFlag]) -> str:
        """Generate recommendation"""
        # Check for critical flags
        critical_flags = [f for f in flags if f.severity == "critical"]
        if critical_flags:
            return "REJECT"

        if risk_score >= 70:
            return "REJECT"
        elif risk_score >= 40:
            return "REVIEW"
        else:
            return "APPROVE"
```

---

## 7. Services Layer

### Step 7.1: Create Services Directory

Create `/sentinel/app/services/__init__.py`:
```python
# Empty file
```

### Step 7.2: Create Redis Service

Create `/sentinel/app/services/redis_service.py`:

```python
import redis
from typing import Optional, Dict
from app.core.config import settings
from app.core.logging_config import logger


class RedisService:
    """Redis service for caching, velocity tracking, and rate limiting"""

    def __init__(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True
        )

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: str, ttl: int = None):
        """Set value in Redis with optional TTL"""
        try:
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))

    async def incr(self, key: str, ttl: int = None) -> int:
        """Increment counter"""
        try:
            value = self.client.incr(key)
            if ttl and value == 1:  # Set TTL only on first increment
                self.client.expire(key, ttl)
            return value
        except Exception as e:
            logger.error("redis_incr_error", key=key, error=str(e))
            return 0

    async def get_velocity(self, identifier: str) -> Dict:
        """Get velocity metrics for identifier"""
        try:
            return {
                "count_1min": int(self.client.get(f"velocity:{identifier}:1min") or 0),
                "count_10min": int(self.client.get(f"velocity:{identifier}:10min") or 0),
                "count_1hour": int(self.client.get(f"velocity:{identifier}:1hour") or 0),
                "count_24hour": int(self.client.get(f"velocity:{identifier}:24hour") or 0),
            }
        except Exception as e:
            logger.error("redis_velocity_error", identifier=identifier, error=str(e))
            return {"count_1min": 0, "count_10min": 0, "count_1hour": 0, "count_24hour": 0}

    async def track_velocity(self, identifier: str):
        """Track velocity for identifier across multiple time windows"""
        try:
            # 1 minute window
            await self.incr(f"velocity:{identifier}:1min", ttl=60)

            # 10 minute window
            await self.incr(f"velocity:{identifier}:10min", ttl=600)

            # 1 hour window
            await self.incr(f"velocity:{identifier}:1hour", ttl=3600)

            # 24 hour window
            await self.incr(f"velocity:{identifier}:24hour", ttl=86400)
        except Exception as e:
            logger.error("redis_track_velocity_error", identifier=identifier, error=str(e))


# Global instance
redis_service = RedisService()
```

### Step 7.3: Create Cache Service

Create `/sentinel/app/services/cache_service.py`:

```python
import json
import hashlib
from typing import Optional
from app.services.redis_service import RedisService
from app.models.schemas import TransactionCheckRequest, TransactionCheckResponse
from app.core.config import settings
from app.core.logging_config import logger


class CacheService:
    """Caching service for transaction results"""

    def __init__(self, redis: RedisService):
        self.redis = redis
        self.ttl = settings.CACHE_TTL

    def _generate_cache_key(self, request: TransactionCheckRequest) -> str:
        """Generate cache key from request"""
        # Create a hash of the request data
        request_dict = request.model_dump()
        request_str = json.dumps(request_dict, sort_keys=True)
        hash_value = hashlib.sha256(request_str.encode()).hexdigest()
        return f"fraud_check:{hash_value}"

    async def get(self, request: TransactionCheckRequest) -> Optional[TransactionCheckResponse]:
        """Get cached result"""
        try:
            cache_key = self._generate_cache_key(request)
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                logger.info("cache_hit", transaction_id=request.transaction_id)
                data = json.loads(cached_data)
                return TransactionCheckResponse(**data)

            return None
        except Exception as e:
            logger.error("cache_get_error", error=str(e))
            return None

    async def set(self, request: TransactionCheckRequest, response: TransactionCheckResponse):
        """Cache result"""
        try:
            cache_key = self._generate_cache_key(request)
            response_data = response.model_dump()
            response_data["cached"] = True
            await self.redis.set(cache_key, json.dumps(response_data), ttl=self.ttl)
            logger.info("cache_set", transaction_id=request.transaction_id)
        except Exception as e:
            logger.error("cache_set_error", error=str(e))
```

### Step 7.4: Create Rules Engine

Create `/sentinel/app/services/rules.py`:

```python
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.schemas import TransactionCheckRequest, FraudFlag, TransactionType, Industry
from app.services.redis_service import RedisService
from app.core.security import hash_pii
from datetime import datetime, timedelta


class RulesEngine:
    """Fraud detection rules engine"""

    def __init__(self, db: Session, redis: RedisService):
        self.db = db
        self.redis = redis

    async def evaluate(
        self,
        request: TransactionCheckRequest,
        context: Dict
    ) -> Tuple[List[FraudFlag], int]:
        """
        Evaluate all fraud rules

        Returns:
            Tuple of (flags, risk_score)
        """
        flags = []
        total_score = 0

        # Get all rule methods
        rules = [
            (1, self._rule_high_velocity_device, 15, "high"),
            (2, self._rule_high_velocity_phone, 15, "high"),
            (3, self._rule_unusual_amount, 10, "medium"),
            (4, self._rule_late_night_transaction, 5, "low"),
            (5, self._rule_new_device, 8, "medium"),
            (6, self._rule_loan_stacking, 20, "critical"),
            (7, self._rule_velocity_spike, 12, "high"),
            (8, self._rule_round_amount, 5, "low"),
            (9, self._rule_multiple_applications, 18, "critical"),
            (10, self._rule_device_history_fraud, 15, "high"),
        ]

        # Industry-specific rules
        if request.industry == Industry.ECOMMERCE:
            rules.extend([
                (16, self._rule_shipping_mismatch, 12, "high"),
                (17, self._rule_card_testing, 15, "high"),
            ])
        elif request.industry == Industry.BETTING:
            rules.extend([
                (20, self._rule_bonus_abuse, 10, "medium"),
                (21, self._rule_arbitrage_betting, 15, "high"),
            ])
        elif request.industry == Industry.CRYPTO:
            rules.extend([
                (24, self._rule_suspicious_wallet, 18, "critical"),
                (25, self._rule_rapid_deposits, 12, "high"),
            ])
        elif request.industry == Industry.MARKETPLACE:
            rules.extend([
                (27, self._rule_new_seller_fraud, 15, "high"),
                (28, self._rule_high_risk_category, 10, "medium"),
            ])

        # Execute all rules
        for rule_id, rule_func, score, severity in rules:
            try:
                is_triggered, message = await rule_func(request, context)
                if is_triggered:
                    flags.append(FraudFlag(
                        rule_id=rule_id,
                        rule_name=rule_func.__name__.replace("_rule_", "").replace("_", " ").title(),
                        severity=severity,
                        message=message,
                        confidence=0.8
                    ))
                    total_score += score
            except Exception as e:
                # Log error but continue with other rules
                pass

        # Cap score at 100
        total_score = min(100, total_score)

        return flags, total_score

    # Core Fintech Rules
    async def _rule_high_velocity_device(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 1: High velocity on device"""
        velocity = context.get("device_velocity", {})
        if velocity.get("count_1hour", 0) > 10:
            return True, f"Device made {velocity['count_1hour']} transactions in 1 hour"
        return False, ""

    async def _rule_high_velocity_phone(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 2: High velocity on phone"""
        velocity = context.get("phone_velocity", {})
        if velocity.get("count_1hour", 0) > 5:
            return True, f"Phone number used in {velocity['count_1hour']} transactions in 1 hour"
        return False, ""

    async def _rule_unusual_amount(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 3: Unusual transaction amount"""
        if request.amount > 1000000:  # > 1M NGN
            return True, f"Unusually high amount: ₦{request.amount:,.2f}"
        if request.amount < 100 and request.transaction_type == TransactionType.LOAN_APPLICATION:
            return True, f"Unusually low loan amount: ₦{request.amount:,.2f}"
        return False, ""

    async def _rule_late_night_transaction(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 4: Transaction during unusual hours"""
        hour = datetime.now().hour
        if 2 <= hour <= 5:  # 2 AM to 5 AM
            return True, f"Transaction at unusual hour: {hour}:00"
        return False, ""

    async def _rule_new_device(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 5: New device making large transaction"""
        device_history = context.get("device_history", {})
        if device_history.get("total_transactions", 0) == 0 and request.amount > 50000:
            return True, "New device attempting large transaction"
        return False, ""

    async def _rule_loan_stacking(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 6: Multiple loan applications (loan stacking)"""
        if request.transaction_type == TransactionType.LOAN_APPLICATION:
            velocity = context.get("phone_velocity", {})
            if velocity.get("count_24hour", 0) >= 3:
                return True, f"Multiple loan applications detected: {velocity['count_24hour']} in 24 hours"
        return False, ""

    async def _rule_velocity_spike(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 7: Sudden spike in transaction velocity"""
        velocity = context.get("device_velocity", {})
        if velocity.get("count_10min", 0) >= 3:
            return True, f"Rapid transactions: {velocity['count_10min']} in 10 minutes"
        return False, ""

    async def _rule_round_amount(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 8: Suspiciously round amount"""
        if request.amount % 10000 == 0 and request.amount >= 100000:
            return True, f"Suspiciously round amount: ₦{request.amount:,.2f}"
        return False, ""

    async def _rule_multiple_applications(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 9: Multiple applications from same user"""
        if request.bvn and request.transaction_type == TransactionType.LOAN_APPLICATION:
            velocity = context.get("phone_velocity", {})
            if velocity.get("count_1hour", 0) >= 2:
                return True, f"Multiple loan applications from same user in 1 hour"
        return False, ""

    async def _rule_device_history_fraud(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 10: Device has history of fraud"""
        device_history = context.get("device_history", {})
        total = device_history.get("total_transactions", 0)
        fraud = device_history.get("fraud_count", 0)
        if total > 0 and fraud / total > 0.5:
            return True, f"Device has {fraud}/{total} fraudulent transactions"
        return False, ""

    # E-commerce Rules
    async def _rule_shipping_mismatch(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 16: Shipping address mismatch"""
        # This would check if shipping location differs significantly from IP location
        # Simplified implementation
        return False, ""

    async def _rule_card_testing(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 17: Card testing pattern"""
        if request.transaction_type == TransactionType.PURCHASE:
            velocity = context.get("device_velocity", {})
            if velocity.get("count_10min", 0) >= 5 and request.amount < 1000:
                return True, "Potential card testing: multiple small transactions"
        return False, ""

    # Betting Rules
    async def _rule_bonus_abuse(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 20: Bonus abuse pattern"""
        if request.transaction_type == TransactionType.BET_PLACEMENT:
            device_history = context.get("device_history", {})
            if device_history.get("total_transactions", 0) == 0:
                return True, "New account with immediate betting activity"
        return False, ""

    async def _rule_arbitrage_betting(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 21: Arbitrage betting pattern"""
        # Simplified - would check for simultaneous bets on opposing outcomes
        return False, ""

    # Crypto Rules
    async def _rule_suspicious_wallet(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 24: Suspicious wallet address"""
        # Would check against known bad wallet addresses
        return False, ""

    async def _rule_rapid_deposits(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 25: Rapid deposits and withdrawals"""
        if request.transaction_type in [TransactionType.CRYPTO_DEPOSIT, TransactionType.CRYPTO_WITHDRAWAL]:
            velocity = context.get("device_velocity", {})
            if velocity.get("count_1hour", 0) >= 5:
                return True, f"Rapid crypto transactions: {velocity['count_1hour']} in 1 hour"
        return False, ""

    # Marketplace Rules
    async def _rule_new_seller_fraud(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 27: New seller with suspicious activity"""
        if request.transaction_type == TransactionType.MARKETPLACE_LISTING:
            device_history = context.get("device_history", {})
            if device_history.get("total_transactions", 0) == 0 and request.amount > 100000:
                return True, "New seller listing high-value item"
        return False, ""

    async def _rule_high_risk_category(self, request: TransactionCheckRequest, context: Dict) -> Tuple[bool, str]:
        """Rule 28: High-risk product category"""
        # Would check metadata for high-risk categories (electronics, gift cards, etc.)
        return False, ""
```

### Step 7.5: Create ML Detector

Create `/sentinel/app/services/ml_detector.py`:

```python
import os
import joblib
import numpy as np
from typing import Dict, Optional
from app.models.schemas import TransactionCheckRequest
from app.core.logging_config import logger


class MLDetector:
    """Machine learning fraud detector using XGBoost"""

    def __init__(self):
        self.model = None
        self.model_path = "models/fraud_model.pkl"
        self._load_model()

    def _load_model(self):
        """Load trained ML model"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info("ml_model_loaded", path=self.model_path)
            else:
                logger.warning("ml_model_not_found", path=self.model_path)
        except Exception as e:
            logger.error("ml_model_load_error", error=str(e))
            self.model = None

    async def predict(self, request: TransactionCheckRequest, context: Dict) -> float:
        """
        Predict fraud probability

        Returns:
            Float between 0 and 1
        """
        if self.model is None:
            return 0.0

        try:
            # Extract features
            features = self._extract_features(request, context)

            # Make prediction
            prediction = self.model.predict_proba([features])[0][1]

            return float(prediction)
        except Exception as e:
            logger.error("ml_prediction_error", error=str(e))
            return 0.0

    def _extract_features(self, request: TransactionCheckRequest, context: Dict) -> np.ndarray:
        """Extract features for ML model"""
        features = []

        # Amount features
        features.append(request.amount)
        features.append(np.log1p(request.amount))

        # Velocity features
        device_velocity = context.get("device_velocity", {})
        features.append(device_velocity.get("count_1min", 0))
        features.append(device_velocity.get("count_10min", 0))
        features.append(device_velocity.get("count_1hour", 0))
        features.append(device_velocity.get("count_24hour", 0))

        phone_velocity = context.get("phone_velocity", {})
        features.append(phone_velocity.get("count_1hour", 0))
        features.append(phone_velocity.get("count_24hour", 0))

        # Device history
        device_history = context.get("device_history", {})
        features.append(device_history.get("total_transactions", 0))
        features.append(device_history.get("fraud_count", 0))
        features.append(device_history.get("avg_amount", 0))

        # Time features
        hour = context["timestamp"].hour
        day_of_week = context["timestamp"].weekday()
        features.append(hour)
        features.append(day_of_week)
        features.append(1 if 2 <= hour <= 5 else 0)  # Late night flag

        # Transaction type (one-hot encoded)
        txn_types = [
            "loan_application", "transfer", "withdrawal",
            "purchase", "bet_placement", "crypto_deposit"
        ]
        for txn_type in txn_types:
            features.append(1 if request.transaction_type.value == txn_type else 0)

        return np.array(features)
```

### Step 7.6: Create Consortium Service

Create `/sentinel/app/services/consortium.py`:

```python
from typing import Dict
from sqlalchemy.orm import Session
from app.models.database import ConsortiumIntelligence
from app.core.logging_config import logger


class ConsortiumService:
    """Privacy-preserving consortium intelligence"""

    def __init__(self, db: Session):
        self.db = db

    async def check_signals(
        self,
        bvn_hash: str,
        phone_hash: str,
        email_hash: str,
        device_hash: str
    ) -> Dict:
        """
        Check consortium intelligence for fraud signals

        Returns dict with:
            - match_found: bool
            - fraud_rate: float (0-1)
            - client_count: int
        """
        try:
            # Check for any matching hashes
            matches = self.db.query(ConsortiumIntelligence).filter(
                (ConsortiumIntelligence.device_hash == device_hash) |
                (ConsortiumIntelligence.bvn_hash == bvn_hash) |
                (ConsortiumIntelligence.phone_hash == phone_hash) |
                (ConsortiumIntelligence.email_hash == email_hash)
            ).all()

            if not matches:
                return {
                    "match_found": False,
                    "fraud_rate": 0.0,
                    "client_count": 0
                }

            # Aggregate fraud rate
            total_fraud = sum(m.fraud_count for m in matches)
            total_transactions = sum(m.total_count for m in matches)
            client_count = max(m.client_count for m in matches)

            fraud_rate = total_fraud / total_transactions if total_transactions > 0 else 0

            return {
                "match_found": True,
                "fraud_rate": fraud_rate,
                "client_count": client_count,
                "fraud_count": total_fraud,
                "total_count": total_transactions
            }
        except Exception as e:
            logger.error("consortium_check_error", error=str(e))
            return {
                "match_found": False,
                "fraud_rate": 0.0,
                "client_count": 0
            }

    async def update_signals(
        self,
        bvn_hash: str,
        phone_hash: str,
        email_hash: str,
        device_hash: str,
        is_fraud: bool,
        client_id: int
    ):
        """Update consortium intelligence"""
        try:
            # Update or create entries for each identifier
            for hash_value, hash_type in [
                (device_hash, "device"),
                (bvn_hash, "bvn"),
                (phone_hash, "phone"),
                (email_hash, "email")
            ]:
                if hash_value:
                    await self._update_hash_entry(hash_value, hash_type, is_fraud, client_id)
        except Exception as e:
            logger.error("consortium_update_error", error=str(e))

    async def _update_hash_entry(self, hash_value: str, hash_type: str, is_fraud: bool, client_id: int):
        """Update single hash entry"""
        field_name = f"{hash_type}_hash"

        entry = self.db.query(ConsortiumIntelligence).filter(
            getattr(ConsortiumIntelligence, field_name) == hash_value
        ).first()

        if entry:
            # Update existing
            entry.total_count += 1
            if is_fraud:
                entry.fraud_count += 1
            entry.fraud_rate = entry.fraud_count / entry.total_count
            # Update client count (approximate - would need more sophisticated tracking)
            entry.client_count = max(entry.client_count, 1)
        else:
            # Create new
            entry = ConsortiumIntelligence(
                **{field_name: hash_value},
                fraud_count=1 if is_fraud else 0,
                total_count=1,
                fraud_rate=1.0 if is_fraud else 0.0,
                client_count=1,
                risk_level="high" if is_fraud else "low"
            )
            self.db.add(entry)

        self.db.commit()
```

### Step 7.7: Create Additional Services

Create `/sentinel/app/services/webhook.py`:

```python
import hmac
import hashlib
import httpx
from typing import Dict
from app.core.logging_config import logger


async def send_webhook(
    url: str,
    secret: str,
    payload: Dict
):
    """Send webhook notification"""
    try:
        # Generate HMAC signature
        signature = hmac.new(
            secret.encode(),
            str(payload).encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-Sentinel-Signature": signature,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        logger.info("webhook_sent", url=url, status=response.status_code)
    except Exception as e:
        logger.error("webhook_error", url=url, error=str(e))
```

Create `/sentinel/app/services/bvn_verification.py`:

```python
from typing import Optional, Dict
import httpx
from app.core.config import settings
from app.core.logging_config import logger


async def verify_bvn(bvn: str, name: str, phone: str) -> Dict:
    """Verify BVN against NIBSS/NIMC"""
    try:
        # In production, integrate with NIBSS API
        # This is a mock implementation
        if settings.NIBSS_API_URL and settings.NIBSS_API_KEY:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.NIBSS_API_URL}/verify",
                    json={"bvn": bvn, "name": name, "phone": phone},
                    headers={"Authorization": f"Bearer {settings.NIBSS_API_KEY}"}
                )
                return response.json()

        # Mock response
        return {
            "verified": True,
            "match_score": 0.95,
            "name_match": True,
            "phone_match": True
        }
    except Exception as e:
        logger.error("bvn_verification_error", error=str(e))
        return {
            "verified": False,
            "error": str(e)
        }
```

Create `/sentinel/app/services/learning.py`:

```python
from sqlalchemy.orm import Session
from app.models.database import RuleAccuracy, Transaction
from app.core.logging_config import logger


class LearningService:
    """Continuous learning from feedback"""

    def __init__(self, db: Session):
        self.db = db

    async def process_feedback(self, transaction_id: str, actual_fraud: bool):
        """Process feedback to update rule accuracy"""
        try:
            # Get transaction
            transaction = self.db.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()

            if not transaction:
                return

            # Update rule accuracy for each triggered flag
            if transaction.flags:
                for flag in transaction.flags:
                    await self._update_rule_accuracy(
                        flag["rule_id"],
                        actual_fraud,
                        transaction.risk_level == "high"
                    )
        except Exception as e:
            logger.error("learning_process_error", error=str(e))

    async def _update_rule_accuracy(self, rule_id: int, actual_fraud: bool, predicted_fraud: bool):
        """Update accuracy metrics for a rule"""
        try:
            rule_acc = self.db.query(RuleAccuracy).filter(
                RuleAccuracy.rule_id == rule_id
            ).first()

            if not rule_acc:
                rule_acc = RuleAccuracy(rule_id=rule_id, rule_name=f"Rule {rule_id}")
                self.db.add(rule_acc)

            # Update confusion matrix
            if actual_fraud and predicted_fraud:
                rule_acc.true_positives += 1
            elif not actual_fraud and predicted_fraud:
                rule_acc.false_positives += 1
            elif not actual_fraud and not predicted_fraud:
                rule_acc.true_negatives += 1
            else:
                rule_acc.false_negatives += 1

            # Calculate metrics
            tp = rule_acc.true_positives
            fp = rule_acc.false_positives
            tn = rule_acc.true_negatives
            fn = rule_acc.false_negatives

            rule_acc.precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            rule_acc.recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            rule_acc.accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
            rule_acc.total_evaluations += 1

            # Adjust weight based on accuracy
            rule_acc.weight = rule_acc.accuracy

            self.db.commit()
        except Exception as e:
            logger.error("rule_accuracy_update_error", rule_id=rule_id, error=str(e))
```

---

## 8. API Layer

### Step 8.1: Create API Router

Create `/sentinel/app/api/v1/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/api/v1/api.py`:

```python
from fastapi import APIRouter
from app.api.v1.endpoints import fraud_detection, feedback, dashboard, consortium

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    fraud_detection.router,
    tags=["fraud-detection"]
)

api_router.include_router(
    feedback.router,
    tags=["feedback"]
)

api_router.include_router(
    dashboard.router,
    tags=["dashboard"]
)

api_router.include_router(
    consortium.router,
    tags=["consortium"]
)
```

### Step 8.2: Create Fraud Detection Endpoints

Create `/sentinel/app/api/v1/endpoints/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/api/v1/endpoints/fraud_detection.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.api.deps import get_current_client
from app.db.session import get_db
from app.models.database import Transaction, Client
from app.models.schemas import (
    TransactionCheckRequest,
    TransactionCheckResponse,
    BatchCheckRequest,
    BatchCheckResponse,
    FraudFlag
)
from app.core.fraud_detector import FraudDetector
from app.services.redis_service import redis_service
from app.services.cache_service import CacheService
from app.core.security import hash_pii
from app.core.logging_config import logger

router = APIRouter()
cache_service = CacheService(redis_service)


@router.post("/check-transaction", response_model=TransactionCheckResponse)
async def check_transaction(
    request: TransactionCheckRequest,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Check single transaction for fraud"""
    start_time = datetime.now()

    # Check cache first
    cached_result = await cache_service.get(request)
    if cached_result:
        return cached_result

    # Create fraud detector
    detector = FraudDetector(db, redis_service)

    # Run fraud detection
    risk_score, risk_level, recommendation, flags, context = await detector.check_transaction(
        request,
        client.id
    )

    processing_time = (datetime.now() - start_time).total_seconds() * 1000

    # Track velocity
    if request.device_id:
        await redis_service.track_velocity(f"device:{hash_pii(request.device_id)}")
    if request.phone:
        await redis_service.track_velocity(f"phone:{hash_pii(request.phone)}")

    # Save transaction
    transaction = Transaction(
        transaction_id=request.transaction_id,
        client_id=client.id,
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
        transaction_type=request.transaction_type,
        industry=request.industry,
        bvn_hash=hash_pii(request.bvn or ""),
        phone_hash=hash_pii(request.phone or ""),
        email_hash=hash_pii(request.email or ""),
        device_id=request.device_id,
        device_fingerprint=request.device_fingerprint.model_dump() if request.device_fingerprint else None,
        ip_address=request.ip_address,
        user_agent=request.user_agent,
        location_data=request.location.model_dump() if request.location else None,
        risk_score=risk_score,
        risk_level=risk_level,
        flags=[f.model_dump() for f in flags],
        recommendation=recommendation,
        processing_time_ms=processing_time,
        cached=False
    )
    db.add(transaction)
    db.commit()

    # Create response
    response = TransactionCheckResponse(
        transaction_id=request.transaction_id,
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=recommendation,
        flags=flags,
        processing_time_ms=processing_time,
        cached=False,
        consortium_match=context.get("consortium_signals", {}).get("match_found", False)
    )

    # Cache result
    await cache_service.set(request, response)

    # Send webhook if configured
    if client.webhook_url and risk_level in ["high", "critical"]:
        from app.services.webhook import send_webhook
        await send_webhook(
            client.webhook_url,
            client.webhook_secret,
            response.model_dump()
        )

    return response


@router.post("/check-transactions-batch", response_model=BatchCheckResponse)
async def check_transactions_batch(
    request: BatchCheckRequest,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Check multiple transactions in batch"""
    start_time = datetime.now()

    results = []
    for txn in request.transactions:
        try:
            result = await check_transaction(txn, client, db)
            results.append(result)
        except Exception as e:
            logger.error("batch_transaction_error", transaction_id=txn.transaction_id, error=str(e))
            # Continue with other transactions

    processing_time = (datetime.now() - start_time).total_seconds() * 1000

    return BatchCheckResponse(
        results=results,
        total_processed=len(results),
        processing_time_ms=processing_time
    )


@router.get("/transaction/{transaction_id}", response_model=dict)
async def get_transaction(
    transaction_id: str,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get transaction details"""
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id,
        Transaction.client_id == client.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "transaction_id": transaction.transaction_id,
        "amount": transaction.amount,
        "risk_score": transaction.risk_score,
        "risk_level": transaction.risk_level,
        "recommendation": transaction.recommendation,
        "flags": transaction.flags,
        "created_at": transaction.created_at,
        "actual_fraud": transaction.actual_fraud
    }
```

### Step 8.3: Create Feedback Endpoints

Create `/sentinel/app/api/v1/endpoints/feedback.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_current_client
from app.db.session import get_db
from app.models.database import Transaction, Client
from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.learning import LearningService
from app.services.consortium import ConsortiumService
from app.core.security import hash_pii

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Submit feedback on fraud detection accuracy"""

    # Get transaction
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == request.transaction_id,
        Transaction.client_id == client.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update transaction
    transaction.actual_fraud = request.actual_fraud
    transaction.feedback_timestamp = datetime.now()
    db.commit()

    # Process feedback for learning
    learning_service = LearningService(db)
    await learning_service.process_feedback(request.transaction_id, request.actual_fraud)

    # Update consortium intelligence
    consortium = ConsortiumService(db)
    await consortium.update_signals(
        transaction.bvn_hash,
        transaction.phone_hash,
        transaction.email_hash,
        hash_pii(transaction.device_id or ""),
        request.actual_fraud,
        client.id
    )

    return FeedbackResponse(
        message="Feedback received successfully",
        transaction_id=request.transaction_id
    )
```

### Step 8.4: Create Dashboard Endpoints

Create `/sentinel/app/api/v1/endpoints/dashboard.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from app.api.deps import get_current_client
from app.db.session import get_db
from app.models.database import Transaction, Client
from app.models.schemas import DashboardStats, TransactionHistory, ClientInfo

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    days: int = Query(default=7, ge=1, le=90),
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""

    since = datetime.now() - timedelta(days=days)

    # Total transactions
    total = db.query(func.count(Transaction.id)).filter(
        Transaction.client_id == client.id,
        Transaction.created_at >= since
    ).scalar()

    # High risk transactions
    high_risk = db.query(func.count(Transaction.id)).filter(
        Transaction.client_id == client.id,
        Transaction.risk_level.in_(["high", "critical"]),
        Transaction.created_at >= since
    ).scalar()

    # Average risk score
    avg_risk = db.query(func.avg(Transaction.risk_score)).filter(
        Transaction.client_id == client.id,
        Transaction.created_at >= since
    ).scalar() or 0

    # Average processing time
    avg_time = db.query(func.avg(Transaction.processing_time_ms)).filter(
        Transaction.client_id == client.id,
        Transaction.created_at >= since
    ).scalar() or 0

    fraud_rate = (high_risk / total * 100) if total > 0 else 0

    return DashboardStats(
        total_transactions=total or 0,
        fraud_detected=high_risk or 0,
        fraud_rate=fraud_rate,
        avg_risk_score=float(avg_risk),
        high_risk_count=high_risk or 0,
        processing_time_avg=float(avg_time)
    )


@router.get("/transactions", response_model=List[TransactionHistory])
async def get_transactions(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    risk_level: str = Query(default=None),
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get transaction history"""

    query = db.query(Transaction).filter(Transaction.client_id == client.id)

    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level)

    transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

    return [
        TransactionHistory(
            id=t.id,
            transaction_id=t.transaction_id,
            amount=t.amount,
            risk_score=t.risk_score,
            risk_level=t.risk_level,
            recommendation=t.recommendation,
            created_at=t.created_at
        )
        for t in transactions
    ]


@router.get("/client-info", response_model=ClientInfo)
async def get_client_info(
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get client information"""

    # Get today's API call count
    today = datetime.now().date()
    api_calls = db.query(func.count(Transaction.id)).filter(
        Transaction.client_id == client.id,
        func.date(Transaction.created_at) == today
    ).scalar()

    return ClientInfo(
        name=client.name,
        subscription_plan=client.subscription_plan.value,
        rate_limit=client.rate_limit,
        industry=client.industry.value,
        api_calls_today=api_calls or 0
    )
```

### Step 8.5: Create Consortium Endpoints

Create `/sentinel/app/api/v1/endpoints/consortium.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict

from app.api.deps import get_current_client
from app.db.session import get_db
from app.models.database import ConsortiumIntelligence, Client

router = APIRouter()


@router.get("/consortium-insights", response_model=Dict)
async def get_consortium_insights(
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get consortium intelligence insights"""

    # Total fraud patterns in consortium
    total_patterns = db.query(func.count(ConsortiumIntelligence.id)).scalar()

    # High risk patterns
    high_risk = db.query(func.count(ConsortiumIntelligence.id)).filter(
        ConsortiumIntelligence.risk_level == "high"
    ).scalar()

    # Average fraud rate
    avg_fraud_rate = db.query(func.avg(ConsortiumIntelligence.fraud_rate)).scalar() or 0

    return {
        "total_patterns": total_patterns or 0,
        "high_risk_patterns": high_risk or 0,
        "avg_fraud_rate": float(avg_fraud_rate),
        "consortium_enabled": True
    }
```

### Step 8.6: Create Main Application

Create `/sentinel/app/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/main.py`:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.core.monitoring import setup_monitoring
from app.api.v1.api import api_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.db.session import engine, Base


# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("application_starting", version=settings.APP_VERSION)

    # Create database tables
    Base.metadata.create_all(bind=engine)

    yield

    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered fraud detection for Nigerian financial services",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup monitoring
setup_monitoring(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

---

## 9. Middleware

### Step 9.1: Create Rate Limiting Middleware

Create `/sentinel/app/middleware/__init__.py`:
```python
# Empty file
```

Create `/sentinel/app/middleware/rate_limit.py`:

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.redis_service import redis_service
from app.core.logging_config import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if api_key:
            # Check rate limit
            rate_limit_key = f"rate_limit:{api_key}"
            current_count = await redis_service.incr(rate_limit_key, ttl=60)

            # Get client's rate limit (would query database in production)
            # For now, use default limit
            rate_limit = 1000  # Default: 1000 requests per minute

            if current_count > rate_limit:
                logger.warning("rate_limit_exceeded", api_key=api_key[:10])
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - current_count))
            response.headers["X-RateLimit-Reset"] = "60"

            return response

        return await call_next(request)
```

---

## 10. Database Initialization

### Step 10.1: Create Database Initialization Script

Create `/sentinel/scripts/__init__.py`:
```python
# Empty file
```

Create `/sentinel/scripts/init_db.py`:

```python
#!/usr/bin/env python3
"""Initialize database with tables and sample data"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.session import engine, Base, SessionLocal
from app.models.database import Client, Transaction, ConsortiumIntelligence, RuleAccuracy
from app.core.security import generate_api_key, hash_password, hash_pii
import random
from datetime import datetime, timedelta


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")


def create_demo_client(db: Session):
    """Create demo client"""
    print("\nCreating demo client...")

    api_key = generate_api_key()

    client = Client(
        name="Demo Financial Services",
        email="demo@example.com",
        api_key=api_key,
        api_key_hash=hash_password(api_key),
        subscription_plan="pro",
        rate_limit=1000,
        industry="fintech",
        is_active=True
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    print(f"✓ Demo client created")
    print(f"  Client ID: {client.id}")
    print(f"  API Key: {api_key}")
    print(f"  Email: {client.email}")
    print(f"\n⚠️  SAVE THIS API KEY - IT WON'T BE SHOWN AGAIN!")

    return client


def create_sample_transactions(db: Session, client: Client, count: int = 20):
    """Create sample transactions"""
    print(f"\nCreating {count} sample transactions...")

    transaction_types = ["loan_application", "transfer", "withdrawal", "purchase"]
    risk_levels = ["low", "medium", "high"]

    for i in range(count):
        transaction = Transaction(
            transaction_id=f"TXN{i+1:06d}",
            client_id=client.id,
            user_id=f"USER{random.randint(1, 100):04d}",
            amount=random.uniform(1000, 500000),
            currency="NGN",
            transaction_type=random.choice(transaction_types),
            industry="fintech",
            bvn_hash=hash_pii(f"12345678{random.randint(10, 99)}"),
            phone_hash=hash_pii(f"080{random.randint(10000000, 99999999)}"),
            device_id=f"DEVICE{random.randint(1, 50):03d}",
            ip_address=f"192.168.1.{random.randint(1, 255)}",
            risk_score=random.randint(0, 100),
            risk_level=random.choice(risk_levels),
            recommendation="APPROVE" if random.random() > 0.3 else "REVIEW",
            flags=[],
            processing_time_ms=random.uniform(50, 200),
            created_at=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        db.add(transaction)

    db.commit()
    print(f"✓ Created {count} sample transactions")


def initialize_rule_accuracy(db: Session):
    """Initialize rule accuracy tracking"""
    print("\nInitializing rule accuracy tracking...")

    rules = [
        (1, "High Velocity Device"),
        (2, "High Velocity Phone"),
        (3, "Unusual Amount"),
        (4, "Late Night Transaction"),
        (5, "New Device"),
        (6, "Loan Stacking"),
        (7, "Velocity Spike"),
        (8, "Round Amount"),
        (9, "Multiple Applications"),
        (10, "Device History Fraud"),
    ]

    for rule_id, rule_name in rules:
        rule_acc = RuleAccuracy(
            rule_id=rule_id,
            rule_name=rule_name,
            precision=0.8,
            recall=0.7,
            accuracy=0.75,
            weight=1.0
        )
        db.add(rule_acc)

    db.commit()
    print(f"✓ Initialized {len(rules)} rules")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("Sentinel Database Initialization")
    print("=" * 60)

    # Create tables
    create_tables()

    # Create database session
    db = SessionLocal()

    try:
        # Create demo client
        client = create_demo_client(db)

        # Create sample transactions
        create_sample_transactions(db, client, count=20)

        # Initialize rule accuracy
        initialize_rule_accuracy(db)

        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

Make the script executable:
```bash
chmod +x scripts/init_db.py
```

### Step 10.2: Run Database Initialization

```bash
# Activate virtual environment
source venv/bin/activate

# Run initialization script
python scripts/init_db.py
```

---

**(Continuing with remaining sections...)**

Due to length constraints, I'll create a separate continuation file. Let me know if you'd like me to continue with Steps 11-17 in the response!
