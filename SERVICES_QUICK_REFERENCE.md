# Sentinel Services - Quick Reference Guide

## All 9 Core Services Summary

| Service | File | Purpose | Key Methods | Calls | Called By |
|---------|------|---------|-------------|-------|-----------|
| **Cache Service** | cache_service.py | 5ms response caching | get/set_cached_result, invalidate_user_cache | RedisService | fraud_detection endpoint |
| **Redis Service** | redis_service.py | Velocity, rate limit, caching | track_velocity, check_rate_limit, cache_* | Redis server | Cache, RateLimitMiddleware |
| **BVN Verification** | bvn_verification.py | Nigerian identity verification | verify_bvn, verify_nin, verify_phone | NIBSS/NIMC APIs | API endpoints |
| **Fingerprint Rules** | fingerprint_rules.py | Device fingerprint fraud detection | check_fingerprint_fraud (4 rules) | Database (Transaction) | FraudDetector |
| **Consortium Service** | consortium.py | Cross-lender fraud intelligence | check_fraud_patterns, report_fraud | Database | FraudDetector, Feedback |
| **Learning Service** | learning.py | Continuous rule improvement | process_feedback, get_rule_accuracy | Database | Feedback endpoint |
| **ML Fraud Detector** | ml_detector.py | XGBoost ML predictions (85%+ accuracy) | predict, _engineer_features | Models, Database | FraudDetector |
| **Webhook Service** | webhook.py | Real-time fraud alerts | send_fraud_alert, send_feedback_notification | HTTP (async) | Endpoints, Background tasks |
| **Fraud Rules Engine** | rules.py | 160+ fraud detection rules | check_all_rules, run 160+ rule checks | Database | FraudDetector |

---

## Quick Service Lookup

### By Use Case

**Need to cache fraud checks?**
→ CacheService + RedisService

**Need to track user velocity?**
→ RedisService.track_transaction_velocity()

**Need to verify Nigerian identity?**
→ BVNVerificationService.verify_bvn/nin/phone()

**Need to detect loan stacking?**
→ FingerprintFraudRules._check_multiple_users_same_device()
→ ConsortiumService.check_loan_stacking()

**Need to get fraud patterns across all lenders?**
→ ConsortiumService.check_fraud_patterns()

**Need to improve detection accuracy?**
→ LearningService.process_feedback()

**Need ML-based fraud scoring?**
→ MLFraudDetector.predict()

**Need to alert merchants?**
→ WebhookService.send_fraud_alert()

**Need all fraud detection rules?**
→ FraudRulesEngine (160+ rules)

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Cached Response Time | ~5ms |
| Uncached Response Time | ~87ms |
| ML Model Accuracy | 85%+ |
| ML Prediction Time | <50ms |
| Cache Hit Rate | 15-30% |
| Cache TTL | 5 minutes |
| Fraud Rules Count | 160+ |
| Fingerprint Rules | 4 |
| Max Retries (Webhook) | 3 |
| Rate Limit Window | 60 seconds |

---

## Database Queries by Service

| Service | Reads | Writes |
|---------|-------|--------|
| **Cache Service** | None (Redis) | None (Redis) |
| **Redis Service** | None (Redis only) | None (Redis only) |
| **BVN Verification** | None | None |
| **Fingerprint Rules** | transactions (4 queries) | None |
| **Consortium Service** | transactions, consortium_intelligence | consortium_intelligence |
| **Learning Service** | transactions, rule_accuracy | transactions, rule_accuracy |
| **ML Fraud Detector** | None (models only) | None |
| **Webhook Service** | clients | None |
| **Fraud Rules Engine** | transactions (context dependent) | None |

---

## Configuration Quick Reference

```bash
# Most Important Config
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost:5432/sentinel
RISK_THRESHOLD_HIGH=70
RISK_THRESHOLD_MEDIUM=40

# BVN Integration (Optional)
NIBSS_API_KEY=your_api_key

# ML Models
models/fraud_model.json              # Primary model
models/fraud_model_{vertical}.json   # Per-vertical models
```

---

## Integration Patterns

### Pattern 1: Simple Cache Check
```python
# In endpoint
cache_result = await cache_service.get_cached_result(transaction)
if cache_result:
    return cache_result  # 5ms response

# Process fraud check (87ms)
result = await detector.check_transaction(transaction)

# Cache for next time
await cache_service.set_cached_result(transaction, result)
return result
```

### Pattern 2: Cross-Lender Detection
```python
# Detect loan stacking across lenders
consortium = ConsortiumService(db, client_id)
patterns = consortium.check_fraud_patterns(transaction)
# Returns: client_count, fraud_count, alerts, risk_level
```

### Pattern 3: Continuous Learning
```python
# When merchant provides feedback
learning = LearningService(db)
result = learning.process_feedback(txn_id, "fraud", "loan_stacking")
# Updates: rule accuracy, weights, consortium intelligence
```

### Pattern 4: Real-Time Alerts
```python
# Send async webhook without blocking
webhook = WebhookService()
asyncio.create_task(
    webhook.send_fraud_alert(client, transaction, "transaction.high_risk")
)
```

---

## Fingerprint Fraud Rules Details

### Rule 1: Loan Stacking
- **Threshold**: 3+ users on device in 7 days
- **Score**: 60-80 (critical)
- **Query**: COUNT(DISTINCT user_id) WHERE fingerprint & created_at >= 7d

### Rule 2: High Velocity
- **Threshold**: >5 transactions today
- **Score**: 40-60
- **Query**: COUNT(*) WHERE fingerprint & created_at >= TODAY

### Rule 3: Fraud History
- **Threshold**: Any confirmed fraud (is_fraud=true)
- **Score**: 80-100 (critical)
- **Query**: COUNT(*) WHERE fingerprint & is_fraud=true

### Rule 4: Consortium Detection
- **Threshold**: 2+ other lenders in 7 days
- **Score**: 70-90 (critical)
- **Query**: COUNT(DISTINCT client_id) WHERE fingerprint & client_id != current

---

## Fraud Rules Engine (160+ Rules) - Categories

1. **Account & Auth** (30 rules) - Quick signup, failed logins, ATO
2. **Device & Browser** (35 rules) - Emulator, jailbreak, fingerprint anomalies
3. **Behavioral** (25 rules) - Typing, mouse, session patterns
4. **Velocity** (25 rules) - Transaction rate, acceleration
5. **Geographic** (10 rules) - Impossible travel, location consistency
6. **Contact & ID** (15 rules) - Phone/email changes, verification
7. **Identity** (15 rules) - BVN, synthetic identity, common names
8. **Financial** (20 rules) - Card testing, bank transfers, payments
9. **Crypto** (10 rules) - Wallet age, P2P velocity
10. **E-Commerce** (15 rules) - Shipping mismatch, digital goods
11. **Betting** (10 rules) - Bonus abuse, arbitrage
12. **Consortium** (15 rules) - Network velocity, fraud rings
13. **ML & Anomaly** (15 rules) - XGBoost, ensemble, LSTM
14. **Advanced** (20 rules) - Profile matching, connections

---

## Redis Key Patterns Reference

```
velocity:{client_id}:{user_id}:1min          # 1-min velocity window
velocity:{client_id}:{user_id}:10min         # 10-min velocity window
velocity_amount:{client_id}:{user_id}:1hour  # Amount in 1 hour
ratelimit:{client_id}                        # Rate limit counter
device:{client_id}:{device_id}:users         # Users per device
session:{session_id}                         # Session data
consortium:{hash}                            # Consortium cache
cache:{key}                                  # Generic cache
counter:{key}                                # Statistics counter
fraud_check_cache:{hash}                     # Fraud check results
```

---

## Performance Tuning Tips

1. **Cache Hit Rate**: Typical 15-30%, depends on duplicate request patterns
2. **Redis Memory**: ~1-2GB for production traffic
3. **DB Connection Pool**: 20 connections recommended
4. **ML Model Loading**: ~500ms on startup, amortized after
5. **Rule Execution**: O(1) - most rules don't hit DB
6. **Consortium Check**: O(log n) with proper indexes

---

## Troubleshooting Matrix

| Problem | Service | Solution |
|---------|---------|----------|
| Slow responses | CacheService | Check Redis connectivity |
| High rate limit errors | RateLimitMiddleware | Increase tier or Redis memory |
| BVN verification fails | BVNVerificationService | Check NIBSS API key |
| Loan stacking not detected | FingerprintFraudRules + ConsortiumService | Check fingerprint data in DB |
| Webhooks not sending | WebhookService | Check webhook URL, verify signature |
| Accuracy declining | LearningService | Check feedback submission rate |
| High false positives | FraudRulesEngine | Review rule weights, adjust thresholds |
| Out of memory | RedisService | Reduce cache TTL or increase RAM |

---

## File Locations

```
/home/user/sentinel/
├── app/
│   ├── services/
│   │   ├── cache_service.py              # Cache (5ms optimization)
│   │   ├── redis_service.py              # Redis wrapper
│   │   ├── bvn_verification.py           # Identity verification
│   │   ├── fingerprint_rules.py          # Fingerprint fraud (4 rules)
│   │   ├── consortium.py                 # Cross-lender intelligence
│   │   ├── learning.py                   # Continuous learning
│   │   ├── ml_detector.py                # XGBoost ML (85%+ accuracy)
│   │   ├── webhook.py                    # Real-time alerts
│   │   └── rules.py                      # 160+ fraud rules (5346 lines!)
│   │
│   ├── core/
│   │   ├── fraud_detector.py             # Main orchestrator
│   │   ├── config.py                     # Configuration
│   │   └── security.py                   # Hashing functions
│   │
│   ├── api/
│   │   └── v1/endpoints/
│   │       ├── fraud_detection.py        # /check-transaction endpoint
│   │       ├── feedback.py               # /feedback endpoint
│   │       ├── consortium.py             # /consortium endpoints
│   │       └── dashboard.py              # /dashboard endpoints
│   │
│   ├── models/
│   │   ├── database.py                   # SQLAlchemy models
│   │   └── schemas.py                    # Pydantic schemas
│   │
│   ├── middleware/
│   │   └── rate_limit.py                 # Rate limiting middleware
│   │
│   └── main.py                           # FastAPI app
│
├── models/
│   ├── fraud_model.json                  # XGBoost global model
│   ├── fraud_model_scaler.pkl
│   ├── fraud_model_features.pkl
│   ├── fraud_model_lending.json          # Lending-specific
│   ├── fraud_model_crypto.json           # Crypto-specific
│   └── ... (per-vertical models)
│
└── SERVICES_DOCUMENTATION.md             # Full documentation
```

---

**Quick Reference Version**: 1.0
**Last Updated**: November 22, 2025
**All Files Located**: `/home/user/sentinel/app/services/`

