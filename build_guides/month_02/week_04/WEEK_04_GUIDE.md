# WEEK 4: Feature Storage & Aggregation
**Days 50-56 | Month 2**

## Overview
This week adds feature storage and aggregation capabilities:
- Store 249+ features in PostgreSQL JSONB columns
- Feature aggregation across time windows
- Historical feature tracking
- Feature retrieval for ML models (Month 3)

## Files to Build

```
app/services/
├── feature_storage.py            # 285 lines - Feature storage in JSONB
└── feature_aggregation.py        # 420 lines - Feature aggregation logic
```

**Total for Week 4:** 2 files, ~705 lines of code

---

## Dependencies

No new dependencies:

```
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
alembic==1.12.1
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
email-validator==2.1.0
phonenumbers==8.13.26
redis==5.0.1
hiredis==2.2.3
```

---

## File Details

### 1. `app/services/feature_storage.py` (285 lines)

**Purpose:** Store and retrieve transaction features in PostgreSQL

**Key Features:**
- Store all 249+ features as JSONB
- Query historical features
- Feature versioning
- Efficient JSONB indexing

**Key Functions:**

```python
class FeatureStorageService:
    def __init__(self, db_session):
        self.db = db_session

    def store_features(self, transaction_id: str, features: dict):
        """
        Store all transaction features in database

        Args:
            transaction_id: Transaction UUID
            features: Dict with all 249+ features
        """
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if transaction:
            transaction.metadata = features
            self.db.commit()

    def get_features(self, transaction_id: str) -> dict:
        """Retrieve stored features for a transaction"""
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        return transaction.metadata if transaction else {}

    def get_user_feature_history(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get feature history for user"""
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()

        return [txn.metadata for txn in transactions if txn.metadata]
```

---

### 2. `app/services/feature_aggregation.py` (420 lines)

**Purpose:** Aggregate features across time windows for velocity calculations

**Key Functions:**

```python
class FeatureAggregationService:
    def __init__(self, db_session, redis_service):
        self.db = db_session
        self.redis = redis_service

    def aggregate_user_features(self, user_id: str, window: str = "24h") -> dict:
        """
        Aggregate user features over time window

        Returns aggregated metrics:
        - Total transaction count
        - Total amount
        - Average transaction amount
        - Unique devices used
        - Unique IPs used
        - Most common transaction type
        """
        # Calculate time window
        if window == "1h":
            delta = timedelta(hours=1)
        elif window == "24h":
            delta = timedelta(days=1)
        elif window == "7d":
            delta = timedelta(days=7)
        else:
            delta = timedelta(days=30)

        start_time = datetime.utcnow() - delta

        # Query transactions in window
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= start_time
        ).all()

        # Aggregate
        total_amount = sum(t.amount for t in transactions)
        avg_amount = total_amount / len(transactions) if transactions else 0
        devices = set()
        ips = set()

        for txn in transactions:
            if txn.metadata:
                if txn.metadata.get("device_id"):
                    devices.add(txn.metadata["device_id"])
                if txn.metadata.get("ip_address"):
                    ips.add(txn.metadata["ip_address"])

        return {
            "transaction_count": len(transactions),
            "total_amount": total_amount,
            "average_amount": avg_amount,
            "unique_devices": len(devices),
            "unique_ips": len(ips),
            "window": window
        }

    def get_velocity_features(self, user_id: str) -> dict:
        """Get velocity features for all time windows"""
        return {
            "velocity_1h": self.aggregate_user_features(user_id, "1h"),
            "velocity_24h": self.aggregate_user_features(user_id, "24h"),
            "velocity_7d": self.aggregate_user_features(user_id, "7d"),
            "velocity_30d": self.aggregate_user_features(user_id, "30d")
        }
```

---

## Update Fraud Detector

Integrate feature storage with fraud detector:

```python
from app.services.feature_storage import FeatureStorageService
from app.services.feature_aggregation import FeatureAggregationService

class FraudDetector:
    def __init__(self):
        self.redis = RedisService()
        self.rule_engine = FraudRulesEngine()
        self.db_session = SessionLocal()
        self.feature_storage = FeatureStorageService(self.db_session)
        self.feature_aggregation = FeatureAggregationService(
            self.db_session, self.redis
        )

    def check_transaction(self, request: TransactionCheckRequest):
        # 1. Build context
        context = self._build_context(request)

        # 2. Add aggregated velocity features
        velocity_features = self.feature_aggregation.get_velocity_features(
            request.user_id
        )
        context.update(velocity_features)

        # 3. Run rule engine
        rule_flags = self.rule_engine.evaluate_transaction(context)

        # 4. Calculate score
        score = sum(flag["score"] for flag in rule_flags)

        # 5. Store all features for future analysis
        features = self._extract_features(request, velocity_features)
        transaction = self._store_transaction(request, score, status, rule_flags)
        self.feature_storage.store_features(transaction.id, features)

        # 6. Return result
        ...
```

---

## Testing with curl

### Test 1: Transaction with Feature Storage

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "feature_test_user",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "email": "test@example.com",
    "phone": "+2348012345678",
    "device_id": "device123",
    "ip_address": "197.210.70.1",
    "is_vpn": false
  }'
```

**Features Stored:**
- All input fields from request
- Aggregated velocity metrics
- Risk score and flags
- Timestamp

---

### Test 2: Verify Feature Storage

```bash
python3 << 'EOF'
from app.services.feature_storage import FeatureStorageService
from app.db.session import SessionLocal
from app.models.database import Transaction

db = SessionLocal()
storage = FeatureStorageService(db)

# Get latest transaction
txn = db.query(Transaction).order_by(Transaction.created_at.desc()).first()

if txn:
    features = storage.get_features(str(txn.id))
    print(f"✓ Transaction: {txn.id}")
    print(f"✓ Stored features: {len(features)} fields")
    print(f"  User ID: {features.get('user_id')}")
    print(f"  Amount: {features.get('amount')}")
    print(f"  IP Address: {features.get('ip_address')}")
    print(f"  Device ID: {features.get('device_id')}")
EOF
```

---

### Test 3: Feature Aggregation

```bash
python3 << 'EOF'
from app.services.feature_aggregation import FeatureAggregationService
from app.services.redis_service import RedisService
from app.db.session import SessionLocal

db = SessionLocal()
redis = RedisService()
aggregation = FeatureAggregationService(db, redis)

user_id = "feature_test_user"
velocity = aggregation.get_velocity_features(user_id)

print(f"✓ Velocity features for {user_id}:")
print(f"  Last 1 hour:  {velocity['velocity_1h']['transaction_count']} txns")
print(f"  Last 24 hours: {velocity['velocity_24h']['transaction_count']} txns")
print(f"  Last 7 days:   {velocity['velocity_7d']['transaction_count']} txns")
EOF
```

---

## Success Criteria

By the end of Week 4 (Month 2), you should have:

- ✅ Feature storage in PostgreSQL working
- ✅ All 249+ features stored as JSONB
- ✅ Feature aggregation across time windows
- ✅ Velocity features calculated (1h, 24h, 7d, 30d)
- ✅ Historical feature queries working
- ✅ Integration with fraud detector complete

---

## Month 2 Complete! 🎉

You've now built:
- ✅ Rule engine foundation (Week 1)
- ✅ 155 rules across 7 verticals (Weeks 1-2)
- ✅ All 273 rules complete (Week 3)
- ✅ Feature storage and aggregation (Week 4)

**Total Month 2:** ~6,800 lines of code, 273 fraud detection rules

---

## Next Month Preview

**Month 3: Advanced Services & ML**

Week 1: Consortium network + BVN verification
Week 2: Dashboard, analytics, feedback endpoints
Week 3: ML detector (XGBoost), fingerprinting
Week 4: Webhooks, monitoring, scripts

---

## File Checklist

Week 4 files to create:
- [ ] app/services/feature_storage.py
- [ ] app/services/feature_aggregation.py
- [ ] Update app/core/fraud_detector.py (integrate feature services)
- [ ] requirements.txt (in build_guides/month_02/week_04/)

---

**End of Week 4 Guide - Month 2 Complete!**
