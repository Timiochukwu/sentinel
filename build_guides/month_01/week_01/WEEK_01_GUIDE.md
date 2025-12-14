# WEEK 1: Database Models & Configuration
**Days 1-7 | Month 1**

## Overview
This week establishes the foundation of the Sentinel Fraud Detection System:
- Database configuration and connection pooling
- SQLAlchemy ORM models (Transaction, User, FraudFlag)
- Application configuration management
- Logging setup

## Files to Build

```
app/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py                 # 147 lines - Environment & app config
│   └── logging_config.py         # 62 lines - Logging setup
├── db/
│   ├── __init__.py
│   └── session.py                # 30 lines - Database session management
└── models/
    ├── __init__.py
    └── database.py               # 180 lines - SQLAlchemy models
```

**Total for Week 1:** 8 files, ~419 lines of code

---

## Dependencies

Create `requirements.txt` in this folder:

```
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
alembic==1.12.1
```

### Installation

```bash
# Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r build/month_01/week_01/requirements.txt
```

---

## File Details

### 1. `app/core/config.py` (147 lines)

**Purpose:** Application configuration using Pydantic Settings

**Key Features:**
- Environment variable management (.env file support)
- Database URL configuration
- Redis configuration
- API settings (CORS, API keys)
- JWT secret configuration
- Logging levels

**Environment Variables Required:**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sentinel

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_KEY=your-secret-api-key-here
SECRET_KEY=your-jwt-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=True
```

---

### 2. `app/core/logging_config.py` (62 lines)

**Purpose:** Structured logging configuration

**Key Features:**
- Console and file handlers
- JSON-formatted logs for production
- Log rotation (10MB per file, keep 5 backups)
- Different log levels per environment

**Log Locations:**
- Development: Console + `logs/sentinel.log`
- Production: `logs/sentinel.log` (JSON format)

---

### 3. `app/db/session.py` (30 lines)

**Purpose:** Database session management and connection pooling

**Key Features:**
- SQLAlchemy engine creation with connection pooling
- SessionLocal factory for dependency injection
- Database connection parameters:
  - Pool size: 10 connections
  - Max overflow: 20 connections
  - Pool pre-ping: True (connection health check)
  - Echo: False (no SQL logging in production)

**Functions:**
- `get_db()` - Dependency for FastAPI endpoints

---

### 4. `app/models/database.py` (180 lines)

**Purpose:** SQLAlchemy ORM models for core entities

**Models:**

#### `Transaction` Model
Main transaction record with fraud detection results.

**Fields:**
- `id` (UUID) - Primary key
- `user_id` (String) - User identifier
- `amount` (Numeric) - Transaction amount
- `currency` (String) - Currency code
- `transaction_type` (String) - Type (transfer, withdrawal, etc.)
- `status` (String) - approved/declined/review
- `fraud_score` (Integer) - Calculated fraud score
- `created_at` (DateTime) - Transaction timestamp
- `updated_at` (DateTime) - Last update timestamp
- `metadata` (JSONB) - Flexible metadata storage

**Relationships:**
- `fraud_flags` - One-to-many with FraudFlag
- `user` - Many-to-one with User

#### `User` Model
User account information and fraud history.

**Fields:**
- `id` (UUID) - Primary key
- `user_id` (String, unique) - External user identifier
- `email` (String, unique) - Email address
- `phone` (String) - Phone number
- `created_at` (DateTime) - Account creation
- `last_login` (DateTime) - Last login timestamp
- `is_blocked` (Boolean) - Account blocked status
- `risk_level` (String) - low/medium/high/critical
- `metadata` (JSONB) - User metadata

**Relationships:**
- `transactions` - One-to-many with Transaction
- `fraud_flags` - One-to-many with FraudFlag

#### `FraudFlag` Model
Individual fraud detection flags/alerts.

**Fields:**
- `id` (UUID) - Primary key
- `transaction_id` (UUID) - Foreign key to Transaction
- `user_id` (UUID) - Foreign key to User
- `flag_type` (String) - Rule name that triggered
- `severity` (String) - low/medium/high/critical
- `score` (Integer) - Points contributed
- `confidence` (Float) - Confidence level (0.0-1.0)
- `message` (String) - Human-readable description
- `created_at` (DateTime) - When flag was created

**Relationships:**
- `transaction` - Many-to-one with Transaction
- `user` - Many-to-one with User

---

## Database Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Docker (Recommended for development):**
```bash
docker run -d \
  --name sentinel-postgres \
  -e POSTGRES_USER=sentinel \
  -e POSTGRES_PASSWORD=sentinel123 \
  -e POSTGRES_DB=sentinel \
  -p 5432:5432 \
  postgres:15-alpine
```

### 2. Create Database

```bash
# If using local PostgreSQL
sudo -u postgres psql
CREATE DATABASE sentinel;
CREATE USER sentinel WITH PASSWORD 'sentinel123';
GRANT ALL PRIVILEGES ON DATABASE sentinel TO sentinel;
\q

# If using Docker, database already created
```

### 3. Create .env File

Create `.env` in the project root:

```env
# Database
DATABASE_URL=postgresql://sentinel:sentinel123@localhost:5432/sentinel

# Redis (not needed yet, but include for later)
REDIS_URL=redis://localhost:6379/0

# API
API_KEY=dev-api-key-12345
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=True

# Logging
LOG_LEVEL=INFO
```

---

## Testing & Verification

### Test 1: Configuration Loading

```bash
python3 << 'EOF'
from app.core.config import settings

print("✓ Configuration loaded successfully")
print(f"  Environment: {settings.ENVIRONMENT}")
print(f"  Database URL: {settings.DATABASE_URL[:30]}...")
print(f"  Debug Mode: {settings.DEBUG}")
EOF
```

**Expected Output:**
```
✓ Configuration loaded successfully
  Environment: development
  Database URL: postgresql://sentinel:sentin...
  Debug Mode: True
```

### Test 2: Database Connection

```bash
python3 << 'EOF'
from app.db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print("✓ Database connection successful")
        print(f"  PostgreSQL version: {version.split(',')[0]}")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
EOF
```

**Expected Output:**
```
✓ Database connection successful
  PostgreSQL version: PostgreSQL 15.x
```

### Test 3: Create Tables

```bash
python3 << 'EOF'
from app.db.session import engine
from app.models.database import Base

# Create all tables
Base.metadata.create_all(bind=engine)
print("✓ Database tables created successfully")

# List tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"  Tables created: {', '.join(tables)}")
EOF
```

**Expected Output:**
```
✓ Database tables created successfully
  Tables created: transactions, users, fraud_flags
```

### Test 4: Insert Test Record

```bash
python3 << 'EOF'
from app.db.session import SessionLocal
from app.models.database import User, Transaction, FraudFlag
from datetime import datetime
import uuid

db = SessionLocal()

try:
    # Create test user
    user = User(
        id=uuid.uuid4(),
        user_id="test_user_001",
        email="test@example.com",
        phone="+2348012345678",
        risk_level="low"
    )
    db.add(user)
    db.commit()

    # Create test transaction
    transaction = Transaction(
        id=uuid.uuid4(),
        user_id="test_user_001",
        amount=50000.00,
        currency="NGN",
        transaction_type="transfer",
        status="approved",
        fraud_score=15
    )
    db.add(transaction)
    db.commit()

    # Create test flag
    flag = FraudFlag(
        id=uuid.uuid4(),
        transaction_id=transaction.id,
        user_id=user.id,
        flag_type="velocity_check",
        severity="low",
        score=15,
        confidence=0.65,
        message="3 transactions in 1 hour"
    )
    db.add(flag)
    db.commit()

    print("✓ Test records created successfully")
    print(f"  User: {user.user_id}")
    print(f"  Transaction: {transaction.id}")
    print(f"  Fraud Flag: {flag.flag_type}")

finally:
    db.close()
EOF
```

**Expected Output:**
```
✓ Test records created successfully
  User: test_user_001
  Transaction: 12345678-1234-1234-1234-123456789abc
  Fraud Flag: velocity_check
```

### Test 5: Query Test Records

```bash
python3 << 'EOF'
from app.db.session import SessionLocal
from app.models.database import User, Transaction, FraudFlag

db = SessionLocal()

try:
    # Query user
    user = db.query(User).filter(User.user_id == "test_user_001").first()
    print(f"✓ Found user: {user.email}")

    # Query transactions
    transactions = db.query(Transaction).filter(Transaction.user_id == "test_user_001").all()
    print(f"✓ Found {len(transactions)} transaction(s)")

    # Query flags
    flags = db.query(FraudFlag).filter(FraudFlag.user_id == user.id).all()
    print(f"✓ Found {len(flags)} fraud flag(s)")

    for flag in flags:
        print(f"  - {flag.flag_type}: {flag.message}")

finally:
    db.close()
EOF
```

**Expected Output:**
```
✓ Found user: test@example.com
✓ Found 1 transaction(s)
✓ Found 1 fraud flag(s)
  - velocity_check: 3 transactions in 1 hour
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'app'`

**Solution:** Make sure you're running commands from the project root directory (`/home/user/sentinel/`)

```bash
cd /home/user/sentinel
python3 -c "from app.core.config import settings; print('OK')"
```

### Issue: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions:**
1. Verify PostgreSQL is running:
   ```bash
   # For Docker
   docker ps | grep postgres

   # For system service
   sudo systemctl status postgresql
   ```

2. Check connection details in `.env` file
3. Verify port 5432 is not blocked by firewall

### Issue: `pydantic.error_wrappers.ValidationError`

**Solution:** Missing environment variables. Check your `.env` file contains all required variables.

### Issue: `ImportError: cannot import name 'settings'`

**Solution:** Verify `app/__init__.py` and `app/core/__init__.py` exist (can be empty files)

---

## Database Inspection (Optional)

### Using psql

```bash
# Connect to database
psql postgresql://sentinel:sentinel123@localhost:5432/sentinel

# List tables
\dt

# Describe transactions table
\d transactions

# Query test data
SELECT user_id, amount, status, fraud_score FROM transactions;

# Exit
\q
```

### Using pgAdmin or DBeaver

Download and connect using:
- Host: localhost
- Port: 5432
- Database: sentinel
- Username: sentinel
- Password: sentinel123

---

## Success Criteria

By the end of Week 1, you should have:

- ✅ PostgreSQL database running
- ✅ All 8 Python files created
- ✅ Database tables created (transactions, users, fraud_flags)
- ✅ Configuration loading from .env file
- ✅ Successful database connection and queries
- ✅ Test records created and retrieved
- ✅ Logging configured and working

---

## Next Week Preview

**Week 2:** Basic API Structure & First Endpoint
- FastAPI application setup
- Health check endpoint
- Basic fraud check endpoint (skeleton)
- API key authentication
- CORS middleware

**Dependencies to add:**
- fastapi
- uvicorn
- python-jose
- passlib

---

## Notes

- Keep your `.env` file secure - never commit to git
- Database migrations with Alembic will be added in Week 2
- Connection pooling is configured for production scale (10 base, 20 overflow)
- JSONB fields in PostgreSQL allow flexible metadata storage without schema changes
- All timestamps use UTC timezone

---

## File Checklist

Week 1 files to create:
- [ ] app/__init__.py
- [ ] app/core/__init__.py
- [ ] app/core/config.py
- [ ] app/core/logging_config.py
- [ ] app/db/__init__.py
- [ ] app/db/session.py
- [ ] app/models/__init__.py
- [ ] app/models/database.py
- [ ] .env (from template above)
- [ ] requirements.txt (in build/month_01/week_01/)

---

**End of Week 1 Guide**
