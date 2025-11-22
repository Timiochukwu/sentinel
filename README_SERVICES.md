# Sentinel Fraud Detection Platform - Services Documentation

**Created**: November 22, 2025  
**Total Services**: 9 core services + 160+ fraud detection rules  
**Documentation Size**: 62KB (1,824 lines)  
**Code Size**: 9,805+ lines of service code

---

## Documentation Overview

This package contains comprehensive documentation about all services, their purposes, integration points, and configurations.

### Documentation Files

#### 1. **SERVICES_DOCUMENTATION.md** (1,313 lines - 39KB)
**Comprehensive Technical Reference**
- Full service specifications for all 9 services
- Key classes, methods, and dependencies
- Integration points and architecture
- Database schema details
- Configuration requirements
- Performance metrics
- Deployment checklist

**Best For**: In-depth understanding, implementation details, architecture design

#### 2. **SERVICES_QUICK_REFERENCE.md** (288 lines - 11KB)
**Quick Lookup Guide**
- Service summary table with key metrics
- Use-case based service lookup
- Integration patterns (4 common patterns)
- Troubleshooting matrix
- Redis key patterns reference
- Performance tuning tips
- File locations and structure

**Best For**: Quick lookups, troubleshooting, pattern reference

#### 3. **SERVICES_SUMMARY.txt** (213 lines - 8.5KB)
**Executive Summary**
- Service inventory with key details
- Architecture overview
- Performance metrics summary
- Database integration details
- Configuration reference
- Deployment checklist
- Documentation file guide

**Best For**: High-level overview, project planning, team briefing

#### 4. **SERVICES_MATRIX.csv** (CSV - 3.5KB)
**Structured Comparison Table**
- All 9 services in tabular format
- File paths, line counts, purposes
- Key methods and dependencies
- Database tables (read/write)
- Easy import into Excel/Sheets for analysis

**Best For**: Spreadsheet analysis, comparison, reporting

---

## Services at a Glance

| # | Service | Purpose | Key Feature |
|---|---------|---------|-------------|
| 1 | **Cache Service** | 5ms response caching | 17x faster responses |
| 2 | **Redis Service** | Velocity tracking & rate limiting | 50 concurrent connections |
| 3 | **BVN Verification** | Nigerian identity verification | NIBSS/NIMC integration |
| 4 | **Fingerprint Rules** | Device fingerprint fraud | 4 sophisticated rules |
| 5 | **Consortium Service** | Cross-lender intelligence | Privacy-preserving hashing |
| 6 | **Learning Service** | Continuous improvement | Per-rule weight adjustment |
| 7 | **ML Fraud Detector** | XGBoost ML predictions | 85%+ accuracy |
| 8 | **Webhook Service** | Real-time notifications | 3x retry with backoff |
| 9 | **Fraud Rules Engine** | Comprehensive detection | 160+ detection rules |

---

## Key Statistics

### Code Metrics
- **Total Service Code**: 9,805+ lines
- **Fraud Rules**: 160+ rules across 14 categories
- **Services**: 9 core services
- **Files**: 9 Python files + 4 documentation files

### Performance
- **Cached Response**: 5ms (17x faster)
- **Uncached Response**: 87ms
- **ML Prediction**: <50ms
- **Cache Hit Rate**: 15-30%
- **ML Accuracy**: 85%+

### Scalability
- **Redis Connections**: 50 max
- **DB Connections**: 20 pool size
- **Rate Limit Tiers**: 3 (100/1000/10000 req/min)
- **Verticals Supported**: 7 (lending, crypto, ecommerce, betting, fintech, payments, marketplace)

---

## Quick Start Guide

### For Different User Personas

#### Software Engineer (Implementation)
1. Read: **SERVICES_DOCUMENTATION.md** - Full technical specs
2. Reference: **SERVICES_QUICK_REFERENCE.md** - Quick lookup
3. Use: **SERVICES_MATRIX.csv** - Compare services

#### Project Manager (Planning)
1. Read: **SERVICES_SUMMARY.txt** - Overview and metrics
2. Check: **SERVICES_DOCUMENTATION.md** - Integration Architecture section
3. Review: Deployment checklist

#### DevOps Engineer (Deployment)
1. Read: **SERVICES_SUMMARY.txt** - Configuration reference
2. Reference: **SERVICES_DOCUMENTATION.md** - Configuration Requirements section
3. Use: Deployment checklist

#### QA/Tester (Testing)
1. Read: **SERVICES_QUICK_REFERENCE.md** - Troubleshooting matrix
2. Reference: **SERVICES_DOCUMENTATION.md** - Service specifications
3. Check: **SERVICES_MATRIX.csv** - Dependencies and integration points

---

## Service Architecture

```
HTTP Request
    ↓
RateLimitMiddleware (RedisService)
    ↓
fraud_detection endpoint
    ├─ CacheService (5ms hit)
    │   └─ RedisService
    │
    ├─ FraudDetector
    │   ├─ FraudRulesEngine (160+ rules)
    │   ├─ FingerprintFraudRules (4 rules)
    │   ├─ ConsortiumService (cross-lender)
    │   └─ MLFraudDetector (XGBoost)
    │
    ├─ Cache result
    │
    ├─ Store in database
    │
    └─ Send webhook (async)
        └─ WebhookService

Feedback Loop:
feedback endpoint
    └─ LearningService
        ├─ Update rule accuracy
        ├─ Adjust weights
        └─ Update consortium intelligence
```

---

## Configuration Reference

### Required Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/sentinel
REDIS_URL=redis://localhost:6379/0
```

### Key Configuration
```python
RISK_THRESHOLD_HIGH = 70
RISK_THRESHOLD_MEDIUM = 40
CACHE_TTL = 300  # 5 minutes
MAX_RETRIES = 3  # Webhooks
```

### ML Models Location
```
models/
├── fraud_model.json                 # Primary global model
├── fraud_model_scaler.pkl
├── fraud_model_features.pkl
├── fraud_model_lending.json         # Lending-specific
├── fraud_model_lending_scaler.pkl
├── fraud_model_crypto.json          # Crypto-specific
└── ...                              # Other verticals
```

---

## Integration Examples

### Example 1: Fraud Check with Caching
```python
# Check cache first (5ms)
cached = await cache_service.get_cached_result(transaction)
if cached:
    return cached

# Process fraud check (87ms)
result = await detector.check_transaction(transaction)

# Cache for next time
await cache_service.set_cached_result(transaction, result)
return result
```

### Example 2: Detect Loan Stacking
```python
# Cross-lender detection
consortium = ConsortiumService(db, client_id)
patterns = consortium.check_fraud_patterns(transaction)

# Results include:
# - client_count: Number of other lenders
# - fraud_count: Fraud incidents
# - alerts: Human-readable warnings
# - risk_level: none/medium/high/critical
```

### Example 3: Continuous Learning
```python
# Process merchant feedback
learning = LearningService(db)
result = learning.process_feedback(
    transaction_id=txn_id,
    actual_outcome="fraud",
    fraud_type="loan_stacking"
)

# Automatically:
# - Updates rule accuracy metrics
# - Adjusts rule weights
# - Updates consortium intelligence
# - Improves future predictions
```

---

## Database Tables

### Primary Tables
- **transactions**: Core fraud detection data (all rules read from this)
- **consortium_intelligence**: Hashed fraud patterns (cross-lender sharing)
- **rule_accuracy**: Rule performance metrics (updated by learning service)
- **clients**: Customer configuration

### Critical Indexes
```sql
CREATE INDEX idx_device_fingerprint ON transactions(device_fingerprint);
CREATE INDEX idx_client_id ON transactions(client_id);
CREATE INDEX idx_created_at ON transactions(created_at);
CREATE INDEX idx_risk_level ON consortium_intelligence(risk_level);
```

---

## Fraud Rules Summary

**Total: 160+ rules across 14 categories**

1. Account & Authentication (30+ rules)
2. Device & Browser (35+ rules)
3. Behavioral & Typing (25+ rules)
4. Velocity & Transaction (25+ rules)
5. Geographic & Location (10+ rules)
6. Contact & Verification (15+ rules)
7. Identity & Verification (15+ rules)
8. Financial & Payment (20+ rules)
9. Crypto & Wallet (10+ rules)
10. E-Commerce & Marketplace (15+ rules)
11. Betting & Gaming (10+ rules)
12. Consortium Intelligence (15+ rules)
13. Machine Learning & Anomaly (15+ rules)
14. Advanced Fraud Patterns (20+ rules)

**Fingerprint Rules: 4 core rules**
1. Loan Stacking (3+ users in 7 days)
2. High Velocity (>5 transactions today)
3. Fraud History (confirmed fraud)
4. Consortium Detection (2+ lenders)

---

## Performance Tuning

### Cache Optimization
- Hit rate depends on duplicate requests
- Typical production: 15-30% hit rate
- Each cache entry: ~1-2KB
- TTL: 5 minutes (balance speed vs freshness)

### Redis Optimization
- Connection pool: 50 connections
- Memory: 500MB - 2GB typical
- Velocity tracking: 10+ concurrent time windows per user
- Rate limiting: Sliding window algorithm

### Database Optimization
- Connection pool: 20 connections
- Query optimization: Most rules O(1) or O(log n)
- Indexes on: device_fingerprint, client_id, created_at
- Consortium check: Optimized with hash indexes

---

## Troubleshooting

| Issue | Service | Solution |
|-------|---------|----------|
| Slow responses | CacheService | Verify Redis running, check cache hit rate |
| Rate limit errors | RateLimitMiddleware | Increase tier, check Redis memory |
| BVN fails | BVNVerificationService | Verify NIBSS API key configured |
| Loan stacking undetected | FingerprintFraudRules | Verify fingerprint data in DB |
| Webhooks not sending | WebhookService | Check webhook URL, verify signature |
| False positives | FraudRulesEngine | Review rule weights, adjust thresholds |
| Memory issues | RedisService | Reduce cache TTL, increase RAM |

---

## Deployment Checklist

- [ ] PostgreSQL configured and running
- [ ] Redis instance running (localhost:6379)
- [ ] ML models loaded (fraud_model.json)
- [ ] Per-vertical models available (optional)
- [ ] NIBSS API credentials (optional)
- [ ] Webhook URLs configured
- [ ] Rate limiting tiers defined
- [ ] Risk thresholds customized
- [ ] CORS origins configured
- [ ] SSL/TLS certificates installed
- [ ] Monitoring configured
- [ ] Backup procedures in place

---

## File Locations

```
/home/user/sentinel/
├── app/services/
│   ├── cache_service.py           # CacheService
│   ├── redis_service.py           # RedisService
│   ├── bvn_verification.py        # BVNVerificationService
│   ├── fingerprint_rules.py       # FingerprintFraudRules
│   ├── consortium.py              # ConsortiumService
│   ├── learning.py                # LearningService
│   ├── ml_detector.py             # MLFraudDetector
│   ├── webhook.py                 # WebhookService
│   └── rules.py                   # FraudRulesEngine (160+ rules)
│
├── SERVICES_DOCUMENTATION.md      # This comprehensive guide
├── SERVICES_QUICK_REFERENCE.md    # Quick lookup
├── SERVICES_SUMMARY.txt           # Executive summary
└── SERVICES_MATRIX.csv            # Spreadsheet format
```

---

## Support Resources

- **Technical Documentation**: See SERVICES_DOCUMENTATION.md
- **Quick Reference**: See SERVICES_QUICK_REFERENCE.md
- **Overview**: See SERVICES_SUMMARY.txt
- **Spreadsheet Format**: See SERVICES_MATRIX.csv
- **Code**: /home/user/sentinel/app/services/

---

## Version Information

- **Documentation Version**: 1.0
- **Generated**: November 22, 2025
- **Sentinel Platform**: v1.0.0
- **Total Services**: 9
- **Fraud Rules**: 160+
- **Service Code**: 9,805+ lines
- **Documentation**: 1,824 lines

---

**Last Updated**: November 22, 2025  
**Maintained By**: Sentinel Development Team

