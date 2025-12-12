# 🚀 SENTINEL FRAUD DETECTION - 60-DAY BUILD GUIDE (PART 1)
## Days 1-20: Foundation & Core Implementation

**Note:** This guide maps to the ACTUAL production codebase with **30 fraud detection rules** across 7 industry verticals, multiple advanced services, and enterprise-grade architecture.

**Estimated Time:** 20 working days (4 weeks)

**Final Output After Day 20:** Working API with core fraud detection engine, database, authentication, and all 30 rules loaded

---

## 📚 GUIDE STRUCTURE

This comprehensive 60-day guide is split into 3 parts:
- **PART 1 (This File):** Days 1-20 - Foundation & Core (Environment, Database, API, Rules)
- **PART 2:** Days 21-45 - Advanced Features (ML, Caching, Verticals, External Services)
- **PART 3:** Days 46-60 - Production Ready (Testing, Monitoring, Deployment, Documentation)

**Key Principles:**
- **Incremental Package Installation:** Only install packages when needed for that day's work
- **Production Code Accuracy:** All code matches actual production implementation
- **Progressive Complexity:** Start simple, build towards enterprise features

**Reference Documents:**
- `app/services/rules.py` - All 30 fraud detection rules
- `app/core/config.py` - Configuration with Field() requirements
- `requirements.txt` - Exact package versions

---

# 📅 DAY 1: Python Environment & Project Structure

## 🎯 What We're Building Today
- Python 3.11 virtual environment
- Project directory structure
- Requirements file
- Git initialization
- Environment configuration

## 📦 Install Today (ONLY Required Packages)

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

# Install ONLY what's needed for Day 1
pip install python-dotenv==1.0.0
```

## 📝 Files to Create

### **sentinel/requirements.txt**
```
# This file will grow as we add packages incrementally
# Day 1
python-dotenv==1.0.0
```

### **sentinel/.env.example**
```bash
# Application
APP_NAME=Sentinel Fraud Detection
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
# REQUIRED: Generate with: openssl rand -hex 32
# Must be at least 32 characters long
SECRET_KEY=

# Note: We'll add more configuration in later days as we install packages
```

### **sentinel/.env** (Copy from .env.example and set SECRET_KEY)
```bash
# Application
APP_NAME=Sentinel Fraud Detection
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
# Generate a secure key for development
SECRET_KEY=your_development_secret_key_at_least_32_chars_long_change_in_production

# Note: We'll add database, Redis, and other configs as we install those packages
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

# 📅 DAY 2: Project Structure & Basic Configuration

## 🎯 What We're Building Today
- Complete project directory structure
- Basic configuration setup (without Pydantic yet)
- Module initialization files
- Placeholder files for future development

## 📦 Install Today

```bash
# No new packages needed today - focusing on structure
```

## 📁 Create Directory Structure

```bash
# From project root (sentinel/)
mkdir -p app/{api,core,models,services,middleware,db}
mkdir -p app/api/v1/endpoints
mkdir -p tests
mkdir -p scripts
mkdir -p logs
mkdir -p models  # For ML models later
```

## 📝 Files to Create

### **app/__init__.py**
```python
"""Sentinel Fraud Detection System"""

__version__ = "1.0.0"
```

### **app/core/__init__.py**
```python
"""Core functionality module"""
```

### **app/models/__init__.py**
```python
"""Data models module"""
```

### **app/services/__init__.py**
```python
"""Business logic services module"""
```

### **app/api/__init__.py**
```python
"""API module"""
```

### **app/api/v1/__init__.py**
```python
"""API version 1"""
```

### **app/middleware/__init__.py**
```python
"""Middleware components"""
```

## ✅ End of Day 2 Checklist
- [ ] Project structure created
- [ ] All __init__.py files in place
- [ ] Directory structure matches production
- [ ] Ready for configuration setup

**⏹️ STOP HERE - END OF DAY 2**

---

# 📅 DAY 3: Configuration Management with Pydantic

## 🎯 What We're Building Today
- Pydantic-based configuration system
- Settings management with environment variables
- Field validation for SECRET_KEY
- Type-safe configuration

## 📦 Install Today

```bash
# Install configuration packages
pip install pydantic==2.5.0 pydantic-settings==2.1.0

# Update requirements.txt
echo "# Day 3" >> requirements.txt
echo "pydantic==2.5.0" >> requirements.txt
echo "pydantic-settings==2.1.0" >> requirements.txt
```

## 📝 Files to Create

### **app/core/config.py** (Production Implementation)

```python
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

    # API (will be used later)
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = 10000

    # Database (placeholder - will add URL on Day 5)
    DATABASE_URL: str = "postgresql://sentinel:sentinel_password@localhost:5432/sentinel"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0

    # Redis (placeholder - will configure on Day 22)
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
```

### **Update .env file**

```bash
# Add all configuration values from config.py
# Application
APP_NAME=Sentinel Fraud Detection
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
# Generate with: openssl rand -hex 32
SECRET_KEY=your_development_secret_key_at_least_32_chars_long_change_in_production

# API
API_V1_PREFIX=/api/v1
API_RATE_LIMIT=10000

# Database (will use on Day 5)
DATABASE_URL=postgresql://sentinel:sentinel_password@localhost:5432/sentinel
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis (will use on Day 22)
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Security
API_KEY_HEADER=X-API-Key
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Fraud Detection
RISK_THRESHOLD_HIGH=70
RISK_THRESHOLD_MEDIUM=40
MAX_PROCESSING_TIME_MS=100

# Consortium Intelligence
ENABLE_CONSORTIUM=true
CONSORTIUM_MIN_CLIENTS=2

# Monitoring
SENTRY_DSN=
ENABLE_METRICS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### **Test Configuration**

```python
# test_config.py
from app.core.config import settings

print(f"App Name: {settings.APP_NAME}")
print(f"Environment: {settings.ENVIRONMENT}")
print(f"SECRET_KEY length: {len(settings.SECRET_KEY)}")
print(f"Risk Threshold High: {settings.RISK_THRESHOLD_HIGH}")
```

```bash
python test_config.py
```

## ✅ End of Day 3 Checklist
- [ ] Pydantic and pydantic-settings installed
- [ ] config.py created with Field validation for SECRET_KEY
- [ ] .env file updated with all settings
- [ ] Configuration loads successfully
- [ ] SECRET_KEY validation works (min 32 chars)

**⏹️ STOP HERE - END OF DAY 3**

---

# 📅 DAY 4: Understanding Fraud Rules Architecture

## 🎯 What We're Building Today
- Understanding the fraud rules system
- Base FraudRule class structure
- Rule categories and severity levels
- Planning for 30 production rules

## 📦 Install Today

```bash
# No new packages today - architectural understanding day
```

## 📝 Files to Create

### **app/services/rules_base.py** (Foundation for rules system)

```python
"""Base fraud rule class - foundation for all detection rules"""

from typing import Optional, Dict, Any
from datetime import datetime


class FraudFlag:
    """Represents a triggered fraud rule"""

    def __init__(
        self,
        type: str,
        severity: str,
        message: str,
        score: int,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.type = type
        self.severity = severity
        self.message = message
        self.score = score
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class FraudRule:
    """Base class for all fraud detection rules"""

    def __init__(self, name: str, description: str, base_score: int, severity: str):
        self.name = name
        self.description = description
        self.base_score = base_score
        self.severity = severity

    def check(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> Optional[FraudFlag]:
        """
        Check if this rule is triggered

        Args:
            transaction: Transaction data
            context: Additional context (e.g., consortium data, velocity data)

        Returns:
            FraudFlag if rule is triggered, None otherwise
        """
        raise NotImplementedError
```

## 📚 Understanding the 30 Production Rules

The production system has 30 fraud rules organized into categories:

### Core/Lending Rules (15 rules)
1. NewAccountLargeAmountRule
2. LoanStackingRule
3. SIMSwapPatternRule
4. SuspiciousHoursRule
5. VelocityCheckRule
6. ContactChangeWithdrawalRule
7. NewDeviceRule
8. RoundAmountRule
9. MaximumFirstTransactionRule
10. ImpossibleTravelRule
11. VPNProxyRule
12. DisposableEmailRule
13. DeviceSharingRule
14. DormantAccountActivationRule
15. SequentialApplicationsRule

### E-commerce Rules (4 rules)
16. CardBINFraudRule
17. MultipleFailedPaymentsRule
18. ShippingMismatchRule
19. DigitalGoodsHighValueRule

### Betting/Gaming Rules (4 rules)
20. BonusAbuseRule
21. WithdrawalWithoutWageringRule
22. ArbitrageBettingRule
23. ExcessiveWithdrawalsRule

### Crypto Rules (3 rules)
24. NewWalletHighValueRule
25. SuspiciousWalletRule
26. P2PVelocityRule

### Marketplace Rules (3 rules)
27. NewSellerHighValueRule
28. LowRatedSellerRule
29. HighRiskCategoryRule

### Device Fingerprinting Rules (1 rule)
30. DeviceFingerprintRule (in fingerprint_rules.py)

## ✅ End of Day 4 Checklist
- [ ] Base FraudRule class created
- [ ] FraudFlag class defined
- [ ] Understand 30-rule architecture
- [ ] Ready to implement rules

**⏹️ STOP HERE - END OF DAY 4**

---

# 📅 DAY 5: Database Setup with PostgreSQL & SQLAlchemy

## 🎯 What We're Building Today
- PostgreSQL database connection
- SQLAlchemy models (User, Transaction, Client)
- Database session management
- Connection pooling

## 📦 Install Today

```bash
# Install database packages
pip install sqlalchemy==2.0.23 psycopg2-binary==2.9.9 alembic==1.12.1

# Update requirements.txt
echo "# Day 5" >> requirements.txt
echo "sqlalchemy==2.0.23" >> requirements.txt
echo "psycopg2-binary==2.9.9" >> requirements.txt
echo "alembic==1.12.1" >> requirements.txt

# Assuming PostgreSQL is installed locally
# Create database
createdb sentinel

# Create user (if needed)
createuser -P sentinel
# Enter password: sentinel_password

# Grant privileges
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sentinel TO sentinel;"
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

# 📅 DAY 6-9: Implementing Core Fraud Rules (First 15 Rules)

## 🎯 What We're Building These Days
Days 6-9 are focused on **implementing the first 15 core fraud rules** from the production system.

All fraud rules are already implemented in:
- `app/services/rules.py` (1,500+ lines)
- `app/services/fingerprint_rules.py` (Fingerprinting-specific)
- `app/core/fraud_detector_v2.py` (Advanced fraud detection)

## 📚 Reference Documentation
See: **app/services/rules.py** for complete implementation of all 30 rules

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

```bash
# Install API framework packages
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6

# Update requirements.txt
echo "# Day 10" >> requirements.txt
echo "fastapi==0.104.1" >> requirements.txt
echo "uvicorn[standard]==0.24.0" >> requirements.txt
echo "python-multipart==0.0.6" >> requirements.txt
```

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

# 📅 DAY 13-14: Implementing Additional Fraud Rules

## 🎯 What We're Building
- E-commerce specific rules (4 rules)
- Betting/Gaming rules (4 rules)
- Crypto rules (3 rules)
- Marketplace rules (3 rules)

## 📦 Install Today

```bash
# No new packages needed - continuing rule implementation
```

## 📝 Files to Update

Continue implementing rules in **app/services/rules.py** following the patterns from Days 6-9.

**⏹️ STOP HERE - END OF DAY 14**

---

# 📅 DAY 15: Security & Authentication Foundation

## 🎯 What We're Building Today
- Password hashing with bcrypt
- JWT token generation
- Security utilities
- Authentication preparation

## 📦 Install Today

```bash
# Install security packages
pip install passlib[bcrypt]==1.7.4 python-jose[cryptography]==3.3.0 cryptography==41.0.7

# Update requirements.txt
echo "# Day 15" >> requirements.txt
echo "passlib[bcrypt]==1.7.4" >> requirements.txt
echo "python-jose[cryptography]==3.3.0" >> requirements.txt
echo "cryptography==41.0.7" >> requirements.txt
```

## 📝 Files to Create

### **app/core/security.py** (Production Implementation)

```python
"""Security utilities for password hashing and JWT tokens"""

from datetime import datetime, timedelta
from typing import Optional, Union
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def hash_device_id(device_id: str) -> str:
    """Hash device ID for privacy"""
    return hashlib.sha256(device_id.encode()).hexdigest()


def hash_bvn(bvn: str) -> str:
    """Hash BVN for privacy"""
    return hashlib.sha256(bvn.encode()).hexdigest()


def hash_phone(phone: str) -> str:
    """Hash phone number for privacy"""
    return hashlib.sha256(phone.encode()).hexdigest()


def hash_email(email: str) -> str:
    """Hash email for privacy"""
    return hashlib.sha256(email.lower().encode()).hexdigest()
```

## ✅ End of Day 15 Checklist
- [ ] Security packages installed
- [ ] Password hashing works
- [ ] JWT token generation works
- [ ] Privacy hashing functions created

**⏹️ STOP HERE - END OF DAY 15**

---

# 📅 DAY 16-17: API Endpoints & Integration

## 🎯 What We're Building
- Additional API endpoints
- Request/Response validation
- Error handling
- API versioning structure

## 📝 Continue building API endpoints following patterns from Day 11-12

**⏹️ STOP HERE - END OF DAY 17**

---

# 📅 DAY 18-19: Integration & Testing

## 🎯 What We're Building
- Integration of all components
- Basic testing structure
- Verification of all systems

## 📝 Integration tasks to complete the foundation

**⏹️ STOP HERE - END OF DAY 19**

---

# 📅 DAY 20: Foundation Review & Preparation

## 🎯 What We're Doing Today
- Review all code from Days 1-19
- Ensure all systems are integrated
- Prepare for advanced features

## 📊 Days 1-20 Summary

✅ **Foundation Complete:**
- Python environment with incremental package installation
- PostgreSQL database with complete models
- Configuration with Field() validation for SECRET_KEY
- **30 fraud detection rules** implemented
- FastAPI application with full API structure
- Security and authentication foundation
- All core components integrated

**Package Installation Timeline:**
- Day 1: python-dotenv
- Day 3: pydantic, pydantic-settings
- Day 5: sqlalchemy, psycopg2-binary, alembic
- Day 10: fastapi, uvicorn, python-multipart
- Day 15: passlib, python-jose, cryptography

**Total Progress:**
- Complete project structure
- 30 fraud rules across 7 industry verticals
- Core API endpoints
- Security implementation
- Ready for advanced features (Days 21-45)

**Next: Continue to PART 2 for Days 21-45 - Advanced Features**

---

