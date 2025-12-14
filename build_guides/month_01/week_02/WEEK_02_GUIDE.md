# WEEK 2: Basic API Structure & First Endpoint
**Days 8-14 | Month 1**

## Overview
This week builds the FastAPI application foundation:
- FastAPI application setup with CORS and middleware
- API versioning structure (v1)
- Health check endpoint
- Basic fraud detection endpoint (skeleton)
- API key authentication
- Dependency injection for database sessions

## Files to Build

```
app/
├── main.py                       # 85 lines - FastAPI app initialization
├── api/
│   ├── __init__.py
│   ├── deps.py                   # 45 lines - Dependency injection
│   └── v1/
│       ├── __init__.py
│       ├── api.py                # 30 lines - API router aggregation
│       └── endpoints/
│           ├── __init__.py
│           └── fraud_detection.py # 120 lines - Fraud check endpoint
└── core/
    └── security.py               # 95 lines - Authentication & security
```

**Total for Week 2:** 8 new files, ~375 lines of code

---

## Dependencies

Create `requirements.txt` in this folder (includes Week 1 dependencies):

```
# Week 1 dependencies
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
alembic==1.12.1

# Week 2 dependencies (NEW)
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

### Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r build/month_01/week_02/requirements.txt
```

---

## File Details

### 1. `app/main.py` (85 lines)

**Purpose:** Main FastAPI application initialization

**Key Features:**
- FastAPI app instance creation
- CORS middleware configuration
- API router inclusion
- Health check endpoint
- Startup/shutdown events
- Exception handlers

**Key Code Sections:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sentinel Fraud Detection API",
    description="Multi-vertical fraud detection system",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

---

### 2. `app/core/security.py` (95 lines)

**Purpose:** Authentication and security utilities

**Key Features:**
- API key validation
- JWT token creation and verification
- Password hashing (for future use)
- Security dependencies for FastAPI

**Key Functions:**

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Validate API key from request header"""
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key
```

**Security Features:**
- API key authentication via `X-API-Key` header
- JWT token support (for future admin endpoints)
- Bcrypt password hashing
- Token expiration handling

---

### 3. `app/api/deps.py` (45 lines)

**Purpose:** Reusable dependency injection functions

**Key Dependencies:**

```python
from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    """
    Database session dependency
    Yields a database session and ensures proper cleanup
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Dependencies Provided:**
- `get_db()` - Database session for endpoints
- `get_current_user()` - User authentication (skeleton for future)

---

### 4. `app/api/v1/api.py` (30 lines)

**Purpose:** API router aggregation for v1

**Key Features:**
- Combines all v1 endpoint routers
- Single import point for main.py
- Version prefix management

```python
from fastapi import APIRouter
from app.api.v1.endpoints import fraud_detection

api_router = APIRouter()

api_router.include_router(
    fraud_detection.router,
    prefix="/fraud",
    tags=["fraud-detection"]
)
```

---

### 5. `app/api/v1/endpoints/fraud_detection.py` (120 lines)

**Purpose:** Main fraud detection endpoint (basic version)

**Endpoints:**

#### `POST /api/v1/fraud/check`
Check a transaction for fraud.

**Request Body:**
```json
{
  "user_id": "user123",
  "amount": 50000,
  "transaction_type": "transfer",
  "currency": "NGN",
  "email": "user@example.com",
  "phone": "+2348012345678"
}
```

**Response:**
```json
{
  "transaction_id": "uuid-here",
  "fraud_score": 0,
  "risk_level": "low",
  "status": "approved",
  "flags": [],
  "message": "Transaction approved"
}
```

**Implementation Notes:**
- For Week 2, this endpoint will be a SKELETON
- It accepts the request, validates it, stores in database
- Returns hardcoded fraud_score=0 (no actual fraud detection yet)
- Fraud detection logic will be added in Week 4 (Month 1) and Week 1 (Month 2)

**Key Code:**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.schemas import TransactionCheckRequest
from app.models.database import Transaction
import uuid

router = APIRouter()

@router.post("/check")
async def check_fraud(
    request: TransactionCheckRequest,
    db: Session = Depends(deps.get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Check transaction for fraud
    Week 2: Basic skeleton - returns approved with score 0
    """

    # Create transaction record
    transaction = Transaction(
        id=uuid.uuid4(),
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency or "NGN",
        transaction_type=request.transaction_type,
        status="approved",  # Hardcoded for now
        fraud_score=0  # Hardcoded for now
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        "transaction_id": str(transaction.id),
        "fraud_score": 0,
        "risk_level": "low",
        "status": "approved",
        "flags": [],
        "message": "Transaction approved"
    }
```

---

## Environment Variables

Add to your `.env` file (should already exist from Week 1):

```env
# API Settings (ADD THESE)
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Existing variables from Week 1
DATABASE_URL=postgresql://sentinel:sentinel123@localhost:5432/sentinel
REDIS_URL=redis://localhost:6379/0
API_KEY=dev-api-key-12345
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

---

## Running the Application

### Start the Server

```bash
# From project root (/home/user/sentinel)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Alternative: Run with custom settings

```bash
# Production mode (no reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Custom port
uvicorn app.main:app --reload --port 8080
```

---

## Testing with curl

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Test 2: API Documentation

FastAPI automatically generates interactive API docs.

**Swagger UI:**
```bash
# Open in browser
http://localhost:8000/docs
```

**ReDoc:**
```bash
# Open in browser
http://localhost:8000/redoc
```

---

### Test 3: Fraud Check (No API Key - Should Fail)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer"
  }'
```

**Expected Response (403 Forbidden):**
```json
{
  "detail": "Not authenticated"
}
```

---

### Test 4: Fraud Check (With API Key - Success)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer",
    "currency": "NGN",
    "email": "test@example.com",
    "phone": "+2348012345678"
  }'
```

**Expected Response:**
```json
{
  "transaction_id": "12345678-1234-1234-1234-123456789abc",
  "fraud_score": 0,
  "risk_level": "low",
  "status": "approved",
  "flags": [],
  "message": "Transaction approved"
}
```

---

### Test 5: Fraud Check (Invalid Data - Validation Error)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": -1000,
    "transaction_type": "invalid_type"
  }'
```

**Expected Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error"
    }
  ]
}
```

---

### Test 6: Multiple Transactions

```bash
# Transaction 1
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"user_id": "user001", "amount": 10000, "transaction_type": "transfer"}'

# Transaction 2
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"user_id": "user001", "amount": 25000, "transaction_type": "withdrawal"}'

# Transaction 3
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"user_id": "user002", "amount": 100000, "transaction_type": "purchase"}'
```

**Verify in Database:**
```bash
psql postgresql://sentinel:sentinel123@localhost:5432/sentinel \
  -c "SELECT user_id, amount, transaction_type, status, fraud_score FROM transactions ORDER BY created_at DESC LIMIT 3;"
```

---

## Verification Tests

### Test 7: Verify Database Records

```bash
python3 << 'EOF'
from app.db.session import SessionLocal
from app.models.database import Transaction

db = SessionLocal()
try:
    transactions = db.query(Transaction).all()
    print(f"✓ Total transactions in database: {len(transactions)}")

    for txn in transactions[-3:]:  # Last 3 transactions
        print(f"  - {txn.user_id}: {txn.amount} {txn.currency} ({txn.status})")
finally:
    db.close()
EOF
```

---

### Test 8: API Key Validation

```bash
# Valid API key
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"user_id": "test", "amount": 1000, "transaction_type": "transfer"}' \
  | jq '.status'

# Invalid API key
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  -d '{"user_id": "test", "amount": 1000, "transaction_type": "transfer"}' \
  | jq '.detail'

# Missing API key
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "amount": 1000, "transaction_type": "transfer"}' \
  | jq '.detail'
```

---

## Load Testing (Optional)

### Simple Load Test with curl

```bash
# Send 100 transactions
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/fraud/check \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev-api-key-12345" \
    -d "{\"user_id\": \"user$i\", \"amount\": $((RANDOM % 100000)), \"transaction_type\": \"transfer\"}" \
    > /dev/null 2>&1 &
done

wait
echo "✓ 100 transactions sent"

# Check database
psql postgresql://sentinel:sentinel123@localhost:5432/sentinel \
  -c "SELECT COUNT(*) as total_transactions FROM transactions;"
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Install Week 2 dependencies
```bash
pip install -r build/month_01/week_02/requirements.txt
```

---

### Issue: `ImportError: cannot import name 'TransactionCheckRequest'`

**Solution:** Week 2 needs the schemas from Week 1. Verify `app/models/schemas.py` exists from Week 1. If not, you need to create it first (it's in Week 1 but may have been skipped).

For Week 2, create a MINIMAL version:

```python
# app/models/schemas.py (MINIMAL for Week 2)
from pydantic import BaseModel, Field
from typing import Optional

class TransactionCheckRequest(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0)
    transaction_type: str
    currency: Optional[str] = "NGN"
    email: Optional[str] = None
    phone: Optional[str] = None
```

Full 249+ features version will be added in Week 3.

---

### Issue: `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: database "sentinel" does not exist`

**Solution:** Create database from Week 1
```bash
docker run -d \
  --name sentinel-postgres \
  -e POSTGRES_USER=sentinel \
  -e POSTGRES_PASSWORD=sentinel123 \
  -e POSTGRES_DB=sentinel \
  -p 5432:5432 \
  postgres:15-alpine
```

---

### Issue: Port 8000 already in use

**Solution:** Kill existing process or use different port
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8080
```

---

### Issue: CORS errors in browser

**Solution:** Update `app/main.py` CORS settings
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## API Response Examples

### Successful Fraud Check
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "fraud_score": 0,
  "risk_level": "low",
  "status": "approved",
  "flags": [],
  "message": "Transaction approved",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Failed Validation
```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

### Authentication Error
```json
{
  "detail": "Invalid API key"
}
```

---

## Success Criteria

By the end of Week 2, you should have:

- ✅ FastAPI application running on http://localhost:8000
- ✅ Health check endpoint responding
- ✅ Interactive API docs at /docs and /redoc
- ✅ Fraud check endpoint accepting requests
- ✅ API key authentication working
- ✅ Transactions stored in PostgreSQL database
- ✅ CORS middleware configured
- ✅ All endpoints tested with curl

---

## Next Week Preview

**Week 3:** Pydantic Schemas & Core Models
- Complete TransactionCheckRequest with 249+ features
- Industry enum (fintech, lending, crypto, etc.)
- Response schemas
- Validation rules for all fields
- Feature documentation

**Dependencies to add:**
- email-validator
- phonenumbers

---

## Notes

- Week 2 fraud detection is a SKELETON - returns hardcoded results
- Real fraud detection logic comes in:
  - Week 4 (Month 1): Basic fraud detector
  - Week 1 (Month 2): Full rule engine
  - Week 3 (Month 3): ML detector
- API versioning (/api/v1) allows future v2, v3 without breaking changes
- FastAPI automatically generates OpenAPI schema
- Database sessions are automatically closed via dependency injection

---

## File Checklist

Week 2 files to create:
- [ ] app/main.py
- [ ] app/api/__init__.py
- [ ] app/api/deps.py
- [ ] app/api/v1/__init__.py
- [ ] app/api/v1/api.py
- [ ] app/api/v1/endpoints/__init__.py
- [ ] app/api/v1/endpoints/fraud_detection.py
- [ ] app/core/security.py
- [ ] requirements.txt (in build/month_01/week_02/)

---

**End of Week 2 Guide**
