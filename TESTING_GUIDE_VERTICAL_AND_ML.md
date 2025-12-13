# Testing Guide: Vertical Support & ML Features

**Created:** 2025-12-13
**Purpose:** Comprehensive testing guide for newly implemented vertical support and ML features

---

## What Was Built

### ✅ Part 1: Vertical Support (COMPLETE)
1. **vertical_service.py** - 7 industry configurations
2. **vertical.py endpoints** - REST API for vertical management
3. **Updated rules.py** - Applies vertical-specific weights and thresholds

### ✅ Part 2: ML Features (COMPLETE)
4. **feature_storage.py** - Extracts and stores 249+ features
5. **feature_aggregation.py** - User profiling, velocity tracking, anomaly detection
6. **Updated fraud_detector.py** - Auto-extracts features during fraud checks
7. **train_fraud_model.py** - ML training pipeline for XGBoost

---

## Testing Part 1: Vertical Support

### Test 1: List All Verticals

```bash
# Start the API
uvicorn app.main:app --reload

# In another terminal:
curl http://localhost:8000/api/v1/verticals
```

**Expected response:**
```json
{
  "verticals": ["lending", "fintech", "ecommerce", "betting", "gaming", "crypto", "marketplace"],
  "count": 7,
  "configs": {
    "crypto": {
      "fraud_score_threshold": 50.0,
      "aml_risk_threshold": 60.0,
      "enabled": true,
      "description": "Cryptocurrency exchanges, DeFi platforms, crypto trading",
      "rule_count": 10
    },
    ...
  }
}
```

---

### Test 2: Get Vertical Configuration

```bash
# Get crypto vertical config (strictest threshold)
curl http://localhost:8000/api/v1/verticals/crypto/config
```

**Expected response:**
```json
{
  "vertical": "crypto",
  "fraud_score_threshold": 50.0,
  "aml_risk_threshold": 60.0,
  "enabled": true,
  "description": "Cryptocurrency exchanges, DeFi platforms, crypto trading",
  "rule_weights": {
    "SuspiciousWalletRule": 1.8,
    "NewWalletHighValueRule": 1.7,
    "KYCVerificationRule": 2.0,
    ...
  },
  "weighted_rules_count": 10
}
```

**Key observations:**
- Crypto has threshold of 50% (strictest)
- Lending has threshold of 65% (most lenient)
- Each vertical has custom rule weights

---

### Test 3: Fraud Check with Vertical-Specific Rules

Test the SAME transaction in different verticals to see different risk scores:

```bash
# Test in CRYPTO (strict threshold: 50%)
curl -X POST http://localhost:8000/api/v1/verticals/check \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TEST_CRYPTO_001",
    "user_id": "USER_001",
    "amount": 500000,
    "industry": "crypto",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    "account_age_days": 5
  }'
```

**Expected:**
- Risk score influenced by crypto-specific weights
- `SuspiciousWalletRule` weighted 1.8x if triggered
- Threshold: 50% (stricter than other verticals)

```bash
# Test SAME transaction in LENDING (lenient threshold: 65%)
curl -X POST http://localhost:8000/api/v1/verticals/check \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TEST_LENDING_001",
    "user_id": "USER_001",
    "amount": 500000,
    "industry": "lending",
    "account_age_days": 5
  }'
```

**Expected:**
- Different risk assessment
- `LoanStackingRule` weighted 1.5x if triggered
- Threshold: 65% (more lenient)
- Same fraud pattern may be approved in lending but declined in crypto!

---

### Test 4: Vertical Metrics

```bash
# Get fraud metrics for crypto vertical (last 30 days)
curl http://localhost:8000/api/v1/verticals/crypto/metrics?days=30
```

**Expected response:**
```json
{
  "vertical": "crypto",
  "time_period_days": 30,
  "total_transactions": 127,
  "fraud_detected": 15,
  "fraud_rate_percent": 11.81,
  "average_fraud_score": 42.5,
  "high_risk_count": 18,
  "critical_risk_count": 8,
  "threshold_info": {
    "fraud_score_threshold": 50.0,
    "aml_risk_threshold": 60.0
  },
  "top_triggered_rules": [
    {"rule": "SuspiciousWalletRule", "count": 12},
    {"rule": "NewWalletHighValueRule", "count": 8}
  ]
}
```

---

## Testing Part 2: ML Features

### Test 5: Feature Storage During Fraud Check

```bash
# Make fraud check that triggers feature storage
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TEST_FEATURES_001",
    "user_id": "USER_FEATURES_TEST",
    "amount": 250000,
    "industry": "lending",
    "email": "test@example.com",
    "phone": "+2348012345678",
    "device_fingerprint": "abc123xyz",
    "ip_address": "197.210.85.45",
    "account_age_days": 10,
    "transaction_count": 5
  }'
```

**Then check database:**
```sql
-- Connect to PostgreSQL
psql -U sentinel_user -d sentinel_db

-- Query stored features
SELECT
    transaction_id,
    features_identity->>'email',
    features_behavioral->>'session',
    features_network->>'fraud_linkage'
FROM transactions
WHERE transaction_id = 'TEST_FEATURES_001';
```

**Expected:** All 9 JSONB columns populated with extracted features

---

### Test 6: Feature Aggregation - User Profile

Create a Python script to test feature aggregation:

```python
# test_feature_aggregation.py
from app.models.database import SessionLocal
from app.services.feature_aggregation import feature_aggregation

db = SessionLocal()

# Get user behavioral profile
profile = feature_aggregation.get_user_profile("USER_FEATURES_TEST", db)

print("User Profile:")
print(f"  Total Transactions: {profile['total_transactions']}")
print(f"  Fraud Rate: {profile['fraud_rate']}%")
print(f"  Avg Amount: ₦{profile['avg_transaction_amount']:,.2f}")
print(f"  Last 7d: {profile['transaction_frequency']['last_7d']} txns")
print(f"  Most Active Hour: {profile['behavioral_patterns']['most_active_hour']}")

# Get velocity metrics
velocity = feature_aggregation.calculate_velocity("USER_FEATURES_TEST", db)
print(f"\nVelocity:")
print(f"  Last Hour: {velocity['last_hour']}")
print(f"  Last 24h: {velocity['last_24h']}")
print(f"  Last 7d: {velocity['last_7d']}")

db.close()
```

Run:
```bash
python test_feature_aggregation.py
```

**Expected output:**
```
User Profile:
  Total Transactions: 5
  Fraud Rate: 0.00%
  Avg Amount: ₦250,000.00
  Last 7d: 5 txns
  Most Active Hour: 14

Velocity:
  Last Hour: 0
  Last 24h: 1
  Last 7d: 5
```

---

### Test 7: Anomaly Detection

```python
# test_anomaly_detection.py
from app.models.database import SessionLocal
from app.services.feature_aggregation import feature_aggregation

db = SessionLocal()

# Test anomaly on unusual transaction
anomalies = feature_aggregation.detect_anomalies(
    user_id="USER_FEATURES_TEST",
    current_transaction={
        "amount": 5000000,  # Much higher than user's avg (250k)
        "hour": 3,  # 3 AM (unusual if user typically transacts at 2 PM)
        "fraud_score": 75  # High score
    },
    db=db
)

print("Anomaly Detection:")
print(f"  Is Anomaly: {anomalies['is_anomaly']}")
print(f"  Anomaly Score: {anomalies['anomaly_score']}")
print(f"  Anomalies: {anomalies['anomalies_detected']}")
print(f"  Details: {anomalies['details']}")

db.close()
```

**Expected:**
```
Anomaly Detection:
  Is Anomaly: True
  Anomaly Score: 0.9
  Anomalies: ['amount', 'time', 'fraud_score']
  Details: {'current_amount': 5000000, 'avg_amount': 250000, ...}
```

---

### Test 8: ML Training Pipeline

**Prerequisites:**
- At least 100 transactions with stored features
- Mix of fraudulent and legitimate transactions

```bash
# Install ML dependencies (if not already installed)
pip install xgboost scikit-learn pandas numpy

# Run training pipeline
python scripts/ml/train_fraud_model.py --days 90
```

**Expected output:**
```
============================================================
FRAUD DETECTION ML MODEL TRAINING PIPELINE
============================================================
Loading transactions from last 90 days...
Found 547 transactions with features
Prepared 547 training samples with 25 features
Class distribution: {0: 512, 1: 35}

Splitting data into train/test (80/20)...
Training set: 437 samples
Test set: 110 samples

Class imbalance ratio: 14.63
Using scale_pos_weight=14.63 to handle imbalance

Training XGBoost model...
Evaluating model...

==================================================
MODEL PERFORMANCE
==================================================
Precision: 0.875
Recall: 0.714
F1 Score: 0.786
ROC AUC: 0.923

Confusion Matrix:
  TN: 98, FP: 2
  FN: 2, TP: 8

==================================================
TOP 10 MOST IMPORTANT FEATURES
==================================================
 1. fraud_score                  : 0.2845
 2. device_linked_to_fraud       : 0.1523
 3. amount                        : 0.1204
 4. velocity_24h                  : 0.0987
 5. account_age_days              : 0.0765
 6. failed_logins                 : 0.0654
 7. email_reputation              : 0.0543
 8. ip_reputation                 : 0.0421
 9. has_device_fingerprint        : 0.0389
10. session_duration              : 0.0321

✓ Model saved to: models/fraud_model_xgboost.pkl
✓ Feature names saved to: models/feature_names.json
✓ Metrics saved to: models/model_metrics.json
✓ Feature importance saved to: models/feature_importance.json

Model ready for production use!
============================================================
✓ TRAINING COMPLETE!
============================================================
```

---

## Integration Testing

### Test 9: End-to-End Flow

Test complete fraud detection pipeline with all features:

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "E2E_TEST_001",
    "user_id": "E2E_USER",
    "amount": 500000,
    "industry": "crypto",
    "transaction_type": "crypto_withdrawal",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    "device_fingerprint": "fp_abc123",
    "ip_address": "197.210.85.45",
    "account_age_days": 3,
    "transaction_count": 1,
    "email": "test@disposable-email.com",
    "phone": "+2348012345678",
    "is_unusual_time": true,
    "failed_login_count_24h": 5
  }'
```

**This tests:**
1. ✅ Vertical-specific evaluation (crypto threshold: 50%)
2. ✅ Vertical-specific rule weights (SuspiciousWalletRule 1.8x)
3. ✅ All 29 fraud rules
4. ✅ Feature extraction (249+ features)
5. ✅ Feature storage in JSONB columns
6. ✅ Database transaction recording

**Verify in database:**
```sql
SELECT
    transaction_id,
    risk_score,
    decision,
    industry,
    vertical,
    features_identity IS NOT NULL as has_identity_features,
    features_behavioral IS NOT NULL as has_behavioral_features,
    features_network IS NOT NULL as has_network_features
FROM transactions
WHERE transaction_id = 'E2E_TEST_001';
```

**Expected:** Risk score influenced by crypto weights, all feature columns populated

---

## Performance Testing

### Test 10: Response Time with Feature Extraction

```bash
# Test response time (should still be < 200ms even with feature extraction)
time curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "PERF_TEST_001",
    "user_id": "PERF_USER",
    "amount": 100000,
    "industry": "lending"
  }'
```

**Expected:**
- Processing time < 200ms
- Feature extraction happens asynchronously (doesn't slow down fraud check)

---

## Validation Checklist

### Vertical Support ✅
- [ ] All 7 verticals list correctly
- [ ] Each vertical has correct threshold (crypto: 50%, lending: 65%)
- [ ] Rule weights apply correctly (check metadata in response)
- [ ] Same transaction gets different scores in different verticals
- [ ] Vertical metrics endpoint works

### ML Features ✅
- [ ] Features extracted during every fraud check
- [ ] All 9 JSONB columns populated
- [ ] User profiling works with aggregation service
- [ ] Velocity tracking calculates correctly
- [ ] Anomaly detection identifies unusual patterns
- [ ] ML training pipeline runs successfully
- [ ] Model achieves >80% precision on test set

### Integration ✅
- [ ] Fraud detection + vertical + features work together
- [ ] Performance remains < 200ms
- [ ] Database stores all data correctly
- [ ] No errors in logs

---

## Troubleshooting

### Issue: "Insufficient training data"
**Solution:** Need at least 100 transactions with stored features. Run more fraud checks first.

### Issue: Features not storing
**Check:** Look for warning in console: "Failed to store features for..."
**Solution:** Verify JSONB columns exist in database schema.

### Issue: Vertical weights not applying
**Check:** Look at flag metadata in response - should include `weight_multiplier`
**Solution:** Ensure transaction includes `industry` field.

### Issue: Model training fails with import errors
**Solution:** Install ML dependencies: `pip install xgboost scikit-learn pandas numpy`

---

## Success Criteria

✅ **Vertical Support Working When:**
- Different verticals show different thresholds
- Same transaction gets different risk scores in crypto vs lending
- Rule weights visible in flag metadata
- Metrics endpoint returns per-vertical stats

✅ **ML Features Working When:**
- All 9 JSONB columns populated after fraud check
- User profiles show accurate transaction history
- Anomaly detection identifies unusual patterns
- Training pipeline produces model with >80% precision

✅ **System Ready for Production When:**
- All tests pass
- Response time < 200ms
- Model achieves target metrics
- Feature storage succeeds >95% of time

---

## Next Steps

1. **Monitor Production:**
   - Track vertical-specific fraud rates
   - Analyze feature importance rankings
   - Retrain model monthly with new data

2. **Tune Thresholds:**
   - Adjust vertical thresholds based on actual fraud rates
   - Update rule weights based on production performance

3. **Expand Features:**
   - Add more behavioral features
   - Integrate external data sources
   - Build vertical-specific features

---

**Testing Complete!** 🎉

Your fraud detection system now has:
- ✅ Multi-vertical support (7 industries)
- ✅ Vertical-specific fraud thresholds
- ✅ 249+ ML features automatically extracted
- ✅ ML training pipeline for continuous improvement
- ✅ User behavioral profiling
- ✅ Anomaly detection
- ✅ Production-ready architecture
