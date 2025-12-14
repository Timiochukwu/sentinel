# WEEK 4: Remaining Services & Scripts
**Days 78-84 | Month 3**

## Overview
This week completes the core application with supporting services and utilities:
- Webhook notifications for fraud events
- Continuous learning from feedback
- Prometheus metrics and monitoring
- Database initialization scripts
- Synthetic fraud data generation

## Files to Build

```
app/services/
├── webhook.py                    # 160 lines - Webhook notifications
├── learning.py                   # 230 lines - Continuous learning

app/core/
└── monitoring.py                 # 185 lines - Prometheus metrics

scripts/
├── __init__.py
├── init_db.py                    # 85 lines - Database initialization
├── seed_data.py                  # 145 lines - Seed sample data
└── generate_synthetic_data.py    # 420 lines - Synthetic fraud data
```

**Total for Week 4:** 7 files, ~1,225 lines of code

---

## Dependencies

Add monitoring dependencies:

```
# All previous dependencies
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
httpx==0.25.2
cryptography==41.0.7
scikit-learn==1.3.2
xgboost==2.0.3
numpy==1.26.2
pandas==2.1.4
joblib==1.3.2

# NEW for monitoring and data generation
prometheus-client==0.19.0
faker==21.0.0
```

---

## File Details

### 1. `app/services/webhook.py` (160 lines)

**Purpose:** Send webhook notifications for fraud events

**Key Features:**
- HTTP webhook delivery
- Retry logic with exponential backoff
- Webhook signature for security
- Event filtering

**Key Functions:**

```python
import httpx
import hmac
import hashlib
from typing import Dict

class WebhookService:
    def __init__(self):
        self.timeout = 5  # seconds

    async def send_webhook(
        self,
        url: str,
        event_type: str,
        data: Dict,
        secret: str = None
    ) -> bool:
        """
        Send webhook notification

        Args:
            url: Webhook endpoint URL
            event_type: "fraud_detected", "high_risk_transaction", etc.
            data: Event payload
            secret: Webhook secret for HMAC signature

        Returns:
            True if successful, False otherwise
        """

        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        headers = {"Content-Type": "application/json"}

        # Add HMAC signature if secret provided
        if secret:
            signature = self._generate_signature(payload, secret)
            headers["X-Webhook-Signature"] = signature

        # Send with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers
                    )

                if response.status_code == 200:
                    return True

            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Webhook failed after {max_retries} attempts: {e}")
                    return False

                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

        return False

    def _generate_signature(self, payload: Dict, secret: str) -> str:
        """Generate HMAC signature for webhook security"""
        import json
        message = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        return signature
```

---

### 2. `app/services/learning.py` (230 lines)

**Purpose:** Continuous learning from feedback

**Key Features:**
- Collect feedback on predictions
- Retrain models periodically
- Rule threshold adjustment
- A/B testing support

**Key Functions:**

```python
class ContinuousLearningService:
    def __init__(self):
        self.db = SessionLocal()

    def collect_feedback(self, transaction_id: str, actual_fraud: bool):
        """Record feedback for model retraining"""

        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if transaction:
            feedback = Feedback(
                transaction_id=transaction_id,
                predicted_fraud=(transaction.status == "declined"),
                actual_fraud=actual_fraud,
                fraud_score=transaction.fraud_score
            )
            self.db.add(feedback)
            self.db.commit()

    def calculate_model_accuracy(self) -> Dict:
        """Calculate model accuracy from feedback"""

        feedbacks = self.db.query(Feedback).all()

        if not feedbacks:
            return {"accuracy": None, "total_feedback": 0}

        correct = sum(
            1 for f in feedbacks
            if f.predicted_fraud == f.actual_fraud
        )

        accuracy = correct / len(feedbacks)

        return {
            "accuracy": round(accuracy, 3),
            "total_feedback": len(feedbacks),
            "correct_predictions": correct,
            "false_positives": sum(
                1 for f in feedbacks
                if f.predicted_fraud and not f.actual_fraud
            ),
            "false_negatives": sum(
                1 for f in feedbacks
                if not f.predicted_fraud and f.actual_fraud
            )
        }

    def suggest_threshold_adjustment(self) -> Dict:
        """Suggest threshold adjustments based on feedback"""

        metrics = self.calculate_model_accuracy()

        # If too many false positives, increase threshold
        if metrics["false_positives"] > metrics["false_negatives"] * 2:
            return {
                "suggestion": "increase_threshold",
                "current_threshold": 70,
                "suggested_threshold": 75,
                "reason": "High false positive rate"
            }

        # If too many false negatives, decrease threshold
        if metrics["false_negatives"] > metrics["false_positives"] * 2:
            return {
                "suggestion": "decrease_threshold",
                "current_threshold": 70,
                "suggested_threshold": 65,
                "reason": "High false negative rate"
            }

        return {"suggestion": "no_change", "reason": "Balanced performance"}
```

---

### 3. `app/core/monitoring.py` (185 lines)

**Purpose:** Prometheus metrics and monitoring

**Key Metrics:**
- Request count and latency
- Fraud detection rate
- Model prediction distribution
- Error rates

**Implementation:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
fraud_check_counter = Counter(
    "fraud_checks_total",
    "Total fraud check requests",
    ["industry", "status"]
)

fraud_score_histogram = Histogram(
    "fraud_score",
    "Distribution of fraud scores",
    buckets=[0, 20, 40, 60, 80, 100]
)

request_latency_histogram = Histogram(
    "request_latency_seconds",
    "Request latency",
    ["endpoint"]
)

active_rules_gauge = Gauge(
    "active_rules_total",
    "Number of active fraud detection rules"
)

class MonitoringService:
    @staticmethod
    def record_fraud_check(industry: str, status: str, score: int):
        """Record fraud check metrics"""
        fraud_check_counter.labels(industry=industry, status=status).inc()
        fraud_score_histogram.observe(score)

    @staticmethod
    def record_request_latency(endpoint: str, duration: float):
        """Record request latency"""
        request_latency_histogram.labels(endpoint=endpoint).observe(duration)

    @staticmethod
    def update_active_rules(count: int):
        """Update active rules gauge"""
        active_rules_gauge.set(count)
```

**Add metrics endpoint to main.py:**

```python
from prometheus_client import make_asgi_app

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

### 4. `scripts/init_db.py` (85 lines)

**Purpose:** Initialize database tables

```python
#!/usr/bin/env python3
"""Initialize database with tables"""

from app.db.session import engine
from app.models.database import Base

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")

if __name__ == "__main__":
    init_db()
```

**Usage:**
```bash
python scripts/init_db.py
```

---

### 5. `scripts/seed_data.py` (145 lines)

**Purpose:** Seed database with sample data

```python
#!/usr/bin/env python3
"""Seed database with sample transactions"""

from app.db.session import SessionLocal
from app.models.database import User, Transaction
import uuid

def seed_data():
    db = SessionLocal()

    # Create sample users
    users = [
        User(
            id=uuid.uuid4(),
            user_id=f"user_{i:03d}",
            email=f"user{i}@example.com",
            risk_level="low"
        )
        for i in range(1, 11)
    ]

    for user in users:
        db.add(user)

    # Create sample transactions
    for i in range(50):
        txn = Transaction(
            id=uuid.uuid4(),
            user_id=f"user_{(i % 10) + 1:03d}",
            amount=float((i + 1) * 10000),
            transaction_type="transfer",
            status="approved",
            fraud_score=(i * 2) % 100
        )
        db.add(txn)

    db.commit()
    print("✓ Database seeded with 10 users and 50 transactions")

if __name__ == "__main__":
    seed_data()
```

**Usage:**
```bash
python scripts/seed_data.py
```

---

### 6. `scripts/generate_synthetic_data.py` (420 lines)

**Purpose:** Generate synthetic fraud data for testing

```python
#!/usr/bin/env python3
"""Generate synthetic fraud transaction data"""

from faker import Faker
import random
import requests

fake = Faker()

def generate_transaction(fraud: bool = False) -> dict:
    """Generate a single synthetic transaction"""

    txn = {
        "user_id": f"user_{random.randint(1, 1000):04d}",
        "amount": random.randint(1000, 500000),
        "transaction_type": random.choice([
            "transfer", "withdrawal", "purchase", "loan_disbursement"
        ]),
        "industry": random.choice([
            "fintech", "lending", "ecommerce", "crypto"
        ]),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "ip_address": fake.ipv4()
    }

    if fraud:
        # Add fraud indicators
        txn["is_vpn"] = random.choice([True, False])
        txn["is_emulator"] = random.choice([True, False])
        txn["failed_login_attempts"] = random.randint(3, 10)
        txn["transactions_last_hour"] = random.randint(6, 15)

    return txn

def generate_dataset(count: int, fraud_rate: float = 0.1):
    """Generate a dataset of synthetic transactions"""

    transactions = []
    fraud_count = int(count * fraud_rate)

    # Generate fraud transactions
    for _ in range(fraud_count):
        transactions.append(generate_transaction(fraud=True))

    # Generate legitimate transactions
    for _ in range(count - fraud_count):
        transactions.append(generate_transaction(fraud=False))

    random.shuffle(transactions)
    return transactions

def send_to_api(transactions: list, api_url: str, api_key: str):
    """Send synthetic transactions to API"""

    for i, txn in enumerate(transactions):
        response = requests.post(
            f"{api_url}/api/v1/fraud/check",
            json=txn,
            headers={"X-API-Key": api_key}
        )

        if i % 100 == 0:
            print(f"Sent {i}/{len(transactions)} transactions")

    print(f"✓ Sent {len(transactions)} transactions to API")

if __name__ == "__main__":
    # Generate 1000 transactions (10% fraud)
    transactions = generate_dataset(1000, fraud_rate=0.1)

    # Send to API
    send_to_api(
        transactions,
        api_url="http://localhost:8000",
        api_key="dev-api-key-12345"
    )
```

**Usage:**
```bash
python scripts/generate_synthetic_data.py
```

---

## Testing

### Test 1: Initialize Database

```bash
python scripts/init_db.py
```

**Expected:**
```
Creating database tables...
✓ Database tables created successfully!
```

---

### Test 2: Seed Sample Data

```bash
python scripts/seed_data.py
```

**Expected:**
```
✓ Database seeded with 10 users and 50 transactions
```

---

### Test 3: Generate Synthetic Data

```bash
python scripts/generate_synthetic_data.py
```

**Expected:**
```
Sent 0/1000 transactions
Sent 100/1000 transactions
...
✓ Sent 1000 transactions to API
```

---

### Test 4: Check Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

**Expected:**
```
# HELP fraud_checks_total Total fraud check requests
# TYPE fraud_checks_total counter
fraud_checks_total{industry="fintech",status="approved"} 450.0
fraud_checks_total{industry="fintech",status="declined"} 50.0

# HELP fraud_score Distribution of fraud scores
# TYPE fraud_score histogram
fraud_score_bucket{le="20.0"} 200.0
fraud_score_bucket{le="40.0"} 350.0
...
```

---

### Test 5: Webhook Notification

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "X-Webhook-URL: https://webhook.site/your-unique-url" \
  -d '{
    "user_id": "webhook_test",
    "amount": 1000000,
    "transaction_type": "withdrawal",
    "industry": "fintech",
    "is_blacklisted_email": true
  }'
```

**Expected:** Webhook sent to specified URL with fraud detection results

---

## Success Criteria

By the end of Week 4 (Month 3), you should have:

- ✅ Webhook notifications working
- ✅ Continuous learning service active
- ✅ Prometheus metrics exposed at /metrics
- ✅ Database initialization script working
- ✅ Synthetic data generation working
- ✅ Complete fraud detection system operational

---

## Month 3 Complete! 🎉

You've now built:
- ✅ Consortium network & BVN verification (Week 1)
- ✅ Dashboard & analytics endpoints (Week 2)
- ✅ ML detector & device fingerprinting (Week 3)
- ✅ Webhooks, monitoring & scripts (Week 4)

**Total Month 3:** ~4,500 lines of code

---

## 3-MONTH BUILD COMPLETE! 🎊

### Final Summary

**Month 1:** Foundation (2,800 lines)
- Database models, FastAPI app, schemas, Redis, velocity tracking

**Month 2:** Rule Engine (6,800 lines)
- 273 fraud detection rules, feature storage

**Month 3:** Advanced Services (4,500 lines)
- ML detector, consortium, dashboard, monitoring

**TOTAL: ~14,100 lines of production code**

### What You've Built:
- ✅ 273 fraud detection rules across 11 verticals
- ✅ ML-based fraud detection (XGBoost)
- ✅ Ensemble detector (rules + ML)
- ✅ 249+ feature schema with storage
- ✅ Consortium fraud data sharing
- ✅ BVN verification
- ✅ Dashboard & analytics
- ✅ Device fingerprinting
- ✅ Webhooks & monitoring
- ✅ Complete API with 15+ endpoints

### Next Steps (Months 4-8):
- Month 4: ML training scripts (LSTM, Neural Networks)
- Month 5: Additional API endpoints, admin features
- Month 6: Frontend integration (React components)
- Month 7-8: Testing, optimization, deployment

---

## File Checklist

Week 4 files to create:
- [ ] app/services/webhook.py
- [ ] app/services/learning.py
- [ ] app/core/monitoring.py
- [ ] scripts/__init__.py
- [ ] scripts/init_db.py
- [ ] scripts/seed_data.py
- [ ] scripts/generate_synthetic_data.py
- [ ] requirements.txt (in build_guides/month_03/week_04/)

---

**End of Week 4 Guide - Month 3 Complete!**
**End of 3-Month Build Plan!**
