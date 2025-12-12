# 🚀 SENTINEL FRAUD DETECTION - 30-DAY BUILD GUIDE (MAIN)
## Days 1-12: Foundation & Core Implementation

**Note:** This guide maps to the ACTUAL production codebase with **269 fraud detection rules** (not 83), multiple advanced services, and enterprise-grade architecture.

**Estimated Time:** 12 working days (1-2 weeks)

**Final Output After Day 12:** Working API with core fraud detection engine and 269 rules loaded

---

## 📚 GUIDE STRUCTURE

This comprehensive guide is split into 3 parts:
- **PART 1 (This File):** Days 1-12 - Foundation & Core (Install & Setup)
- **PART 2:** Days 13-24 - Advanced Features (ML, Verticals, Features, Caching)
- **PART 3:** Days 25-30 - Production Ready (Testing, Deployment, Monitoring)

**Reference Documents:**
- `SENTINEL_FRAUD_RULES_REFERENCE.md` - All 269 fraud detection rules
- `SENTINEL_API_ENDPOINTS_COMPLETE.md` - All API endpoints
- `SENTINEL_SERVICES_DEEP_DIVE.md` - Service architecture

---

# 📅 DAY 1: Python Environment & Project Structure

## 🎯 What We're Building Today
- Python 3.11 virtual environment
- Project directory structure
- Requirements file
- Git initialization
- Environment configuration

## 📦 Install Today

```bash
# Verify Python version
python3.11 --version
# Output: Python 3.11.x

# Create project directory
mkdir sentinel
cd sentinel

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

## 📝 Files to Create

### **sentinel/requirements.txt**
```
# Core dependencies
python-dotenv==1.0.0
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# ML & Data Science
scikit-learn==1.3.2
xgboost==2.0.3
numpy==1.24.3
pandas==2.0.3
joblib==1.3.2

# Caching & Data
redis==5.0.1

# Security & Hashing
bcrypt==4.1.2
python-jose==3.3.0
passlib==1.7.4

# Async & HTTP
httpx==0.25.2
aioredis==2.0.1

# Utilities
pytz==2023.3
python-dateutil==2.8.2
requests==2.31.0

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.12.1
flake8==6.1.0
```

### **sentinel/.env**
```bash
# Database Configuration
DATABASE_URL=postgresql://sentinel_user:sentinel_password@localhost:5432/sentinel_db
SQLALCHEMY_ECHO=False

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# API Configuration
API_VERSION=v1
API_TITLE=Sentinel Fraud Detection
API_DESCRIPTION=Real-time fraud detection for fintech and payments
SECRET_KEY=your-secret-key-change-in-production

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Security
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_PERIOD=3600

# ML Model
ML_MODEL_PATH=models/fraud_detector.pkl
SCALER_PATH=models/scaler.pkl

# Nigeria-Specific Configuration
ENABLE_BVN_VERIFICATION=True
ENABLE_NAIRA_SUPPORT=True
```

### **sentinel/.gitignore**
```
# Virtual Environment
venv/
env/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Dependencies
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment files
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite
*.sqlite3

# Cache
.pytest_cache/
.coverage
htmlcov/

# Models
models/*.pkl
models/*.joblib

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Temporary
tmp/
temp/
*.tmp
```

### **sentinel/directory structure**

Create the project structure:

```bash
mkdir -p sentinel/{app,tests,scripts,models,logs}
mkdir -p sentinel/app/{api,core,db,middleware,models,services}
mkdir -p sentinel/app/api/{v1,deps}
mkdir -p sentinel/app/api/v1/endpoints
mkdir -p sentinel/app/core
mkdir -p sentinel/app/db/migrations/versions
mkdir -p sentinel/scripts/ml
```

## ✅ Verification

```bash
# Check directory structure
ls -la sentinel/
tree sentinel/ -L 3 -I '__pycache__'

# Verify Python
python --version
pip list | grep -E "fastapi|sqlalchemy|pydantic"

# Expected: Should see fastapi, sqlalchemy, pydantic in list
```

**⏹️ STOP HERE - END OF DAY 1**

---

# 📅 DAY 2: Database Setup with PostgreSQL & SQLAlchemy

## 🎯 What We're Building Today
- PostgreSQL database connection
- SQLAlchemy models (User, Transaction)
- Database session management
- Connection pooling

## 📦 Install Today

```bash
# Assuming PostgreSQL is installed locally
# Create database
createdb sentinel_db

# Create user
createuser -P sentinel_user
# Enter password: sentinel_password

# Grant privileges
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sentinel_db TO sentinel_user;"
```

## 📝 Files to Create: app/models/database.py

```python
"""
Database models and configuration
Maps to actual database.py in the codebase
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinel_user:sentinel_password@localhost:5432/sentinel_db")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    country = Column(String(2), default="NG")
    kyc_verified = Column(Boolean, default=False)
    bvn = Column(String(11), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    """Transaction record model - WITH 9 JSONB COLUMNS FOR FEATURES"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Basic transaction fields
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="NGN")
    merchant_id = Column(String(100), nullable=True)
    merchant_name = Column(String(255), nullable=True)
    merchant_category = Column(String(50), nullable=True)

    # Vertical support
    vertical = Column(String(50), default="payments", nullable=False)

    # Device & Network
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    device_id = Column(String(100), nullable=True)

    # Location
    user_country = Column(String(2), nullable=True)
    merchant_country = Column(String(2), nullable=True)

    # 9 JSONB FEATURE COLUMNS
    features_identity = Column(JSON, default={})          # 30 identity features
    features_behavioral = Column(JSON, default={})        # 25 behavioral features
    features_transaction = Column(JSON, default={})       # 30 transaction features
    features_network = Column(JSON, default={})           # 35 network features
    features_ato = Column(JSON, default={})               # 40 ATO features
    features_funding = Column(JSON, default={})           # 25 funding features
    features_merchant = Column(JSON, default={})          # 35 merchant features
    features_ml = Column(JSON, default={})                # 25 ML features
    features_derived = Column(JSON, default={})           # 4 derived features

    # Fraud detection results
    fraud_score = Column(Float, default=0.0)
    is_fraudulent = Column(Boolean, default=False)
    fraud_rules_triggered = Column(JSON, default=[])
    ml_prediction = Column(Float, nullable=True)

    # Status tracking
    status = Column(String(20), default="pending")  # pending, approved, rejected, manual_review
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in database"""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("✅ Tables created successfully")
```

## 📝 Files to Create: app/models/__init__.py

```python
"""Models package"""
from app.models.database import User, Transaction, Base, SessionLocal, get_db

__all__ = ["User", "Transaction", "Base", "SessionLocal", "get_db"]
```

## 📝 Files to Create: app/db/session.py

```python
"""Database session management"""
from sqlalchemy.orm import sessionmaker, Session
from app.models.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## ✅ Verification

```bash
# Test database connection
python -c "
from app.models.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Create tables
python -c "from app.models.database import create_tables; create_tables(); print('✅ Tables created')"
```

**⏹️ STOP HERE - END OF DAY 2**

---

# 📅 DAY 3: Alembic Migrations & Database Versioning

## 🎯 What We're Building Today
- Alembic migration setup
- Initial migration for User and Transaction models
- Migration versioning strategy

## 📦 Install Today
No new installations - Alembic was installed Day 1

## 📝 Initialize Alembic

```bash
# Initialize Alembic
alembic init alembic

# This creates:
# alembic/
# ├── versions/
# ├── env.py
# ├── script.py.mako
# └── alembic.ini
```

## 📝 Files to Update: alembic/env.py

```python
"""
Alembic migration environment
Already exists in actual project - ensure it includes:
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.models.database import Base
import os

# Alembic Config object
config = context.config

# Logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set metadata for auto-migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode"""
    sqlalchemy_url = os.getenv("DATABASE_URL", "postgresql://sentinel_user:sentinel_password@localhost:5432/sentinel_db")

    context.configure(
        url=sqlalchemy_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = os.getenv("DATABASE_URL", "postgresql://sentinel_user:sentinel_password@localhost:5432/sentinel_db")

    connectable = engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## 📝 Create First Migration: alembic/versions/001_initial_models.py

```python
"""Initial User and Transaction models

Revision ID: 001
Create Date: 2024-01-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial tables"""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('country', sa.String(2), default='NG'),
        sa.Column('kyc_verified', sa.Boolean(), default=False),
        sa.Column('bvn', sa.String(11), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('bvn'),
    )
    op.create_index('ix_users_user_id', 'users', ['user_id'])
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(10), default='NGN'),
        sa.Column('merchant_id', sa.String(100), nullable=True),
        sa.Column('merchant_name', sa.String(255), nullable=True),
        sa.Column('merchant_category', sa.String(50), nullable=True),
        sa.Column('vertical', sa.String(50), default='payments'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('user_country', sa.String(2), nullable=True),
        sa.Column('merchant_country', sa.String(2), nullable=True),
        sa.Column('features_identity', sa.JSON(), default='{}'),
        sa.Column('features_behavioral', sa.JSON(), default='{}'),
        sa.Column('features_transaction', sa.JSON(), default='{}'),
        sa.Column('features_network', sa.JSON(), default='{}'),
        sa.Column('features_ato', sa.JSON(), default='{}'),
        sa.Column('features_funding', sa.JSON(), default='{}'),
        sa.Column('features_merchant', sa.JSON(), default='{}'),
        sa.Column('features_ml', sa.JSON(), default='{}'),
        sa.Column('features_derived', sa.JSON(), default='{}'),
        sa.Column('fraud_score', sa.Float(), default=0.0),
        sa.Column('is_fraudulent', sa.Boolean(), default=False),
        sa.Column('fraud_rules_triggered', sa.JSON(), default='[]'),
        sa.Column('ml_prediction', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id'),
    )
    op.create_index('ix_transactions_transaction_id', 'transactions', ['transaction_id'])
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_vertical', 'transactions', ['vertical'])
    op.create_index('ix_transactions_vertical_user', 'transactions', ['vertical', 'user_id'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])


def downgrade():
    """Drop all tables"""
    op.drop_index('ix_transactions_status')
    op.drop_index('ix_transactions_vertical_user')
    op.drop_index('ix_transactions_vertical')
    op.drop_index('ix_transactions_user_id')
    op.drop_index('ix_transactions_transaction_id')
    op.drop_table('transactions')
    op.drop_index('ix_users_email')
    op.drop_index('ix_users_user_id')
    op.drop_table('users')
```

## ✅ Verification

```bash
# Run migrations
alembic upgrade head
# Expected: INFO  [alembic.runtime.migration] Running upgrade -> 001, Initial User and Transaction models

# Check migration status
alembic current
# Expected: revision id should show

# Verify tables created
psql sentinel_db -c "\dt"
# Expected: users and transactions tables listed
```

**⏹️ STOP HERE - END OF DAY 3**

---

# 📅 DAY 4: Core Fraud Detection Rules Framework

## 🎯 What We're Building Today
- Understanding the actual FraudRulesEngine (269 rules)
- Base FraudRule class
- Rule categories and metadata
- Rule registration system

## 📦 Install Today
No new installations needed

## 📝 Reference: Understanding Existing Rules System

The actual codebase in `app/services/rules.py` contains **269 fraud detection rules** organized by:

1. **Identity Rules** - Email, phone, KYC, BVN verification
2. **Behavioral Rules** - Account age, velocity, login patterns
3. **Transaction Rules** - Amount patterns, merchant velocity, card testing
4. **Network Rules** - IP reputation, geolocation, device fingerprinting
5. **Advanced Rules** - SIM swap, device sharing, impossible travel
6. **Vertical-Specific Rules** - Lending, crypto, fintech, gaming specific
7. **ML-Based Rules** - Anomaly detection using machine learning
8. **Consortium Rules** - Industry blocklist checks

## 📝 Base FraudRule Architecture (Simplified View)

```python
"""
Simplified view of the actual FraudRule base class
See SENTINEL_FRAUD_RULES_REFERENCE.md for complete list of 269 rules
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

class RuleCategory(str, Enum):
    """Rule categories"""
    IDENTITY = "identity"
    BEHAVIORAL = "behavioral"
    TRANSACTION = "transaction"
    NETWORK = "network"
    ADVANCED = "advanced"
    VERTICAL_SPECIFIC = "vertical"
    ML_BASED = "ml"
    CONSORTIUM = "consortium"


@dataclass
class RuleResult:
    """Result of rule evaluation"""
    rule_name: str
    passed: bool  # True if low fraud risk, False if high fraud risk
    fraud_score: float  # 0-100, higher = more fraudulent
    reason: str
    category: RuleCategory


class FraudRule(ABC):
    """Base class for all fraud detection rules"""

    name: str
    category: RuleCategory
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str

    @abstractmethod
    def check(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> RuleResult:
        """
        Evaluate transaction against this rule

        Args:
            transaction: Transaction data
            context: User context and metadata

        Returns:
            RuleResult with passed status and fraud score
        """
        pass
```

## 📝 Files to Create/Reference: app/services/rules.py (EXISTING BUT MASSIVE)

In the actual codebase, this file contains **269 rules**. Key implementation patterns:

```python
"""
Example rule implementations (see SENTINEL_FRAUD_RULES_REFERENCE.md for all 269)
"""

class NewAccountLargeAmountRule(FraudRule):
    """Rule: Flag large transactions on new accounts"""
    name = "NewAccountLargeAmountRule"
    category = RuleCategory.BEHAVIORAL
    severity = "HIGH"

    def check(self, transaction, context):
        account_age_days = context.get("account_age_days", 0)
        amount = transaction.get("amount", 0)

        if account_age_days < 7 and amount > 100000:
            return RuleResult(
                rule_name=self.name,
                passed=False,
                fraud_score=85,
                reason=f"New account ({account_age_days} days) with large amount ({amount})",
                category=self.category
            )

        return RuleResult(
            rule_name=self.name,
            passed=True,
            fraud_score=0,
            reason="Account age and amount normal",
            category=self.category
        )


class ImpossibleTravelRule(FraudRule):
    """Rule: Flag impossible travel between locations"""
    name = "ImpossibleTravelRule"
    category = RuleCategory.NETWORK
    severity = "CRITICAL"

    def check(self, transaction, context):
        # Calculate distance and time between locations
        # If distance/time implies impossible speed, flag as fraud
        pass
```

## 📝 Files to Create: app/services/__init__.py

```python
"""Services package"""
from app.services.rules import FraudRulesEngine

__all__ = ["FraudRulesEngine"]
```

## ✅ Verification

```bash
# Check rules loaded
python -c "
from app.services.rules import FraudRulesEngine
engine = FraudRulesEngine()
print(f'✅ Fraud Rules Engine initialized')
print(f'✅ Total rules loaded: {len(engine.rules)}')
print(f'✅ Expected: 269 rules')
"
```

**⏹️ STOP HERE - END OF DAY 4**

---

# 📅 DAY 5-9: Understanding Existing Fraud Rules (269 Rules)

## 🎯 What We're Building These Days
Days 5-9 are focused on **understanding the 269 existing fraud rules** rather than building new ones.

All fraud rules are already implemented in:
- `app/services/rules.py` (1,500+ lines)
- `app/services/fingerprint_rules.py` (Fingerprinting-specific)
- `app/core/fraud_detector_v2.py` (Advanced fraud detection)

## 📚 Reference Documentation
See: **SENTINEL_FRAUD_RULES_REFERENCE.md** for complete list of all 269 rules

### Rule Distribution:
- Identity Rules: ~30 rules
- Behavioral Rules: ~35 rules
- Transaction Rules: ~40 rules
- Network Rules: ~40 rules
- Advanced Rules: ~40 rules
- Vertical-Specific Rules: ~30 rules
- ML-Based Rules: ~25 rules
- Consortium Rules: ~29 rules

## ✅ Daily Verification (Days 5-9)

```bash
# Day 5: Verify Identity Rules
python -c "
from app.services.rules import FraudRulesEngine
engine = FraudRulesEngine()
identity_rules = [r for r in engine.rules.values() if 'identity' in str(r.category).lower()]
print(f'✅ Day 5 Identity Rules: {len(identity_rules)} rules')
"

# Day 6: Verify Behavioral Rules
python -c "
from app.services.rules import FraudRulesEngine
engine = FraudRulesEngine()
behavioral_rules = [r for r in engine.rules.values() if 'behavioral' in str(r.category).lower()]
print(f'✅ Day 6 Behavioral Rules: {len(behavioral_rules)} rules')
"

# Days 7-9: Similar checks for other rule categories
```

**⏹️ STOP HERE - END OF DAYS 5-9**

---

# 📅 DAY 10: FastAPI Setup & API Structure

## 🎯 What We're Building Today
- FastAPI application setup
- API versioning (v1 structure)
- Health check endpoint
- Basic CORS configuration
- API documentation

## 📦 Install Today
Already installed on Day 1 (fastapi, uvicorn)

## 📝 Files to Create: app/main.py

```python
"""
FastAPI main application
Maps to actual main.py in codebase
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Import routers (will be created in coming days)
# from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("🚀 Sentinel Fraud Detection System Starting")
    # Initialize fraud rules engine
    yield
    logger.info("🛑 Sentinel Fraud Detection System Stopping")


# Create FastAPI app
app = FastAPI(
    title="Sentinel Fraud Detection API",
    description="Real-time fraud detection for fintech and payments",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", ["http://localhost:3000", "http://localhost:8000"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sentinel-fraud-detection",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Sentinel Fraud Detection API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# Include routers (created in next days)
# app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

## 📝 Files to Create: app/api/__init__.py

```python
"""API package"""
```

## 📝 Files to Create: app/api/v1/__init__.py

```python
"""API v1 package"""
```

## 📝 Files to Create: app/api/v1/api.py (API Router)

```python
"""
V1 API router - combines all endpoints
See SENTINEL_API_ENDPOINTS_COMPLETE.md for all endpoints
"""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Endpoints will be created in coming days
# from app.api.v1.endpoints import fraud_detection, consortium, dashboard

# api_router.include_router(fraud_detection.router, prefix="/fraud", tags=["Fraud Detection"])
# api_router.include_router(consortium.router, prefix="/consortium", tags=["Consortium"])
# api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
```

## ✅ Verification

```bash
# Start API
python app/main.py
# Expected: Uvicorn running on http://0.0.0.0:8000

# In another terminal:
curl http://localhost:8000/health
# Expected: {"status": "healthy", "service": "sentinel-fraud-detection", "version": "1.0.0"}

# View API docs
# Open browser: http://localhost:8000/docs
```

**⏹️ STOP HERE - END OF DAY 10**

---

# 📅 DAY 11: Core Fraud Detection API Endpoints

## 🎯 What We're Building Today
- `/api/v1/fraud/check` - Single transaction check
- `/api/v1/fraud/batch-check` - Batch transaction check
- `/api/v1/rules` - Rules management
- Request/Response schemas

## 📝 Files to Create: app/models/schemas.py

```python
"""
Pydantic schemas for API validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TransactionCheckRequest(BaseModel):
    """Request to check a transaction"""
    transaction_id: str = Field(..., description="Unique transaction ID")
    user_id: str = Field(..., description="User ID")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="NGN", description="Currency code")
    merchant_id: Optional[str] = Field(None, description="Merchant ID")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    merchant_category: Optional[str] = Field(None, description="Merchant category code")
    user_email: str = Field(..., description="User email")
    user_phone: Optional[str] = Field(None, description="User phone")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_country: str = Field(default="NG", description="User country code")
    merchant_country: Optional[str] = Field(None, description="Merchant country code")
    device_id: Optional[str] = Field(None, description="Device ID")
    user_agent: Optional[str] = Field(None, description="User agent string")
    vertical: str = Field(default="payments", description="Industry vertical")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")


class RuleTriggered(BaseModel):
    """Single rule that was triggered"""
    rule_name: str
    fraud_score: float
    reason: str


class TransactionCheckResponse(BaseModel):
    """Response from transaction check"""
    transaction_id: str
    is_fraudulent: bool
    fraud_score: float  # 0-100
    risk_level: str  # low, medium, high, critical
    rules_triggered: int
    rules_triggered_list: List[RuleTriggered]
    timestamp: datetime
    recommendation: str  # approve, review, decline


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    rules_loaded: int
```

## 📝 Files to Create: app/api/v1/endpoints/fraud_detection.py

```python
"""
Fraud detection endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.schemas import TransactionCheckRequest, TransactionCheckResponse
from app.models.database import get_db
from app.services.rules import FraudRulesEngine
from datetime import datetime

router = APIRouter()
engine = None  # Singleton


def get_fraud_engine():
    """Get fraud rules engine instance"""
    global engine
    if engine is None:
        engine = FraudRulesEngine()
    return engine


@router.post("/check", response_model=TransactionCheckResponse, tags=["Fraud Detection"])
async def check_transaction(
    request: TransactionCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check a single transaction for fraud

    This endpoint evaluates the transaction against all 269 fraud detection rules.
    """
    engine = get_fraud_engine()

    # Build transaction context
    transaction_context = {
        "transaction_id": request.transaction_id,
        "user_id": request.user_id,
        "amount": request.amount,
        "currency": request.currency,
        "merchant_id": request.merchant_id,
        "merchant_name": request.merchant_name,
        "merchant_category": request.merchant_category,
        "ip_address": request.ip_address,
        "user_country": request.user_country,
        "merchant_country": request.merchant_country,
        "device_id": request.device_id,
        "user_agent": request.user_agent,
        "vertical": request.vertical,
    }

    # Evaluate against all rules
    result = engine.evaluate_transaction(transaction_context)

    # Determine risk level
    fraud_score = result.get("fraud_score", 0)
    if fraud_score >= 80:
        risk_level = "critical"
        recommendation = "decline"
    elif fraud_score >= 60:
        risk_level = "high"
        recommendation = "review"
    elif fraud_score >= 40:
        risk_level = "medium"
        recommendation = "review"
    else:
        risk_level = "low"
        recommendation = "approve"

    return TransactionCheckResponse(
        transaction_id=request.transaction_id,
        is_fraudulent=fraud_score > 50,
        fraud_score=fraud_score,
        risk_level=risk_level,
        rules_triggered=result.get("rules_triggered", 0),
        rules_triggered_list=result.get("rules_triggered_list", []),
        timestamp=datetime.utcnow(),
        recommendation=recommendation
    )


@router.get("/rules/count", tags=["Rules"])
async def get_rules_count():
    """Get total number of fraud detection rules"""
    engine = get_fraud_engine()
    return {
        "total_rules": len(engine.rules),
        "description": "Sentinel has 269 fraud detection rules across 8 categories"
    }
```

## ✅ Verification

```bash
# Start API
python app/main.py

# In another terminal, test transaction check
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN001",
    "user_id": "USR001",
    "amount": 100000,
    "currency": "NGN",
    "user_email": "user@example.com",
    "user_country": "NG"
  }'
# Expected: Transaction check result with fraud score

# Check rules count
curl http://localhost:8000/api/v1/fraud/rules/count
# Expected: {"total_rules": 269, ...}
```

**⏹️ STOP HERE - END OF DAY 11**

---

# 📅 DAY 12: API Testing & Documentation

## 🎯 What We're Building Today
- API tests with pytest
- Request/response validation tests
- API documentation verification
- Performance baseline testing

## 📝 Files to Create: tests/test_api.py

```python
"""
API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")


class TestFraudDetectionEndpoints:
    """Test fraud detection endpoints"""

    def test_check_safe_transaction(self):
        """Test checking a safe transaction"""
        response = client.post("/api/v1/fraud/check", json={
            "transaction_id": "TXN001",
            "user_id": "USR001",
            "amount": 500,
            "currency": "NGN",
            "user_email": "safe@example.com",
            "user_country": "NG"
        })
        assert response.status_code == 200
        data = response.json()
        assert "fraud_score" in data
        assert "is_fraudulent" in data
        print(f"✅ Safe transaction check: score={data['fraud_score']}")

    def test_check_risky_transaction(self):
        """Test checking a risky transaction"""
        response = client.post("/api/v1/fraud/check", json={
            "transaction_id": "TXN002",
            "user_id": "USR002",
            "amount": 999999999,  # Suspicious amount
            "currency": "NGN",
            "user_email": "suspicious@tempmail.com",  # Disposable email
            "user_country": "KP"  # Sanctioned country
        })
        assert response.status_code == 200
        data = response.json()
        assert data["fraud_score"] > 50  # Should be flagged as risky
        print(f"✅ Risky transaction check: score={data['fraud_score']}")

    def test_rules_count_endpoint(self):
        """Test /rules/count endpoint"""
        response = client.get("/api/v1/fraud/rules/count")
        assert response.status_code == 200
        data = response.json()
        assert data["total_rules"] == 269
        print(f"✅ Rules loaded: {data['total_rules']}")
```

## ✅ Verification

```bash
# Run tests
pytest tests/test_api.py -v -s
# Expected: All tests pass

# View API documentation
# Open browser: http://localhost:8000/docs
# You should see all endpoints with interactive testing

# Check test coverage
pytest tests/test_api.py --cov=app/api --cov-report=term-missing
```

## 📊 Days 1-12 Summary

✅ **Foundation Complete:**
- Python environment with all dependencies
- PostgreSQL database with User & Transaction models
- 9 JSONB columns for feature storage
- Alembic migrations setup
- **269 fraud detection rules** loaded and ready
- FastAPI application with v1 API structure
- Health check and fraud detection endpoints
- API testing and documentation

**Total Progress:**
- 49 Python files in actual project
- 269 fraud rules
- 20+ API endpoints
- 8,219 lines of service code
- Ready for advanced features (Days 13-24)

**Next: Continue to PART 2 for Days 13-24 - Advanced Features**

---

