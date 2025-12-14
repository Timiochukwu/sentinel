# WEEK 2: Dashboard & Vertical Endpoints
**Days 64-70 | Month 3**

## Overview
This week adds analytics, dashboards, and configuration management:
- Dashboard statistics and fraud trends
- Vertical-specific threshold configuration
- Feedback loop for rule tuning
- Analytics and reporting endpoints

## Files to Build

```
app/api/v1/endpoints/
├── dashboard.py                  # 290 lines - Dashboard & analytics
├── vertical.py                   # 145 lines - Vertical configs
└── feedback.py                   # 120 lines - Feedback endpoints

app/services/
└── vertical_service.py           # 180 lines - Vertical management
```

**Total for Week 2:** 4 files, ~735 lines of code

---

## Dependencies

No new dependencies (same as Week 1):

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
httpx==0.25.2
cryptography==41.0.7
```

---

## File Details

### 1. `app/api/v1/endpoints/dashboard.py` (290 lines)

**Purpose:** Dashboard statistics and analytics

**Endpoints:**

#### GET /api/v1/dashboard/stats
Get overall fraud detection statistics

```python
@router.get("/stats")
async def get_dashboard_stats(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""

    # Query recent transactions
    total_txns = db.query(Transaction).count()
    declined_txns = db.query(Transaction).filter(
        Transaction.status == "declined"
    ).count()

    # Top fraud flags
    top_flags = db.query(
        FraudFlag.flag_type,
        func.count(FraudFlag.id).label("count")
    ).group_by(FraudFlag.flag_type).order_by(
        desc("count")
    ).limit(10).all()

    # Fraud by industry
    industry_stats = db.query(
        Transaction.industry,
        func.count(Transaction.id).label("count"),
        func.avg(Transaction.fraud_score).label("avg_score")
    ).group_by(Transaction.industry).all()

    return {
        "total_transactions": total_txns,
        "declined_transactions": declined_txns,
        "decline_rate": declined_txns / total_txns if total_txns > 0 else 0,
        "top_fraud_flags": [
            {"flag_type": f.flag_type, "count": f.count}
            for f in top_flags
        ],
        "industry_stats": [
            {
                "industry": s.industry,
                "count": s.count,
                "avg_fraud_score": round(s.avg_score, 2)
            }
            for s in industry_stats
        ]
    }
```

#### GET /api/v1/dashboard/trends
Get fraud trends over time

```python
@router.get("/trends")
async def get_fraud_trends(
    days: int = 7,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get fraud trends for last N days"""

    start_date = datetime.utcnow() - timedelta(days=days)

    # Daily fraud counts
    daily_stats = db.query(
        func.date(Transaction.created_at).label("date"),
        func.count(Transaction.id).label("total"),
        func.sum(case(
            (Transaction.status == "declined", 1),
            else_=0
        )).label("declined")
    ).filter(
        Transaction.created_at >= start_date
    ).group_by("date").order_by("date").all()

    return {
        "period_days": days,
        "trends": [
            {
                "date": str(s.date),
                "total_transactions": s.total,
                "declined_transactions": s.declined,
                "decline_rate": s.declined / s.total if s.total > 0 else 0
            }
            for s in daily_stats
        ]
    }
```

---

### 2. `app/api/v1/endpoints/vertical.py` (145 lines)

**Purpose:** Vertical-specific configuration management

**Endpoints:**

#### GET /api/v1/verticals/{industry}
Get vertical configuration

```python
@router.get("/{industry}")
async def get_vertical_config(
    industry: str,
    api_key: str = Depends(verify_api_key)
):
    """Get configuration for an industry vertical"""

    service = VerticalService()
    config = service.get_config(industry)

    return config
```

#### PUT /api/v1/verticals/{industry}
Update vertical thresholds

```python
@router.put("/{industry}")
async def update_vertical_config(
    industry: str,
    config: VerticalConfigUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update vertical configuration"""

    service = VerticalService()
    updated = service.update_config(industry, config.dict())

    return updated
```

---

### 3. `app/api/v1/endpoints/feedback.py` (120 lines)

**Purpose:** Feedback loop for rule tuning

**Endpoints:**

#### POST /api/v1/feedback
Submit feedback on fraud decision

```python
@router.post("")
async def submit_feedback(
    feedback: FeedbackRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on fraud decision

    Use this to report false positives/negatives
    """

    transaction = db.query(Transaction).filter(
        Transaction.id == feedback.transaction_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Store feedback
    feedback_record = Feedback(
        transaction_id=feedback.transaction_id,
        actual_fraud=feedback.actual_fraud,
        notes=feedback.notes,
        submitted_by=feedback.submitted_by
    )
    db.add(feedback_record)
    db.commit()

    # Update transaction if needed
    if feedback.actual_fraud != (transaction.status == "declined"):
        transaction.feedback_status = "mismatch"
        db.commit()

    return {"status": "feedback_recorded"}
```

---

### 4. `app/services/vertical_service.py` (180 lines)

**Purpose:** Vertical configuration management service

**Key Functions:**

```python
class VerticalService:
    VERTICAL_CONFIGS = {
        "fintech": {
            "decline_threshold": 70,
            "review_threshold": 50,
            "enabled_rules": [],  # All rules
            "max_transaction_amount": 1000000
        },
        "lending": {
            "decline_threshold": 60,  # Lower threshold
            "review_threshold": 40,
            "enabled_rules": [],
            "max_loan_amount": 5000000
        },
        "crypto": {
            "decline_threshold": 80,  # Higher threshold
            "review_threshold": 60,
            "enabled_rules": [],
            "max_withdrawal_amount": 10000000
        },
        # ... other verticals
    }

    def get_config(self, industry: str) -> dict:
        """Get configuration for industry"""
        return self.VERTICAL_CONFIGS.get(
            industry,
            self.VERTICAL_CONFIGS["fintech"]  # Default
        )

    def update_config(self, industry: str, updates: dict) -> dict:
        """Update vertical configuration"""
        if industry in self.VERTICAL_CONFIGS:
            self.VERTICAL_CONFIGS[industry].update(updates)
            return self.VERTICAL_CONFIGS[industry]
        raise ValueError(f"Unknown industry: {industry}")
```

---

## Testing with curl

### Test 1: Dashboard Stats

```bash
curl -X GET http://localhost:8000/api/v1/dashboard/stats \
  -H "X-API-Key: dev-api-key-12345"
```

**Expected Response:**
```json
{
  "total_transactions": 1250,
  "declined_transactions": 87,
  "decline_rate": 0.0696,
  "top_fraud_flags": [
    {"flag_type": "high_velocity", "count": 45},
    {"flag_type": "vpn_detected", "count": 32},
    {"flag_type": "low_credit_score", "count": 28}
  ],
  "industry_stats": [
    {"industry": "fintech", "count": 500, "avg_fraud_score": 25.5},
    {"industry": "lending", "count": 350, "avg_fraud_score": 35.2}
  ]
}
```

---

### Test 2: Fraud Trends

```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/trends?days=7" \
  -H "X-API-Key: dev-api-key-12345"
```

**Expected Response:**
```json
{
  "period_days": 7,
  "trends": [
    {
      "date": "2024-01-10",
      "total_transactions": 150,
      "declined_transactions": 12,
      "decline_rate": 0.08
    },
    {
      "date": "2024-01-11",
      "total_transactions": 180,
      "declined_transactions": 15,
      "decline_rate": 0.083
    }
  ]
}
```

---

### Test 3: Get Vertical Config

```bash
curl -X GET http://localhost:8000/api/v1/verticals/lending \
  -H "X-API-Key: dev-api-key-12345"
```

**Expected Response:**
```json
{
  "decline_threshold": 60,
  "review_threshold": 40,
  "enabled_rules": [],
  "max_loan_amount": 5000000
}
```

---

### Test 4: Submit Feedback (False Positive)

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "actual_fraud": false,
    "notes": "Legitimate transaction - false positive",
    "submitted_by": "admin@example.com"
  }'
```

**Expected Response:**
```json
{
  "status": "feedback_recorded"
}
```

---

## Success Criteria

By the end of Week 2 (Month 3), you should have:

- ✅ Dashboard statistics endpoint working
- ✅ Fraud trends visualization data
- ✅ Vertical-specific configurations
- ✅ Feedback submission working
- ✅ Analytics queries optimized

---

## Next Week Preview

**Week 3:** ML Detector & Fingerprinting
- ML-based fraud detection (XGBoost)
- Device fingerprinting (Canvas, WebGL)
- Enhanced fraud detector with ML + rules
- Rate limiting middleware

---

## File Checklist

Week 2 files to create:
- [ ] app/api/v1/endpoints/dashboard.py
- [ ] app/api/v1/endpoints/vertical.py
- [ ] app/api/v1/endpoints/feedback.py
- [ ] app/services/vertical_service.py
- [ ] requirements.txt (in build_guides/month_03/week_02/)

---

**End of Week 2 Guide - Month 3**
