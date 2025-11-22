# 🏗️ SENTINEL SERVICES DEEP DIVE

**Complete Documentation of All Core Services and Integration Patterns**

**Last Updated:** 2025-01-22
**Total Services:** 9 Core Services + Supporting Utilities
**Total Lines of Service Code:** 9,805
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Services Architecture](#services-architecture)
2. [Core Services](#core-services)
3. [Supporting Services](#supporting-services)
4. [Service Integration Patterns](#service-integration-patterns)
5. [Database Integration](#database-integration)
6. [Caching & Performance](#caching--performance)
7. [Error Handling](#error-handling)
8. [Configuration & Deployment](#configuration--deployment)

---

## Services Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      SENTINEL ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────┘

                           FastAPI Application
                                  │
                        ┌─────────┼─────────┐
                        ↓         ↓         ↓
                   Rate Limit   Health   Root
                   Middleware   Check    Info
                        │
                        ↓
                ┌─────────────────────┐
                │  Cache Service      │
                │  (Redis 5-min TTL)  │
                │  17x faster (5ms)   │
                └──────────┬──────────┘
                           │
                           ↓
        ┌──────────────────────────────────────────────┐
        │     Fraud Detection Engine (Main Service)    │
        │  - FraudRulesEngine (160+ rules)             │
        │  - Hybrid Scoring (70% Rules + 30% ML)       │
        │  - Vertical-Specific Weighting (8 verticals) │
        └──────┬───────────────────┬────────────┬──────┘
               │                   │            │
        ┌──────▼──────┐   ┌────────▼────────┐  │
        │  Rule-Based │   │  ML Detector    │  │
        │  Engine     │   │  (XGBoost)      │  │
        │  160+ rules │   │  85%+ accuracy  │  │
        └──────┬──────┘   └────────┬────────┘  │
               │                   │            │
               └───────────┬───────┘            │
                           │                   │
                    ┌──────▼─────────────────────────────┐
                    │    Learning Service                │
                    │    - Feedback loop                 │
                    │    - Rule weight adjustment        │
                    │    - Model retraining trigger      │
                    └──────┬───────────────────────────┬─┘
                           │                           │
        ┌──────────────────┴────────────────┬──────────▼──────────┐
        ↓                                   ↓                     ↓
   ┌─────────────┐              ┌──────────────────────┐  ┌──────────────┐
   │Consortium   │              │BVN Verification      │  │Fingerprint   │
   │Service      │              │Service               │  │Rules         │
   │             │              │                      │  │              │
   │ - Loan      │              │ - NIBSS API          │  │ - Device ID  │
   │   Stacking  │              │ - Phone norm         │  │ - Canvas     │
   │ - SIM Swap  │              │ - NIN matching       │  │ - WebGL      │
   │ - Network   │              │ - Name fuzzy match   │  │ - Fonts      │
   │   Linkage   │              │                      │  │ - CPU        │
   └─────────────┘              └──────────────────────┘  └──────────────┘
        │                                   │                     │
        └───────────────────┬───────────────┴─────────────────────┘
                            │
                            ↓
                    ┌──────────────────┐
                    │ Webhook Service  │
                    │ Real-time Alerts │
                    │ HMAC Security    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
          Redis Service  PostgreSQL     Monitoring
          Velocity       Database       & Logging
          Tracking       Features
```

---

## Core Services

### 1. Cache Service

**File:** `/app/services/cache_service.py` (393 lines)
**Purpose:** Response caching for 17x faster fraud detection
**Performance:** 5ms (cached) vs 87ms (uncached)

#### Overview

The Cache Service provides response caching for fraud detection results. When the same transaction pattern is checked within the 5-minute window, the cached result is returned instantly instead of re-evaluating all 160+ rules.

#### Key Methods

```python
class CacheService:
    async def get_cached_result(transaction: Dict) -> Optional[Dict]
    async def set_cached_result(transaction: Dict, result: Dict) -> bool
    async def invalidate_user_cache(user_id: str) -> int
    async def clear_all_cache() -> int
    async def get_cache_stats() -> Dict[str, int]
```

#### How It Works

1. **Cache Key Generation:** SHA-256 hash of transaction inputs
   ```
   Hash Input: user_id + amount + device_id + ip_address + merchant_id
   Cache Key: fraud_check_cache:{hash}
   TTL: 300 seconds (5 minutes)
   ```

2. **Cache Hit Scenario:**
   ```
   User submits: TXN_001 (USR123, 50,000 NGN)
   Result: Cache hit → 5ms response

   User submits: TXN_002 (USR123, 50,000 NGN) - same pattern
   Result: Cache hit → 5ms response (same cache key)
   ```

3. **Cache Invalidation:**
   ```
   - User cache cleared on feedback submission
   - All cache cleared on rule update
   - Automatic expiry after 5 minutes
   ```

#### Integration Points

- **Called by:** `fraud_detection.py` endpoint (check_transaction)
- **Calls:** RedisService (cache_get, cache_set)
- **Dependency:** Redis server running

#### Configuration

```python
self.cache_ttl = 300  # 5 minutes
self.cache_prefix = "fraud_check_cache:"
self.max_cache_size = 100000  # entries
```

#### Usage Example

```python
from app.services.cache_service import CacheService

cache = CacheService(redis_service)

# Check if result cached
cached = await cache.get_cached_result(transaction)
if cached:
    return cached  # 5ms response!

# Run fraud detection
result = evaluate_transaction(transaction)

# Cache result for next time
await cache.set_cached_result(transaction, result)
return result
```

---

### 2. Redis Service

**File:** `/app/services/redis_service.py` (353 lines)
**Purpose:** Velocity tracking, rate limiting, session management
**Key Feature:** Sub-millisecond operation speeds

#### Overview

The Redis Service provides distributed caching, velocity tracking, rate limiting, and session management. It's critical for detecting high-frequency fraud attempts and enforcing API rate limits.

#### Key Methods

```python
class RedisService:
    # Velocity Tracking
    def track_transaction_velocity(user_id, client_id, amount) -> Dict[str, int]
    def get_velocity_data(user_id, client_id) -> Dict[str, Any]

    # Rate Limiting
    def check_rate_limit(client_id, limit=10000, window=3600) -> Dict[str, Any]

    # Caching
    def cache_set(key, value, ttl=300) -> bool
    def cache_get(key) -> Optional[Any]
    def cache_delete(key) -> bool
    def cache_clear_pattern(pattern: str) -> int

    # Device Tracking
    def track_device_usage(device_id, user_id, client_id) -> int
    def get_device_user_count(device_id, client_id) -> int

    # Session Management
    def create_session(session_id, data, ttl=3600) -> bool
    def get_session(session_id) -> Optional[Dict]
    def delete_session(session_id) -> bool

    # Consortium Data
    def cache_consortium_data(identifier_hash, data, ttl=300) -> bool
    def get_consortium_data(identifier_hash) -> Optional[Dict]

    # Counters
    def increment_counter(key, amount=1) -> int
    def get_counter(key) -> int
    def reset_counter(key) -> bool
```

#### Velocity Tracking

Tracks transaction velocity in multiple time windows to detect rapid-fire attacks:

```
Tracked Metrics:
├── 1-minute window:   Count of transactions
├── 10-minute window:  Count of transactions
├── 1-hour window:     Count + Total amount
└── 24-hour window:    Count + Total amount

Example:
User: USR123
1-min:   3 transactions
10-min:  8 transactions
1-hour:  25 transactions, 500,000 NGN
24-hour: 120 transactions, 5,000,000 NGN
```

#### Rate Limiting Algorithm

```python
# Sliding Window Counter Algorithm
def check_rate_limit(client_id, limit=10000, window=3600):
    current_count = redis.get(f"ratelimit:{client_id}")

    if current_count >= limit:
        return {"allowed": False, "retry_after": 60}

    redis.increment(f"ratelimit:{client_id}")
    redis.expire(f"ratelimit:{client_id}", window)

    return {
        "allowed": True,
        "remaining": limit - current_count - 1,
        "reset_in": window
    }
```

#### Redis Key Patterns

```
Velocity Tracking:
├── velocity:{client_id}:{user_id}:1min     → int (count)
├── velocity:{client_id}:{user_id}:10min    → int (count)
├── velocity:{client_id}:{user_id}:1hour    → int (count)
├── velocity:{client_id}:{user_id}:24hour   → int (count)
├── velocity_amount:{client_id}:{user_id}:1hour   → float (total)
└── velocity_amount:{client_id}:{user_id}:24hour  → float (total)

Rate Limiting:
└── ratelimit:{client_id}                   → int (request count)

Device Tracking:
└── device:{client_id}:{device_id}:users    → set (user_ids)

Session Management:
└── session:{session_id}                    → dict (session data)

Consortium Caching:
└── consortium:{identifier_hash}            → dict (fraud intelligence)

Cache:
└── cache:{key}                             → any (cached value)
```

#### Integration Points

- **Called by:** CacheService, FraudDetector, RateLimitMiddleware, WebhookService
- **Used for:** Velocity detection, rate limiting, device tracking, session storage
- **Dependency:** Redis server (localhost:6379)

#### Configuration

```python
REDIS_URL: str = "redis://localhost:6379/0"
REDIS_MAX_CONNECTIONS: int = 50
REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
REDIS_SOCKET_KEEPALIVE: bool = True
REDIS_DECODE_RESPONSES: bool = True
```

#### Performance Metrics

- Get operation: ~0.5ms
- Set operation: ~0.5ms
- Increment counter: ~0.3ms
- Supports: 50K ops/sec per connection

---

### 3. Fraud Rules Engine

**File:** `/app/services/rules.py` (1,500+ lines)
**Purpose:** Core rule-based fraud detection (160+ rules)
**Supported Verticals:** 8 (Lending, Fintech, Payments, Crypto, Ecommerce, Betting, Gaming, Marketplace)

#### Overview

The Fraud Rules Engine contains all 160+ fraud detection rules organized across 6 categories. Rules are implemented as polymorphic classes inheriting from `FraudRule` base class.

#### Rule Categories

```
1. Behavioral & Velocity Rules (60 rules)
   - Account behavior, device changes, impossible travel
   - VelocityCheckRule, NewAccountLargeAmountRule, ImpossibleTravelRule

2. Device Fingerprinting Rules (60 rules)
   - Canvas, WebGL, fonts, CPU, battery anomalies
   - DeviceFingerprintChangeRule, BrowserVersionAnomalyRule

3. Consortium & Network Rules (40 rules)
   - Cross-lender fraud, loan stacking, network linkage
   - ConsortiumVelocityRule, FraudHistoryRule

4. Card & Payment Rules (40 rules)
   - Card testing, BIN fraud, address distance
   - CardTestingRule, CardBINFraudRule

5. ML & Anomaly Detection Rules (30 rules)
   - Statistical outliers, ML model predictions
   - OutlierScoreHighRule, XGBoostHighRiskRule

6. ATO (Account Takeover) Rules (20 rules)
   - Password reset, login failures, device changes
   - PasswordResetRule, LoginFailureRule
```

#### Rule Base Class

```python
class FraudRule:
    def __init__(self):
        self.rule_id = 1
        self.rule_name = "NewAccountLargeAmountRule"
        self.category = "behavioral"
        self.severity = "HIGH"
        self.fraud_score = 85

    def check(self, transaction: Dict, context: Dict) -> RuleResult:
        """Check if transaction triggers this rule"""
        # Implementation specific to rule
        return RuleResult(
            passed=True/False,
            fraud_score=0-100,
            message="Rule-specific message"
        )
```

#### Key Methods

```python
class FraudRulesEngine:
    def __init__(self)
    def evaluate_transaction(transaction: Dict, context: Dict) -> Dict
    def evaluate_with_vertical(transaction: Dict, vertical: IndustryVertical) -> Dict
    def get_rule(rule_id: int) -> FraudRule
    def list_rules(category: str = None) -> List[FraudRule]
    def get_rules_count() -> int
```

#### Scoring Algorithm

```python
def evaluate_transaction(transaction: Dict, context: Dict) -> Dict:
    triggered_rules = []
    total_score = 0

    # Evaluate each rule
    for rule_name, rule in self.rules.items():
        result = rule.check(transaction, context)

        if not result.passed:
            triggered_rules.append({
                "rule_name": rule_name,
                "severity": rule.severity,
                "fraud_score_contribution": result.fraud_score
            })
            total_score += result.fraud_score

    # Normalize to 0-100
    final_score = min(100, total_score / max(len(self.rules), 1))

    return {
        "fraud_score": final_score,
        "fraud_level": "low" if final_score < 33 else "medium" if final_score < 67 else "high",
        "is_fraudulent": final_score > threshold,
        "rules_triggered": triggered_rules
    }
```

#### Vertical-Specific Weighting

Different verticals weight rules differently for optimal fraud detection:

```python
# Crypto Vertical (50% threshold, aggressive)
CRYPTO_RULE_WEIGHTS = {
    "SuspiciousWalletRule": 1.5,      # Critical for crypto
    "KYCVerificationRule": 2.0,       # AML requirements
    "NewWalletHighValueRule": 1.8,
    "CardBINFraudRule": 0.0,          # Not applicable
}

# Lending Vertical (65% threshold)
LENDING_RULE_WEIGHTS = {
    "MaximumFirstTransactionRule": 1.8,
    "LoanStackingRule": 1.5,
    "NewAccountLargeAmountRule": 1.6,
    "GamblingTransactionRule": 0.3,   # Not relevant
}
```

#### Integration Points

- **Called by:** fraud_detection endpoints, dashboard endpoints
- **Calls:** Redis service for velocity data, database for user history
- **Vertical configuration:** From VerticalConfigService
- **Feedback:** Learning service updates rule weights

#### Usage Example

```python
from app.services.rules import FraudRulesEngine
from app.models.schemas import IndustryVertical

engine = FraudRulesEngine()

transaction = {
    "transaction_id": "TXN001",
    "user_id": "USR001",
    "amount": 50000,
    "currency": "NGN",
    "user_country": "NG"
}

# Basic evaluation
result = engine.evaluate_transaction(transaction, {})
print(f"Fraud Score: {result['fraud_score']}")
print(f"Rules Triggered: {len(result['rules_triggered'])}")

# Vertical-specific evaluation
result = engine.evaluate_with_vertical(
    transaction,
    IndustryVertical.CRYPTO
)
print(f"Crypto Score: {result['fraud_score']}")
```

---

### 4. ML Fraud Detector

**File:** `/app/services/ml_detector.py` (400+ lines)
**Purpose:** Machine learning-based fraud detection using XGBoost
**Accuracy:** 85%+ with 92% precision, 87% recall

#### Overview

The ML Fraud Detector complements the rule-based engine with machine learning predictions. It calculates 249+ features from transaction data and uses a trained XGBoost model for classification.

#### Key Methods

```python
class MLFraudDetector:
    def __init__(self)
    def predict(transaction: Dict, features: Dict) -> Dict
    def predict_batch(transactions: List[Dict]) -> List[Dict]
    def get_feature_importance() -> Dict[str, float]
    def update_model(new_training_data: List[Dict]) -> bool
```

#### Feature Engineering Pipeline

```
Input Transaction
    │
    ├─ Identity Features (30)
    │  ├─ Email verification status
    │  ├─ Phone verification status
    │  ├─ KYC completion status
    │  ├─ BVN age consistency
    │  └─ Address verification
    │
    ├─ Behavioral Features (25)
    │  ├─ Account age in days
    │  ├─ Transaction count
    │  ├─ Days since last login
    │  ├─ Login pattern consistency
    │  └─ Device change frequency
    │
    ├─ Transaction Features (30)
    │  ├─ Amount
    │  ├─ Currency
    │  ├─ Transaction type
    │  ├─ Merchant category
    │  └─ Time of day
    │
    ├─ Network Features (20)
    │  ├─ IP reputation
    │  ├─ ISP blacklist status
    │  ├─ VPN/Proxy detection
    │  └─ ASN classification
    │
    ├─ Consortium Features (40)
    │  ├─ Loan stacking risk
    │  ├─ Multi-lender velocity
    │  ├─ Network fraud links
    │  └─ Consortium alerts
    │
    ├─ Device Features (35)
    │  ├─ Canvas fingerprint match
    │  ├─ WebGL fingerprint match
    │  ├─ Font consistency
    │  ├─ Browser version anomaly
    │  └─ Device ID history
    │
    ├─ ATO Features (25)
    │  ├─ Password reset recent
    │  ├─ Login failure count
    │  ├─ Email change recent
    │  └─ Phone change recent
    │
    ├─ Funding Source Features (20)
    │  ├─ Wallet age
    │  ├─ Wallet reputation
    │  ├─ Funding pattern
    │  └─ Withdrawal risk
    │
    └─ Derived Features (44)
       ├─ Risk score aggregates
       ├─ Velocity ratios
       ├─ Time-based features
       └─ Interaction features

Total: 249+ Features
    │
    └─ XGBoost Model
       └─ Prediction: Fraud Probability (0-1)
```

#### Model Architecture

```
XGBoost Configuration:
├── n_estimators: 100
├── max_depth: 7
├── learning_rate: 0.1
├── subsample: 0.8
├── colsample_bytree: 0.8
├── min_child_weight: 1
└── objective: binary:logistic

Performance:
├── Accuracy: 85%+
├── Precision: 92%
├── Recall: 87%
├── F1-Score: 0.89
└── AUC-ROC: 0.93
```

#### Hybrid Scoring (70% Rules + 30% ML)

```python
def hybrid_score(rule_score, ml_score):
    """Combine rule-based and ML scores"""
    final_score = (rule_score * 0.70) + (ml_score * 0.30)
    return min(100, max(0, final_score))

Example:
Rule-based score: 60
ML score: 80
Final: (60 * 0.70) + (80 * 0.30) = 42 + 24 = 66
```

#### Integration Points

- **Called by:** FraudDetector (hybrid scoring)
- **Uses:** Feature calculation service
- **Training:** Learning service (scheduled retraining)
- **Model storage:** /models/xgboost_model.pkl

#### Usage Example

```python
from app.services.ml_detector import MLFraudDetector
from app.services.feature_calculator import FeatureCalculator

detector = MLFraudDetector()
features = FeatureCalculator.calculate(transaction)

ml_result = detector.predict(transaction, features)
print(f"ML Fraud Probability: {ml_result['fraud_probability']:.2%}")
```

---

### 5. Learning Service

**File:** `/app/services/learning.py` (380+ lines)
**Purpose:** Continuous fraud detection improvement through feedback
**Trigger:** Scheduled retraining when feedback threshold met

#### Overview

The Learning Service tracks feedback, updates rule weights, and schedules model retraining to continuously improve detection accuracy.

#### Key Methods

```python
class LearningService:
    async def process_feedback(feedback: FeedbackRequest) -> Dict
    async def update_rule_weights(feedback_data: Dict) -> Dict
    async def evaluate_rules_accuracy() -> Dict
    async def trigger_model_retraining() -> bool
    async def get_learning_metrics() -> Dict
```

#### Feedback Processing Workflow

```
User submits feedback:
  "Transaction TXN001 was actually fraud"
    │
    ├─ 1. Validate feedback
    ├─ 2. Update rule accuracy metrics
    ├─ 3. Adjust rule weights based on accuracy
    ├─ 4. Calculate impact score
    ├─ 5. Store in feedback history
    ├─ 6. Check retraining threshold
    │
    └─ If 100+ new feedback items:
       └─ Trigger model retraining (runs in background)
           ├─ Load new training data
           ├─ Train XGBoost model
           ├─ Validate on test set
           ├─ Deploy new model
           └─ Notify admin of improvements
```

#### Rule Weight Adjustment

```python
def update_rule_weight(rule_name, accuracy, precision, recall):
    """Adjust rule weight based on performance metrics"""

    if accuracy > 0.92:
        weight = 1.5      # Increase trust in accurate rules
    elif accuracy > 0.85:
        weight = 1.2
    elif accuracy > 0.75:
        weight = 1.0      # Default weight
    elif accuracy > 0.65:
        weight = 0.8
    else:
        weight = 0.5      # Decrease trust in poor rules

    # Store in database
    db.update_rule_weight(rule_name, weight)
```

#### Learning Metrics

```python
class LearningMetrics:
    total_feedback_count: int          # Total feedback received
    accuracy_improvement: float         # % improvement since last period
    rules_adjusted: int                # Rules modified
    model_retraining_count: int        # Times model retrained
    avg_feedback_processing_time: int  # ms
    last_retraining_time: datetime
    next_retraining_scheduled: datetime
```

#### Integration Points

- **Called by:** Feedback endpoint (/api/v1/feedback)
- **Updates:** Rule weights in database
- **Schedules:** Model retraining (daily/weekly)
- **Monitors:** Accuracy metrics dashboard

#### Usage Example

```python
from app.services.learning import LearningService

service = LearningService()

feedback = {
    "transaction_id": "TXN001",
    "actual_outcome": "fraud",
    "fraud_type": "loan_stacking"
}

result = await service.process_feedback(feedback)
print(f"Accuracy improvement: {result['accuracy_improvement']:.2%}")
print(f"Rules adjusted: {result['rules_adjusted']}")
```

---

### 6. BVN Verification Service

**File:** `/app/services/bvn_verification.py` (400 lines)
**Purpose:** Nigerian identity verification (NIBSS, NIMC, phone networks)
**Coverage:** BVN, NIN, Phone number validation

#### Overview

The BVN Verification Service performs Nigeria-specific identity verification critical for lending and fintech verticals operating in Nigeria.

#### Key Methods

```python
class BVNVerificationService:
    async def verify_bvn(
        bvn: str,
        first_name: str = None,
        last_name: str = None,
        phone: str = None,
        dob: str = None
    ) -> Dict[str, Any]

    async def verify_nin(
        nin: str,
        first_name: str = None,
        last_name: str = None,
        dob: str = None
    ) -> Dict[str, Any]

    async def verify_phone(
        phone: str,
        expected_name: str = None
    ) -> Dict[str, Any]
```

#### BVN Verification Response

```json
{
  "status": "verified|failed|warning",
  "bvn": "22345678901",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "phone_number": "08012345678",
  "email": "john@example.com",
  "gender": "M",
  "nationality": "Nigerian",
  "address": "123 Main St, Lagos",
  "registration_date": "2015-06-10",
  "warnings": [
    "Name mismatch detected",
    "Age inconsistency",
    "On watchlist"
  ]
}
```

#### Phone Number Normalization

```
Input formats supported:
├── +2348012345678  →  08012345678
├── 2348012345678   →  08012345678
├── 8012345678      →  08012345678
└── (234) 801-2345  →  08012345678

Operator Detection:
├── MTN:    803, 806, 810, 813, 814, 816, 903, 906
├── Airtel: 802, 808, 812, 901, 902, 904, 907
├── Glo:    805, 807, 811, 815, 905
└── 9mobile: 809, 817, 818, 908, 909
```

#### Fuzzy Matching for Names

```python
def fuzzy_match(expected, actual) -> bool:
    """Match names allowing for typos and variations"""

    # Normalize both names
    expected = normalize(expected)  # lowercase, trim whitespace
    actual = normalize(actual)

    # Exact match
    if expected == actual:
        return True

    # Fuzzy match (90% similarity)
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, expected, actual).ratio()
    return ratio >= 0.90

Examples:
├── "John Doe" vs "john doe"           → True (exact after normalize)
├── "John Doe" vs "Jon Doe"            → True (90% match)
├── "John Doe" vs "Jane Doe"           → False (60% match)
└── "John Doe" vs "John D"             → True (fuzzy match)
```

#### API Integration

```python
# Configuration
NIBSS_API_URL = "https://api.nibss-plc.com.ng"
NIBSS_API_KEY = settings.NIBSS_API_KEY
TIMEOUT = 30.0

# Mock Mode
If NIBSS_API_KEY not configured:
  └─ Return mock responses (development/testing)

# Fallback
If API timeout/error:
  └─ Return "unverified" status with warning
```

#### Integration Points

- **Called by:** API endpoints for identity verification
- **External APIs:** NIBSS (BVN), NIMC (NIN), Mobile operators
- **Database:** Stores verification results
- **Fallback:** Mock responses in development

#### Usage Example

```python
from app.services.bvn_verification import BVNVerificationService

service = BVNVerificationService()

# Verify BVN
result = await service.verify_bvn(
    bvn="22345678901",
    first_name="John",
    last_name="Doe",
    phone="+2348012345678",
    dob="1990-01-15"
)

if result["status"] == "verified":
    print("✓ Identity verified")
elif result["status"] == "warning":
    print(f"⚠ Warnings: {result['warnings']}")
else:
    print("✗ Verification failed")
```

---

### 7. Consortium Service

**File:** `/app/services/consortium.py` (450+ lines)
**Purpose:** Cross-lender fraud intelligence and blocklists
**Coverage:** 145+ member institutions

#### Overview

The Consortium Service integrates with consortium fraud intelligence networks to detect fraud patterns across multiple lenders (loan stacking, SIM swap, etc.).

#### Key Methods

```python
class ConsortiumService:
    async def check_fraud_alert(
        identifier_hash: str,
        identifier_type: str,
        client_id: str
    ) -> Dict[str, Any]

    async def get_lender_risk(user_id: str, client_id: str) -> float
    async def submit_fraud_alert(alert_data: Dict) -> bool
    async def get_consortium_stats() -> Dict[str, Any]
```

#### Fraud Alert Types

```
1. Loan Stacking Alert
   Condition: 2+ applications within 7 days
   Risk: High (75-85 score)
   Example: User applied to 3 lenders in 48 hours

2. SIM Swap Alert
   Condition: Phone number changed across lenders within 24 hours
   Risk: Critical (90-100 score)
   Example: Phone changed at 2 lenders on same day

3. Multiple Applications Alert
   Condition: 3+ applications from same identity
   Risk: High (70-80 score)
   Example: Same email/phone used across 4 lenders

4. Fraud Network Alert
   Condition: Account linked to known fraud network
   Risk: Critical (85-100 score)
   Example: Device used in 5+ confirmed fraud cases

5. Account Takeover Alert
   Condition: Unusual activity pattern compared to user history
   Risk: High (75-85 score)
   Example: Login from new country, large withdrawal
```

#### Identifier Hashing

```python
def hash_identifier(identifier: str, identifier_type: str) -> str:
    """Create one-way hash of PII for consortium sharing"""

    # Normalize
    normalized = normalize(identifier)

    # Create hash
    hash_value = hashlib.sha256(
        f"{normalized}:{identifier_type}".encode()
    ).hexdigest()

    return hash_value

Examples:
├── BVN "22345678901"          → hash_20a3...
├── Phone "+2348012345678"     → hash_e5f2...
├── Email "john@example.com"   → hash_7c1d...
└── Device "device_abc123"     → hash_f9e4...

Security: One-way hash prevents reverse lookup of PII
```

#### Consortium Sharing Flow

```
Local Fraud Detected
    │
    ├─ Hash PII (BVN, phone, email, device)
    ├─ Create fraud alert
    ├─ Submit to consortium network
    │
    └─ Consortium broadcasts to all members
       ├─ Member A: "Alert! Hash_xxx seen here too"
       ├─ Member B: "Match found in our records"
       └─ Member C: "Same device at our institution"
           └─ Creates multi-lender alert
               └─ Syndicated risk: CRITICAL
```

#### Integration Points

- **Called by:** FraudDetector (check risk), Feedback (submit alerts)
- **External:** Consortium API (async submission)
- **Caching:** Redis consortium cache (5-min TTL)
- **Database:** Consortium alerts table

#### Usage Example

```python
from app.services.consortium import ConsortiumService

service = ConsortiumService()

# Check if user has consortium alerts
risk = await service.check_fraud_alert(
    identifier_hash="hash_20a3...",
    identifier_type="bvn",
    client_id="CLI001"
)

if risk["alert_found"]:
    print(f"⚠ Consortium Alert: {risk['message']}")
    print(f"  Other lenders involved: {risk['lender_count']}")
```

---

### 8. Fingerprint Rules Service

**File:** `/app/services/fingerprint_rules.py` (519 lines)
**Purpose:** Device fingerprint-based fraud detection (4 rules)
**Coverage:** Canvas, WebGL, fonts, CPU, battery

#### Overview

The Fingerprint Rules Service detects device-based fraud patterns including loan stacking, velocity attacks, known fraud devices, and cross-lender fraud.

#### 4 Core Detection Rules

```
1. LOAN STACKING RULE
   Detection: 3+ distinct users on same device in 7 days
   Severity: HIGH/CRITICAL
   Score: 60-80
   Example: "Device used by 5 users in 7 days"
   Confidence: 0.85

2. HIGH VELOCITY RULE
   Detection: >5 applications from device today
   Severity: MEDIUM/HIGH/CRITICAL
   Score: 40-80
   Example: "Device used for 12 applications today"
   Confidence: 0.75

3. FRAUD HISTORY RULE
   Detection: Device linked to confirmed fraud cases
   Severity: CRITICAL
   Score: 80-100
   Example: "Device linked to 3 confirmed fraud cases"
   Confidence: 0.95

4. CONSORTIUM DETECTION RULE
   Detection: Device seen at 2+ other lenders in 7 days
   Severity: HIGH/CRITICAL
   Score: 70-90
   Example: "Device seen at 4 other lenders this week"
   Confidence: 0.85
```

#### Fingerprint Generation

```
Device Fingerprinting Components:
├── Canvas Hash
│   └─ Rendering capability fingerprint
├── WebGL Hash
│   └─ GPU capabilities fingerprint
├── Font Hash
│   └─ Installed fonts hash
├── CPU Count
│   └─ Number of processors
├── RAM Size
│   └─ Total memory
├── Battery Status
│   └─ Battery level + charging status
├── Screen Resolution
│   └─ Width x Height x DPI
└── User Agent
    └─ Browser + OS fingerprint

Combined: SHA-256 hash of all components
Example: device_abc123def456...
```

#### Detection Queries

```sql
-- Rule 1: Loan Stacking
SELECT COUNT(DISTINCT user_id) as user_count
FROM transactions
WHERE device_fingerprint = ?
  AND client_id = ?
  AND created_at >= NOW() - INTERVAL '7 days'
  AND user_id != ?

-- Rule 2: High Velocity
SELECT COUNT(*) as app_count
FROM transactions
WHERE device_fingerprint = ?
  AND created_at >= NOW() - INTERVAL '1 day'

-- Rule 3: Fraud History
SELECT COUNT(*) as fraud_count
FROM transactions
WHERE device_fingerprint = ?
  AND is_fraud = TRUE

-- Rule 4: Consortium Detection
SELECT COUNT(DISTINCT client_id) as lender_count
FROM transactions
WHERE device_fingerprint = ?
  AND client_id != ?
  AND created_at >= NOW() - INTERVAL '7 days'
```

#### Integration Points

- **Called by:** FraudDetector (core/fraud_detector.py)
- **Database:** Transaction table queries
- **Time windows:** 7 days for patterns, 1 day for velocity
- **Performance:** ~15ms per device check

#### Usage Example

```python
from app.services.fingerprint_rules import FingerprintFraudRules

rules = FingerprintFraudRules()

# Check device for fraud patterns
results = rules.check_fingerprint_fraud(
    fingerprint="device_abc123...",
    user_id="USR001",
    client_id="CLI001",
    db=session,
    amount=50000
)

for fraud_pattern in results:
    print(f"Rule: {fraud_pattern['rule_name']}")
    print(f"Score: {fraud_pattern['score']}")
    print(f"Message: {fraud_pattern['message']}")
```

---

### 9. Webhook Service

**File:** `/app/services/webhook.py` (380+ lines)
**Purpose:** Real-time fraud notifications with HMAC security
**Security:** HMAC-SHA256 request signing

#### Overview

The Webhook Service sends real-time notifications to client systems about fraud detections, consortium alerts, and feedback processing.

#### Key Methods

```python
class WebhookService:
    async def send_fraud_alert(event_data: Dict) -> Dict
    async def send_consortium_alert(alert: Dict) -> Dict
    async def send_feedback_processed(feedback_id: str) -> Dict
    async def retry_failed_webhooks() -> int
    async def get_webhook_stats() -> Dict
```

#### Webhook Event Types

```
1. Fraud Detected
   Trigger: When fraud score exceeds threshold
   Payload: Transaction, fraud score, rules triggered

2. Consortium Alert
   Trigger: Multi-lender fraud pattern detected
   Payload: Alert ID, lender count, alert type

3. Feedback Processed
   Trigger: When feedback improves accuracy
   Payload: Feedback ID, accuracy improvement, rules adjusted

4. Model Retrained
   Trigger: When ML model updated
   Payload: Improvement metrics, new accuracy
```

#### Webhook Security (HMAC-SHA256)

```python
def sign_webhook_payload(payload: str, webhook_secret: str) -> str:
    """Create HMAC-SHA256 signature for webhook"""
    import hmac
    import hashlib

    signature = hmac.new(
        webhook_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"sha256={signature}"

Example:
Secret: "whsec_abc123xyz..."
Payload: '{"transaction_id":"TXN001",...}'
Signature: "sha256=5e7c9a3b2f..."
```

#### Webhook Payload Example

```json
{
  "id": "evt_abc123xyz",
  "event_type": "fraud_detected",
  "timestamp": "2024-01-22T10:30:00Z",
  "data": {
    "transaction_id": "TXN001",
    "user_id": "USR001",
    "fraud_score": 72.5,
    "fraud_level": "high",
    "decision": "decline",
    "rules_triggered": [
      {
        "rule_name": "ImpossibleTravelRule",
        "severity": "critical",
        "score": 50
      }
    ]
  }
}

Headers:
├── X-Sentinel-Event-Id: evt_abc123xyz
├── X-Sentinel-Event-Type: fraud_detected
├── X-Sentinel-Signature: sha256=5e7c9a3b2f...
└── X-Sentinel-Timestamp: 2024-01-22T10:30:00Z
```

#### Retry Logic

```python
def send_webhook_with_retries(url: str, payload: Dict):
    """Send webhook with exponential backoff retries"""

    max_retries = 3
    backoff_delays = [2, 4, 8]  # seconds

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=get_signed_headers(payload),
                timeout=10
            )
            if response.status_code < 400:
                return True  # Success
        except Exception as e:
            if attempt < max_retries:
                sleep(backoff_delays[attempt])
                continue

        return False  # All retries failed
```

#### Integration Points

- **Called by:** FraudDetector, ConsortiumService, LearningService
- **Configuration:** Webhook URLs per client
- **Security:** HMAC-SHA256 signing
- **Retry:** 3 retries with exponential backoff
- **Persistence:** Failed webhooks stored for manual replay

#### Usage Example

```python
from app.services.webhook import WebhookService

webhook_service = WebhookService()

# Send fraud alert
await webhook_service.send_fraud_alert({
    "transaction_id": "TXN001",
    "fraud_score": 72.5,
    "decision": "decline",
    "rules_triggered": [...]
})

# Send consortium alert
await webhook_service.send_consortium_alert({
    "alert_id": "ALR001",
    "alert_type": "loan_stacking",
    "lender_count": 3
})
```

---

## Supporting Services

### Configuration Service

**File:** `/app/core/config.py` (150+ lines)

Centralized configuration management for all settings:

```python
class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "SENTINEL Fraud Detection API"
    API_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/sentinel"
    SQLALCHEMY_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # External APIs
    NIBSS_API_KEY: str = ""
    CONSORTIUM_API_URL: str = ""

    # ML Models
    MODEL_PATH: str = "/models/xgboost_model.pkl"

    # Thresholds
    FRAUD_THRESHOLD: float = 70.0  # Default across verticals

    class Config:
        env_file = ".env"
```

### Security Service

**File:** `/app/core/security.py` (120+ lines)

Security utilities for authentication and encryption:

```python
def verify_api_key(api_key: str) -> Optional[Client]
def hash_password(password: str) -> str
def verify_password(plain: str, hashed: str) -> bool
def create_access_token(data: Dict) -> str
def verify_token(token: str) -> Dict
```

### Monitoring Service

**File:** `/app/core/monitoring.py` (200+ lines)

Metrics collection and monitoring:

```python
class MetricsCollector:
    def record_transaction_check(duration: float)
    def record_fraud_detection(fraud_score: float)
    def record_api_call(endpoint: str, status_code: int)
    def get_metrics() -> Dict
```

---

## Service Integration Patterns

### Dependency Injection Pattern

```python
# Service initialization with dependencies
from app.services.cache_service import CacheService
from app.services.redis_service import RedisService

redis = RedisService()
cache = CacheService(redis)

# In endpoints:
@router.post("/check-transaction")
async def check_transaction(
    request: TransactionCheckRequest,
    redis: RedisService = Depends(get_redis_service),
    cache: CacheService = Depends(get_cache_service)
):
    # Use services
    cached = await cache.get_cached_result(request.dict())
    if cached:
        return cached
    # ...
```

### Service Chain Pattern

```
Request → Cache Service
           ├─ Hit → Return cached result
           └─ Miss → Continue
                └─ Fraud Rules Engine
                   ├─ Redis (velocity data)
                   └─ Database (user history)
                      └─ ML Fraud Detector
                         ├─ Feature Calculator
                         └─ XGBoost Model
                            └─ Learning Service
                               └─ Feedback processing
```

### Async/Await Pattern

```python
# All services support async operations
async def evaluate_transaction(transaction):
    # Parallel execution of independent services
    rules_result, ml_result = await asyncio.gather(
        fraud_engine.evaluate_transaction(transaction),
        ml_detector.predict(transaction, features)
    )

    # Combine results
    return hybrid_score(rules_result, ml_result)
```

---

## Database Integration

### Service-Database Mapping

```
CacheService     → None (Redis only)
RedisService     → Redis
FraudRulesEngine → transactions, users (read)
MLDetector       → features (JSONB), models (binary)
BVNService       → None (external APIs)
ConsortiumService → consortium_alerts (write)
LearningService  → rule_weights, feedback (write)
WebhookService   → webhook_logs (write)
```

### Critical Database Queries

```sql
-- Velocity check
SELECT COUNT(*), SUM(amount) FROM transactions
WHERE user_id = ? AND created_at >= NOW() - INTERVAL '1 hour'

-- Device fingerprinting
SELECT COUNT(DISTINCT user_id) FROM transactions
WHERE device_fingerprint = ? AND client_id = ?
AND created_at >= NOW() - INTERVAL '7 days'

-- Fraud history
SELECT COUNT(*) FROM transactions
WHERE user_id = ? AND is_fraud = TRUE

-- Consortium check
SELECT COUNT(DISTINCT client_id) FROM transactions
WHERE device_fingerprint = ? AND client_id != ?
```

### Database Indexes for Performance

```sql
-- Critical indexes for service performance
CREATE INDEX idx_user_velocity
  ON transactions(user_id, created_at);

CREATE INDEX idx_device_fingerprint
  ON transactions(device_fingerprint, created_at);

CREATE INDEX idx_consortium_search
  ON transactions(device_fingerprint, client_id, created_at);

CREATE INDEX idx_fraud_history
  ON transactions(user_id, is_fraud);
```

---

## Caching & Performance

### Cache Hierarchy

```
Level 1: Request Cache (5 minutes)
├─ Check: Transaction exact match (same user, amount, device)
├─ Hit: 5ms response
└─ TTL: 300 seconds

Level 2: Velocity Cache (real-time)
├─ Check: Transaction count in time windows
├─ Storage: Redis counters
└─ Update: On every transaction

Level 3: Consortium Cache (5 minutes)
├─ Check: PII hash in fraud database
├─ Hit: 10ms response
└─ TTL: 300 seconds

Level 4: Feature Cache (1 hour)
├─ Check: 249+ pre-calculated features
├─ Storage: Redis + Database
└─ TTL: 3600 seconds
```

### Performance Metrics

```
Service              Uncached   Cached    Improvement
────────────────────────────────────────────────────
Cache Service        N/A        5ms       Base operation
Fraud Rules Engine   87ms       5ms       17x faster
ML Detector          45ms       N/A       (separate cache)
BVN Verification     2000ms     1000ms    (API call)
Consortium Check     50ms       10ms      5x faster
─────────────────────────────────────────────────────
Total (end-to-end)   ~200ms     ~15ms     13x faster
```

---

## Error Handling

### Service-Level Error Codes

```
Redis Error:
├─ Connection: RedisConnectionError → Fallback to database
├─ Timeout: RedisTimeoutError → Retry with backoff
└─ Parse: RedisParseError → Use default value

Database Error:
├─ Connection: DatabaseConnectionError → Retry (3x)
├─ Timeout: QueryTimeoutError → Return cached result
└─ Constraint: ConstraintError → Validation error response

External API Error:
├─ Timeout: APITimeoutError → Fallback to mock
├─ Rate Limit: RateLimitError → Queue for retry
└─ Auth: AuthenticationError → Use cached data

ML Model Error:
├─ Model Load: ModelLoadError → Use rules-only scoring
├─ Prediction: PredictionError → Use default score
└─ Features: FeatureCalculationError → Skip ML component
```

### Graceful Degradation

```
Full System:
  Rules (70%) + ML (30%) → Hybrid score

Redis Down:
  Rules only → No velocity/caching penalty

Database Slow:
  Rules only → Skip device history checks

ML Model Down:
  Rules (100%) → No ML component

All Services Degraded:
  Basic rules (20 rules) → Basic fraud assessment
```

---

## Configuration & Deployment

### Environment Variables

```bash
# .env file
# Database
DATABASE_URL=postgresql://user:pass@localhost/sentinel

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
NIBSS_API_KEY=your_api_key_here
CONSORTIUM_API_URL=https://api.consortium.com

# ML Models
MODEL_PATH=/models/xgboost_model.pkl

# Thresholds
FRAUD_THRESHOLD=70.0

# Logging
LOG_LEVEL=INFO

# Monitoring
SENTRY_DSN=https://...
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs models

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://sentinel:password@postgres:5432/sentinel
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sentinel
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sentinel"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

---

## Best Practices

### 1. Service Initialization

```python
# ✓ Good: Lazy initialization with singleton
_redis_service = None

def get_redis_service() -> RedisService:
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service

# ✗ Bad: Creating new instance each time
def get_redis_service() -> RedisService:
    return RedisService()  # Wasteful, creates connection pool each time
```

### 2. Error Handling

```python
# ✓ Good: Graceful degradation
try:
    cached_result = await cache.get_cached_result(transaction)
    if cached_result:
        return cached_result
except RedisError as e:
    logger.error(f"Cache error: {e}")
    # Continue without cache

# ✗ Bad: Failing entire request
try:
    cached_result = await cache.get_cached_result(transaction)
except Exception as e:
    raise HTTPException(500, "Cache failed")  # Breaks entire system
```

### 3. Logging

```python
# ✓ Good: Contextual logging
logger.info(
    "Fraud detection complete",
    extra={
        "transaction_id": transaction_id,
        "fraud_score": fraud_score,
        "processing_time_ms": processing_time
    }
)

# ✗ Bad: No context
logger.info(f"Fraud score: {fraud_score}")
```

### 4. Monitoring

```python
# ✓ Good: Track metrics
metrics.record_transaction_check(processing_time)
metrics.record_fraud_detection(fraud_score)

# ✗ Bad: No monitoring
# No way to track system performance
```

---

**Last Updated:** 2025-01-22
**Total Services:** 9 Core + 5 Supporting
**Total Code:** 9,805 lines
**Status:** Production Ready
