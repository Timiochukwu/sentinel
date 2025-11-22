# Sentinel Fraud Detection Platform - Services Documentation

**Last Updated**: November 22, 2025
**Total Services**: 9 core services + 160+ fraud detection rules
**Architecture**: Multi-layered fraud detection with Redis caching, ML models, and consortium intelligence

---

## Table of Contents
1. [Core Services Overview](#core-services-overview)
2. [Service Specifications](#service-specifications)
3. [Integration Architecture](#integration-architecture)
4. [Database Schema](#database-schema)
5. [Configuration Requirements](#configuration-requirements)

---

## Core Services Overview

### Service Architecture Diagram
```
FastAPI Request → RateLimitMiddleware → CacheService (Redis) → FraudDetector
                                                                    ↓
                                    ┌──────────────────────────────┼──────────────────────────────┐
                                    ↓                              ↓                              ↓
                            FraudRulesEngine            ConsortiumService      FingerprintFraudRules
                            (160+ rules)                (cross-lender)         (device patterns)
                                    ↓                              ↓                              ↓
                            LearningService          BVNVerificationService   WebhookService
                            (feedback loop)          (identity verification)  (real-time alerts)
```

---

## Service Specifications

### 1. CACHE SERVICE (cache_service.py)
**File**: `/home/user/sentinel/app/services/cache_service.py` (393 lines)

#### Purpose
Response caching for fraud detection results to achieve 17x faster responses (5ms vs 87ms) for duplicate transactions.

#### Key Classes & Methods
```python
class CacheService:
    def __init__(self, redis_service: RedisService)
    async def get_cached_result(transaction: Dict) -> Optional[Dict]
    async def set_cached_result(transaction: Dict, result: Dict) -> bool
    async def invalidate_user_cache(user_id: str) -> int
    async def clear_all_cache() -> int
    async def get_cache_stats() -> Dict[str, int]
```

#### Key Methods Details
- **get_cached_result()**: Retrieves cached fraud check results if available
- **set_cached_result()**: Stores fraud detection results with 5-minute TTL
- **invalidate_user_cache()**: Clears all cached results for a specific user
- **clear_all_cache()**: Clears all fraud check cache entries
- **get_cache_stats()**: Returns memory usage and cache key count

#### Dependencies (Imports)
```python
- hashlib
- json
- typing (Dict, Any, Optional)
- app.services.redis_service.RedisService
```

#### Integration Points
- Called by: `app/api/v1/endpoints/fraud_detection.py` (check_transaction endpoint)
- Calls: RedisService
- Dependency: Redis service must be running

#### Configuration
```python
self.cache_ttl = 300  # 5 minutes
self.cache_prefix = "fraud_check_cache:"
```

#### Database Tables Used
- None directly (uses Redis only)

#### Cache Key Generation
- Uses SHA-256 hash of transaction inputs (user_id, amount, device_id, etc.)
- Example: `fraud_check_cache:7f8a9b2c...`
- **Critical**: Ignores transaction_id to cache identical patterns regardless of ID

---

### 2. REDIS SERVICE (redis_service.py)
**File**: `/home/user/sentinel/app/services/redis_service.py` (353 lines)

#### Purpose
High-performance caching, velocity tracking, rate limiting, session management, and real-time operations.

#### Key Classes & Methods
```python
class RedisService:
    def __init__()
    def track_transaction_velocity(user_id, client_id, amount) -> Dict[str, int]
    def get_velocity_data(user_id, client_id) -> Dict[str, Any]
    def check_rate_limit(client_id, limit=10000, window=3600) -> Dict[str, Any]
    def cache_set(key, value, ttl=300) -> bool
    def cache_get(key) -> Optional[Any]
    def cache_delete(key) -> bool
    def cache_clear_pattern(pattern: str) -> int
    def track_device_usage(device_id, user_id, client_id) -> int
    def get_device_user_count(device_id, client_id) -> int
    def create_session(session_id, data, ttl=3600) -> bool
    def get_session(session_id) -> Optional[Dict]
    def delete_session(session_id) -> bool
    def cache_consortium_data(identifier_hash, data, ttl=300) -> bool
    def get_consortium_data(identifier_hash) -> Optional[Dict]
    def increment_counter(key, amount=1) -> int
    def get_counter(key) -> int
    def reset_counter(key) -> bool
    def health_check() -> bool
    def get_info() -> Dict[str, Any]
```

#### Key Features
- **Velocity Tracking**: Tracks transaction counts in 1min, 10min, 1hour, 24hour windows
- **Rate Limiting**: Sliding window algorithm for API request throttling
- **Device Tracking**: Tracks unique users per device
- **Session Management**: Stores user session data with TTL
- **Consortium Caching**: Caches fraud intelligence data by hashed identifiers
- **Counter Management**: Tracks statistics across operations

#### Dependencies
```python
- redis
- json
- typing
- datetime
- app.core.config.settings
```

#### Integration Points
- Called by: CacheService, FraudDetector, RateLimitMiddleware, WebhookService
- Dependency: Redis server (localhost:6379)
- Fallback: API continues without Redis (degraded performance)

#### Configuration
```python
REDIS_URL: str = "redis://localhost:6379/0"
REDIS_MAX_CONNECTIONS: int = 50
```

#### Redis Key Patterns
```
velocity:{client_id}:{user_id}:1min
velocity:{client_id}:{user_id}:10min
velocity:{client_id}:{user_id}:1hour
velocity:{client_id}:{user_id}:24hour
velocity_amount:{client_id}:{user_id}:1hour
velocity_amount:{client_id}:{user_id}:24hour
ratelimit:{client_id}
device:{client_id}:{device_id}:users
session:{session_id}
consortium:{identifier_hash}
cache:{key}
counter:{key}
```

---

### 3. BVN VERIFICATION SERVICE (bvn_verification.py)
**File**: `/home/user/sentinel/app/services/bvn_verification.py` (400 lines)

#### Purpose
Nigerian identity verification through BVN (Bank Verification Number), NIN, and phone verification with integration to NIBSS and NIMC APIs.

#### Key Classes & Methods
```python
class BVNVerificationService:
    def __init__()
    async def verify_bvn(bvn, first_name=None, last_name=None, phone=None, dob=None) -> Dict[str, Any]
    async def verify_nin(nin, first_name=None, last_name=None, dob=None) -> Dict[str, Any]
    async def verify_phone(phone, expected_name=None) -> Dict[str, Any]
    
    # Private helpers
    async def _call_nibss_api(bvn, phone=None, dob=None) -> Dict[str, Any]
    def _mock_nibss_response(bvn) -> Dict[str, Any]
    def _fuzzy_match(expected, actual) -> bool
    def _normalize_phone(phone) -> Optional[str]
    def _detect_operator(phone) -> str
    def _check_warnings(bvn_data, matches) -> list
```

#### Key Features
- **BVN Verification**: 11-digit Bank Verification Number validation against NIBSS
- **Name Matching**: Fuzzy string matching to verify identity information
- **Phone Normalization**: Converts Nigerian phone numbers to standard format
- **Operator Detection**: Identifies mobile network (MTN, Airtel, Glo, 9mobile)
- **Warning Detection**: Flags watchlist status, name mismatches, DOB mismatches
- **Mock Mode**: Returns mock responses in development (when API key not configured)

#### Dependencies
```python
- typing
- datetime
- httpx (async HTTP client)
- app.core.config.settings
```

#### Integration Points
- Called by: API endpoints for identity verification
- External APIs: NIBSS (BVN), NIMC (NIN), Mobile operators
- Fallback: Mock responses when API credentials not configured

#### Configuration
```python
NIBSS_API_URL = "https://api.nibss-plc.com.ng"
NIBSS_API_KEY = settings.NIBSS_API_KEY
timeout = 30.0 seconds
```

#### Phone Number Formats Supported
```
+2348012345678 → 08012345678
2348012345678  → 08012345678
8012345678     → 08012345678
```

#### Operator Detection Prefixes
```
MTN:    803, 806, 810, 813, 814, 816, 903, 906
Airtel: 802, 808, 812, 901, 902, 904, 907
Glo:    805, 807, 811, 815, 905
9mobile: 809, 817, 818, 908, 909
```

---

### 4. FINGERPRINT FRAUD RULES (fingerprint_rules.py)
**File**: `/home/user/sentinel/app/services/fingerprint_rules.py` (519 lines)

#### Purpose
Detect device fingerprint-based fraud patterns including loan stacking, high-velocity attacks, and cross-lender fraud.

#### Key Classes & Methods
```python
class FingerprintFraudRules:
    def __init__()
    def check_fingerprint_fraud(fingerprint, user_id, client_id, db, amount=None) -> List[Dict[str, Any]]
    def _check_multiple_users_same_device(fingerprint, user_id, client_id, db, amount) -> Optional[Dict]
    def _check_high_velocity(fingerprint, client_id, db) -> Optional[Dict]
    def _check_fraud_history(fingerprint, db) -> Optional[Dict]
    def _check_consortium_detection(fingerprint, client_id, db) -> Optional[Dict]
    def get_fingerprint_analytics(fingerprint, db) -> Dict[str, Any]
```

#### Key Detection Rules

**Rule 1: Loan Stacking (Multiple Users Same Device)**
- Threshold: 3+ distinct users on same device in 7 days
- Severity: high/critical (score: 60-80)
- Confidence: 0.85
- Example: "Device used by 5 users in 7 days (loan stacking)"

**Rule 2: High Velocity (Automated Fraud)**
- Threshold: >5 applications from device today
- Severity: medium/high/critical (score: 40-60)
- Confidence: 0.75
- Example: "Device used for 12 applications today"

**Rule 3: Fraud History (Known Fraudster Device)**
- Threshold: Any confirmed fraud cases (is_fraud=True)
- Severity: critical (score: 80-100)
- Confidence: 0.95 (very high)
- Example: "Device linked to 3 confirmed fraud cases"

**Rule 4: Consortium Detection (Cross-Lender Fraud)**
- Threshold: Device seen at 2+ other lenders in 7 days
- Severity: high/critical (score: 70-90)
- Confidence: 0.85
- Example: "Device seen at 4 other lenders this week"

#### Dependencies
```python
- typing
- datetime
- sqlalchemy.orm.Session
- sqlalchemy (func, and_, or_)
- app.models.database.Transaction
```

#### Integration Points
- Called by: FraudDetector (core/fraud_detector.py)
- Database: Queries Transaction table
- Time windows: 7 days for patterns, 1 day for velocity

#### Database Queries
```sql
-- Rule 1: Count distinct users with fingerprint at lender
SELECT COUNT(DISTINCT user_id) FROM transactions
WHERE device_fingerprint = ? AND client_id = ? 
  AND created_at >= NOW() - INTERVAL '7 days'
  AND user_id != ?

-- Rule 2: Count transactions today
SELECT COUNT(*) FROM transactions
WHERE device_fingerprint = ? AND client_id = ?
  AND created_at >= TODAY

-- Rule 3: Count fraud cases
SELECT COUNT(*) FROM transactions
WHERE device_fingerprint = ? AND is_fraud = true

-- Rule 4: Count distinct lenders
SELECT COUNT(DISTINCT client_id) FROM transactions
WHERE device_fingerprint = ? AND client_id != ?
  AND created_at >= NOW() - INTERVAL '7 days'
```

---

### 5. CONSORTIUM SERVICE (consortium.py)
**File**: `/home/user/sentinel/app/services/consortium.py` (307 lines)

#### Purpose
Privacy-preserving cross-lender fraud detection using SHA-256 hashed identifiers to share fraud patterns across lending consortium members.

#### Key Classes & Methods
```python
class ConsortiumService:
    def __init__(db: Session, client_id: str)
    def check_fraud_patterns(transaction) -> Dict[str, Any]
    def report_fraud(transaction, fraud_type, amount) -> None
    def _update_consortium_record(device_hash=None, bvn_hash=None, phone_hash=None, 
                                  email_hash=None, fraud_type=None, amount=0) -> None
    def check_loan_stacking(transaction, days=7) -> Dict[str, Any]
    def get_statistics() -> Dict[str, Any]
```

#### Key Features
- **Privacy-First Architecture**: Uses SHA-256 hashes to store identifiers (PII never stored)
- **Multi-Identifier Tracking**: Tracks fraud patterns by device, BVN, phone, and email
- **Risk Assessment**: Calculates overall risk based on fraud count and client count
- **Alerts Generation**: Generates human-readable alerts based on consortium findings
- **Loan Stacking Detection**: Identifies applicants applying to multiple lenders

#### Privacy Hashing
```python
device_hash = hash_device_id(device_id)      # SHA-256(device_id)
bvn_hash = hash_bvn(bvn)                    # SHA-256(bvn)
phone_hash = hash_phone(phone)              # SHA-256(phone)
email_hash = hash_email(email)              # SHA-256(email)
```

#### Alert Triggers
```
client_count >= 3:     "⚠️ LOAN STACKING: Applied to X other lenders"
fraud_count >= 2:      "🚨 KNOWN FRAUDSTER: Flagged X times by other lenders"
total_amount > ₦1M:    "💰 HIGH EXPOSURE: Involved in ₦X of fraud"
```

#### Risk Levels
```
risk_level = "none"     if no matches
risk_level = "medium"   if fraud_count >= 1
risk_level = "high"     if fraud_count >= 3
risk_level = "critical" if fraud_count >= 5
```

#### Dependencies
```python
- typing
- datetime
- sqlalchemy.orm.Session
- app.models.database (ConsortiumIntelligence, Transaction)
- app.core.security (hash_*, functions)
- app.models.schemas.TransactionCheckRequest
```

#### Integration Points
- Called by: FraudDetector
- Database: Reads Transaction table, reads/writes ConsortiumIntelligence table
- Feedback flow: Called when fraud is confirmed via feedback endpoint

#### Database Tables
**Reads from**:
- `transactions` table (to check for matching identifiers across lenders)

**Writes to**:
- `consortium_intelligence` table (stores hashed fraud patterns)

---

### 6. LEARNING SERVICE (learning.py)
**File**: `/home/user/sentinel/app/services/learning.py` (223 lines)

#### Purpose
Continuous learning from fraud feedback to improve rule accuracy and adjust rule weights over time.

#### Key Classes & Methods
```python
class LearningService:
    def __init__(db: Session)
    def process_feedback(transaction_id, actual_outcome, fraud_type=None) -> Dict[str, any]
    def get_total_feedback_count() -> int
    def get_rule_accuracy(rule_name) -> Optional[Dict]
    def get_all_rule_accuracies() -> list
    def calculate_overall_accuracy(client_id=None) -> Dict
```

#### Key Features
- **Rule Accuracy Tracking**: Tracks true/false positives for each fraud rule
- **Weight Adjustment**: Increases weight for accurate rules, decreases for inaccurate ones
- **Metrics Calculation**: Computes accuracy, precision, recall, false positive rate
- **Continuous Improvement**: Uses feedback to improve model over time
- **Per-Rule Learning**: Adjusts individual rule weights based on performance

#### Accuracy Calculations
```python
# For each triggered rule:
accuracy = correct_predictions / triggered_count
precision = correct_predictions / (correct_predictions + false_positives)

# Weight adjustment:
if accuracy >= 0.80:
    weight = min(1.5, weight + 0.1)  # Increase trust
elif accuracy < 0.60:
    weight = max(0.5, weight - 0.1)  # Decrease trust
```

#### Overall Metrics
```python
accuracy = (TP + TN) / total
precision = TP / (TP + FP)
recall = TP / (TP + FN)
false_positive_rate = FP / (FP + TN)
```

#### Dependencies
```python
- typing
- sqlalchemy.orm.Session
- app.models.database (RuleAccuracy, Transaction)
- decimal.Decimal
```

#### Integration Points
- Called by: Feedback endpoint (app/api/v1/endpoints/feedback.py)
- Database: Reads/writes Transaction and RuleAccuracy tables
- Feedback loop: Processes merchant feedback about fraud outcomes

#### Database Tables
**Reads/Writes to**:
- `transactions` (reads is_fraud, writes fraud_type)
- `rule_accuracy` (tracks rule performance metrics)

---

### 7. ML FRAUD DETECTOR (ml_detector.py)
**File**: `/home/user/sentinel/app/services/ml_detector.py` (400+ lines)

#### Purpose
Machine learning-based fraud detection using XGBoost with per-vertical models, feature engineering, and model versioning.

#### Key Classes & Methods
```python
class MLFraudDetector:
    def __init__(model_path="models/fraud_model.json")
    def load_model(path) -> bool
    def predict(transaction, context, industry=None) -> Dict[str, Any]
    def _engineer_features(transaction, context) -> Dict[str, float]
    def _get_feature_importance() -> Dict[str, float]
    def _calculate_confidence(fraud_probability) -> float
```

#### Key Features
- **85%+ Accuracy**: High fraud detection accuracy
- **Real-time Prediction**: <50ms response time
- **Per-Vertical Models**: Separate XGBoost models for each industry
- **Feature Engineering**: 50+ features including velocity, behavioral, temporal
- **Model Versioning**: Tracks which model/vertical was used
- **Explainability**: Returns top 5 most important features

#### Supported Verticals/Industries
```
- lending (traditional lending loans)
- crypto (cryptocurrency transactions)
- ecommerce (online shopping)
- betting (sports betting/gaming)
- fintech (fintech apps)
- payments (payment processors)
- marketplace (vendor marketplaces)
```

#### Feature Categories
**Amount Features**:
- amount
- amount_log
- amount_sqrt

**Account Age Features**:
- account_age_days
- account_age_log
- is_new_account (<7 days)
- is_very_new_account (<3 days)

**Transaction History**:
- transaction_count
- transaction_count_log
- is_first_transaction

**Contact Changes**:
- phone_changed_recently
- email_changed_recently
- any_contact_changed

**Temporal Features**:
- hour_of_day
- day_of_week
- is_weekend
- is_night
- is_business_hours

**Velocity Features**:
- velocity_1min, 10min, 1hour, 24hour
- amount_1hour, 24hour

**Other Features**:
- dormant_days
- is_dormant_reactivation
- (50+ additional features)

#### Model Output
```python
{
    "fraud_probability": 0.75,      # 0-1 scale
    "ml_risk_score": 75,            # 0-100 scale
    "confidence": 0.92,              # How confident in prediction
    "model_version": "xgboost_v1.0_lending",  # Which model used
    "features_used": 48,             # Number of features
    "top_features": [                # Feature importance
        {"name": "velocity_24hour", "importance": 0.15},
        ...
    ],
    "industry": "lending"            # Industry vertical
}
```

#### Dependencies
```python
- os
- pickle
- numpy
- typing
- datetime
- xgboost
- sklearn.preprocessing.StandardScaler
- app.models.schemas.TransactionCheckRequest
```

#### Integration Points
- Called by: FraudDetector
- Models location: `/models/` directory
- Per-vertical models: `fraud_model_{vertical}.json`
- Scalers: `fraud_model_{vertical}_scaler.pkl`
- Feature lists: `fraud_model_{vertical}_features.pkl`

#### Model Files
```
models/
├── fraud_model.json              # Global model
├── fraud_model_scaler.pkl
├── fraud_model_features.pkl
├── fraud_model_lending.json      # Lending-specific
├── fraud_model_lending_scaler.pkl
├── fraud_model_lending_features.pkl
├── fraud_model_crypto.json       # Crypto-specific
├── ... (per-vertical models)
```

#### Configuration
```python
self.supported_verticals = [
    "lending", "crypto", "ecommerce", "betting", "fintech", "payments", "marketplace"
]
```

---

### 8. WEBHOOK SERVICE (webhook.py)
**File**: `/home/user/sentinel/app/services/webhook.py` (264 lines)

#### Purpose
Real-time fraud alert notifications with HMAC signature verification, exponential backoff retry, and multiple event types.

#### Key Classes & Methods
```python
class WebhookService:
    def __init__()
    async def send_fraud_alert(client, transaction, event_type="transaction.high_risk") -> bool
    async def send_feedback_notification(client, transaction_id, actual_outcome, fraud_type=None) -> bool
    async def send_batch_summary(client, summary) -> bool
    def _build_payload(transaction, event_type) -> Dict[str, Any]
    def _generate_signature(payload, secret) -> str
    async def _send_with_retry(url, payload, headers) -> bool
    def verify_signature(payload, signature, secret) -> bool
```

#### Event Types
```
transaction.high_risk      # High risk transaction detected
transaction.declined       # Transaction declined by system
fraud.confirmed           # Merchant confirmed fraud
fraud.false_positive      # Merchant reported false positive
batch.summary             # Daily/hourly summary report
```

#### Webhook Payload Examples

**Fraud Alert Event**:
```json
{
    "event": "transaction.high_risk",
    "transaction_id": "txn_12345",
    "user_id": "user_789",
    "amount": 250000,
    "risk_score": 85,
    "risk_level": "high",
    "decision": "decline",
    "flags": [...],
    "recommendation": "Decline or request video verification",
    "consortium_alerts": ["Applied to 3 lenders"],
    "timestamp": "2025-11-22T10:30:45"
}
```

**Feedback Notification**:
```json
{
    "event": "fraud.confirmed",
    "transaction_id": "txn_12345",
    "actual_outcome": "fraud",
    "fraud_type": "loan_stacking",
    "timestamp": "2025-11-22T10:30:45"
}
```

**Batch Summary**:
```json
{
    "event": "batch.summary",
    "period": "daily",
    "total_transactions": 1250,
    "high_risk_count": 145,
    "fraud_prevented_amount": 52500000,
    "timestamp": "2025-11-22T10:30:45"
}
```

#### Security Features
- **HMAC-SHA256 Signature**: Clients verify webhook authenticity
- **Headers**: X-Sentinel-Signature, X-Sentinel-Event, X-Sentinel-Timestamp
- **Signature Verification**: `hmac.compare_digest()` prevents timing attacks

#### Retry Mechanism
```python
max_retries = 3
retry_delays = [2, 4, 8]  # seconds (exponential backoff)
timeout = 10.0  # seconds per request
```

#### Success Criteria
- 2xx status codes: Success
- 4xx status codes: Don't retry (client error)
- 5xx status codes: Retry with backoff
- Connection errors: Retry with backoff

#### Dependencies
```python
- hmac
- hashlib
- asyncio
- typing
- datetime
- httpx (async HTTP)
- sqlalchemy.orm.Session
- app.models.database.Client
- app.core.config.settings
```

#### Integration Points
- Called by: Fraud detection endpoints, feedback endpoint
- Used by: Background task `send_webhook_async()`
- Triggered on: High risk transactions, fraud confirmation, batch schedules

#### Configuration
```python
max_retries = 3
retry_delays = [2, 4, 8]
timeout = 10.0
```

---

### 9. FRAUD RULES ENGINE (rules.py)
**File**: `/home/user/sentinel/app/services/rules.py` (5346 lines)

#### Purpose
Comprehensive fraud detection rules engine with 160+ detection rules covering all industry verticals and fraud patterns.

#### Key Classes & Methods
```python
class FraudRule:
    def __init__(name, description, base_score, severity, verticals=None)
    def check(transaction, context) -> Optional[FraudFlag]
    def applies_to_vertical(industry) -> bool

class FraudRulesEngine:
    def check_all_rules(transaction, context) -> List[FraudFlag]
```

#### Rule Categories (160+ Rules)

**A. Account & Authentication Rules (30+ rules)**
- New Account Large Amount (Rule 1)
- Quick Signup Transaction (Rule 3)
- Multiple Devices Same User (Rule 33)
- Failed Login Velocity ATO (Rule 104)
- Password Reset Withdrawal (Rule 103)
- Two Factor Bypass (Rule 105)
- Biometric Auth Failure (Rule 106)

**B. Device & Browser Rules (35+ rules)**
- New Device (Rule 7)
- Device Sharing (Rule 12)
- Device Fingerprint Change (Rule 34)
- Browser Version Anomaly (Rule 35)
- GPU Fingerprint Anomaly (Rule 36)
- Canvas Fingerprinter (Rule 47)
- WebGL Fingerprint (Rule 48)
- Font List Anomaly (Rule 49)
- CPU Core Anomaly (Rule 50)
- Battery Drain Anomaly (Rule 51)
- Emulator Detection (Rule 172)
- Jailbreak Detection (Rule 173)
- Malware App Detection (Rule 174)

**C. Behavioral & Typing Pattern Rules (25+ rules)**
- Mouse Movement Suspicious (Rule 52)
- Typing Speed Constant (Rule 53)
- Keystroke Dynamics Failure (Rule 54)
- Copy Paste Abuse (Rule 55)
- Session Duration Anomaly (Rule 56)
- Form Filling Speed (Rule 66)
- Hesitation Detection (Rule 67)
- Error Correction Pattern (Rule 68)
- Tab Switching (Rule 69)
- Window Resize Activity (Rule 70)

**D. Velocity & Transaction Rules (25+ rules)**
- Loan Stacking (Rule 2)
- Velocity Check (Rule 5)
- High Velocity Acceleration (Rule 59)
- Unusual Timing Pattern (Rule 65)
- Transaction Velocity Acceleration (Rule 60)
- Duplicate Transaction (Rule 105)
- Multiple Failed Payments (Rule 16)
- Excessive Withdrawals (Rule 24)

**E. Geographic & Location Rules (10+ rules)**
- Impossible Travel (Rule 10)
- IP Location Consistency (Rule 38)
- ISP Reputation (Rule 39)
- ASN Blacklist (Rule 40)
- Address Distance Anomaly (Rule 85)
- Shipping Billing Distance (Rule 3)
- Geographic Impossibility ATO (Rule 102)

**F. Contact & Verification Rules (15+ rules)**
- Phone Changed Recently (Rule 3)
- Email Changed Recently (Rule 3)
- Contact Change Withdrawal (Rule 6)
- Unverified Phone (Rule 30)
- Phone Verification Failure (Rule 26)
- Phone Country Mismatch (Rule 27)
- Email Domain Legitimacy (Rule 32)
- Email Verification Mismatch (Rule 33)
- Unverified Address (Rule 3)
- Unverified Social Media (Rule 38)

**G. Identity & Verification Rules (15+ rules)**
- BVN Age Inconsistency (Rule 28)
- BVN Fraud History (Rule 125)
- Synthetic Identity (Rule 119)
- Common Name Detection (Rule 127)
- Illegal Email Domain (Rule 129)
- High Risk Phone Carrier (Rule 130)
- Email Fraud History (Rule 82)
- Phone Fraud History (Rule 83)
- Device Fraud History (Rule 84)

**H. Financial & Payment Rules (20+ rules)**
- Card Age New (Rule 77)
- Card Testing Pattern (Rule 78)
- Card Reputation Low (Rule 79)
- First Time Card (Rule 91)
- Card Velocity (Rule 92)
- Multiple Cards Device (Rule 89)
- Card BIN Mismatch (Rule 90)
- Card BIN Fraud (Rule 14)
- Multiple Failed Payments (Rule 16)
- New Bank Account Withdrawal (Rule 81)
- Bank Account Verification Fail (Rule 82)

**I. Crypto & Wallet Rules (10+ rules)**
- New Wallet High Value (Rule 25)
- Suspicious Wallet (Rule 26)
- P2P Velocity (Rule 27)
- Crypto New Wallet High Value (Rule 87)
- Crypto Withdrawal After Deposit (Rule 88)
- New Wallet High Value (Rule 118)

**J. E-Commerce & Marketplace Rules (15+ rules)**
- Shipping Mismatch (Rule 19)
- Digital Goods High Value (Rule 20)
- Digital Goods High Amount (Rule 104)
- Bulk Digital Goods (Rule 105)
- New Seller High Value (Rule 49)
- Low Rated Seller (Rule 50)
- High Risk Category (Rule 51)
- Dropshipping (Rule 178)
- Merchant High Risk Category (Rule 89)
- Merchant Chargeback Rate (Rule 90)
- Merchant Refund Rate (Rule 91)

**K. Betting & Gaming Rules (10+ rules)**
- Bonus Abuse (Rule 21)
- Withdrawal Without Wagering (Rule 22)
- Arbitrage Betting (Rule 23)
- Excessive Withdrawals (Rule 24)
- Arbitrage Betting High Likelihood (Rule 180)

**L. Consortium Intelligence Rules (15+ rules)**
- Consortium Email Frequency (Rule 95)
- Consortium Phone Frequency (Rule 96)
- Consortium Device Frequency (Rule 97)
- Consortium BVN Frequency (Rule 98)
- Network Velocity Email (Rule 99)
- Network Velocity Phone (Rule 100)
- Network Velocity Device (Rule 101)
- Network Velocity IP (Rule 102)
- Same IP Multiple Users (Rule 103)
- Same Device Multiple Users (Rule 104)
- Same Address Multiple Users (Rule 105)
- Connected Accounts Detected (Rule 108)
- Fraud Ring Detection (Rule 130)
- Money Mule (Rule 133)

**M. Machine Learning & Anomaly Rules (15+ rules)**
- Outlier Score High (Rule 112)
- XGBoost High Risk (Rule 113)
- Neural Network High Risk (Rule 114)
- Ensemble Model Consensus (Rule 115)
- LSTM Sequence Anomaly (Rule 116)
- GNN Graph Anomaly (Rule 117)
- ML Anomaly Detection (Rule 164)
- Fraud Probability High (Rule 111)
- Low Legitimacy Score (Rule 167)
- Profile Deviation (Rule 168)

**N. Advanced Fraud Patterns (20+ rules)**
- Fraudster Profile Match (Rule 118)
- Email Similarity High (Rule 119)
- Behavior Similarity High (Rule 120)
- Family Connection Detected (Rule 121)
- Business Connection Detected (Rule 122)
- Geographic Connection Detected (Rule 123)
- Sequential Applications (Rule 13)
- Dormant Account Activation (Rule 11)
- Round Amount (Rule 8)
- Maximum First Transaction (Rule 9)
- SIM Swap Pattern (Rule 3)
- Suspicious Hours (Rule 4)
- VPN/Proxy (Rule 11)
- Disposable Email (Rule 12)

#### Rule Structure
```python
class ExampleRule(FraudRule):
    def __init__(self):
        super().__init__(
            name="example_rule",
            description="What this rule detects",
            base_score=30,  # Points contributed if triggered
            severity="medium",  # low, medium, high, critical
            verticals=["lending", "fintech"]  # Industries affected
        )
    
    def check(self, transaction, context) -> Optional[FraudFlag]:
        # Check if rule is triggered
        if self.is_triggered(transaction, context):
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message="Human-readable explanation",
                score=self.base_score,
                confidence=0.85,
                metadata={"additional": "context"}
            )
        return None
```

#### Rule Scoring
- **Low**: 10-20 points
- **Medium**: 30-40 points
- **High**: 50-70 points
- **Critical**: 80+ points

#### Vertical-Specific Rules
```
Lending-specific:
- Loan Stacking (critical)
- SIM Swap Pattern (critical)
- Sequential Applications (high)

Crypto-specific:
- New Wallet High Value
- Suspicious Wallet
- P2P Velocity

Betting-specific:
- Bonus Abuse
- Withdrawal Without Wagering
- Arbitrage Betting

E-Commerce-specific:
- Shipping Mismatch
- Digital Goods High Value
- Dropshipping
```

#### Dependencies
```python
- typing
- datetime
- time
- re (regex)
- sqlalchemy
- app.models.schemas (FraudFlag, TransactionCheckRequest)
```

#### Integration Points
- Called by: FraudDetector
- Central to: All fraud detection logic
- Configurable: Per-vertical rule weights in settings

---

## Integration Architecture

### Request Flow Diagram
```
1. HTTP Request (POST /api/v1/check-transaction)
   ↓
2. RateLimitMiddleware (check API key + rate limit)
   ↓
3. Dependency Injection (get_current_client, get_db)
   ↓
4. check_transaction endpoint
   ├─ Cache lookup (CacheService.get_cached_result)
   │  ├─ Cache HIT → return cached result (5ms)
   │  └─ Cache MISS → continue
   │
   ├─ FraudDetector.check_transaction
   │  ├─ Build context (velocity, location, etc.)
   │  ├─ Run 160+ fraud rules (FraudRulesEngine)
   │  ├─ Check fingerprint patterns (FingerprintFraudRules)
   │  ├─ Check consortium intelligence (ConsortiumService)
   │  ├─ Run ML model (MLFraudDetector)
   │  └─ Calculate final risk score
   │
   ├─ Cache result (CacheService.set_cached_result)
   │
   ├─ Store in database (app/models/database.py)
   │
   └─ Send webhook (WebhookService.send_fraud_alert) - async

5. Return response (TransactionCheckResponse)
   Total time: 5ms (cached) or 87ms (uncached)
```

### Service Call Hierarchy
```
API Endpoint (fraud_detection.py)
    ↓
FraudDetector (core/fraud_detector.py)
    ├─ FraudRulesEngine (services/rules.py)
    │   └─ 160+ FraudRule implementations
    │
    ├─ FingerprintFraudRules (services/fingerprint_rules.py)
    │   └─ Database queries (transactions table)
    │
    ├─ ConsortiumService (services/consortium.py)
    │   ├─ Database queries (transactions table)
    │   └─ Database writes (consortium_intelligence table)
    │
    ├─ MLFraudDetector (services/ml_detector.py)
    │   └─ Feature engineering
    │
    └─ [Store result in database]

Support Services:
├─ CacheService (services/cache_service.py)
│   └─ RedisService (services/redis_service.py)
│
├─ WebhookService (services/webhook.py)
│   └─ Async HTTP requests
│
├─ LearningService (services/learning.py)
│   └─ Database writes (rule_accuracy table)
│
└─ BVNVerificationService (services/bvn_verification.py)
   └─ External API calls (NIBSS, NIMC)
```

---

## Database Schema

### Key Tables

#### 1. transactions
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    transaction_type VARCHAR(50),
    industry VARCHAR(50) DEFAULT 'lending',
    device_id VARCHAR(255),
    device_fingerprint VARCHAR(255),
    ip_address INET,
    account_age_days INTEGER,
    transaction_count INTEGER,
    phone_changed_recently BOOLEAN DEFAULT FALSE,
    email_changed_recently BOOLEAN DEFAULT FALSE,
    bvn VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    city VARCHAR(100),
    country VARCHAR(100),
    risk_score INTEGER,
    risk_level VARCHAR(20),
    decision VARCHAR(20),
    flags JSONB,
    is_fraud BOOLEAN,
    fraud_type VARCHAR(100),
    fraud_confirmed_at TIMESTAMP,
    created_at TIMESTAMP,
    
    -- Indexes for query performance
    INDEX idx_client_id (client_id),
    INDEX idx_user_id (user_id),
    INDEX idx_device_fingerprint (device_fingerprint),
    INDEX idx_created_at (created_at),
    INDEX idx_industry (industry)
);
```

#### 2. consortium_intelligence
```sql
CREATE TABLE consortium_intelligence (
    id SERIAL PRIMARY KEY,
    device_hash VARCHAR(255),      -- SHA-256(device_id)
    bvn_hash VARCHAR(255),         -- SHA-256(bvn)
    phone_hash VARCHAR(255),       -- SHA-256(phone)
    email_hash VARCHAR(255),       -- SHA-256(email)
    fraud_count INTEGER DEFAULT 0,
    client_count INTEGER DEFAULT 0,
    fraud_types JSONB,             -- Array of fraud type strings
    total_amount_involved NUMERIC(15, 2),
    risk_level VARCHAR(20),
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX idx_device_hash (device_hash),
    INDEX idx_bvn_hash (bvn_hash),
    INDEX idx_phone_hash (phone_hash),
    INDEX idx_email_hash (email_hash),
    INDEX idx_risk_level (risk_level)
);
```

#### 3. rule_accuracy
```sql
CREATE TABLE rule_accuracy (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL UNIQUE,
    triggered_count INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    accuracy DECIMAL(5, 4),
    precision DECIMAL(5, 4),
    current_weight DECIMAL(3, 2) DEFAULT 1.0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX idx_rule_name (rule_name)
);
```

#### 4. clients
```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    subscription_tier VARCHAR(50),
    webhook_url VARCHAR(500),
    webhook_secret VARCHAR(255),
    risk_thresholds JSONB,
    rule_weights JSONB,
    vertical VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Configuration Requirements

### Environment Variables
```bash
# Application
APP_NAME=Sentinel Fraud Detection
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://sentinel:password@localhost:5432/sentinel
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Security
API_KEY_HEADER=X-API-Key
CORS_ORIGINS=https://example.com,https://app.example.com
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Fraud Detection
RISK_THRESHOLD_HIGH=70
RISK_THRESHOLD_MEDIUM=40
MAX_PROCESSING_TIME_MS=100

# Per-Vertical Configuration
VERTICAL_RISK_THRESHOLDS={
    "lending": {"high": 70, "medium": 40},
    "crypto": {"high": 60, "medium": 30},
    "ecommerce": {"high": 75, "medium": 45},
    ...
}

# Monitoring
SENTRY_DSN=https://...
ENABLE_METRICS=True
LOG_LEVEL=INFO

# BVN Integration
NIBSS_API_URL=https://api.nibss-plc.com.ng
NIBSS_API_KEY=your-api-key
```

### Redis Configuration
```
Host: localhost (or REDIS_URL)
Port: 6379
Database: 0
Max Connections: 50
```

### PostgreSQL Configuration
```
Host: localhost
Port: 5432
Database: sentinel
User: sentinel
Password: sentinel_password
Pool Size: 20
Max Overflow: 0
```

### Per-Vertical Risk Thresholds
```python
VERTICAL_RISK_THRESHOLDS = {
    "lending": {"high": 70, "medium": 40},
    "fintech": {"high": 65, "medium": 35},
    "payments": {"high": 65, "medium": 35},
    "crypto": {"high": 60, "medium": 30},
    "ecommerce": {"high": 75, "medium": 45},
    "betting": {"high": 55, "medium": 25},
    "gaming": {"high": 55, "medium": 25},
    "marketplace": {"high": 70, "medium": 40}
}
```

### Per-Vertical Rule Weights
```python
VERTICAL_RULE_WEIGHTS = {
    "crypto": {
        "new_wallet_high_value": 1.3,
        "suspicious_wallet": 1.5,
        "p2p_velocity": 1.2
    },
    "betting": {
        "bonus_abuse": 1.4,
        "withdrawal_without_wagering": 1.5,
        "device_sharing": 1.3
    },
    ...
}
```

---

## Service Dependencies Summary

### External Services
- **NIBSS API**: BVN verification (bvn_verification_service)
- **NIMC API**: NIN verification (bvn_verification_service)
- **Mobile Operators**: Phone verification (bvn_verification_service)

### Internal Dependencies
- **PostgreSQL**: Primary data store
- **Redis**: Caching, velocity tracking, rate limiting
- **XGBoost**: ML fraud prediction
- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **SQLAlchemy**: ORM

### Optional Services
- **Sentry**: Error tracking
- **Prometheus**: Metrics (if ENABLE_METRICS=True)
- **Datadog/CloudWatch**: Monitoring

---

## Performance Metrics

### Response Times
- **Cached request**: ~5ms (17x faster)
- **Uncached request**: ~87ms
- **ML model prediction**: <50ms
- **Database query**: ~20-30ms

### Throughput
- **Per-server**: 10,000+ requests/minute
- **Recommended deployment**: Load balancer with 3-5 backend servers

### Cache Hit Rate
- **Production typical**: 15-30%
- **Cache TTL**: 5 minutes
- **Cache key**: SHA-256 hash of transaction inputs

### Redis Keys (Typical)
- **Fraud check cache**: ~100,000-500,000 keys
- **Velocity tracking**: ~10,000-100,000 keys per hour
- **Session storage**: ~1,000-10,000 keys
- **Memory usage**: 500MB - 2GB depending on traffic

---

## API Endpoints Using Services

### Primary Endpoints
- **POST** `/api/v1/check-transaction` → Uses all services
- **POST** `/api/v1/feedback` → Uses LearningService, ConsortiumService
- **GET** `/api/v1/consortium/statistics` → Uses ConsortiumService
- **GET** `/api/v1/dashboard` → Uses LearningService, Analytics
- **GET** `/health` → Uses RedisService, Database

---

## Deployment Checklist

- [ ] PostgreSQL database configured
- [ ] Redis instance running
- [ ] ML models loaded (`models/fraud_model.json`)
- [ ] Per-vertical models (optional): `models/fraud_model_*.json`
- [ ] NIBSS API credentials configured (optional)
- [ ] Webhook URLs configured for clients
- [ ] Rate limiting tiers configured
- [ ] Risk thresholds per vertical reviewed
- [ ] Rule weights per vertical customized
- [ ] CORS origins configured
- [ ] SSL/TLS certificates installed
- [ ] Monitoring/alerting configured
- [ ] Backup strategy in place

---

**Document Version**: 1.0
**Generated**: November 22, 2025
**Sentinel Platform**: Version 1.0.0
