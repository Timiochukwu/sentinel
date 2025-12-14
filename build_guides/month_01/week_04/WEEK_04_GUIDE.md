# WEEK 4: Redis Service & Velocity Tracking
**Days 22-28 | Month 1**

## Overview
This week adds caching and velocity tracking capabilities:
- Redis connection and connection pooling
- Velocity calculations (transaction count/amount per time window)
- Cache service for fraud detection features
- Rate limiting infrastructure
- Basic fraud detector with velocity checks

## Files to Build

```
app/
├── services/
│   ├── __init__.py
│   ├── redis_service.py           # 145 lines - Redis connection
│   └── cache_service.py            # 78 lines - Caching utilities
└── core/
    └── fraud_detector.py           # 650 lines - Basic fraud detector
```

**Total for Week 4:** 4 files, ~873 lines of code

---

## Dependencies

Create `requirements.txt` in this folder (includes Weeks 1-3):

```
# Week 1 dependencies
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
alembic==1.12.1

# Week 2 dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Week 3 dependencies
email-validator==2.1.0
phonenumbers==8.13.26

# Week 4 dependencies (NEW)
redis==5.0.1
hiredis==2.2.3
```

### Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r build/month_01/week_04/requirements.txt
```

---

## File Details

### 1. `app/services/redis_service.py` (145 lines)

**Purpose:** Redis connection management and velocity tracking

**Key Features:**
- Connection pooling (max 50 connections)
- Velocity tracking by user_id, IP, device
- Time-based windows (1 hour, 24 hours, 7 days)
- Automatic key expiration

**Key Functions:**

```python
class RedisService:
    def __init__(self):
        """Initialize Redis connection pool"""
        self.redis = redis.from_url(
            settings.REDIS_URL,
            max_connections=50,
            decode_responses=True
        )

    def track_transaction(self, user_id: str, amount: float):
        """Track transaction for velocity calculation"""
        # Increment counters with TTL
        # Store amount for sum calculations

    def get_velocity(self, user_id: str, window: str) -> dict:
        """Get transaction count and amount for time window"""
        # Returns: {"count": 5, "total_amount": 250000}

    def set_cache(self, key: str, value: Any, ttl: int):
        """Cache a value with TTL"""

    def get_cache(self, key: str) -> Any:
        """Retrieve cached value"""
```

**Velocity Keys:**
```
velocity:{user_id}:1h:count    # Transactions last hour
velocity:{user_id}:1h:amount   # Amount last hour
velocity:{user_id}:24h:count   # Transactions last 24 hours
velocity:{user_id}:24h:amount  # Amount last 24 hours
velocity:{ip}:1h:count         # IP-based velocity
velocity:{device}:1h:count     # Device-based velocity
```

---

### 2. `app/services/cache_service.py` (78 lines)

**Purpose:** High-level caching utilities for fraud detection

**Key Features:**
- Cache user risk scores
- Cache blacklist checks
- Cache BVN verification results
- Automatic cache invalidation

**Key Functions:**

```python
class CacheService:
    def __init__(self):
        self.redis = RedisService()

    def cache_user_risk(self, user_id: str, risk_level: str, ttl=3600):
        """Cache user's risk level for 1 hour"""

    def get_user_risk(self, user_id: str) -> Optional[str]:
        """Get cached risk level"""

    def cache_blacklist(self, identifier: str, list_type: str):
        """Add to blacklist cache (email, phone, IP, device)"""

    def is_blacklisted(self, identifier: str, list_type: str) -> bool:
        """Check if identifier is blacklisted"""
```

---

### 3. `app/core/fraud_detector.py` (650 lines)

**Purpose:** Basic fraud detection engine (without ML, with basic rules)

**Key Features:**
- Velocity-based fraud checks
- Basic risk scoring (0-100 scale)
- Hardcoded threshold rules
- Integration with Redis velocity tracking

**Implementation Phases:**

**Week 4 Version:** Basic velocity checks only
- High velocity detection (>5 txns/hour = +30 points)
- Large amount checks (>100k = +20 points)
- VPN/Proxy detection (+15 points each)
- Basic risk level assignment

**Later Versions:**
- Month 2: Full rule engine (271 rules)
- Month 3: ML detector integration

**Key Code Structure:**

```python
class FraudDetector:
    def __init__(self):
        self.redis = RedisService()
        self.db_session = SessionLocal()

    def check_transaction(self, request: TransactionCheckRequest) -> TransactionCheckResponse:
        """
        Main fraud check method

        Week 4: Basic velocity and threshold checks
        Returns fraud score (0-100) and risk level
        """

        score = 0
        flags = []

        # 1. Velocity checks
        velocity = self.redis.get_velocity(request.user_id, "1h")
        if velocity["count"] > 5:
            score += 30
            flags.append({
                "flag_type": "high_velocity",
                "severity": "high",
                "score": 30,
                "message": f"{velocity['count']} transactions in 1 hour"
            })

        # 2. Amount checks
        if request.amount > 100000:
            score += 20
            flags.append({
                "flag_type": "large_amount",
                "severity": "medium",
                "score": 20,
                "message": f"Amount {request.amount} exceeds threshold"
            })

        # 3. Network checks
        if request.is_vpn:
            score += 15
            flags.append({
                "flag_type": "vpn_detected",
                "severity": "medium",
                "score": 15,
                "message": "Transaction from VPN"
            })

        # 4. Determine risk level and status
        risk_level = self._calculate_risk_level(score)
        status = self._determine_status(score, risk_level)

        # 5. Track this transaction in Redis
        self.redis.track_transaction(request.user_id, request.amount)

        # 6. Store in database
        transaction = self._store_transaction(request, score, status, flags)

        return TransactionCheckResponse(
            transaction_id=str(transaction.id),
            fraud_score=score,
            risk_level=risk_level,
            status=status,
            flags=flags,
            message=self._get_status_message(status),
            timestamp=datetime.utcnow()
        )

    def _calculate_risk_level(self, score: int) -> str:
        """Calculate risk level from score"""
        if score >= 70:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"

    def _determine_status(self, score: int, risk_level: str) -> str:
        """Determine transaction status"""
        if score >= 70:
            return "declined"
        elif score >= 50:
            return "review"
        else:
            return "approved"
```

---

## Environment Variables

Update your `.env` file:

```env
# Redis Configuration (ADD THIS)
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Velocity Thresholds (ADD THIS)
VELOCITY_1H_THRESHOLD=5
VELOCITY_24H_THRESHOLD=20
AMOUNT_1H_THRESHOLD=500000
AMOUNT_24H_THRESHOLD=2000000

# Fraud Scoring Thresholds (ADD THIS)
FRAUD_SCORE_DECLINE_THRESHOLD=70
FRAUD_SCORE_REVIEW_THRESHOLD=50
FRAUD_SCORE_APPROVE_THRESHOLD=30

# Existing variables from Weeks 1-3
DATABASE_URL=postgresql://sentinel:sentinel123@localhost:5432/sentinel
API_KEY=dev-api-key-12345
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

---

## Redis Setup

### Option 1: Docker (Recommended)

```bash
# Start Redis container
docker run -d \
  --name sentinel-redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify Redis is running
docker ps | grep redis
```

### Option 2: Local Installation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

### Verify Redis Connection

```bash
# Test connection
redis-cli ping
# Expected: PONG

# Check Redis info
redis-cli info server
```

---

## Update Fraud Detection Endpoint

Modify `app/api/v1/endpoints/fraud_detection.py` to use the new fraud detector:

```python
# Add import
from app.core.fraud_detector import FraudDetector

# Update endpoint
@router.post("/check")
async def check_fraud(
    request: TransactionCheckRequest,
    db: Session = Depends(deps.get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Check transaction for fraud
    Week 4: Now uses real fraud detection with velocity checks
    """

    detector = FraudDetector()
    result = detector.check_transaction(request)

    return result
```

---

## Testing with curl

### Test 1: First Transaction (Low Velocity)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "velocity_test_user",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "fintech"
  }'
```

**Expected Response:**
```json
{
  "transaction_id": "uuid-here",
  "fraud_score": 0,
  "risk_level": "low",
  "status": "approved",
  "flags": [],
  "message": "Transaction approved",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Test 2: High Velocity (6 Transactions in 1 Hour)

```bash
# Send 6 transactions rapidly
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/fraud/check \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev-api-key-12345" \
    -d '{
      "user_id": "high_velocity_user",
      "amount": 10000,
      "transaction_type": "transfer",
      "industry": "fintech"
    }'
  sleep 1
done
```

**Expected Response (6th transaction):**
```json
{
  "transaction_id": "uuid-here",
  "fraud_score": 30,
  "risk_level": "medium",
  "status": "approved",
  "flags": [
    {
      "flag_type": "high_velocity",
      "severity": "high",
      "score": 30,
      "confidence": 0.8,
      "message": "6 transactions in 1 hour"
    }
  ],
  "message": "Transaction approved",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### Test 3: Large Amount

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "large_amount_user",
    "amount": 500000,
    "transaction_type": "withdrawal",
    "industry": "fintech"
  }'
```

**Expected Response:**
```json
{
  "transaction_id": "uuid-here",
  "fraud_score": 20,
  "risk_level": "low",
  "status": "approved",
  "flags": [
    {
      "flag_type": "large_amount",
      "severity": "medium",
      "score": 20,
      "confidence": 0.6,
      "message": "Amount 500000 exceeds threshold"
    }
  ],
  "message": "Transaction approved"
}
```

---

### Test 4: VPN Detection

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "vpn_user",
    "amount": 75000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "is_vpn": true,
    "ip_address": "1.2.3.4"
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 15,
  "risk_level": "low",
  "status": "approved",
  "flags": [
    {
      "flag_type": "vpn_detected",
      "severity": "medium",
      "score": 15,
      "message": "Transaction from VPN"
    }
  ]
}
```

---

### Test 5: Multiple Fraud Signals (High Score)

```bash
# First create high velocity
for i in {1..7}; do
  curl -s -X POST http://localhost:8000/api/v1/fraud/check \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev-api-key-12345" \
    -d "{\"user_id\": \"risky_user\", \"amount\": 10000, \"transaction_type\": \"transfer\", \"industry\": \"fintech\"}" \
    > /dev/null
  sleep 0.5
done

# Then send a large amount from VPN
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "risky_user",
    "amount": 600000,
    "transaction_type": "withdrawal",
    "industry": "fintech",
    "is_vpn": true,
    "is_proxy": true
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 95,
  "risk_level": "critical",
  "status": "declined",
  "flags": [
    {
      "flag_type": "high_velocity",
      "severity": "high",
      "score": 30,
      "message": "8 transactions in 1 hour"
    },
    {
      "flag_type": "large_amount",
      "severity": "medium",
      "score": 20,
      "message": "Amount 600000 exceeds threshold"
    },
    {
      "flag_type": "vpn_detected",
      "severity": "medium",
      "score": 15,
      "message": "Transaction from VPN"
    },
    {
      "flag_type": "proxy_detected",
      "severity": "medium",
      "score": 15,
      "message": "Transaction from proxy"
    }
  ],
  "message": "Transaction declined due to high fraud risk"
}
```

---

## Redis Verification

### Check Velocity Keys

```bash
# Connect to Redis CLI
redis-cli

# List all velocity keys
KEYS velocity:*

# Check specific user velocity
GET velocity:high_velocity_user:1h:count
GET velocity:high_velocity_user:1h:amount

# Check TTL (time to live)
TTL velocity:high_velocity_user:1h:count

# Exit Redis CLI
exit
```

---

### Verify Velocity Tracking with Python

```bash
python3 << 'EOF'
from app.services.redis_service import RedisService

redis = RedisService()

# Check velocity for a user
user_id = "high_velocity_user"
velocity_1h = redis.get_velocity(user_id, "1h")
velocity_24h = redis.get_velocity(user_id, "24h")

print(f"✓ Velocity for {user_id}:")
print(f"  Last 1 hour: {velocity_1h['count']} transactions, {velocity_1h['total_amount']} NGN")
print(f"  Last 24 hours: {velocity_24h['count']} transactions, {velocity_24h['total_amount']} NGN")
EOF
```

---

## Load Testing

### Simulate 100 Users with Varying Velocities

```bash
#!/bin/bash
# Save as test_velocity.sh

echo "Simulating 100 users with varying transaction patterns..."

# Low velocity users (1-2 txns)
for i in {1..50}; do
  curl -s -X POST http://localhost:8000/api/v1/fraud/check \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev-api-key-12345" \
    -d "{\"user_id\": \"low_vel_$i\", \"amount\": 10000, \"transaction_type\": \"transfer\", \"industry\": \"fintech\"}" \
    > /dev/null &
done

# Medium velocity users (3-5 txns)
for i in {1..30}; do
  for j in {1..3}; do
    curl -s -X POST http://localhost:8000/api/v1/fraud/check \
      -H "Content-Type: application/json" \
      -H "X-API-Key: dev-api-key-12345" \
      -d "{\"user_id\": \"med_vel_$i\", \"amount\": 15000, \"transaction_type\": \"transfer\", \"industry\": \"fintech\"}" \
      > /dev/null &
  done
done

# High velocity users (10+ txns)
for i in {1..10}; do
  for j in {1..10}; do
    curl -s -X POST http://localhost:8000/api/v1/fraud/check \
      -H "Content-Type: application/json" \
      -H "X-API-Key: dev-api-key-12345" \
      -d "{\"user_id\": \"high_vel_$i\", \"amount\": 5000, \"transaction_type\": \"transfer\", \"industry\": \"fintech\"}" \
      > /dev/null &
  done
done

wait
echo "✓ Load test complete!"

# Check results
echo "Checking fraud scores in database..."
psql postgresql://sentinel:sentinel123@localhost:5432/sentinel \
  -c "SELECT
        CASE
          WHEN fraud_score >= 70 THEN 'critical'
          WHEN fraud_score >= 50 THEN 'high'
          WHEN fraud_score >= 30 THEN 'medium'
          ELSE 'low'
        END as risk_level,
        COUNT(*) as count
      FROM transactions
      GROUP BY risk_level
      ORDER BY
        CASE risk_level
          WHEN 'critical' THEN 1
          WHEN 'high' THEN 2
          WHEN 'medium' THEN 3
          ELSE 4
        END;"
```

**Expected Output:**
```
 risk_level | count
------------+-------
 low        |   50
 medium     |   90
 high       |  100
 critical   |   10
```

---

## Troubleshooting

### Issue: `redis.exceptions.ConnectionError`

**Solution:** Verify Redis is running
```bash
# Check if Redis is running
docker ps | grep redis

# Or for local Redis
sudo systemctl status redis

# Restart if needed
docker restart sentinel-redis
```

---

### Issue: Velocity not incrementing

**Solution:** Check Redis keys
```bash
redis-cli
KEYS velocity:*
# If empty, check fraud_detector.py track_transaction() is being called
```

---

### Issue: All scores are 0

**Solution:** Verify fraud_detector.py is imported correctly in fraud_detection.py endpoint

---

## Success Criteria

By the end of Week 4 (Month 1), you should have:

- ✅ Redis running and connected
- ✅ Velocity tracking working (1h, 24h windows)
- ✅ Fraud scores calculated (0-100)
- ✅ Risk levels assigned (low, medium, high, critical)
- ✅ Transaction status determined (approved, review, declined)
- ✅ Multiple fraud flags can trigger
- ✅ High velocity transactions flagged
- ✅ Large amounts flagged
- ✅ VPN/Proxy detection working

---

## Month 1 Complete! 🎉

You've now built:
- ✅ Database models (Week 1)
- ✅ FastAPI application (Week 2)
- ✅ 249+ feature schemas (Week 3)
- ✅ Redis velocity tracking (Week 4)
- ✅ Basic fraud detection (Week 4)

**Total:** ~15 files, ~2,800 lines of code

---

## Next Month Preview

**Month 2: Core Rule Engine (271 Rules)**

Week 1: Rule engine foundation + first verticals (65 rules)
Week 2: More rule verticals (64 rules)
Week 3: Lending rules (89 rules)
Week 4: Feature storage & aggregation

---

## Notes

- Week 4 fraud detector is BASIC - only velocity and threshold checks
- Full rule engine (271 rules) comes in Month 2
- ML detector comes in Month 3
- Current fraud detection is sufficient for testing velocity infrastructure
- Redis keys auto-expire (1h keys expire after 3600 seconds)

---

## File Checklist

Week 4 files to create:
- [ ] app/services/__init__.py
- [ ] app/services/redis_service.py
- [ ] app/services/cache_service.py
- [ ] app/core/fraud_detector.py
- [ ] Update app/api/v1/endpoints/fraud_detection.py (use FraudDetector)
- [ ] requirements.txt (in build/month_01/week_04/)
- [ ] .env (add Redis and threshold configs)

---

**End of Week 4 Guide - Month 1 Complete!**
