# WEEK 3: ML Detector & Fingerprinting
**Days 71-77 | Month 3**

## Overview
This week adds machine learning capabilities and advanced device fingerprinting:
- ML-based fraud detection using XGBoost
- Device fingerprinting (Canvas, WebGL, GPU)
- Enhanced fraud detector combining ML + rules
- Rate limiting and logging middleware

## Files to Build

```
app/services/
├── ml_detector.py                # 450 lines - ML fraud detection
└── fingerprint_rules.py          # 320 lines - Device fingerprinting

app/core/
└── fraud_detector_v2.py          # 780 lines - Enhanced detector (ML + rules)

app/middleware/
├── __init__.py
├── rate_limit.py                 # 95 lines - Rate limiting
└── logging.py                    # 75 lines - Request logging
```

**Total for Week 3:** 6 files, ~1,720 lines of code

---

## Dependencies

Add new ML dependencies:

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

# NEW for ML (Month 3 Week 3)
scikit-learn==1.3.2
xgboost==2.0.3
numpy==1.26.2
pandas==2.1.4
joblib==1.3.2
```

---

## File Details

### 1. `app/services/ml_detector.py` (450 lines)

**Purpose:** Machine learning-based fraud detection

**Key Features:**
- XGBoost classifier for fraud prediction
- Feature engineering from transaction data
- Model loading and inference
- Confidence scores

**Key Functions:**

```python
import xgboost as xgb
import numpy as np
from typing import Dict, List

class MLFraudDetector:
    def __init__(self, model_path: str = "models/fraud_model.xgb"):
        """Initialize ML detector with trained model"""
        self.model = xgb.Booster()
        self.model.load_model(model_path)

    def predict(self, features: Dict) -> Dict:
        """
        Predict fraud probability using ML model

        Args:
            features: Dict with transaction features

        Returns:
            {
                "fraud_probability": 0.85,
                "ml_score": 85,
                "confidence": 0.9,
                "risk_factors": ["high_amount", "new_device"]
            }
        """

        # Engineer features
        feature_vector = self._engineer_features(features)

        # Convert to DMatrix
        dmatrix = xgb.DMatrix(feature_vector)

        # Predict
        probability = self.model.predict(dmatrix)[0]

        # Calculate score (0-100 scale)
        ml_score = int(probability * 100)

        # Identify key risk factors
        risk_factors = self._get_risk_factors(features, probability)

        return {
            "fraud_probability": round(probability, 3),
            "ml_score": ml_score,
            "confidence": 0.9 if probability > 0.8 or probability < 0.2 else 0.7,
            "risk_factors": risk_factors
        }

    def _engineer_features(self, features: Dict) -> np.ndarray:
        """Convert transaction features to ML feature vector"""

        feature_list = []

        # Numerical features
        feature_list.append(features.get("amount", 0))
        feature_list.append(features.get("account_age_days", 0))
        feature_list.append(features.get("transactions_last_hour", 0))
        feature_list.append(features.get("transactions_last_day", 0))
        feature_list.append(features.get("credit_score", 500))

        # Boolean features (convert to 0/1)
        feature_list.append(1 if features.get("is_vpn") else 0)
        feature_list.append(1 if features.get("is_tor") else 0)
        feature_list.append(1 if features.get("kyc_verified") else 0)

        # Categorical features (one-hot encoded)
        # Industry encoding
        industries = ["fintech", "lending", "crypto", "betting", "ecommerce"]
        for ind in industries:
            feature_list.append(1 if features.get("industry") == ind else 0)

        return np.array([feature_list], dtype=np.float32)

    def _get_risk_factors(self, features: Dict, probability: float) -> List[str]:
        """Identify key risk factors driving ML prediction"""

        risk_factors = []

        if features.get("amount", 0) > 500000:
            risk_factors.append("high_amount")

        if features.get("account_age_days", 999) < 30:
            risk_factors.append("new_account")

        if features.get("is_vpn"):
            risk_factors.append("vpn_usage")

        if features.get("transactions_last_hour", 0) > 5:
            risk_factors.append("high_velocity")

        return risk_factors[:3]  # Top 3
```

---

### 2. `app/services/fingerprint_rules.py` (320 lines)

**Purpose:** Advanced device fingerprinting

**Key Features:**
- Canvas fingerprinting detection
- WebGL fingerprinting
- GPU fingerprinting
- Fingerprint spoofing detection

**Key Functions:**

```python
class DeviceFingerprintService:
    def analyze_fingerprint(self, fingerprint_data: Dict) -> Dict:
        """
        Analyze device fingerprint for fraud indicators

        Args:
            fingerprint_data: {
                "canvas_fingerprint": "abc123...",
                "webgl_fingerprint": "xyz789...",
                "gpu_info": "NVIDIA GeForce...",
                "browser": "Chrome",
                "os": "Windows 10"
            }

        Returns:
            {
                "fingerprint_risk_score": 25,
                "spoofing_detected": False,
                "fingerprint_flags": []
            }
        """

        risk_score = 0
        flags = []

        # Check for fingerprint spoofing
        if self._is_spoofed(fingerprint_data):
            risk_score += 40
            flags.append("fingerprint_spoofing")

        # Check for known fraud devices
        if self._is_known_fraud_device(fingerprint_data):
            risk_score += 60
            flags.append("known_fraud_device")

        # Check for emulator indicators
        if self._is_emulator(fingerprint_data):
            risk_score += 50
            flags.append("emulator_detected")

        return {
            "fingerprint_risk_score": risk_score,
            "spoofing_detected": "fingerprint_spoofing" in flags,
            "fingerprint_flags": flags
        }

    def _is_spoofed(self, data: Dict) -> bool:
        """Detect fingerprint spoofing"""
        # Implementation: Check for inconsistencies
        return False

    def _is_known_fraud_device(self, data: Dict) -> bool:
        """Check if device is in fraud database"""
        # Implementation: Query Redis/DB
        return False

    def _is_emulator(self, data: Dict) -> bool:
        """Detect Android emulator"""
        gpu = data.get("gpu_info", "").lower()
        return "goldfish" in gpu or "ranchu" in gpu
```

---

### 3. `app/core/fraud_detector_v2.py` (780 lines)

**Purpose:** Enhanced fraud detector combining ML + rules

**Key Features:**
- Combines rule-based (273 rules) + ML predictions
- Weighted scoring (60% rules, 40% ML)
- Ensemble decision making
- Explainability (which rules + ML contributed)

**Key Implementation:**

```python
from app.services.ml_detector import MLFraudDetector
from app.services.rules.base import FraudRulesEngine

class FraudDetectorV2:
    """Enhanced fraud detector with ML + rules"""

    def __init__(self):
        self.rule_engine = FraudRulesEngine()
        self.ml_detector = MLFraudDetector()
        self.redis = RedisService()

    def check_transaction(self, request: TransactionCheckRequest) -> Dict:
        """
        Check transaction using both rules and ML

        Scoring: 60% rule-based, 40% ML-based
        """

        # 1. Build context
        context = self._build_context(request)

        # 2. Run rule engine
        rule_flags = self.rule_engine.evaluate_transaction(context)
        rule_score = sum(flag["score"] for flag in rule_flags)

        # 3. Run ML detector
        ml_result = self.ml_detector.predict(context)
        ml_score = ml_result["ml_score"]

        # 4. Ensemble scoring (weighted average)
        final_score = int((rule_score * 0.6) + (ml_score * 0.4))

        # 5. Determine risk level and status
        risk_level = self._calculate_risk_level(final_score)
        status = self._determine_status(final_score)

        # 6. Build response with explainability
        return {
            "transaction_id": str(uuid.uuid4()),
            "fraud_score": final_score,
            "risk_level": risk_level,
            "status": status,
            "rule_score": rule_score,
            "ml_score": ml_score,
            "ml_probability": ml_result["fraud_probability"],
            "flags": rule_flags,
            "ml_risk_factors": ml_result["risk_factors"],
            "message": self._get_message(status),
            "timestamp": datetime.utcnow()
        }
```

---

### 4. `app/middleware/rate_limit.py` (95 lines)

**Purpose:** Rate limiting middleware

```python
from fastapi import Request, HTTPException
from app.services.redis_service import RedisService

async def rate_limit_middleware(request: Request, call_next):
    """Rate limit API requests by API key"""

    redis = RedisService()
    api_key = request.headers.get("X-API-Key")

    if api_key:
        # Check rate limit (100 requests per minute)
        key = f"rate_limit:{api_key}"
        count = redis.redis.incr(key)

        if count == 1:
            redis.redis.expire(key, 60)  # 1 minute window

        if count > 100:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded (100 req/min)"
            )

    response = await call_next(request)
    return response
```

---

## Testing with curl

### Test 1: ML-Based Fraud Detection

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "ml_test_user",
    "amount": 500000,
    "transaction_type": "withdrawal",
    "industry": "fintech",
    "account_age_days": 5,
    "is_vpn": true,
    "transactions_last_hour": 8,
    "use_ml": true
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 75,
  "risk_level": "critical",
  "status": "declined",
  "rule_score": 85,
  "ml_score": 90,
  "ml_probability": 0.9,
  "flags": [
    {"flag_type": "high_velocity", "score": 30},
    {"flag_type": "vpn_detected", "score": 25},
    {"flag_type": "new_account_high_value", "score": 35}
  ],
  "ml_risk_factors": ["high_amount", "new_account", "vpn_usage"]
}
```

---

### Test 2: Device Fingerprinting

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "fingerprint_test",
    "amount": 100000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "canvas_fingerprint": "abc123xyz789",
    "webgl_fingerprint": "webgl456",
    "gpu_info": "goldfish"
  }'
```

**Expected:** Emulator detection flag triggered

---

### Test 3: Rate Limiting

```bash
# Send 105 requests rapidly
for i in {1..105}; do
  curl -X GET http://localhost:8000/health \
    -H "X-API-Key: dev-api-key-12345" &
done
wait
```

**Expected:** First 100 succeed, last 5 return 429 (Rate limit exceeded)

---

## Success Criteria

By the end of Week 3 (Month 3), you should have:

- ✅ ML fraud detector working with XGBoost
- ✅ Ensemble detector (rules + ML) functional
- ✅ Device fingerprinting detecting emulators/spoofing
- ✅ Rate limiting middleware working
- ✅ ML explainability (risk factors shown)

---

## Next Week Preview

**Week 4:** Remaining Services & Scripts
- Webhook notifications
- Continuous learning from feedback
- Prometheus monitoring
- Database initialization scripts
- Synthetic data generation

---

## File Checklist

Week 3 files to create:
- [ ] app/services/ml_detector.py
- [ ] app/services/fingerprint_rules.py
- [ ] app/core/fraud_detector_v2.py
- [ ] app/middleware/__init__.py
- [ ] app/middleware/rate_limit.py
- [ ] app/middleware/logging.py
- [ ] requirements.txt (in build_guides/month_03/week_03/)

---

**End of Week 3 Guide - Month 3**
